#!/usr/bin/env python3
"""
Minimal RAG Test - Just to verify everything works
"""

import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer

def minimal_test():
    print("🧪 Minimal RAG Test")
    
    try:
        # Test 1: ChromaDB
        print("1️⃣ Testing ChromaDB...")
        client = chromadb.Client()
        collection = client.create_collection("test")
        print("   ✅ ChromaDB OK")
        
        # Test 2: SentenceTransformers
        print("2️⃣ Testing SentenceTransformers...")
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device='cpu')
        print("   ✅ SentenceTransformers OK")
        
        # Test 3: Simple embedding
        print("3️⃣ Testing embedding generation...")
        test_texts = ["món phở ngon", "bánh mì thịt"]
        embeddings = model.encode(test_texts)
        print(f"   ✅ Generated embeddings: {embeddings.shape}")
        
        # Test 4: Add to ChromaDB
        print("4️⃣ Testing ChromaDB add...")
        collection.add(
            documents=test_texts,
            embeddings=embeddings.tolist(),
            ids=["doc1", "doc2"]
        )
        print("   ✅ ChromaDB add OK")
        
        # Test 5: Search
        print("5️⃣ Testing search...")
        query_embedding = model.encode(["món ăn Việt Nam"])
        results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=2
        )
        print(f"   ✅ Search OK, found: {len(results['documents'][0])} results")
        
        print("\n🎉 All tests passed! RAG system is working.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def load_one_feature():
    print("\n📊 Testing with real data...")
    
    try:
        # Load one small CSV
        csv_path = "./rag_features/recipes.csv"
        df = pd.read_csv(csv_path)
        print(f"📈 Loaded {len(df)} recipes")
        
        # Setup
        client = chromadb.Client()
        collection = client.create_collection("recipes_test")
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device='cpu')
        
        # Take first 5 recipes
        sample_docs = df['recipe_text'].head(5).tolist()
        print(f"📝 Processing {len(sample_docs)} sample recipes")
        
        # Generate embeddings
        embeddings = model.encode(sample_docs)
        print(f"🔢 Generated embeddings: {embeddings.shape}")
        
        # Add to ChromaDB
        collection.add(
            documents=sample_docs,
            embeddings=embeddings.tolist(),
            ids=[f"recipe_{i}" for i in range(len(sample_docs))]
        )
        print("✅ Added to ChromaDB")
        
        # Test search
        query = "món ăn Việt Nam"
        query_embedding = model.encode([query])
        results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=3
        )
        
        print(f"\n🔍 Search results for '{query}':")
        for i, doc in enumerate(results['documents'][0]):
            print(f"  {i+1}. {doc[:80]}...")
        
        print("\n✅ Feature loading test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Feature test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 RAG System Verification")
    print("=" * 40)
    
    # Run minimal test first
    if minimal_test():
        # If basic test passes, try with real data
        load_one_feature()
    else:
        print("❌ Basic tests failed, check your setup")
