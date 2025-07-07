#!/usr/bin/env python3
"""
RAG Feature Loader - Load split features into ChromaDB with GPU acceleration
"""

import os
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
import torch
import json
import time
from typing import Dict, List, Any
from datetime import datetime

class RAGFeatureLoader:
    def __init__(self, features_dir: str = "./rag_features", use_gpu: bool = True):
        """Initialize RAG feature loader"""
        self.features_dir = features_dir
        self.use_gpu = use_gpu and torch.cuda.is_available()
        
        # Setup device
        self.device = 'cuda' if self.use_gpu else 'cpu'
        print(f"🚀 Initializing RAG Feature Loader on device: {self.device}")
        
        if self.use_gpu:
            print(f"🎯 GPU: {torch.cuda.get_device_name(0)}")
            print(f"💾 GPU Memory: {torch.cuda.get_device_properties(0).total_memory // 1024**3} GB")
        
        # Initialize embedding model
        print("🔧 Loading embedding model...")
        try:
            self.embedding_model = SentenceTransformer(
                'paraphrase-multilingual-mpnet-base-v2',
                device=self.device
            )
            # Disable flash attention warnings
            import warnings
            warnings.filterwarnings("ignore", message=".*flash attention.*")
            print("✅ Embedding model loaded")
        except Exception as e:
            print(f"⚠️ GPU model failed: {str(e)}")
            print("🔄 Falling back to CPU...")
            self.device = 'cpu'
            self.use_gpu = False
            self.embedding_model = SentenceTransformer(
                'paraphrase-multilingual-mpnet-base-v2',
                device='cpu'
            )
            print("✅ Embedding model loaded (CPU)")
        
        # Initialize ChromaDB
        print("🔧 Initializing ChromaDB...")
        try:
            # Try persistent client first
            chroma_dir = "./chroma_rag_db"
            os.makedirs(chroma_dir, exist_ok=True)
            self.client = chromadb.PersistentClient(path=chroma_dir)
            print(f"✅ ChromaDB initialized (persistent): {chroma_dir}")
        except Exception as e:
            print(f"⚠️ Persistent client failed: {str(e)}")
            print("🔄 Using in-memory client...")
            self.client = chromadb.Client()
            print("✅ ChromaDB initialized (in-memory)")
        
        self.collections = {}
        
        # Load features summary if available
        self.features_summary = self._load_features_summary()
    
    def _load_features_summary(self) -> Dict[str, Any]:
        """Load features summary"""
        summary_file = os.path.join(self.features_dir, "features_summary.json")
        if os.path.exists(summary_file):
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                print(f"📋 Loaded features summary: {len(summary.get('features', {}))} features")
                return summary
            except Exception as e:
                print(f"⚠️ Error loading features summary: {str(e)}")
        
        return {'features': {}}
    
    def load_feature_to_chromadb(self, feature_name: str, csv_file: str, 
                                text_column: str, id_column: str = None,
                                batch_size: int = 32) -> Dict[str, Any]:
        """Load a single feature CSV into ChromaDB"""
        
        print(f"\n📊 Loading feature: {feature_name}")
        print(f"📁 File: {csv_file}")
        print(f"📝 Text column: {text_column}")
        
        try:
            # Load CSV
            csv_path = os.path.join(self.features_dir, csv_file)
            if not os.path.exists(csv_path):
                return {'success': False, 'error': f'File not found: {csv_path}'}
            
            df = pd.read_csv(csv_path)
            print(f"📈 Loaded {len(df)} rows")
            
            # Check text column exists
            if text_column not in df.columns:
                return {'success': False, 'error': f'Text column {text_column} not found'}
            
            # Create or get collection
            collection_name = f"rag_{feature_name}"
            try:
                # Delete existing collection if it exists
                existing_collections = [col.name for col in self.client.list_collections()]
                if collection_name in existing_collections:
                    self.client.delete_collection(collection_name)
                    print(f"🗑️ Deleted existing collection: {collection_name}")
            except Exception as e:
                print(f"⚠️ Note: {str(e)}")
            
            # Create new collection
            collection = self.client.create_collection(collection_name)
            self.collections[feature_name] = collection
            print(f"✅ Created collection: {collection_name}")
            
            # Prepare data
            documents = []
            metadatas = []
            ids = []
            
            for idx, row in df.iterrows():
                # Get text content
                text_content = str(row[text_column]) if pd.notna(row[text_column]) else ""
                if not text_content.strip():
                    continue
                
                documents.append(text_content)
                
                # Create metadata from all other columns
                metadata = {}
                for col in df.columns:
                    if col != text_column and pd.notna(row[col]):
                        # Convert to string and handle special types
                        value = row[col]
                        if isinstance(value, (int, float)):
                            metadata[col] = str(value)
                        else:
                            metadata[col] = str(value)[:500]  # Limit metadata length
                
                metadata['feature_type'] = feature_name
                metadata['row_index'] = str(idx)
                metadatas.append(metadata)
                
                # Generate ID
                if id_column and id_column in df.columns and pd.notna(row[id_column]):
                    doc_id = f"{feature_name}_{row[id_column]}"
                else:
                    doc_id = f"{feature_name}_{idx}"
                ids.append(doc_id)
            
            print(f"📝 Prepared {len(documents)} documents")
            
            if not documents:
                return {'success': False, 'error': 'No valid documents to process'}
            
            # Process in batches with GPU
            total_added = 0
            total_embed_time = 0
            total_add_time = 0
            
            for i in range(0, len(documents), batch_size):
                batch_end = min(i + batch_size, len(documents))
                batch_docs = documents[i:batch_end]
                batch_metas = metadatas[i:batch_end]
                batch_ids = ids[i:batch_end]
                
                batch_num = i // batch_size + 1
                total_batches = (len(documents) + batch_size - 1) // batch_size
                print(f"⚡ Processing batch {batch_num}/{total_batches} ({len(batch_docs)} docs)")
                
                # Generate embeddings with GPU
                start_time = time.time()
                try:
                    embeddings = self.embedding_model.encode(
                        batch_docs,
                        convert_to_tensor=False,
                        show_progress_bar=False,
                        batch_size=min(batch_size, 8)  # Limit GPU batch size further
                    )
                    embed_time = time.time() - start_time
                    total_embed_time += embed_time
                    
                    # Add to ChromaDB
                    start_time = time.time()
                    collection.add(
                        documents=batch_docs,
                        embeddings=embeddings.tolist(),
                        metadatas=batch_metas,
                        ids=batch_ids
                    )
                    add_time = time.time() - start_time
                    total_add_time += add_time
                    
                    total_added += len(batch_docs)
                    print(f"  ✅ Embedded: {embed_time:.2f}s, Added: {add_time:.2f}s")
                    
                    # Clear GPU cache periodically
                    if self.use_gpu and batch_num % 5 == 0:
                        torch.cuda.empty_cache()
                        print("  🧹 GPU cache cleared")
                    
                except Exception as e:
                    print(f"  ❌ Batch {batch_num} failed: {str(e)}")
                    continue
            
            # Final GPU cleanup
            if self.use_gpu:
                torch.cuda.empty_cache()
            
            print(f"✅ Feature '{feature_name}' loaded successfully!")
            print(f"   📊 Total documents: {total_added}")
            print(f"   ⏱️ Total embedding time: {total_embed_time:.2f}s")
            print(f"   ⏱️ Total ChromaDB time: {total_add_time:.2f}s")
            print(f"   📈 Avg embedding speed: {total_added/total_embed_time:.1f} docs/sec")
            
            return {
                'success': True,
                'feature_name': feature_name,
                'collection_name': collection_name,
                'total_documents': total_added,
                'embedding_time': total_embed_time,
                'add_time': total_add_time,
                'source_file': csv_file
            }
            
        except Exception as e:
            print(f"❌ Error loading feature '{feature_name}': {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def load_all_features(self, batch_size: int = 8) -> Dict[str, Any]:
        """Load all features from summary"""
        print("🚀 Loading all features into ChromaDB...")
        
        results = {}
        total_start_time = time.time()
        
        # Define feature configurations
        feature_configs = {
            'customer_profiles': {
                'file': 'customer_profiles.csv',
                'text_column': 'profile_text',
                'id_column': 'customer_id'
            },
            'customer_demographics': {
                'file': 'customer_demographics.csv', 
                'text_column': 'demographic_text',
                'id_column': 'customer_id'
            },
            'recipes': {
                'file': 'recipes.csv',
                'text_column': 'recipe_text',
                'id_column': 'recipe_name'
            },
            'nutrition_info': {
                'file': 'nutrition_info.csv',
                'text_column': 'nutrition_text', 
                'id_column': 'recipe_name'
            },
            'customer_interactions': {
                'file': 'customer_interactions.csv',
                'text_column': 'interaction_text',
                'id_column': None
            },
            'recommendation_scores': {
                'file': 'recommendation_scores.csv',
                'text_column': 'recommendation_text',
                'id_column': None
            }
        }
        
        # Load each feature
        for feature_name, config in feature_configs.items():
            result = self.load_feature_to_chromadb(
                feature_name=feature_name,
                csv_file=config['file'],
                text_column=config['text_column'],
                id_column=config['id_column'],
                batch_size=batch_size
            )
            results[feature_name] = result
        
        total_time = time.time() - total_start_time
        
        # Summary
        print(f"\n🎉 All features loading completed!")
        print(f"⏱️ Total time: {total_time:.2f}s")
        
        successful_features = [name for name, result in results.items() if result.get('success')]
        failed_features = [name for name, result in results.items() if not result.get('success')]
        
        print(f"✅ Successful features: {len(successful_features)}")
        for name in successful_features:
            docs = results[name].get('total_documents', 0)
            print(f"   - {name}: {docs} documents")
        
        if failed_features:
            print(f"❌ Failed features: {len(failed_features)}")
            for name in failed_features:
                error = results[name].get('error', 'Unknown error')
                print(f"   - {name}: {error}")
        
        results['summary'] = {
            'total_time': total_time,
            'successful_features': successful_features,
            'failed_features': failed_features,
            'total_successful': len(successful_features),
            'total_failed': len(failed_features)
        }
        
        return results
    
    def test_collections(self) -> Dict[str, Any]:
        """Test all loaded collections"""
        print("\n🔍 Testing loaded collections...")
        
        test_results = {}
        test_queries = [
            "món ăn Việt Nam truyền thống",
            "khách hàng ở Hồ Chí Minh", 
            "món ăn giảm cân ít calo",
            "thông tin dinh dưỡng protein",
            "gợi ý món ăn phù hợp"
        ]
        
        for collection_name, collection in self.collections.items():
            print(f"\n📊 Testing collection: {collection_name}")
            
            try:
                # Get collection stats
                count = collection.count()
                print(f"   📈 Documents: {count}")
                
                if count == 0:
                    test_results[collection_name] = {'status': 'empty', 'count': 0}
                    continue
                
                # Test queries
                collection_results = []
                for query in test_queries[:2]:  # Test first 2 queries per collection
                    try:
                        query_embedding = self.embedding_model.encode([query], convert_to_tensor=False)
                        results = collection.query(
                            query_embeddings=query_embedding.tolist(),
                            n_results=min(3, count)
                        )
                        
                        if results['documents'][0]:
                            collection_results.append({
                                'query': query,
                                'results_count': len(results['documents'][0]),
                                'sample_result': results['documents'][0][0][:100] + "..."
                            })
                            print(f"   ✅ Query '{query}': {len(results['documents'][0])} results")
                        else:
                            print(f"   ⚠️ Query '{query}': No results")
                            
                    except Exception as e:
                        print(f"   ❌ Query '{query}' failed: {str(e)}")
                
                test_results[collection_name] = {
                    'status': 'success',
                    'count': count,
                    'test_queries': collection_results
                }
                
            except Exception as e:
                print(f"   ❌ Collection test failed: {str(e)}")
                test_results[collection_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return test_results
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        stats = {
            'gpu_enabled': self.use_gpu,
            'device': self.device,
            'collections': {},
            'total_documents': 0,
            'embedding_model': 'paraphrase-multilingual-mpnet-base-v2'
        }
        
        if self.use_gpu:
            stats['gpu_name'] = torch.cuda.get_device_name(0)
            stats['gpu_memory_gb'] = torch.cuda.get_device_properties(0).total_memory // 1024**3
        
        for name, collection in self.collections.items():
            try:
                count = collection.count()
                stats['collections'][name] = count
                stats['total_documents'] += count
            except Exception as e:
                stats['collections'][name] = f"Error: {str(e)}"
        
        return stats

def main():
    """Main function to load features"""
    print("🎯 RAG Feature Loader with GPU + ChromaDB")
    print("=" * 50)
    
    # Initialize loader
    loader = RAGFeatureLoader(use_gpu=True)
    
    # Load all features
    results = loader.load_all_features(batch_size=8)
    
    # Test collections
    test_results = loader.test_collections()
    
    # Show system stats
    stats = loader.get_system_stats()
    print(f"\n📊 System Statistics:")
    print(f"   🎯 GPU: {stats['gpu_enabled']}")
    print(f"   📱 Device: {stats['device']}")
    if stats.get('gpu_name'):
        print(f"   🚀 GPU: {stats['gpu_name']}")
    print(f"   📚 Collections: {len(stats['collections'])}")
    print(f"   📄 Total documents: {stats['total_documents']}")
    
    return loader, results, test_results, stats

if __name__ == "__main__":
    loader, results, test_results, stats = main()
