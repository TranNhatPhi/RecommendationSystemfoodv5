#!/usr/bin/env python3
"""
GPU Optimized RAG Loader for 3GB GPU
Specifically designed for RTX 3050 Ti with memory management
"""

import os
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
import torch
import time
import gc
import warnings
from typing import Dict, List, Any
import psutil

# Suppress warnings
warnings.filterwarnings("ignore")
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

class GPUOptimizedRAGLoader:
    def __init__(self, features_dir: str = "./rag_features"):
        """Initialize GPU optimized RAG loader for 3GB GPU"""
        self.features_dir = features_dir
        
        # Memory management settings
        self.max_batch_size = 2  # Very small for 3GB GPU
        self.max_sequence_length = 256  # Shorter sequences
        
        # Setup device and model
        self.device = self._setup_optimized_device()
        self.embedding_model = self._setup_optimized_model()
        
        # Initialize ChromaDB
        self.client = self._setup_chromadb()
        self.collections = {}
        
        print("✅ GPU Optimized RAG Loader initialized")
    
    def _setup_optimized_device(self):
        """Setup device with GPU memory optimization"""
        if not torch.cuda.is_available():
            print("🔧 CUDA not available, using CPU")
            return 'cpu'
        
        # Check GPU memory
        gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory // 1024**3
        print(f"🚀 GPU: {torch.cuda.get_device_name(0)}")
        print(f"💾 GPU Memory: {gpu_memory_gb} GB")
        
        if gpu_memory_gb < 4:  # Less than 4GB
            print("⚠️ Limited GPU memory detected, using conservative settings")
            
            # Set memory fraction to prevent OOM
            torch.cuda.set_per_process_memory_fraction(0.7)  # Use only 70% of GPU memory
            
            # Enable memory optimization
            torch.backends.cudnn.benchmark = False
            torch.backends.cudnn.deterministic = True
            
        return 'cuda'
    
    def _setup_optimized_model(self):
        """Setup optimized embedding model for 3GB GPU"""
        print("🔧 Loading optimized embedding model...")
        
        try:
            if self.device == 'cuda':
                # Use smaller, more efficient model for limited GPU memory
                model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'  # Smaller model
                
                model = SentenceTransformer(model_name, device=self.device)
                
                # Set model to half precision to save memory
                if hasattr(model, 'half'):
                    model = model.half()
                
                print(f"✅ Embedding model loaded (GPU - optimized)")
                print(f"📏 Model: {model_name}")
                return model
            else:
                # CPU fallback
                model = SentenceTransformer(
                    'paraphrase-multilingual-mpnet-base-v2',
                    device='cpu'
                )
                print("✅ Embedding model loaded (CPU)")
                return model
                
        except Exception as e:
            print(f"⚠️ GPU model failed: {str(e)}")
            print("🔄 Falling back to CPU...")
            
            model = SentenceTransformer(
                'paraphrase-multilingual-mpnet-base-v2',
                device='cpu'
            )
            self.device = 'cpu'
            print("✅ Embedding model loaded (CPU fallback)")
            return model
    
    def _setup_chromadb(self):
        """Setup ChromaDB with optimization"""
        print("🔧 Initializing ChromaDB...")
        
        try:
            # Use in-memory for better performance with small datasets
            client = chromadb.Client()
            print("✅ ChromaDB initialized (in-memory)")
            return client
        except Exception as e:
            print(f"❌ ChromaDB initialization failed: {str(e)}")
            raise e
    
    def _clear_gpu_memory(self):
        """Clear GPU memory"""
        if self.device == 'cuda':
            torch.cuda.empty_cache()
            gc.collect()
    
    def _get_memory_info(self):
        """Get current memory usage"""
        if self.device == 'cuda':
            gpu_memory = torch.cuda.memory_allocated() / 1024**3
            gpu_cached = torch.cuda.memory_reserved() / 1024**3
            return f"GPU: {gpu_memory:.2f}GB allocated, {gpu_cached:.2f}GB cached"
        else:
            ram_usage = psutil.virtual_memory().percent
            return f"RAM: {ram_usage:.1f}% used"
    
    def load_feature_optimized(self, feature_name: str, csv_file: str, 
                             text_column: str) -> Dict[str, Any]:
        """Load feature with GPU memory optimization"""
        
        print(f"\n📊 Loading: {feature_name}")
        print(f"💾 Memory before: {self._get_memory_info()}")
        
        try:
            # Load CSV
            csv_path = os.path.join(self.features_dir, csv_file)
            if not os.path.exists(csv_path):
                return {'success': False, 'error': f'File not found'}
            
            df = pd.read_csv(csv_path)
            print(f"📈 Rows: {len(df)}")
            
            if text_column not in df.columns:
                return {'success': False, 'error': f'Column {text_column} not found'}
            
            # Create collection
            collection_name = f"rag_{feature_name}"
            
            # Clean up existing collection
            existing_collections = [col.name for col in self.client.list_collections()]
            if collection_name in existing_collections:
                self.client.delete_collection(collection_name)
            
            collection = self.client.create_collection(collection_name)
            self.collections[feature_name] = collection
            
            # Prepare documents with memory optimization
            documents = []
            metadatas = []
            ids = []
            
            for idx, row in df.iterrows():
                text = str(row[text_column]) if pd.notna(row[text_column]) else ""
                
                # Truncate very long texts to save memory
                if len(text) > self.max_sequence_length * 4:  # Rough character estimate
                    text = text[:self.max_sequence_length * 4] + "..."
                
                if len(text.strip()) < 5:
                    continue
                
                documents.append(text)
                
                # Minimal metadata to save memory
                metadata = {
                    'feature_type': feature_name,
                    'row_index': str(idx)
                }
                
                # Only add essential metadata
                key_columns = ['customer_id', 'recipe_name', 'rating', 'difficulty', 'meal_time']
                for col in key_columns:
                    if col in df.columns and pd.notna(row[col]):
                        metadata[col] = str(row[col])[:50]  # Limit length
                
                metadatas.append(metadata)
                ids.append(f"{feature_name}_{idx}")
            
            print(f"📝 Valid documents: {len(documents)}")
            
            if not documents:
                return {'success': False, 'error': 'No valid documents'}
            
            # Process in micro-batches for GPU memory management
            total_added = 0
            batch_size = self.max_batch_size
            
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_metas = metadatas[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]
                
                batch_num = i // batch_size + 1
                total_batches = (len(documents) + batch_size - 1) // batch_size
                
                try:
                    print(f"  ⚡ Batch {batch_num}/{total_batches} ({len(batch_docs)} docs)")
                    
                    # Clear memory before processing
                    self._clear_gpu_memory()
                    
                    # Generate embeddings with memory optimization
                    start_time = time.time()
                    
                    if self.device == 'cuda':
                        # Process one document at a time for very limited memory
                        embeddings_list = []
                        for doc in batch_docs:
                            with torch.no_grad():  # Disable gradient computation
                                emb = self.embedding_model.encode(
                                    [doc],
                                    convert_to_tensor=False,
                                    show_progress_bar=False,
                                    batch_size=1,
                                    normalize_embeddings=True  # Normalize to save space
                                )
                                embeddings_list.append(emb[0])
                            self._clear_gpu_memory()  # Clear after each document
                        
                        embeddings = embeddings_list
                    else:
                        # CPU processing
                        embeddings = self.embedding_model.encode(
                            batch_docs,
                            convert_to_tensor=False,
                            show_progress_bar=False,
                            batch_size=batch_size
                        )
                    
                    embed_time = time.time() - start_time
                    
                    # Add to ChromaDB
                    start_time = time.time()
                    
                    # Ensure embeddings are in correct format
                    if isinstance(embeddings, list) and isinstance(embeddings[0], (list, tuple)):
                        # Already in list format
                        embeddings_list = embeddings
                    elif hasattr(embeddings, 'tolist'):
                        # Numpy array
                        embeddings_list = embeddings.tolist()
                    else:
                        # Convert to list format
                        embeddings_list = [emb.tolist() if hasattr(emb, 'tolist') else emb for emb in embeddings]
                    
                    collection.add(
                        documents=batch_docs,
                        embeddings=embeddings_list,
                        metadatas=batch_metas,
                        ids=batch_ids
                    )
                    add_time = time.time() - start_time
                    
                    total_added += len(batch_docs)
                    
                    print(f"    ✅ Embed: {embed_time:.2f}s, Add: {add_time:.2f}s")
                    print(f"    💾 Memory: {self._get_memory_info()}")
                    
                    # Force memory cleanup every few batches
                    if batch_num % 10 == 0:
                        self._clear_gpu_memory()
                        time.sleep(0.1)  # Small pause to let GPU recover
                    
                except Exception as e:
                    print(f"    ❌ Batch {batch_num} failed: {str(e)}")
                    self._clear_gpu_memory()
                    continue
            
            # Final cleanup
            self._clear_gpu_memory()
            
            print(f"✅ {feature_name}: {total_added} documents loaded")
            print(f"💾 Memory after: {self._get_memory_info()}")
            
            return {
                'success': True,
                'feature_name': feature_name,
                'total_documents': total_added,
                'collection_name': collection_name
            }
            
        except Exception as e:
            print(f"❌ Error loading {feature_name}: {str(e)}")
            self._clear_gpu_memory()
            return {'success': False, 'error': str(e)}
    
    def load_all_features_optimized(self) -> Dict[str, Any]:
        """Load all features with GPU optimization"""
        print("🚀 Loading all features with GPU optimization...")
        
        # Prioritize smaller features first to manage memory
        features = {
            'recipes': ('recipes.csv', 'recipe_text'),
            'nutrition_info': ('nutrition_info.csv', 'nutrition_text'),
            'customer_profiles': ('customer_profiles.csv', 'profile_text'),
            'customer_demographics': ('customer_demographics.csv', 'demographic_text'),
            'customer_interactions': ('customer_interactions.csv', 'interaction_text'),
            'recommendation_scores': ('recommendation_scores.csv', 'recommendation_text')
        }
        
        results = {}
        total_docs = 0
        start_time = time.time()
        
        for feature_name, (csv_file, text_col) in features.items():
            print(f"\n🔄 Starting {feature_name}...")
            
            # Clear everything before each feature
            self._clear_gpu_memory()
            
            result = self.load_feature_optimized(feature_name, csv_file, text_col)
            results[feature_name] = result
            
            if result.get('success'):
                total_docs += result.get('total_documents', 0)
                print(f"✅ {feature_name} completed successfully")
            else:
                print(f"❌ {feature_name} failed: {result.get('error', 'Unknown error')}")
            
            # Pause between features to let GPU cool down
            time.sleep(1)
        
        total_time = time.time() - start_time
        
        print(f"\n🎉 All features processing completed!")
        print(f"⏱️ Total time: {total_time:.2f}s")
        print(f"📚 Total collections: {len(self.collections)}")
        print(f"📄 Total documents: {total_docs}")
        print(f"💾 Final memory: {self._get_memory_info()}")
        
        return results
    
    def test_search_optimized(self, query: str = "món ăn Việt Nam") -> Dict[str, Any]:
        """Test search with memory optimization"""
        print(f"\n🔍 Testing search: '{query}'")
        
        results = {}
        
        for feature_name, collection in self.collections.items():
            try:
                count = collection.count()
                if count == 0:
                    continue
                
                # Clear memory before search
                self._clear_gpu_memory()
                
                # Search with memory optimization
                with torch.no_grad():
                    query_embedding = self.embedding_model.encode(
                        [query], 
                        convert_to_tensor=False,
                        show_progress_bar=False
                    )
                
                search_results = collection.query(
                    query_embeddings=query_embedding.tolist(),
                    n_results=min(3, count)
                )
                
                if search_results['documents'][0]:
                    results[feature_name] = {
                        'count': len(search_results['documents'][0]),
                        'sample': search_results['documents'][0][0][:100] + "..."
                    }
                    print(f"  ✅ {feature_name}: {len(search_results['documents'][0])} results")
                
                # Clear memory after search
                self._clear_gpu_memory()
                
            except Exception as e:
                print(f"  ❌ {feature_name}: {str(e)}")
                self._clear_gpu_memory()
        
        return results

def main():
    """Main function optimized for 3GB GPU"""
    print("🎯 GPU Optimized RAG Loader for 3GB GPU")
    print("=" * 50)
    
    try:
        # Initialize optimized loader
        loader = GPUOptimizedRAGLoader()
        
        # Load all features with optimization
        results = loader.load_all_features_optimized()
        
        # Show results summary
        successful = [name for name, result in results.items() if result.get('success')]
        failed = [name for name, result in results.items() if not result.get('success')]
        
        print(f"\n📊 Final Results:")
        print(f"✅ Successful features: {len(successful)}")
        for name in successful:
            docs = results[name].get('total_documents', 0)
            print(f"   - {name}: {docs} documents")
        
        if failed:
            print(f"❌ Failed features: {len(failed)}")
            for name in failed:
                error = results[name].get('error', 'Unknown')
                print(f"   - {name}: {error}")
        
        # Test search if we have successful collections
        if successful:
            print("\n🔍 Testing search functionality...")
            test_results = loader.test_search_optimized("món ăn Việt Nam truyền thống")
            
            if test_results:
                print("✅ Search test completed successfully")
            else:
                print("⚠️ No search results found")
        
        return loader
        
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
        return None

if __name__ == "__main__":
    loader = main()
