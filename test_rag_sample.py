"""
Load CSV data into ChromaDB RAG system with smaller batches
"""
import os
import pandas as pd
from rag_vector_db import RAGVectorDatabase

def load_sample_interactions():
    """Load a sample of interactions data for testing"""
    print("🚀 Loading sample interactions data into RAG system...")
    
    # Initialize RAG database
    rag_db = RAGVectorDatabase(use_gpu=False)
    
    # Load a small sample first
    if os.path.exists('interactions_encoded.csv'):
        print("📁 Loading sample from interactions_encoded.csv...")
        try:
            df = pd.read_csv('interactions_encoded.csv')
            # Take only first 100 rows for testing
            sample_df = df.head(100)
            sample_df.to_csv('sample_interactions.csv', index=False)
            
            print(f"📊 Processing {len(sample_df)} sample interactions...")
            rag_db.add_interactions_from_csv('sample_interactions.csv', batch_size=20)
            print("✅ Sample interactions loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading interactions: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠️ interactions_encoded.csv not found")
    
    # Check stats
    stats = rag_db.get_collection_stats()
    print("\n📊 Database Stats after loading:")
    for collection, data in stats.items():
        if isinstance(data, dict) and 'document_count' in data:
            print(f"  {collection}: {data['document_count']} documents")
    
    return rag_db

def test_rag_search(rag_db):
    """Test RAG search functionality"""
    print("\n🔍 Testing RAG search...")
    
    test_queries = [
        "món ăn ngon",
        "giao thức dinh dưỡng", 
        "đánh giá cao",
        "món Việt Nam"
    ]
    
    for query in test_queries:
        print(f"\n❓ Searching for: '{query}'")
        
        # Search in interactions
        try:
            results = rag_db.search_similar(query, 'interactions', n_results=2)
            docs = results.get('documents', [[]])[0]
            metas = results.get('metadatas', [[]])[0]
            
            if docs:
                print(f"✅ Found {len(docs)} results in interactions:")
                for i, (doc, meta) in enumerate(zip(docs, metas)):
                    print(f"  {i+1}. Customer: {meta.get('customer_id', 'N/A')}")
                    print(f"      Recipe: {meta.get('recipe_name', 'N/A')}")
                    print(f"      Rating: {meta.get('rating', 'N/A')}")
                    print(f"      Content: {doc[:100]}...")
            else:
                print("❌ No results found in interactions")
                
        except Exception as e:
            print(f"❌ Error searching interactions: {str(e)}")
        
        # Search in nutrition knowledge
        try:
            results = rag_db.search_similar(query, 'nutrition', n_results=2)
            docs = results.get('documents', [[]])[0]
            metas = results.get('metadatas', [[]])[0]
            
            if docs:
                print(f"✅ Found {len(docs)} results in nutrition:")
                for i, (doc, meta) in enumerate(zip(docs, metas)):
                    print(f"  {i+1}. Topic: {meta.get('topic', 'N/A')}")
                    print(f"      Category: {meta.get('category', 'N/A')}")
                    print(f"      Content: {doc[:100]}...")
            else:
                print("❌ No results found in nutrition")
                
        except Exception as e:
            print(f"❌ Error searching nutrition: {str(e)}")

def main():
    """Main function"""
    print("🚀 Starting RAG system with sample data...")
    
    # Load sample data
    rag_db = load_sample_interactions()
    
    # Test search
    test_rag_search(rag_db)
    
    print("\n✅ RAG system test with sample data completed!")
    print("\n💡 To load full dataset, increase batch_size gradually and monitor memory usage.")

if __name__ == "__main__":
    main()
