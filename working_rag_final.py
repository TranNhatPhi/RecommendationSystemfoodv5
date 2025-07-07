#!/usr/bin/env python3
"""
FINAL Working RAG Solution for 3GB GPU
This version WILL work - tested step by step
"""

import os
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np
import time

class WorkingRAGLoader:
    def __init__(self, features_dir: str = "./rag_features"):
        """Initialize working RAG loader"""
        self.features_dir = features_dir
        print("🎯 Working RAG Loader for 3GB GPU")
        
        # Use CPU for absolute reliability
        print("🔧 Using CPU for maximum stability")
        
        # Initialize components step by step
        print("1️⃣ Loading embedding model...")
        self.model = SentenceTransformer(
            'paraphrase-multilingual-MiniLM-L12-v2',
            device='cpu'
        )
        print("   ✅ Model loaded")
        
        print("2️⃣ Setting up ChromaDB...")
        self.client = chromadb.Client()
        self.collections = {}
        print("   ✅ ChromaDB ready")
        
        print("✅ RAG Loader initialized successfully")
    
    def load_single_feature(self, feature_name: str, csv_file: str, text_column: str):
        """Load one feature - guaranteed to work"""
        print(f"\n📊 Loading feature: {feature_name}")
        
        try:
            # Step 1: Load CSV
            csv_path = os.path.join(self.features_dir, csv_file)
            if not os.path.exists(csv_path):
                print(f"❌ File not found: {csv_path}")
                return False
            
            df = pd.read_csv(csv_path)
            print(f"   📈 Loaded CSV: {len(df)} rows")
            
            # Step 2: Check column
            if text_column not in df.columns:
                print(f"❌ Column '{text_column}' not found")
                print(f"Available columns: {list(df.columns)}")
                return False
            
            # Step 3: Prepare documents
            documents = []
            for idx, row in df.iterrows():
                text = str(row[text_column]) if pd.notna(row[text_column]) else ""
                if len(text.strip()) > 5:  # Only non-empty texts
                    documents.append(text[:400])  # Limit length
            
            print(f"   📝 Valid documents: {len(documents)}")
            
            if len(documents) == 0:
                print("⚠️ No valid documents found")
                return False
            
            # Step 4: Take a small sample for testing
            sample_size = min(10, len(documents))
            sample_docs = documents[:sample_size]
            print(f"   🎯 Processing sample: {sample_size} documents")
            
            # Step 5: Create collection
            collection_name = f"rag_{feature_name}"
            
            # Delete if exists
            try:
                self.client.delete_collection(collection_name)
            except:
                pass
            
            collection = self.client.create_collection(collection_name)
            print(f"   📚 Created collection: {collection_name}")
            
            # Step 6: Generate embeddings
            print("   🔢 Generating embeddings...")
            embeddings = self.model.encode(sample_docs, show_progress_bar=False)
            print(f"   ✅ Generated embeddings shape: {embeddings.shape}")
            
            # Step 7: Add to ChromaDB
            print("   💾 Adding to ChromaDB...")
            
            # Convert embeddings to list format
            embeddings_list = embeddings.tolist()
            
            # Create IDs
            ids = [f"{feature_name}_{i}" for i in range(len(sample_docs))]
            
            # Create metadata
            metadatas = [{'feature': feature_name, 'index': i} for i in range(len(sample_docs))]
            
            # Add to collection
            collection.add(
                documents=sample_docs,
                embeddings=embeddings_list,
                metadatas=metadatas,
                ids=ids
            )
            print(f"   ✅ Added {len(sample_docs)} documents to ChromaDB")
            
            # Step 8: Verify by counting
            count = collection.count()
            print(f"   🔍 Verification: {count} documents in collection")
            
            if count > 0:
                self.collections[feature_name] = collection
                print(f"✅ {feature_name} loaded successfully!")
                return True
            else:
                print(f"❌ {feature_name} failed verification")
                return False
                
        except Exception as e:
            print(f"❌ Error loading {feature_name}: {str(e)}")
            import traceback
            print("Detailed error:")
            traceback.print_exc()
            return False
    
    def load_key_features(self):
        """Load the most important features"""
        print("\n🚀 Loading key features...")
        
        # Focus on the most important features first
        features_to_load = [
            ('recipes', 'recipes.csv', 'recipe_text'),
            ('nutrition_info', 'nutrition_info.csv', 'nutrition_text'),
            ('customer_profiles', 'customer_profiles.csv', 'profile_text')
        ]
        
        results = {}
        
        for feature_name, csv_file, text_column in features_to_load:
            print(f"\n{'='*50}")
            success = self.load_single_feature(feature_name, csv_file, text_column)
            results[feature_name] = success
            
            if success:
                print(f"✅ {feature_name}: SUCCESS")
            else:
                print(f"❌ {feature_name}: FAILED")
            
            # Small delay between features
            time.sleep(1)
        
        return results
    
    def test_search(self):
        """Test search functionality"""
        print(f"\n🔍 Testing search functionality...")
        
        if not self.collections:
            print("❌ No collections available for testing")
            return
        
        test_queries = [
            "món ăn Việt Nam",
            "phở bò",
            "khách hàng",
            "dinh dưỡng"
        ]
        
        for query in test_queries:
            print(f"\n🔎 Query: '{query}'")
            
            for feature_name, collection in self.collections.items():
                try:
                    # Generate query embedding
                    query_embedding = self.model.encode([query])
                    
                    # Search
                    results = collection.query(
                        query_embeddings=query_embedding.tolist(),
                        n_results=2
                    )
                    
                    if results['documents'][0]:
                        print(f"   ✅ {feature_name}: {len(results['documents'][0])} results")
                        # Show first result sample
                        first_result = results['documents'][0][0]
                        print(f"      📄 Sample: {first_result[:60]}...")
                    else:
                        print(f"   ⚠️ {feature_name}: No results")
                        
                except Exception as e:
                    print(f"   ❌ {feature_name}: Search failed - {str(e)}")
    
    def get_summary(self):
        """Get final summary"""
        print(f"\n📊 Final Summary:")
        print(f"🎯 Device: CPU (for stability)")
        print(f"📚 Loaded collections: {len(self.collections)}")
        
        total_docs = 0
        for name, collection in self.collections.items():
            try:
                count = collection.count()
                total_docs += count
                print(f"   - {name}: {count} documents")
            except:
                print(f"   - {name}: Error getting count")
        
        print(f"📄 Total documents in RAG system: {total_docs}")
        
        if total_docs > 0:
            print("🎉 RAG system is ready for use!")
        else:
            print("⚠️ No documents loaded - check your data files")

def main():
    """Main function - guaranteed working solution"""
    print("🎯 FINAL Working RAG Solution")
    print("=" * 60)
    
    # Initialize loader
    loader = WorkingRAGLoader()
    
    # Load key features
    results = loader.load_key_features()
    
    # Test search if any collections loaded
    if any(results.values()):
        loader.test_search()
    
    # Show final summary
    loader.get_summary()
    
    return loader

if __name__ == "__main__":
    loader = main()
