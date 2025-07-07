#!/usr/bin/env python3
"""
Minimal GPU ChromaDB test
"""

import chromadb
from sentence_transformers import SentenceTransformer
import torch
import numpy as np

def minimal_test():
    """Minimal test for ChromaDB + GPU"""
    print("🔬 Minimal ChromaDB + GPU Test...")
    
    # Check GPU
    print(f"🎯 GPU Available: {torch.cuda.is_available()}")
    
    # Initialize embedding model
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"🚀 Using device: {device}")
    
    model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2', device=device)
    
    # Test embeddings
    test_texts = [
        "Phở bò Hà Nội",
        "Bánh mì thịt nướng", 
        "Cơm tấm sườn"
    ]
    
    print("⚡ Generating embeddings...")
    embeddings = model.encode(test_texts, convert_to_tensor=False)
    print(f"✅ Embeddings shape: {embeddings.shape}")
    
    # Test ChromaDB
    print("💾 Testing ChromaDB...")
    try:
        # Use in-memory client
        client = chromadb.Client()
        collection = client.create_collection("test_recipes")
        
        # Add data
        collection.add(
            documents=test_texts,
            embeddings=embeddings.tolist(),
            ids=["recipe_1", "recipe_2", "recipe_3"]
        )
        
        print(f"✅ Added {collection.count()} documents")
        
        # Test query
        query_embedding = model.encode(["món ăn sáng"], convert_to_tensor=False)
        results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=2
        )
        
        print("🔍 Query results:")
        for i, doc in enumerate(results['documents'][0]):
            print(f"  {i+1}. {doc}")
        
        print("✅ Minimal test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    minimal_test()
