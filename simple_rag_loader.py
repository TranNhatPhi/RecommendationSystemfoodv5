#!/usr/bin/env python3
"""
Simple RAG Loader - Load features with robust error handling
"""

import os
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
import torch
import time
import warnings
from typing import Dict, List, Any

# Suppress warnings
warnings.filterwarnings("ignore")

class SimpleRAGLoader:
    def __init__(self, features_dir: str = "./rag_features"):
        """Initialize simple RAG loader"""
        self.features_dir = features_dir
        
        # Setup device with fallback
        self.device = self._setup_device()
        
        # Initialize embedding model
        self.embedding_model = self._setup_embedding_model()
        
        # Initialize ChromaDB (in-memory for reliability)
        print("🔧 Initializing ChromaDB...")
        self.client = chromadb.Client()
        self.collections = {}
        print("✅ ChromaDB initialized (in-memory)")
    
    def _setup_device(self):
        """Setup computing device with fallback"""
        # Force CPU for stability
        print("🔧 Using CPU for stability")
        return 'cpu'
    
    def _setup_embedding_model(self):
        """Setup embedding model with fallback"""
        print("🔧 Loading embedding model...")
        
        try:
            # Try GPU first
            if self.device == 'cuda':
                model = SentenceTransformer(
                    'paraphrase-multilingual-mpnet-base-v2',
                    device='cuda'
                )
                print("✅ Embedding model loaded (GPU)")
                return model
        except Exception as e:
            print(f"⚠️ GPU loading failed: {str(e)}")
        
        # Fallback to CPU
        try:
            model = SentenceTransformer(
                'paraphrase-multilingual-mpnet-base-v2',
                device='cpu'
            )
            self.device = 'cpu'
            print("✅ Embedding model loaded (CPU)")
            return model
        except Exception as e:
            print(f"❌ Model loading failed: {str(e)}")
            raise e
    
    def load_single_feature(self, feature_name: str, csv_file: str, 
                           text_column: str, batch_size: int = 4) -> Dict[str, Any]:
        """Load single feature with robust error handling"""
        
        print(f"\n📊 Loading: {feature_name}")
        
        try:
            # Load CSV
            csv_path = os.path.join(self.features_dir, csv_file)
            if not os.path.exists(csv_path):
                return {'success': False, 'error': f'File not found: {csv_path}'}
            
            df = pd.read_csv(csv_path)
            print(f"📈 Rows: {len(df)}")
            
            if text_column not in df.columns:
                return {'success': False, 'error': f'Column {text_column} not found'}
            
            # Create collection
            collection_name = f"rag_{feature_name}"
            if collection_name in [col.name for col in self.client.list_collections()]:
                self.client.delete_collection(collection_name)
            
            collection = self.client.create_collection(collection_name)
            self.collections[feature_name] = collection
            
            # Prepare documents
            documents = []
            metadatas = []
            ids = []
            
            for idx, row in df.iterrows():
                text = str(row[text_column]) if pd.notna(row[text_column]) else ""
                if len(text.strip()) < 10:  # Skip very short texts
                    continue
                
                documents.append(text)
                
                # Simple metadata
                metadata = {
                    'feature_type': feature_name,
                    'row_index': str(idx)
                }
                
                # Add key columns as metadata
                for col in df.columns:
                    if col != text_column and pd.notna(row[col]):
                        value = str(row[col])[:200]  # Limit length
                        metadata[col] = value
                
                metadatas.append(metadata)
                ids.append(f"{feature_name}_{idx}")
            
            print(f"📝 Valid documents: {len(documents)}")
            
            if not documents:
                return {'success': False, 'error': 'No valid documents'}
            
            # Process in small batches
            total_added = 0
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_metas = metadatas[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]
                
                try:
                    # Generate embeddings
                    embeddings = self.embedding_model.encode(
                        batch_docs,
                        convert_to_tensor=False,
                        show_progress_bar=False,
                        batch_size=1  # Very conservative
                    )
                    
                    # Add to collection
                    collection.add(
                        documents=batch_docs,
                        embeddings=embeddings.tolist(),
                        metadatas=batch_metas,
                        ids=batch_ids
                    )
                    
                    total_added += len(batch_docs)
                    print(f"  ✅ Batch {i//batch_size + 1}: {len(batch_docs)} docs")
                    
                    # Clear GPU cache if using GPU
                    if self.device == 'cuda':
                        torch.cuda.empty_cache()
                        
                except Exception as e:
                    print(f"  ❌ Batch {i//batch_size + 1} failed: {str(e)}")
                    continue
            
            print(f"✅ {feature_name}: {total_added} documents loaded")
            
            return {
                'success': True,
                'feature_name': feature_name,
                'total_documents': total_added,
                'collection_name': collection_name
            }
            
        except Exception as e:
            print(f"❌ Error loading {feature_name}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def load_all_features(self) -> Dict[str, Any]:
        """Load all features"""
        print("🚀 Loading all features...")
        
        features = {
            'customer_profiles': ('customer_profiles.csv', 'profile_text'),
            'customer_demographics': ('customer_demographics.csv', 'demographic_text'),
            'recipes': ('recipes.csv', 'recipe_text'),
            'nutrition_info': ('nutrition_info.csv', 'nutrition_text'),
            'customer_interactions': ('customer_interactions.csv', 'interaction_text'),
            'recommendation_scores': ('recommendation_scores.csv', 'recommendation_text')
        }
        
        results = {}
        total_docs = 0
        
        for feature_name, (csv_file, text_col) in features.items():
            result = self.load_single_feature(feature_name, csv_file, text_col, batch_size=4)
            results[feature_name] = result
            
            if result.get('success'):
                total_docs += result.get('total_documents', 0)
        
        print(f"\n🎉 Loading completed!")
        print(f"📚 Total collections: {len(self.collections)}")
        print(f"📄 Total documents: {total_docs}")
        
        return results
    
    def test_search(self, query: str = "món ăn Việt Nam") -> Dict[str, Any]:
        """Test search across collections"""
        print(f"\n🔍 Testing search: '{query}'")
        
        results = {}
        
        for feature_name, collection in self.collections.items():
            try:
                count = collection.count()
                if count == 0:
                    continue
                
                # Search
                query_embedding = self.embedding_model.encode([query], convert_to_tensor=False)
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
                
            except Exception as e:
                print(f"  ❌ {feature_name}: {str(e)}")
        
        return results

def main():
    """Main function"""
    print("🎯 Simple RAG Feature Loader")
    print("=" * 40)
    
    # Initialize loader
    loader = SimpleRAGLoader()
    
    # Load all features
    results = loader.load_all_features()
    
    # Show results
    successful = [name for name, result in results.items() if result.get('success')]
    failed = [name for name, result in results.items() if not result.get('success')]
    
    print(f"\n📊 Results:")
    print(f"✅ Successful: {len(successful)}")
    for name in successful:
        docs = results[name].get('total_documents', 0)
        print(f"   - {name}: {docs} docs")
    
    if failed:
        print(f"❌ Failed: {len(failed)}")
        for name in failed:
            error = results[name].get('error', 'Unknown')
            print(f"   - {name}: {error}")
    
    # Test search
    if successful:
        test_results = loader.test_search("món ăn Việt Nam truyền thống")
    
    return loader

if __name__ == "__main__":
    loader = main()
