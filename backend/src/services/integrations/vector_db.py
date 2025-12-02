"""
Vector database service for RAG (Retrieval Augmented Generation)
Production-ready implementation with Pinecone
"""
from typing import Dict, List, Optional
import pinecone
from sentence_transformers import SentenceTransformer
import numpy as np
from loguru import logger
from src.core.config import settings
import hashlib
from datetime import datetime


class VectorDBService:
    """Vector database service for semantic search and RAG"""
    
    def __init__(self):
        self.api_key = settings.PINECONE_API_KEY
        self.environment = settings.PINECONE_ENVIRONMENT
        self.index_name = "vigilai-competitors"
        self.dimension = 768  # sentence-transformers dimension
        self.model = None
        self.index = None
        
        if self.api_key and self.environment:
            self._initialize()
    
    def _initialize(self):
        """Initialize Pinecone and embedding model"""
        try:
            # Initialize Pinecone
            pinecone.init(
                api_key=self.api_key,
                environment=self.environment
            )
            
            # Create index if it doesn't exist
            if self.index_name not in pinecone.list_indexes():
                logger.info(f"Creating Pinecone index: {self.index_name}")
                pinecone.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    metadata_config={
                        "indexed": ["competitor_id", "data_type", "timestamp"]
                    }
                )
            
            # Connect to index
            self.index = pinecone.Index(self.index_name)
            
            # Load embedding model
            logger.info("Loading embedding model...")
            self.model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
            
            logger.info("Vector database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing vector database: {str(e)}")
            self.index = None
    
    def embed_text(self, text: str) -> List[float]:
        """Convert text to vector embedding"""
        if not self.model:
            logger.warning("Embedding model not initialized")
            return []
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
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
        
        Args:
            competitor_id: ID of the competitor
            competitor_name: Name of the competitor
            data: Data to store (will be embedded)
            data_type: Type of data (pricing, hiring, review, etc.)
            
        Returns:
            Boolean indicating success
        """
        if not self.index:
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
            
            # Store in Pinecone
            self.index.upsert(
                vectors=[(vector_id, embedding, metadata)]
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
        
        Args:
            query: Search query
            competitor_id: Optional filter by competitor
            data_type: Optional filter by data type
            top_k: Number of results to return
            
        Returns:
            List of similar data with scores
        """
        if not self.index:
            logger.warning("Vector database not initialized")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embed_text(query)
            
            if not query_embedding:
                return []
            
            # Prepare filter
            filter_dict = {}
            if competitor_id:
                filter_dict["competitor_id"] = competitor_id
            if data_type:
                filter_dict["data_type"] = data_type
            
            # Search
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filter_dict if filter_dict else None,
                include_metadata=True
            )
            
            # Format results
            formatted_results = []
            for match in results.get('matches', []):
                formatted_results.append({
                    'score': match['score'],
                    'metadata': match['metadata'],
                    'id': match['id']
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
        
        Args:
            competitor_id: ID of the competitor
            query: Context query (e.g., "pricing strategy", "weaknesses")
            max_context_length: Maximum length of returned context
            
        Returns:
            Concatenated relevant context
        """
        if not self.index:
            logger.warning("Vector database not available, using fallback")
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
                content = metadata.get('content_preview', '')
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
        if not self.index:
            return False
        
        try:
            # Delete by filter (requires Pinecone paid plan)
            self.index.delete(
                filter={"competitor_id": competitor_id}
            )
            
            logger.info(f"Deleted vector data for competitor {competitor_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vector data: {str(e)}")
            return False
    
    def get_stats(self) -> Dict:
        """Get vector database statistics"""
        if not self.index:
            return {"status": "not_initialized"}
        
        try:
            stats = self.index.describe_index_stats()
            
            return {
                "status": "active",
                "total_vectors": stats.get('total_vector_count', 0),
                "dimension": stats.get('dimension', 0),
                "index_fullness": stats.get('index_fullness', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting vector DB stats: {str(e)}")
            return {"status": "error", "message": str(e)}


# Fallback implementation without Pinecone
class LocalVectorDB:
    """Simple local vector storage as fallback"""
    
    def __init__(self):
        self.vectors = []
        self.model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        logger.info("Using local vector storage (fallback)")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding"""
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return []
    
    def store_competitor_data(self, competitor_id: int, competitor_name: str, data: Dict, data_type: str) -> bool:
        """Store data locally"""
        try:
            text = str(data)[:1000]
            embedding = self.embed_text(text)
            
            self.vectors.append({
                'competitor_id': competitor_id,
                'competitor_name': competitor_name,
                'data_type': data_type,
                'embedding': embedding,
                'content': text,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            return True
        except Exception as e:
            logger.error(f"Error storing local vector: {str(e)}")
            return False
    
    def search_similar_competitor_data(self, query: str, competitor_id: Optional[int] = None, data_type: Optional[str] = None, top_k: int = 5) -> List[Dict]:
        """Search using cosine similarity"""
        try:
            query_embedding = np.array(self.embed_text(query))
            
            results = []
            for vec in self.vectors:
                # Apply filters
                if competitor_id and vec['competitor_id'] != competitor_id:
                    continue
                if data_type and vec['data_type'] != data_type:
                    continue
                
                # Calculate similarity
                vec_embedding = np.array(vec['embedding'])
                similarity = np.dot(query_embedding, vec_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(vec_embedding)
                )
                
                results.append({
                    'score': float(similarity),
                    'metadata': {
                        'competitor_id': vec['competitor_id'],
                        'competitor_name': vec['competitor_name'],
                        'data_type': vec['data_type'],
                        'content_preview': vec['content'][:200],
                        'timestamp': vec['timestamp']
                    }
                })
            
            # Sort by score
            results.sort(key=lambda x: x['score'], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching local vectors: {str(e)}")
            return []
