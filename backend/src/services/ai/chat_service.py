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
        """Gather relevant context based on query keywords"""
        context_parts = []
        
        # 1. Competitors Context
        # Simple keyword match for now
        comp_result = await db.execute(select(Competitor))
        competitors = comp_result.scalars().all()
        
        relevant_comps = []
        for comp in competitors:
            # If competitor name is in query or query asks about "all competitors"
            if comp.name.lower() in query.lower() or "competitor" in query.lower():
                relevant_comps.append(f"- {comp.name}: {comp.description}")
        
        if relevant_comps:
            context_parts.append(f"COMPETITORS DATA:\n" + "\n".join(relevant_comps))

        # 2. Recent Updates/News
        if "news" in query.lower() or "update" in query.lower() or "happening" in query.lower():
            updates_result = await db.execute(
                select(CompetitorUpdate).order_by(desc(CompetitorUpdate.created_at)).limit(5)
            )
            updates = updates_result.scalars().all()
            if updates:
                news_text = "\n".join([f"- {u.title} ({u.source})" for u in updates])
                context_parts.append(f"RECENT MARKET NEWS:\n{news_text}")

        # 3. Logs/System Health
        if "error" in query.lower() or "system" in query.lower() or "log" in query.lower() or "status" in query.lower():
            # Get error count
            error_count = await db.execute(
                select(LogAnomaly).where(LogAnomaly.is_anomaly == True).limit(5)
            )
            anomalies = error_count.scalars().all()
            if anomalies:
                logs_text = "\n".join([f"- {a.log_message[:100]} (Severity: {a.anomaly_score})" for a in anomalies])
                context_parts.append(f"SYSTEM HEALTH ALERTS:\n{logs_text}")
            else:
                context_parts.append("SYSTEM HEALTH: All systems operational. No recent anomalies.")
                
        # 4. Battlecards
        if "battlecard" in query.lower() or "pitch" in query.lower() or "kill" in query.lower():
             cards_result = await db.execute(select(Battlecard).limit(3))
             cards = cards_result.scalars().all()
             if cards:
                 cards_text = "\n".join([f"- Battlecard for {c.competitor_id}" for c in cards]) # optimizing join query would be better but keeping simple
                 context_parts.append(f"AVAILABLE BATTLECARDS:\n{cards_text}")

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
