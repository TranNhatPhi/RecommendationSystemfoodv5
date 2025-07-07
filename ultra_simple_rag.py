#!/usr/bin/env python3
"""
Ultra Simple RAG Loader for 3GB GPU - Focus on stability and working solution
"""

import os
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
import torch
import numpy as np
import warnings

warnings.filterwarnings("ignore")

class UltraSimpleRAGLoader:
    def __init__(self, features_dir: str = "./rag_features"):
        self.features_dir = features_dir
        self.collections = {}
        
        # Setup in conservative mode
        print("🎯 Ultra Simple RAG Loader for 3GB GPU")
        
        # Force CPU for absolute stability
        self.device = 'cpu'
        print("🔧 Using CPU for maximum stability")
        
        # Load simple embedding model
        print("🔧 Loading embedding model...")
        self.embedding_model = SentenceTransformer(
            'paraphrase-multilingual-MiniLM-L12-v2',
            device='cpu'
        )
        print("✅ Embedding model loaded (CPU)")
        
        # Setup ChromaDB (in-memory)
        print("🔧 Setting up ChromaDB...")
        self.client = chromadb.Client()
        print("✅ ChromaDB ready")
    
    def load_feature_simple(self, feature_name: str, csv_file: str, text_column: str):
        """Load feature with ultra-simple approach"""
        print(f"\n📊 Loading: {feature_name}")
        
        try:
            # Load CSV
            csv_path = os.path.join(self.features_dir, csv_file)
            if not os.path.exists(csv_path):
                print(f"❌ File not found: {csv_path}")
                return False
            
            df = pd.read_csv(csv_path)
            print(f"📈 Loaded {len(df)} rows")
            
            if text_column not in df.columns:
                print(f"❌ Column {text_column} not found")
                return False
            
            # Create collection
            collection_name = f"rag_{feature_name}"
            try:
                self.client.delete_collection(collection_name)
            except:
                pass
            
            collection = self.client.create_collection(collection_name)
            
            # Prepare documents
            documents = []
            metadatas = []
            ids = []
            
            for idx, row in df.iterrows():
                text = str(row[text_column]) if pd.notna(row[text_column]) else ""
                if len(text.strip()) < 5:
                    continue
                
                # Keep text reasonable length
                if len(text) > 500:
                    text = text[:500] + "..."
                
                documents.append(text)
                
                # Minimal metadata
                metadata = {'feature_type': feature_name, 'row_index': str(idx)}
                metadatas.append(metadata)
                ids.append(f"{feature_name}_{idx}")
            
            print(f"📝 Prepared {len(documents)} documents")
            
            if len(documents) == 0:
                print("⚠️ No valid documents found")
                return False
            
            # Process documents in small chunks
            chunk_size = 10
            total_added = 0
            
            for i in range(0, len(documents), chunk_size):
                chunk_docs = documents[i:i+chunk_size]
                chunk_metas = metadatas[i:i+chunk_size]
                chunk_ids = ids[i:i+chunk_size]
                
                try:
                    # Generate embeddings
                    embeddings = self.embedding_model.encode(
                        chunk_docs,
                        show_progress_bar=False,
                        convert_to_tensor=False
                    )
                    
                    # Convert to list if needed
                    if hasattr(embeddings, 'tolist'):
                        embeddings = embeddings.tolist()
                    
                    # Add to collection
                    collection.add(
                        documents=chunk_docs,
                        embeddings=embeddings,
                        metadatas=chunk_metas,
                        ids=chunk_ids
                    )
                    
                    total_added += len(chunk_docs)
                    print(f"  ✅ Chunk {i//chunk_size + 1}: {len(chunk_docs)} docs")
                    
                except Exception as e:
                    print(f"  ❌ Chunk {i//chunk_size + 1} failed: {str(e)}")
                    continue
            
            if total_added > 0:
                self.collections[feature_name] = collection
                print(f"✅ {feature_name}: {total_added} documents loaded successfully")
                return True
            else:
                print(f"❌ {feature_name}: No documents loaded")
                return False
                
        except Exception as e:
            print(f"❌ Error loading {feature_name}: {str(e)}")
            return False
    
    def load_all_features(self):
        """Load all features"""
        print("\n🚀 Loading all features...")
        
        features = {
            'recipes': ('recipes.csv', 'recipe_text'),
            'nutrition_info': ('nutrition_info.csv', 'nutrition_text'),
            'customer_profiles': ('customer_profiles.csv', 'profile_text'),
            'customer_demographics': ('customer_demographics.csv', 'demographic_text')
        }
        
        results = {}
        
        for feature_name, (csv_file, text_col) in features.items():
            success = self.load_feature_simple(feature_name, csv_file, text_col)
            results[feature_name] = success
        
        # Summary
        successful = [name for name, success in results.items() if success]
        failed = [name for name, success in results.items() if not success]
        
        print(f"\n📊 Loading Summary:")
        print(f"✅ Successful: {len(successful)} - {successful}")
        print(f"❌ Failed: {len(failed)} - {failed}")
        
        return results
    
    def test_search(self, query: str = "món ăn Việt Nam"):
        """Test search functionality"""
        print(f"\n🔍 Testing search: '{query}'")
        
        if not self.collections:
            print("❌ No collections loaded")
            return
        
        for feature_name, collection in self.collections.items():
            try:
                count = collection.count()
                print(f"  📚 {feature_name}: {count} documents")
                
                if count > 0:
                    # Generate query embedding
                    query_embedding = self.embedding_model.encode([query])
                    if hasattr(query_embedding, 'tolist'):
                        query_embedding = query_embedding.tolist()
                    
                    # Search
                    results = collection.query(
                        query_embeddings=query_embedding,
                        n_results=min(3, count)
                    )
                    
                    if results['documents'][0]:
                        print(f"    ✅ Found {len(results['documents'][0])} results")
                        print(f"    📄 Sample: {results['documents'][0][0][:80]}...")
                    else:
                        print(f"    ⚠️ No results found")
                        
            except Exception as e:
                print(f"  ❌ {feature_name} search failed: {str(e)}")
    
    def get_stats(self):
        """Get system stats"""
        print(f"\n📊 System Statistics:")
        print(f"🎯 Device: {self.device}")
        print(f"📚 Collections: {len(self.collections)}")
        
        total_docs = 0
        for name, collection in self.collections.items():
            try:
                count = collection.count()
                total_docs += count
                print(f"  - {name}: {count} documents")
            except:
                print(f"  - {name}: Error getting count")
        
        print(f"📄 Total documents: {total_docs}")

def main():
    """Main function"""
    print("=" * 60)
    
    # Initialize loader
    loader = UltraSimpleRAGLoader()
    
    # Load features
    results = loader.load_all_features()
    
    # Test search
    loader.test_search("món ăn ngon")
    
    # Show stats
    loader.get_stats()
    
    print("\n✅ RAG system ready!")
    return loader

if __name__ == "__main__":
    loader = main()
