#!/usr/bin/env python3
"""
Simple GPU-accelerated test for ChromaDB loading
"""

import pandas as pd
import numpy as np
from rag_vector_db import RAGVectorDatabase
import torch
import time

def simple_test():
    """Simple test to verify GPU-accelerated ChromaDB loading"""
    print("🧪 Simple GPU ChromaDB Test...")
    
    # Initialize RAG database
    rag_db = RAGVectorDatabase(use_gpu=True)
    
    # Test with small sample data first
    print(f"🎯 GPU Available: {torch.cuda.is_available()}")
    print(f"💾 GPU Memory Available: {torch.cuda.get_device_properties(0).total_memory // 1024**2} MB")
    
    # Create test data
    test_data = [
        "Phở bò Hà Nội truyền thống với nước dùng trong, thịt bò tái",
        "Bánh mì thịt nướng với pate và rau sống",
        "Cơm tấm sườn nướng với chả trứng và bì",
        "Bún chả Hà Nội với thịt nướng thơm ngon",
        "Gỏi cuốn tôm thịt với nước chấm đậm đà"
    ]
    
    test_metadata = [
        {"recipe_name": "Phở bò", "meal_time": "breakfast", "calories": 350},
        {"recipe_name": "Bánh mì", "meal_time": "breakfast", "calories": 400},
        {"recipe_name": "Cơm tấm", "meal_time": "lunch", "calories": 600},
        {"recipe_name": "Bún chả", "meal_time": "lunch", "calories": 450},
        {"recipe_name": "Gỏi cuốn", "meal_time": "snack", "calories": 200}
    ]
    
    test_ids = [f"test_{i}" for i in range(len(test_data))]
    
    try:
        # Generate embeddings with GPU
        print("⚡ Generating embeddings...")
        start_time = time.time()
        
        with torch.cuda.device(0):
            embeddings = rag_db.embedding_model.encode(
                test_data,
                convert_to_tensor=False,
                show_progress_bar=True,
                batch_size=16
            )
        
        embedding_time = time.time() - start_time
        print(f"✅ Embeddings generated in {embedding_time:.2f}s")
        print(f"📊 Embedding shape: {np.array(embeddings).shape}")
        
        # Add to ChromaDB
        print("💾 Adding to ChromaDB...")
        start_time = time.time()
        
        try:
            collection = rag_db.collections['recipes']
            
            # Convert embeddings to proper format
            if hasattr(embeddings, 'numpy'):
                embeddings_list = embeddings.numpy().tolist()
            elif hasattr(embeddings, 'tolist'):
                embeddings_list = embeddings.tolist()
            else:
                embeddings_list = embeddings
            
            print(f"📊 Embeddings type: {type(embeddings)}, shape: {np.array(embeddings).shape}")
            
            # Add one by one to debug
            for i in range(len(test_data)):
                collection.add(
                    documents=[test_data[i]],
                    embeddings=[embeddings_list[i]],
                    metadatas=[test_metadata[i]],
                    ids=[test_ids[i]]
                )
                print(f"  ✅ Added item {i+1}")
            
            db_time = time.time() - start_time
            print(f"✅ Added to ChromaDB in {db_time:.2f}s")
            
        except Exception as e:
            print(f"❌ ChromaDB error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test search
        print("🔍 Testing search...")
        search_query = "món ăn sáng Việt Nam"
        results = rag_db.search_similar(search_query, 'recipes', n_results=3)
        
        print(f"Search results for '{search_query}':")
        if results['documents'][0]:
            for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                print(f"  {i+1}. {meta['recipe_name']}: {doc[:60]}...")
        
        # Clear GPU cache
        torch.cuda.empty_cache()
        
        print("✅ Simple test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    simple_test()
