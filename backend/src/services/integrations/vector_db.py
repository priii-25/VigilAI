"""
Vector database service for RAG (Retrieval Augmented Generation)
Replacement of Pinecone with ChromaDB (Local & Free)
"""
from typing import Dict, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
import google.generativeai as genai
import numpy as np
from loguru import logger
from src.core.config import settings
import hashlib
from datetime import datetime
import os


class VectorDBService:
    """Vector database service using ChromaDB for semantic search and RAG"""
    
    def __init__(self):
        self.persist_directory = settings.VECTOR_DB_PATH
        self.collection_name = "vigilai_competitors"
        self.model = None # Not used
        self.client = None
        self.collection = None
        
        # Configure Gemini
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        self._initialize()
    
    def _initialize(self):
        """Initialize ChromaDB"""
        try:
            # Ensure directory exists
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialize ChromaDB Client
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            
            # Get or Create Collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info("Vector database (ChromaDB) initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing vector database: {str(e)}")
            self.client = None
            self.collection = None
    
    def embed_text(self, text: str) -> List[float]:
        """Convert text to vector embedding using Gemini"""
        try:
            # text-embedding-004 is current standard
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating embedding with Gemini: {str(e)}")
            return []
    
    def store_competitor_data(
        self,
        competitor_id: int,
        competitor_name: str,
        data: Dict,
        data_type: str
    ) -> bool:
        """
        Store competitor data in vector database
        """
        if not self.collection:
            logger.warning("Vector database not initialized")
            return False
        
        try:
            # Create searchable text from data
            text_content = self._extract_searchable_text(data, data_type)
            
            if not text_content:
                logger.warning("No searchable content extracted")
                return False
            
            # Generate embedding
            embedding = self.embed_text(text_content)
            
            if not embedding:
                return False
            
            # Generate unique ID
            vector_id = self._generate_vector_id(competitor_id, data_type, text_content)
            
            # Prepare metadata
            metadata = {
                "competitor_id": competitor_id,
                "competitor_name": competitor_name,
                "data_type": data_type,
                "timestamp": datetime.utcnow().isoformat(),
                "content_preview": text_content[:200]
            }
            
            # Store in ChromaDB
            self.collection.add(
                ids=[vector_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[text_content]
            )
            
            logger.info(f"Stored vector for {competitor_name} ({data_type})")
            return True
            
        except Exception as e:
            logger.error(f"Error storing vector data: {str(e)}")
            return False
    
    def search_similar_competitor_data(
        self,
        query: str,
        competitor_id: Optional[int] = None,
        data_type: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search for similar competitor data using semantic search
        """
        if not self.collection:
            logger.warning("Vector database not initialized")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embed_text(query)
            
            if not query_embedding:
                return []
            
            # Prepare filter
            where_filter = {}
            if competitor_id:
                where_filter["competitor_id"] = competitor_id
            if data_type:
                where_filter["data_type"] = data_type
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter if where_filter else None,
                include=["metadatas", "distances", "documents"]
            )
            
            # Format results
            formatted_results = []
            if results['ids']:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'score': 1 - results['distances'][0][i], # Convert distance to similarity
                        'metadata': results['metadatas'][0][i],
                        'id': results['ids'][0][i],
                        'content': results['documents'][0][i]
                    })
            
            logger.info(f"Found {len(formatted_results)} similar results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            return []
    
    def get_battlecard_context(
        self,
        competitor_id: int,
        query: str,
        max_context_length: int = 2000
    ) -> str:
        """
        Get relevant context for battlecard generation using RAG
        """
        if not self.collection:
            logger.warning("Vector database not available")
            return ""
        
        try:
            # Search for relevant data
            results = self.search_similar_competitor_data(
                query=query,
                competitor_id=competitor_id,
                top_k=5
            )
            
            # Concatenate context
            context_parts = []
            current_length = 0
            
            for result in results:
                metadata = result.get('metadata', {})
                content = metadata.get('content_preview', '') # Or use 'content' key if available
                if 'content' in result:
                     content = result['content']
                     
                data_type = metadata.get('data_type', '')
                
                # Add source label
                source_label = f"\n[{data_type.upper()}] "
                content_with_label = source_label + content
                
                # Check length
                if current_length + len(content_with_label) > max_context_length:
                    break
                
                context_parts.append(content_with_label)
                current_length += len(content_with_label)
            
            context = '\n'.join(context_parts)
            
            logger.info(f"Retrieved {len(context_parts)} context snippets ({current_length} chars)")
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving battlecard context: {str(e)}")
            return ""
    
    def _extract_searchable_text(self, data: Dict, data_type: str) -> str:
        """Extract searchable text from data based on type"""
        text_parts = []
        
        if data_type == 'pricing':
            plans = data.get('plans', [])
            for plan in plans:
                text_parts.append(f"Plan: {plan.get('name', '')}")
                text_parts.append(f"Price: {plan.get('price', '')}")
                features = plan.get('features', [])
                if features:
                    text_parts.append(f"Features: {' '.join(features[:5])}")
        
        elif data_type == 'hiring':
            jobs = data.get('job_postings', [])
            for job in jobs[:10]:
                text_parts.append(f"Role: {job.get('title', '')}")
                text_parts.append(f"Department: {job.get('department', '')}")
            
            trends = data.get('hiring_trends', {})
            if trends:
                text_parts.append(f"Hiring trends: {str(trends)}")
        
        elif data_type == 'review':
            reviews = data.get('reviews', [])
            for review in reviews[:5]:
                text_parts.append(review.get('title', ''))
                text_parts.append(review.get('text', ''))
                if review.get('pros'):
                    text_parts.append(f"Pros: {review['pros']}")
                if review.get('cons'):
                    text_parts.append(f"Cons: {review['cons']}")
        
        elif data_type == 'news':
            articles = data.get('articles', [])
            for article in articles:
                text_parts.append(article.get('title', ''))
                text_parts.append(article.get('summary', ''))
        
        elif data_type == 'content':
            articles = data.get('articles', [])
            for article in articles[:5]:
                text_parts.append(article.get('title', ''))
                text_parts.append(article.get('summary', ''))
        
        return ' '.join(text_parts)[:3000]  # Limit to 3000 chars
    
    def _generate_vector_id(self, competitor_id: int, data_type: str, content: str) -> str:
        """Generate unique vector ID"""
        # Create hash of content for uniqueness
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        
        return f"comp{competitor_id}_{data_type}_{timestamp}_{content_hash}"
    
    def delete_competitor_data(self, competitor_id: int) -> bool:
        """Delete all data for a competitor"""
        if not self.collection:
            return False
        
        try:
            self.collection.delete(
                where={"competitor_id": competitor_id}
            )
            
            logger.info(f"Deleted vector data for competitor {competitor_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vector data: {str(e)}")
            return False
    
    def get_stats(self) -> Dict:
        """Get vector database statistics"""
        if not self.collection:
            return {"status": "not_initialized"}
        
        try:
            count = self.collection.count()
            
            return {
                "status": "active",
                "total_vectors": count,
                "dimension": 768, # MPNet dimension
                "backend": "chromadb"
            }
            
        except Exception as e:
            logger.error(f"Error getting vector DB stats: {str(e)}")
            return {"status": "error", "message": str(e)}

    def fetch_vectors(
        self,
        competitor_id: int,
        limit: int = 100
    ) -> List[Dict]:
        """
        Fetch raw vectors and metadata for a competitor.
        Used for drift detection analysis.
        """
        if not self.collection:
            return []
            
        try:
            results = self.collection.get(
                where={"competitor_id": competitor_id},
                limit=limit,
                include=["embeddings", "metadatas", "documents"]
            )
            
            formatted = []
            if results['ids']:
                for i in range(len(results['ids'])):
                    formatted.append({
                        'id': results['ids'][i],
                        'embedding': results['embeddings'][i],
                        'metadata': results['metadatas'][i],
                        'content': results['documents'][i]
                    })
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error fetching vectors: {str(e)}")
            return []

# No longer need LocalVectorDB fallback as ChromaDB is local
