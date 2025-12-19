from typing import List, Dict, Optional
import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, text
from src.core.config import settings
from src.models.competitor import Competitor, CompetitorUpdate
from src.models.battlecard import Battlecard
from src.models.log_anomaly import LogAnomaly

class UnifiedChatService:
    """
    Central brain for the platform.
    Aggregates data from Competitors, Battlecards, and Logs to answer user queries.
    """
    
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    async def _get_context(self, db: AsyncSession, query: str) -> str:
        """Gather deep context based on query relevance"""
        context_parts = []
        query_lower = query.lower()
        
        # 1. Fetch all competitors to check for mentions
        comp_result = await db.execute(select(Competitor))
        competitors = comp_result.scalars().all()
        
        mentioned_competitors = []
        for comp in competitors:
            if comp.name.lower() in query_lower:
                mentioned_competitors.append(comp)

        # 2. Deep Context for Mentioned Competitors
        if mentioned_competitors:
            for comp in mentioned_competitors:
                # Basic Info
                details = [f"COMPETITOR: {comp.name}", f"Description: {comp.description}"]
                if comp.extra_data:
                    details.append(f"Metadata: {comp.extra_data}")
                
                # Fetch Battlecard (Strengths/Weaknesses)
                bc_result = await db.execute(
                    select(Battlecard).where(Battlecard.competitor_id == comp.id)
                )
                battlecard = bc_result.scalar_one_or_none()
                if battlecard:
                    details.append(f"STRENGTHS: {', '.join(battlecard.strengths or [])}")
                    details.append(f"WEAKNESSES: {', '.join(battlecard.weaknesses or [])}")
                    details.append(f"KILL POINTS: {', '.join(battlecard.kill_points or [])}")
                
                # Fetch Recent Updates
                updates_result = await db.execute(
                    select(CompetitorUpdate)
                    .where(CompetitorUpdate.competitor_id == comp.id)
                    .order_by(desc(CompetitorUpdate.created_at))
                    .limit(5)
                )
                updates = updates_result.scalars().all()
                if updates:
                    details.append("RECENT INTEL:")
                    for u in updates:
                        details.append(f"- [{u.update_type.upper()}] {u.title} ({u.summary[:100]}...)")
                
                context_parts.append("\n".join(details))
        
        else:
            # 3. Broad Context (if no specific competitor mentioned)
            # List all competitors briefly
            comps_summary = "\n".join([f"- {c.name}: {c.description}" for c in competitors[:10]])
            context_parts.append(f"TRACKED COMPETITORS:\n{comps_summary}")
            
            # Recent Market News (Global)
            updates_result = await db.execute(
                select(CompetitorUpdate).order_by(desc(CompetitorUpdate.created_at)).limit(5)
            )
            updates = updates_result.scalars().all()
            if updates:
                news = "\n".join([f"- {u.title} (re: {u.category})" for u in updates])
                context_parts.append(f"LATEST MARKET UPDATES:\n{news}")

        # 4. System Health (always relevant for 'status' queries)
        if "system" in query_lower or "log" in query_lower or "health" in query_lower:
             error_count = await db.execute(
                select(LogAnomaly).where(LogAnomaly.is_anomaly == True).order_by(desc(LogAnomaly.created_at)).limit(5)
            )
             anomalies = error_count.scalars().all()
             if anomalies:
                logs_text = "\n".join([f"- {a.log_message[:100]} (Severity: {a.anomaly_score})" for a in anomalies])
                context_parts.append(f"SYSTEM ALERTS:\n{logs_text}")

        return "\n\n".join(context_parts)

    async def answer_query(self, query: str, db: AsyncSession) -> str:
        """Generate an answer based on platform data"""
        
        # 1. Gather Context
        context = await self._get_context(db, query)
        
        if not context and len(query.split()) < 3:
             # Fallback context if nothing specific found
             context = "No specific data found in database matching keywords."

        # 2. Ask Gemini
        prompt = f"""
You are VigilAI, a Voice Assistant for a Competitive Intelligence Platform.
Your goal is to answer the user's question concisely using ONLY the provided data context.
If the answer is not in the context, say "I don't have that information right now."
Keep answers suitable for text-to-speech (short sentences, natural phrasing).

CONTEXT DATA:
{context}

USER QUERY:
{query}

ANSWER (Concise, speakable format):
"""
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            return f"I encountered an error processing that: {str(e)}"
