"""
Strategy Drift Detection Service
Analyzes vector embeddings over time to detect strategic shifts in competitor messaging.
"""
import logging
from typing import List, Dict, Any, Tuple
import numpy as np
from datetime import datetime, timedelta
from src.services.integrations.vector_db import VectorDBService
from src.services.ai.processor import AIProcessor

logger = logging.getLogger(__name__)

class StrategyDriftDetector:
    """Detects strategic drift using time-series vector analysis"""
    
    def __init__(self):
        self.vector_db = VectorDBService()
        self.ai = AIProcessor()
        
    async def detect_drift(self, competitor_id: int) -> Dict[str, Any]:
        """
        Analyze embeddings to detect strategic drift.
        Compares recent (last 30 days) vs historical (older than 30 days) vectors.
        """
        # Fetch all vectors for competitor
        vectors = self.vector_db.fetch_vectors(competitor_id, limit=500)
        
        if not vectors or len(vectors) < 5:
            return {"drift_detected": False, "reason": "Insufficient data"}
            
        # Split into recent and historical
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        recent_vectors = []
        historical_vectors = []
        
        recent_docs = []
        historical_docs = []
        
        for v in vectors:
            # Parse timestamp from metadata
            ts_str = v['metadata'].get('timestamp')
            if not ts_str:
                continue
                
            try:
                # Handle ISO format
                ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            except:
                continue
                
            if ts > cutoff_date:
                recent_vectors.append(v['embedding'])
                recent_docs.append(v['content'])
            else:
                historical_vectors.append(v['embedding'])
                historical_docs.append(v['content'])
                
        if not recent_vectors or not historical_vectors:
            return {"drift_detected": False, "reason": "Missing recent or historical data"}
            
        # Calculate centroids (average embedding)
        recent_centroid = np.mean(recent_vectors, axis=0)
        historical_centroid = np.mean(historical_vectors, axis=0)
        
        # Calculate Cosine Distance (1 - Cosine Similarity)
        # CosSim = (A . B) / (||A|| * ||B||)
        dot_product = np.dot(recent_centroid, historical_centroid)
        norm_a = np.linalg.norm(recent_centroid)
        norm_b = np.linalg.norm(historical_centroid)
        
        similarity = dot_product / (norm_a * norm_b)
        distance = 1 - similarity
        
        # Threshold for "Drift" (tuned empirically)
        DRIFT_THRESHOLD = 0.15 
        
        drift_detected = distance > DRIFT_THRESHOLD
        
        analysis = {}
        if drift_detected:
            # improve analysis by asking LLM to compare content samples
            analysis = await self._analyze_drift_reason(historical_docs[:5], recent_docs[:5])
            
        return {
            "drift_detected": drift_detected,
            "drift_score": float(distance),
            "threshold": DRIFT_THRESHOLD,
            "analysis": analysis,
            "recent_count": len(recent_vectors),
            "historical_count": len(historical_vectors)
        }

    async def _analyze_drift_reason(self, historical_texts: List[str], recent_texts: List[str]) -> Dict:
        """Use AI to explain WHY the drift happened."""
        
        prompt = f"""
        Analyze the strategic shift in this competitor's messaging.
        
        HISTORICAL MESSAGING (Older than 30 days):
        {self._format_texts(historical_texts)}
        
        RECENT MESSAGING (Last 30 days):
        {self._format_texts(recent_texts)}
        
        Identify:
        1. What changed in their focus? (e.g., moved from Feature A to Feature B, or SMB to Enterprise)
        2. New keywords or themes.
        3. Strategic implication.
        
        Format as JSON: {{ "shift_summary": "...", "key_changes": ["..."], "implication": "..." }}
        """
        
        try:
            return await self.ai._call_gemini(prompt) # Helper will return text, might need parsing
        except Exception as e:
            logger.error(f"Error analyzing drift reason: {e}")
            return {"error": "Could not analyze reason"}

    def _format_texts(self, texts: List[str]) -> str:
        return "\n".join([f"- {t[:200]}..." for t in texts])
