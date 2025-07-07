#!/usr/bin/env python3
"""
GPU-Accelerated CSV to ChromaDB Loader
Loads CSV files into ChromaDB with GPU acceleration for faster embedding generation
"""

import pandas as pd
import numpy as np
from rag_vector_db import RAGVectorDatabase
import torch
import time
from typing import List, Dict
import os
import json
from datetime import datetime

class GPUChromaDBLoader:
    def __init__(self, rag_db: RAGVectorDatabase):
        self.rag_db = rag_db
        self.use_gpu = rag_db.use_gpu
        
    def chunk_text_data(self, texts: List[str], chunk_size: int = 512) -> List[str]:
        """Chunk long texts into smaller pieces for better embeddings"""
        chunked_texts = []
        
        for text in texts:
            if len(text) <= chunk_size:
                chunked_texts.append(text)
            else:
                # Split into chunks
                words = text.split()
                current_chunk = []
                current_length = 0
                
                for word in words:
                    word_length = len(word) + 1  # +1 for space
                    if current_length + word_length > chunk_size and current_chunk:
                        chunked_texts.append(' '.join(current_chunk))
                        current_chunk = [word]
                        current_length = word_length
                    else:
                        current_chunk.append(word)
                        current_length += word_length
                
                if current_chunk:
                    chunked_texts.append(' '.join(current_chunk))
        
        return chunked_texts
    
    def load_csv_to_chromadb(self, csv_path: str, collection_name: str, 
                           text_columns: List[str], metadata_columns: List[str] = None,
                           chunk_size: int = 512, batch_size: int = None) -> Dict:
        """Load CSV data to ChromaDB with GPU acceleration"""
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        print(f"📊 Loading CSV: {csv_path}")
        df = pd.read_csv(csv_path)
        print(f"📈 Loaded {len(df)} rows")
        
        # Set batch size based on GPU availability
        if batch_size is None:
            batch_size = self.rag_db.batch_size
        
        if metadata_columns is None:
            metadata_columns = [col for col in df.columns if col not in text_columns]
        
        # Prepare data
        documents = []
        metadatas = []
        ids = []
        
        for idx, row in df.iterrows():
            # Combine text columns
            text_content = " | ".join([str(row[col]) for col in text_columns if pd.notna(row[col])])
            
            if not text_content.strip():
                continue
            
            # Chunk the text if it's too long
            chunked_texts = self.chunk_text_data([text_content], chunk_size)
            
            for chunk_idx, chunk in enumerate(chunked_texts):
                documents.append(chunk)
                
                # Create metadata
                metadata = {}
                for col in metadata_columns:
                    if col in row and pd.notna(row[col]):
                        metadata[col] = str(row[col])
                
                metadata['source_row'] = int(idx)
                metadata['chunk_index'] = chunk_idx
                metadata['total_chunks'] = len(chunked_texts)
                
                metadatas.append(metadata)
                ids.append(f"{collection_name}_{idx}_{chunk_idx}")
        
        print(f"📝 Prepared {len(documents)} chunks from {len(df)} rows")
        
        # Get or create collection
        if collection_name not in self.rag_db.collections:
            print(f"🆕 Creating new collection: {collection_name}")
            self.rag_db.collections[collection_name] = self.rag_db.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        
        collection = self.rag_db.collections[collection_name]
        
        # Process in batches with GPU acceleration
        print(f"🚀 Processing in batches of {batch_size} (GPU: {self.use_gpu})")
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        for batch_idx in range(0, len(documents), batch_size):
            batch_end = min(batch_idx + batch_size, len(documents))
            batch_docs = documents[batch_idx:batch_end]
            batch_metas = metadatas[batch_idx:batch_end]
            batch_ids = ids[batch_idx:batch_end]
            
            print(f"⚡ Processing batch {batch_idx//batch_size + 1}/{total_batches} ({len(batch_docs)} items)")
            
            try:
                # Generate embeddings with GPU
                start_time = time.time()
                
                with torch.cuda.device(0) if self.use_gpu else torch.no_grad():
                    embeddings = self.rag_db.embedding_model.encode(
                        batch_docs,
                        convert_to_tensor=False,
                        show_progress_bar=False,
                        batch_size=batch_size if self.use_gpu else 16
                    )
                
                embedding_time = time.time() - start_time
                print(f"  📊 Embeddings generated in {embedding_time:.2f}s")
                
                # Add to ChromaDB
                start_time = time.time()
                collection.add(
                    documents=batch_docs,
                    embeddings=embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings,
                    metadatas=batch_metas,
                    ids=batch_ids
                )
                
                db_time = time.time() - start_time
                print(f"  💾 Added to DB in {db_time:.2f}s")
                
                # Clear GPU cache if using CUDA
                if self.use_gpu:
                    torch.cuda.empty_cache()
                
            except Exception as e:
                print(f"❌ Error processing batch {batch_idx//batch_size + 1}: {str(e)}")
                continue
        
        # Get final collection stats
        stats = {
            'collection_name': collection_name,
            'total_documents': collection.count(),
            'source_file': csv_path,
            'source_rows': len(df),
            'chunks_created': len(documents),
            'gpu_used': self.use_gpu,
            'batch_size': batch_size
        }
        
        print(f"✅ Loaded {stats['total_documents']} documents to collection '{collection_name}'")
        return stats

def load_food_data():
    """Load all food-related CSV files to ChromaDB"""
    print("🍽️ Starting GPU-accelerated food data loading...")
    
    # Initialize RAG database with GPU
    rag_db = RAGVectorDatabase(use_gpu=True)
    loader = GPUChromaDBLoader(rag_db)
    
    # Data files and their configurations
    data_configs = [
        {
            'file': 'customers_data.csv',
            'collection': 'customers',
            'text_columns': ['full_name', 'region'],
            'metadata_columns': ['customer_id', 'gender', 'age_group', 'registration_date']
        },
        {
            'file': 'food_recipes_enhanced.csv',
            'collection': 'recipes',
            'text_columns': ['recipe_name', 'difficulty', 'meal_time', 'nutrition_category'],
            'metadata_columns': ['recipe_url', 'estimated_calories', 'preparation_time_minutes', 
                               'ingredient_count', 'estimated_price_vnd', 'avg_rating']
        },
        {
            'file': 'customer_interactions_enhanced.csv',
            'collection': 'interactions',
            'text_columns': ['recipe_name', 'difficulty', 'meal_time', 'nutrition_category', 'comment'],
            'metadata_columns': ['customer_id', 'recipe_url', 'rating', 'interaction_type', 
                               'interaction_date', 'estimated_calories']
        }
    ]
    
    results = {}
    total_start_time = time.time()
    
    for config in data_configs:
        file_path = config['file']
        
        if os.path.exists(file_path):
            print(f"\n📂 Processing {file_path}...")
            try:
                stats = loader.load_csv_to_chromadb(
                    csv_path=file_path,
                    collection_name=config['collection'],
                    text_columns=config['text_columns'],
                    metadata_columns=config.get('metadata_columns'),
                    chunk_size=512,
                    batch_size=64 if rag_db.use_gpu else 16
                )
                results[config['collection']] = stats
                
            except Exception as e:
                print(f"❌ Error loading {file_path}: {str(e)}")
                results[config['collection']] = {'error': str(e)}
        else:
            print(f"⚠️ File not found: {file_path}")
            results[config['collection']] = {'error': 'File not found'}
    
    total_time = time.time() - total_start_time
    
    # Summary
    print(f"\n🎉 Data loading complete in {total_time:.2f} seconds!")
    print("\n📊 Summary:")
    for collection, stats in results.items():
        if 'error' not in stats:
            print(f"  {collection}: {stats['total_documents']} documents")
        else:
            print(f"  {collection}: ERROR - {stats['error']}")
    
    # Save loading report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_time_seconds': total_time,
        'gpu_used': rag_db.use_gpu,
        'device_info': torch.cuda.get_device_name(0) if rag_db.use_gpu else 'CPU',
        'collections': results
    }
    
    with open('rag_loading_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Loading report saved to: rag_loading_report.json")
    
    return results, rag_db

if __name__ == "__main__":
    results, rag_db = load_food_data()
    
    # Test some queries
    print("\n🔍 Testing some sample queries...")
    test_queries = [
        "món ăn Việt Nam truyền thống",
        "món ăn ít calo giảm cân",
        "khách hàng ở Hà Nội",
        "món ăn cho người tiểu đường"
    ]
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        for collection_name in ['recipes', 'interactions', 'customers']:
            if collection_name in rag_db.collections:
                try:
                    results = rag_db.search_similar(query, collection_name, n_results=2)
                    if results['documents'][0]:
                        print(f"  📚 {collection_name}: {results['documents'][0][0][:100]}...")
                except Exception as e:
                    print(f"  ❌ {collection_name}: Error - {str(e)}")
