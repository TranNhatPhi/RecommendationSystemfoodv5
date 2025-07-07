"""
Load CSV data into ChromaDB RAG system
"""
import os
import pandas as pd
from rag_vector_db import RAGVectorDatabase

def load_interactions_data():
    """Load interactions data into RAG system"""
    print("🚀 Loading interactions data into RAG system...")
    
    # Initialize RAG database
    rag_db = RAGVectorDatabase(use_gpu=False)  # Use CPU
    
    # Load interactions data
    if os.path.exists('interactions_encoded.csv'):
        print("📁 Loading interactions_encoded.csv...")
        try:
            rag_db.add_interactions_from_csv('interactions_encoded.csv', batch_size=50)
            print("✅ Interactions data loaded successfully")
        except Exception as e:
            print(f"❌ Error loading interactions: {str(e)}")
    else:
        print("⚠️ interactions_encoded.csv not found")
    
    # Check stats
    stats = rag_db.get_collection_stats()
    print("\n📊 Database Stats after loading:")
    for collection, data in stats.items():
        if isinstance(data, dict) and 'document_count' in data:
            print(f"  {collection}: {data['document_count']} documents")
    
    return rag_db

def test_rag_queries(rag_db):
    """Test RAG queries with loaded data"""
    print("\n🔍 Testing RAG queries...")
    
    test_queries = [
        ("món ăn giảm cân", "nutrition"),
        ("gợi ý món ăn", "interactions"), 
        ("món ngon", "interactions"),
        ("dinh dưỡng", "nutrition")
    ]
    
    for query, collection in test_queries:
        print(f"\n❓ Query: '{query}' in {collection}")
        try:
            results = rag_db.search_similar(query, collection, n_results=3)
            docs = results.get('documents', [[]])[0]
            metas = results.get('metadatas', [[]])[0]
            
            if docs:
                print(f"✅ Found {len(docs)} results:")
                for i, (doc, meta) in enumerate(zip(docs[:2], metas[:2])):
                    print(f"  {i+1}. {doc[:100]}...")
                    if meta.get('recipe_name'):
                        print(f"     Recipe: {meta['recipe_name']}")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Error querying: {str(e)}")

def main():
    """Main function"""
    print("🚀 Starting CSV to RAG loading process...")
    
    # Load data
    rag_db = load_interactions_data()
    
    # Test queries
    test_rag_queries(rag_db)
    
    print("\n✅ CSV to RAG loading completed!")

if __name__ == "__main__":
    main()
