"""
Simple RAG test without complex LangChain integration
"""
import os
import sys

def test_basic_rag():
    """Test basic RAG functionality"""
    try:
        print("🚀 Testing basic RAG functionality...")
        
        # Test ChromaDB installation
        import chromadb
        print("✅ ChromaDB imported successfully")
        
        # Test sentence transformers
        from sentence_transformers import SentenceTransformer
        print("✅ SentenceTransformers imported successfully")
        
        # Test basic embedding
        model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        test_text = ["món ăn giảm cân", "chicken salad", "healthy food"]
        embeddings = model.encode(test_text)
        print(f"✅ Generated embeddings with shape: {embeddings.shape}")
        
        # Test ChromaDB basic operations
        client = chromadb.PersistentClient(path="./test_chromadb")
        collection = client.get_or_create_collection(name="test_collection")
        
        # Add some test data
        collection.add(
            documents=test_text,
            metadatas=[{"type": "food"}, {"type": "food"}, {"type": "food"}],
            ids=["1", "2", "3"],
            embeddings=embeddings.tolist()
        )
        
        # Test query
        query_embedding = model.encode(["món ăn lành mạnh"])
        results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=2
        )
        
        print(f"✅ Query results: {results['documents'][0]}")
        
        # Test CSV loading
        import pandas as pd
        if os.path.exists('interactions_encoded.csv'):
            df = pd.read_csv('interactions_encoded.csv')
            print(f"✅ Loaded CSV with {len(df)} rows")
        
        print("🎉 Basic RAG test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error in basic RAG test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_rag_integration():
    """Test RAG integration with existing system"""
    try:
        print("\n🔗 Testing RAG integration...")
        
        # Import our RAG components
        from rag_vector_db import RAGVectorDatabase
        print("✅ RAG Vector Database imported")
        
        # Initialize RAG DB
        rag_db = RAGVectorDatabase(use_gpu=False)  # Force CPU
        print("✅ RAG Database initialized")
        
        # Test search
        results = rag_db.search_similar("món ăn giảm cân", 'nutrition', n_results=3)
        print(f"✅ Search completed, found {len(results.get('documents', [[]])[0])} results")
        
        # Test stats
        stats = rag_db.get_collection_stats()
        print("✅ Database stats:")
        for collection, data in stats.items():
            if isinstance(data, dict) and 'document_count' in data:
                print(f"  {collection}: {data['document_count']} documents")
        
        print("🎉 RAG integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in RAG integration test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🧪 Starting RAG System Tests...")
    
    # Test 1: Basic functionality
    basic_success = test_basic_rag()
    
    # Test 2: Integration
    if basic_success:
        integration_success = test_rag_integration()
    else:
        integration_success = False
    
    # Summary
    print(f"\n📊 Test Results:")
    print(f"  Basic RAG: {'✅ PASS' if basic_success else '❌ FAIL'}")
    print(f"  Integration: {'✅ PASS' if integration_success else '❌ FAIL'}")
    
    if basic_success and integration_success:
        print("\n🎉 All RAG tests passed! System is ready.")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
