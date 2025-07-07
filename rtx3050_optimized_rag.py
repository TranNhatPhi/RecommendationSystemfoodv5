#!/usr/bin/env python3
"""
RTX 3050 Ti Optimized RAG System for Food Recommendation
Specifically designed for 3GB GPU memory with intelligent fallback to CPU
"""

import os
import gc
import torch
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np
import time
import psutil
from typing import List, Dict, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RTX3050RAGSystem:
    def __init__(self, features_dir: str = "./rag_features", use_gpu: bool = True):
        """
        Initialize RAG system optimized for RTX 3050 Ti (3GB VRAM)
        """
        self.features_dir = features_dir
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device = 'cuda' if self.use_gpu else 'cpu'
        self.batch_size = self._calculate_optimal_batch_size()
        
        logger.info("🚀 RTX 3050 Ti Optimized RAG System Starting...")
        logger.info(f"🔧 Device: {self.device}")
        
        if self.use_gpu:
            self._setup_gpu_monitoring()
        
        self._initialize_components()
        
    def _calculate_optimal_batch_size(self) -> int:
        """Calculate optimal batch size for RTX 3050 Ti"""
        if self.use_gpu:
            # Conservative batch size for 3GB VRAM
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            logger.info(f"🎮 GPU Memory: {gpu_memory:.1f}GB")
            
            if gpu_memory <= 3.5:  # RTX 3050 Ti
                return 16  # Small batch for 3GB
            elif gpu_memory <= 6:
                return 32
            else:
                return 64
        else:
            return 32  # CPU batch size
    
    def _setup_gpu_monitoring(self):
        """Setup GPU memory monitoring"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            logger.info(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"🎮 Total VRAM: {gpu_memory:.1f}GB")
            logger.info(f"📊 Batch Size: {self.batch_size}")
    
    def _monitor_memory(self) -> Dict[str, float]:
        """Monitor GPU and RAM usage"""
        memory_info = {
            'ram_percent': psutil.virtual_memory().percent,
            'ram_available_gb': psutil.virtual_memory().available / 1024**3
        }
        
        if self.use_gpu and torch.cuda.is_available():
            memory_info.update({
                'gpu_allocated_gb': torch.cuda.memory_allocated() / 1024**3,
                'gpu_reserved_gb': torch.cuda.memory_reserved() / 1024**3,
                'gpu_free_gb': (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_reserved()) / 1024**3
            })
        
        return memory_info
    
    def _initialize_components(self):
        """Initialize embedding model and ChromaDB with memory optimization"""
        try:
            logger.info("1️⃣ Loading embedding model...")
            
            # Use smaller, GPU-friendly model for RTX 3050 Ti
            model_name = 'all-MiniLM-L6-v2'  # Lighter model
            
            self.model = SentenceTransformer(
                model_name,
                device=self.device
            )
            
            # Optimize model for inference
            if self.use_gpu:
                self.model.eval()
                torch.cuda.empty_cache()
            
            logger.info(f"   ✅ Model loaded on {self.device}")
            
            # Initialize ChromaDB
            logger.info("2️⃣ Setting up ChromaDB...")
            self.client = chromadb.Client()
            self.collections = {}
            logger.info("   ✅ ChromaDB ready")
            
            # Memory check
            memory_info = self._monitor_memory()
            logger.info(f"💾 Memory after init: RAM {memory_info['ram_percent']:.1f}%")
            if self.use_gpu:
                logger.info(f"🎮 GPU allocated: {memory_info.get('gpu_allocated_gb', 0):.2f}GB")
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            # Fallback to CPU
            if self.use_gpu:
                logger.info("🔄 Falling back to CPU...")
                self.use_gpu = False
                self.device = 'cpu'
                self._initialize_components()
            else:
                raise
    
    def _batch_encode(self, texts: List[str]) -> np.ndarray:
        """Encode texts in batches with memory management"""
        embeddings = []
        total_batches = len(texts) // self.batch_size + (1 if len(texts) % self.batch_size else 0)
        
        logger.info(f"🔢 Encoding {len(texts)} texts in {total_batches} batches of {self.batch_size}")
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            
            try:
                # Monitor memory before encoding
                if self.use_gpu and batch_num % 5 == 1:  # Check every 5 batches
                    memory_info = self._monitor_memory()
                    if memory_info.get('gpu_free_gb', 0) < 0.5:  # Less than 500MB free
                        logger.warning("⚠️ Low GPU memory, cleaning cache...")
                        torch.cuda.empty_cache()
                        gc.collect()
                
                # Encode batch
                with torch.no_grad():
                    batch_embeddings = self.model.encode(
                        batch,
                        show_progress_bar=False,
                        convert_to_numpy=True,
                        normalize_embeddings=True
                    )
                
                embeddings.append(batch_embeddings)
                
                if batch_num % 10 == 0:
                    logger.info(f"   📊 Processed batch {batch_num}/{total_batches}")
                
                # Clear GPU cache periodically
                if self.use_gpu and batch_num % 5 == 0:
                    torch.cuda.empty_cache()
                
            except Exception as e:
                logger.error(f"❌ Batch {batch_num} failed: {e}")
                
                # Try to recover
                if self.use_gpu and "out of memory" in str(e).lower():
                    logger.warning("🔄 GPU OOM detected, switching to CPU...")
                    self.use_gpu = False
                    self.device = 'cpu'
                    self.model = self.model.to('cpu')
                    
                    # Retry with CPU
                    batch_embeddings = self.model.encode(
                        batch,
                        show_progress_bar=False,
                        convert_to_numpy=True,
                        normalize_embeddings=True
                    )
                    embeddings.append(batch_embeddings)
                else:
                    raise
        
        # Combine all embeddings
        if embeddings:
            all_embeddings = np.vstack(embeddings)
            logger.info(f"✅ Generated embeddings shape: {all_embeddings.shape}")
            return all_embeddings
        else:
            raise ValueError("No embeddings generated")
    
    def load_feature_optimized(self, feature_name: str, csv_file: str, text_column: str, max_records: int = 1000):
        """Load feature with RTX 3050 Ti optimizations"""
        logger.info(f"\n📊 Loading feature: {feature_name}")
        
        try:
            # Load CSV
            csv_path = os.path.join(self.features_dir, csv_file)
            if not os.path.exists(csv_path):
                logger.error(f"❌ File not found: {csv_path}")
                return False
            
            df = pd.read_csv(csv_path)
            logger.info(f"   📈 Loaded CSV: {len(df)} rows")
            
            # Check column
            if text_column not in df.columns:
                logger.error(f"❌ Column '{text_column}' not found")
                logger.info(f"Available columns: {list(df.columns)}")
                return False
            
            # Prepare documents
            documents = []
            metadata = []
            
            for idx, row in df.iterrows():
                if len(documents) >= max_records:
                    break
                
                text = str(row[text_column]) if pd.notna(row[text_column]) else ""
                if len(text.strip()) > 5:
                    # Truncate for memory efficiency
                    clean_text = text[:300] 
                    documents.append(clean_text)
                    
                    # Store metadata
                    meta = {'row_id': idx}
                    for col in df.columns:
                        if col != text_column and pd.notna(row[col]):
                            meta[col] = str(row[col])[:100]  # Limit metadata size
                    metadata.append(meta)
            
            logger.info(f"   📝 Valid documents: {len(documents)}")
            
            if len(documents) == 0:
                logger.warning("⚠️ No valid documents found")
                return False
            
            # Create collection
            collection_name = f"rag_{feature_name}"
            
            try:
                self.client.delete_collection(collection_name)
            except:
                pass
            
            collection = self.client.create_collection(collection_name)
            logger.info(f"   📚 Created collection: {collection_name}")
            
            # Generate embeddings with memory optimization
            logger.info("   🔢 Generating embeddings with RTX 3050 Ti optimization...")
            start_time = time.time()
            
            embeddings = self._batch_encode(documents)
            
            encoding_time = time.time() - start_time
            logger.info(f"   ⏱️ Encoding time: {encoding_time:.2f}s")
            
            # Add to ChromaDB
            logger.info("   💾 Adding to ChromaDB...")
            
            ids = [f"{feature_name}_{i}" for i in range(len(documents))]
            
            # Add in batches to ChromaDB
            chroma_batch_size = 100
            for i in range(0, len(documents), chroma_batch_size):
                end_idx = min(i + chroma_batch_size, len(documents))
                
                collection.add(
                    embeddings=embeddings[i:end_idx].tolist(),
                    documents=documents[i:end_idx],
                    metadatas=metadata[i:end_idx],
                    ids=ids[i:end_idx]
                )
            
            # Store collection reference
            self.collections[feature_name] = collection
            
            # Final memory check
            memory_info = self._monitor_memory()
            logger.info(f"✅ Feature '{feature_name}' loaded successfully!")
            logger.info(f"💾 Memory usage: RAM {memory_info['ram_percent']:.1f}%")
            if self.use_gpu:
                logger.info(f"🎮 GPU allocated: {memory_info.get('gpu_allocated_gb', 0):.2f}GB")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load {feature_name}: {e}")
            
            # Clean up on failure
            if self.use_gpu:
                torch.cuda.empty_cache()
            gc.collect()
            
            return False
    
    def search_optimized(self, collection_name: str, query: str, n_results: int = 5):
        """Search with GPU optimization"""
        if collection_name not in self.collections:
            logger.error(f"❌ Collection '{collection_name}' not found")
            return None
        
        try:
            logger.info(f"🔍 Searching in '{collection_name}' for: '{query[:50]}...'")
            
            # Generate query embedding
            with torch.no_grad():
                query_embedding = self.model.encode([query], normalize_embeddings=True)
            
            # Search in ChromaDB
            results = self.collections[collection_name].query(
                query_embeddings=query_embedding.tolist(),
                n_results=n_results
            )
            
            logger.info(f"✅ Found {len(results['documents'][0])} results")
            
            return {
                'documents': results['documents'][0],
                'metadatas': results['metadatas'][0],
                'distances': results['distances'][0]
            }
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return None
    
    def load_all_features(self):
        """Load all available features with RTX 3050 Ti optimization"""
        features_config = [
            ('recipes', 'recipes.csv', 'name'),
            ('nutrition', 'nutrition_info.csv', 'food_name'),
            ('customers', 'customer_profiles.csv', 'dietary_restrictions'),
            ('interactions', 'interactions.csv', 'food_item'),
            ('ingredients', 'ingredients.csv', 'ingredient_name')
        ]
        
        logger.info("🎯 Loading all features for RTX 3050 Ti...")
        
        success_count = 0
        for feature_name, csv_file, text_column in features_config:
            if self.load_feature_optimized(feature_name, csv_file, text_column, max_records=500):
                success_count += 1
            
            # Memory cleanup between features
            if self.use_gpu:
                torch.cuda.empty_cache()
            gc.collect()
            time.sleep(1)  # Brief pause
        
        logger.info(f"✅ Successfully loaded {success_count}/{len(features_config)} features")
        
        # Final memory status
        memory_info = self._monitor_memory()
        logger.info(f"🎮 Final GPU allocation: {memory_info.get('gpu_allocated_gb', 0):.2f}GB")
        logger.info(f"💾 Final RAM usage: {memory_info['ram_percent']:.1f}%")
        
        return success_count == len(features_config)
    
    def demo_search(self):
        """Demo search functionality"""
        logger.info("\n🔍 Demo: Searching across loaded features...")
        
        test_queries = [
            "healthy chicken recipe",
            "vegetarian protein",
            "low sodium food",
            "breakfast ideas"
        ]
        
        for query in test_queries:
            logger.info(f"\n🔎 Query: '{query}'")
            
            for collection_name in self.collections.keys():
                results = self.search_optimized(collection_name, query, n_results=3)
                if results:
                    logger.info(f"  📚 {collection_name}: {len(results['documents'])} results")
                    for i, (doc, distance) in enumerate(zip(results['documents'][:2], results['distances'][:2])):
                        logger.info(f"    {i+1}. {doc[:100]}... (similarity: {1-distance:.3f})")

def main():
    """Main function to run RTX 3050 Ti optimized RAG system"""
    try:
        # Initialize system
        rag_system = RTX3050RAGSystem(use_gpu=True)
        
        # Load all features
        success = rag_system.load_all_features()
        
        if success:
            logger.info("🎉 All features loaded successfully!")
            
            # Demo search
            rag_system.demo_search()
            
            logger.info("\n✅ RTX 3050 Ti RAG System ready for use!")
        else:
            logger.warning("⚠️ Some features failed to load")
        
    except Exception as e:
        logger.error(f"❌ System failed: {e}")
        raise

if __name__ == "__main__":
    main()
