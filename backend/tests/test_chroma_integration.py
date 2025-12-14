import sys
import os
import shutil

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Mock settings just in case environment variables aren't picked up correctly in test env
# But since we use default value in config.py for VECTOR_DB_PATH, it should be fine.

from src.services.integrations.vector_db import VectorDBService

def test_vector_db():
    print("Initializing VectorDBService with ChromaDB...")
    try:
        service = VectorDBService()
    except Exception as e:
        print(f"Failed to initialize: {e}")
        return

    # cleanup previous run if exists for clean test
    # service.client.reset() # ChromaDB reset is disabled by default usually
    
    # Test Data
    test_data = {
        "reviews": [{"title": "Great product", "text": "I love the new features.", "pros": "Fast", "cons": "Expensive"}]
    }
    
    # 1. Store Data
    print("Storing data...")
    success = service.store_competitor_data(
        competitor_id=999,
        competitor_name="Test Corp",
        data=test_data,
        data_type="review"
    )
    if not success:
        print("Failed to store data")
        exit(1)
    
    # 2. Search Data
    print("Searching data...")
    results = service.search_similar_competitor_data(query="features")
    print(f"Found {len(results)} results")
    if len(results) == 0:
        print("No results found")
        exit(1)
        
    print(f"Top result: {results[0]['content'][:50]}...")
    
    # 3. Stats
    stats = service.get_stats()
    print("Stats:", stats)
    if stats.get('total_vectors', 0) == 0:
        print("Stats reported 0 vectors")
        exit(1)
    
    # 4. Battlecard Context (RAG)
    print("Testing Battlecard Context RAG...")
    context = service.get_battlecard_context(999, "features")
    print(f"Context length: {len(context)}")
    if len(context) == 0:
        print("No context retrieved")
        exit(1)

    # 5. Delete Data
    print("Deleting data...")
    service.delete_competitor_data(999)
    stats_after = service.get_stats()
    print("Stats after delete:", stats_after)
    
    print("Test Complete & Successful!")

if __name__ == "__main__":
    test_vector_db()
