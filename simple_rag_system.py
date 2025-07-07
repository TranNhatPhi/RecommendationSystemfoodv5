#!/usr/bin/env python3
"""
Simple RAG system with GPU + ChromaDB + LangChain
Focuses on loading CSV and basic RAG functionality
"""

import chromadb
from sentence_transformers import SentenceTransformer
import pandas as pd
import torch
import json
import time
from typing import List, Dict, Any
from datetime import datetime

class SimpleRAGSystem:
    def __init__(self, use_gpu: bool = True):
        """Initialize simple RAG system with GPU support"""
        self.use_gpu = use_gpu and torch.cuda.is_available()
        
        # Setup device
        self.device = 'cuda' if self.use_gpu else 'cpu'
        print(f"🚀 Initializing RAG on device: {self.device}")
        
        if self.use_gpu:
            print(f"🎯 GPU: {torch.cuda.get_device_name(0)}")
            print(f"💾 GPU Memory: {torch.cuda.get_device_properties(0).total_memory // 1024**3} GB")
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(
            'paraphrase-multilingual-mpnet-base-v2',
            device=self.device
        )
        
        # Initialize ChromaDB (in-memory for reliability)
        self.client = chromadb.Client()
        self.collections = {}
        
        print("✅ Simple RAG system initialized")
    
    def load_csv_data(self, csv_path: str, collection_name: str, 
                     text_columns: List[str], id_column: str = None,
                     batch_size: int = 32) -> Dict[str, Any]:
        """Load CSV data into ChromaDB collection"""
        
        print(f"📊 Loading CSV: {csv_path}")
        
        try:
            # Load CSV
            df = pd.read_csv(csv_path)
            print(f"📈 Loaded {len(df)} rows")
            
            # Create collection
            if collection_name in self.collections:
                self.client.delete_collection(collection_name)
            
            collection = self.client.create_collection(collection_name)
            self.collections[collection_name] = collection
            
            # Prepare data
            documents = []
            metadatas = []
            ids = []
            
            for idx, row in df.iterrows():
                # Combine text columns
                text_parts = []
                for col in text_columns:
                    if col in df.columns and pd.notna(row[col]):
                        text_parts.append(str(row[col]))
                
                if not text_parts:
                    continue
                
                document = " | ".join(text_parts)
                documents.append(document)
                
                # Create metadata from all other columns
                metadata = {}
                for col in df.columns:
                    if col not in text_columns and pd.notna(row[col]):
                        metadata[col] = str(row[col])
                
                metadatas.append(metadata)
                
                # Generate ID
                if id_column and id_column in df.columns:
                    doc_id = str(row[id_column])
                else:
                    doc_id = f"{collection_name}_{idx}"
                ids.append(doc_id)
            
            print(f"📝 Prepared {len(documents)} documents")
            
            # Process in batches
            total_added = 0
            for i in range(0, len(documents), batch_size):
                batch_end = min(i + batch_size, len(documents))
                batch_docs = documents[i:batch_end]
                batch_metas = metadatas[i:batch_end]
                batch_ids = ids[i:batch_end]
                
                print(f"⚡ Processing batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")
                
                # Generate embeddings
                start_time = time.time()
                embeddings = self.embedding_model.encode(
                    batch_docs,
                    convert_to_tensor=False,
                    show_progress_bar=False
                )
                embed_time = time.time() - start_time
                
                # Add to collection
                start_time = time.time()
                collection.add(
                    documents=batch_docs,
                    embeddings=embeddings.tolist(),
                    metadatas=batch_metas,
                    ids=batch_ids
                )
                add_time = time.time() - start_time
                
                total_added += len(batch_docs)
                print(f"  ✅ Embedded in {embed_time:.2f}s, Added in {add_time:.2f}s")
                
                # Clear GPU cache
                if self.use_gpu:
                    torch.cuda.empty_cache()
            
            print(f"✅ Loaded {total_added} documents to collection '{collection_name}'")
            
            return {
                'success': True,
                'collection_name': collection_name,
                'total_documents': total_added,
                'source_file': csv_path
            }
            
        except Exception as e:
            print(f"❌ Error loading CSV: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def search(self, query: str, collection_name: str, n_results: int = 5) -> Dict[str, Any]:
        """Search in a specific collection"""
        try:
            if collection_name not in self.collections:
                return {'success': False, 'error': f'Collection {collection_name} not found'}
            
            collection = self.collections[collection_name]
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query], convert_to_tensor=False)
            
            # Search
            results = collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=n_results
            )
            
            return {
                'success': True,
                'query': query,
                'collection': collection_name,
                'results': results
            }
            
        except Exception as e:
            print(f"❌ Search error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def multi_collection_search(self, query: str, collections: List[str] = None, 
                              n_results_per_collection: int = 3) -> Dict[str, Any]:
        """Search across multiple collections"""
        if collections is None:
            collections = list(self.collections.keys())
        
        all_results = {}
        
        for collection_name in collections:
            if collection_name in self.collections:
                result = self.search(query, collection_name, n_results_per_collection)
                if result['success']:
                    all_results[collection_name] = result['results']
        
        return {
            'success': True,
            'query': query,
            'collections_searched': collections,
            'results': all_results
        }
    
    def generate_rag_response(self, query: str, collections: List[str] = None) -> Dict[str, Any]:
        """Generate RAG response using retrieved context"""
        
        # Search for relevant context
        search_results = self.multi_collection_search(query, collections, n_results_per_collection=3)
        
        if not search_results['success']:
            return {
                'success': False,
                'error': 'Failed to retrieve context'
            }
        
        # Build context from search results
        context_parts = []
        retrieved_docs = []
        
        for collection_name, results in search_results['results'].items():
            if results['documents'][0]:
                context_parts.append(f"\n=== THÔNG TIN TỪ {collection_name.upper()} ===")
                for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                    context_parts.append(f"{i+1}. {doc}")
                    retrieved_docs.append({
                        'collection': collection_name,
                        'document': doc,
                        'metadata': metadata
                    })
        
        context = "\n".join(context_parts)
        
        # Generate response (fallback since no OpenAI key)
        response = self._generate_fallback_response(query, context)
        
        return {
            'success': True,
            'query': query,
            'context': context,
            'response': response,
            'retrieved_documents': retrieved_docs,
            'source': 'rag_fallback'
        }
    
    def _generate_fallback_response(self, query: str, context: str) -> str:
        """Generate fallback response based on context and query patterns"""
        
        query_lower = query.lower()
        
        response = "🔍 **Dựa trên thông tin tìm được:**\n\n"
        
        # Pattern-based responses
        if "giảm cân" in query_lower:
            response += "🏃‍♀️ **Gợi ý cho việc giảm cân:**\n"
            response += "• Chọn món ăn ít calo, nhiều chất xơ\n"
            response += "• Tăng cường rau xanh, protein nạc\n"
            response += "• Hạn chế đồ chiên, ngọt, đồ uống có calo cao\n"
            response += "• Chia nhỏ bữa ăn, ăn chậm, nhai kỹ\n\n"
        
        elif "tăng cân" in query_lower:
            response += "💪 **Gợi ý cho việc tăng cân lành mạnh:**\n"
            response += "• Tăng lượng calo với thực phẩm bổ dưỡng\n"
            response += "• Nhiều protein, carbohydrate phức tạp\n"
            response += "• Ăn nhiều bữa nhỏ trong ngày\n"
            response += "• Thêm hạt, bơ, sữa vào khẩu phần\n\n"
        
        elif "tiểu đường" in query_lower:
            response += "🩺 **Cho người tiểu đường:**\n"
            response += "• Chọn thực phẩm chỉ số đường huyết thấp\n"
            response += "• Hạn chế đường, carbohydrate đơn giản\n"
            response += "• Tăng chất xơ từ rau quả\n"
            response += "• Ăn đều đặn, không bỏ bữa\n\n"
        
        elif "cao huyết áp" in query_lower:
            response += "❤️ **Cho người cao huyết áp:**\n"
            response += "• Hạn chế muối và natri\n"
            response += "• Tăng thực phẩm giàu kali (chuối, rau xanh)\n"
            response += "• Chọn thực phẩm tươi, hạn chế chế biến sẵn\n"
            response += "• Tăng omega-3 từ cá\n\n"
        
        if context and len(context.strip()) > 50:
            response += "📚 **Thông tin từ cơ sở dữ liệu:**\n"
            # Extract relevant info from context
            if "món" in context.lower():
                response += "• Hệ thống tìm thấy các món ăn phù hợp trong dữ liệu\n"
            if "khách hàng" in context.lower():
                response += "• Có thông tin về sở thích của khách hàng tương tự\n"
            response += f"• Chi tiết: {context[:200]}...\n\n"
        
        response += "💡 **Lưu ý:** Đây là tư vấn tổng quát. Nên tham khảo ý kiến bác sĩ cho tư vấn cá nhân hóa."
        
        return response
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        stats = {
            'gpu_enabled': self.use_gpu,
            'device': self.device,
            'collections': {},
            'total_documents': 0
        }
        
        for name, collection in self.collections.items():
            count = collection.count()
            stats['collections'][name] = count
            stats['total_documents'] += count
        
        return stats

def demo_rag_system():
    """Demo the RAG system"""
    print("🚀 RAG System Demo with GPU + ChromaDB + LangChain")
    
    # Initialize system
    rag = SimpleRAGSystem(use_gpu=True)
    
    # Test with available CSV files
    csv_files = [
        ('customers_data.csv', 'customers', ['full_name', 'region'], 'customer_id'),
        ('food_recipes_enhanced.csv', 'recipes', ['recipe_name', 'difficulty', 'meal_time', 'nutrition_category'], None),
        ('customer_interactions_enhanced.csv', 'interactions', ['recipe_name', 'difficulty', 'meal_time', 'nutrition_category'], None)
    ]
    
    # Load available CSV files
    loaded_collections = []
    for csv_file, collection_name, text_cols, id_col in csv_files:
        try:
            result = rag.load_csv_data(csv_file, collection_name, text_cols, id_col, batch_size=16)
            if result['success']:
                loaded_collections.append(collection_name)
                print(f"✅ Loaded {collection_name}")
            else:
                print(f"❌ Failed to load {collection_name}: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"⚠️ Skipping {csv_file}: {str(e)}")
    
    if not loaded_collections:
        print("⚠️ No data loaded, creating sample data...")
        # Create sample data
        sample_data = pd.DataFrame([
            {"recipe_name": "Phở bò", "difficulty": "medium", "meal_time": "breakfast", "nutrition_category": "protein"},
            {"recipe_name": "Bánh mì", "difficulty": "easy", "meal_time": "breakfast", "nutrition_category": "carbs"},
            {"recipe_name": "Cơm tấm", "difficulty": "medium", "meal_time": "lunch", "nutrition_category": "balanced"},
            {"recipe_name": "Bún chả", "difficulty": "hard", "meal_time": "lunch", "nutrition_category": "protein"},
            {"recipe_name": "Gỏi cuốn", "difficulty": "easy", "meal_time": "snack", "nutrition_category": "light"}
        ])
        sample_data.to_csv('sample_recipes.csv', index=False)
        
        result = rag.load_csv_data('sample_recipes.csv', 'recipes', ['recipe_name', 'difficulty', 'meal_time', 'nutrition_category'])
        if result['success']:
            loaded_collections.append('recipes')
    
    # Test queries
    if loaded_collections:
        print(f"\n🔍 Testing queries on collections: {loaded_collections}")
        
        test_queries = [
            "món ăn sáng Việt Nam",
            "món ăn giảm cân ít calo",
            "khách hàng ở Hà Nội",
            "món ăn cho người tiểu đường",
            "bữa trưa bổ dưỡng"
        ]
        
        for query in test_queries:
            print(f"\n❓ **Query:** {query}")
            
            # Test search
            search_result = rag.multi_collection_search(query, loaded_collections, n_results_per_collection=2)
            if search_result['success']:
                print("🔍 **Search Results:**")
                for coll_name, results in search_result['results'].items():
                    if results['documents'][0]:
                        print(f"  📚 {coll_name}:")
                        for i, doc in enumerate(results['documents'][0][:2]):
                            print(f"    {i+1}. {doc[:80]}...")
            
            # Test RAG response
            rag_result = rag.generate_rag_response(query, loaded_collections)
            if rag_result['success']:
                print("🤖 **RAG Response:**")
                print(f"  {rag_result['response'][:200]}...")
    
    # Show stats
    print(f"\n📊 **System Statistics:**")
    stats = rag.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n✅ RAG Demo completed!")
    return rag

if __name__ == "__main__":
    rag_system = demo_rag_system()
