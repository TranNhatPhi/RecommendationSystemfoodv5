import pandas as pd
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
import os
import json
from datetime import datetime

class RAGVectorDatabase:
    def __init__(self, persist_directory: str = "./chromadb_data", use_gpu: bool = True):
        """Initialize RAG Vector Database with ChromaDB and GPU acceleration"""
        self.persist_directory = persist_directory
        self.use_gpu = use_gpu and torch.cuda.is_available()
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Initialize embedding model with GPU support
        device = 'cuda' if self.use_gpu else 'cpu'
        print(f"🚀 Initializing embedding model on device: {device}")
        
        if self.use_gpu:
            print(f"🎯 GPU Info: {torch.cuda.get_device_name(0)}")
            print(f"💾 GPU Memory: {torch.cuda.get_device_properties(0).total_memory // 1024**3} GB")
        
        # Use a multilingual model that works well with Vietnamese
        self.embedding_model = SentenceTransformer(
            'paraphrase-multilingual-mpnet-base-v2',
            device=device
        )
        
        # Set batch size based on device
        self.batch_size = 32 if self.use_gpu else 16
        
        # Collections for different data types
        self.collections = {}
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize ChromaDB collections for different data types"""
        try:
            # Food recipes collection
            self.collections['recipes'] = self.client.get_or_create_collection(
                name="food_recipes",
                metadata={"hnsw:space": "cosine"}
            )
            
            # Customer interactions collection
            self.collections['interactions'] = self.client.get_or_create_collection(
                name="customer_interactions",
                metadata={"hnsw:space": "cosine"}
            )
            
            # Nutrition knowledge collection
            self.collections['nutrition'] = self.client.get_or_create_collection(
                name="nutrition_knowledge",
                metadata={"hnsw:space": "cosine"}
            )
            
            print("✅ ChromaDB collections initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing collections: {str(e)}")
            raise
    
    def chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks for better retrieval"""
        if not text or len(text) < chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at word boundaries
            if end < len(text):
                last_space = chunk.rfind(' ')
                if last_space > start:
                    chunk = text[start:start + last_space]
                    end = start + last_space
            
            chunks.append(chunk.strip())
            start = end - overlap
            
            if start >= len(text):
                break
        
        return chunks
    
    def add_recipes_from_csv(self, csv_file: str, batch_size: int = 100):
        """Add recipes from CSV file to ChromaDB with chunking and GPU acceleration"""
        try:
            print(f"📁 Loading recipes from {csv_file}")
            df = pd.read_csv(csv_file)
            
            print(f"📊 Found {len(df)} recipes to process")
            
            # Process in batches for better performance
            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i+batch_size]
                print(f"🔄 Processing batch {i//batch_size + 1}/{(len(df)-1)//batch_size + 1}")
                
                documents = []
                metadatas = []
                ids = []
                
                for idx, row in batch_df.iterrows():
                    # Create comprehensive text for embedding
                    recipe_text = f"""
                    Tên món: {row.get('recipe_name', '')}
                    Độ khó: {row.get('difficulty', '')}
                    Bữa ăn: {row.get('meal_time', '')}
                    Loại dinh dưỡng: {row.get('nutrition_category', '')}
                    Calories ước tính: {row.get('estimated_calories', '')}
                    Thời gian chuẩn bị: {row.get('preparation_time_minutes', '')} phút
                    Số lượng nguyên liệu: {row.get('ingredient_count', '')}
                    Giá ước tính: {row.get('estimated_price_vnd', '')} VND
                    Đánh giá: {row.get('avg_rating', '')}/5
                    """
                    
                    # Chunk the text
                    chunks = self.chunk_text(recipe_text)
                    
                    for chunk_idx, chunk in enumerate(chunks):
                        documents.append(chunk)
                        metadatas.append({
                            'recipe_name': str(row.get('recipe_name', '')),
                            'recipe_url': str(row.get('recipe_url', '')),
                            'difficulty': str(row.get('difficulty', '')),
                            'meal_time': str(row.get('meal_time', '')),
                            'nutrition_category': str(row.get('nutrition_category', '')),
                            'estimated_calories': float(row.get('estimated_calories', 0)),
                            'preparation_time_minutes': float(row.get('preparation_time_minutes', 0)),
                            'ingredient_count': int(row.get('ingredient_count', 0)),
                            'estimated_price_vnd': float(row.get('estimated_price_vnd', 0)),
                            'avg_rating': float(row.get('avg_rating', 0)),
                            'chunk_index': chunk_idx,
                            'total_chunks': len(chunks),
                            'data_type': 'recipe'
                        })
                        ids.append(f"recipe_{idx}_{chunk_idx}")
                
                # Generate embeddings using GPU
                print(f"🧠 Generating embeddings for {len(documents)} chunks...")
                embeddings = self.embedding_model.encode(
                    documents,
                    batch_size=32,
                    show_progress_bar=True,
                    convert_to_tensor=False
                ).tolist()
                
                # Add to ChromaDB
                self.collections['recipes'].add(
                    documents=documents,
                    metadatas=metadatas,
                    embeddings=embeddings,
                    ids=ids
                )
                
                print(f"✅ Added batch {i//batch_size + 1} to ChromaDB")
            
            print(f"🎉 Successfully added {len(df)} recipes to ChromaDB")
            
        except Exception as e:
            print(f"❌ Error adding recipes from CSV: {str(e)}")
            raise
    
    def add_interactions_from_csv(self, csv_file: str, batch_size: int = 100):
        """Add customer interactions from CSV to ChromaDB"""
        try:
            print(f"📁 Loading interactions from {csv_file}")
            df = pd.read_csv(csv_file)
            
            print(f"📊 Found {len(df)} interactions to process")
            
            # Process in batches
            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i+batch_size]
                print(f"🔄 Processing interaction batch {i//batch_size + 1}/{(len(df)-1)//batch_size + 1}")
                
                documents = []
                metadatas = []
                ids = []
                
                for idx, row in batch_df.iterrows():
                    # Create text for interaction
                    interaction_text = f"""
                    Khách hàng: {row.get('customer_id', '')}
                    Món ăn: {row.get('recipe_name', '')}
                    Đánh giá: {row.get('rating', '')}/5
                    Loại tương tác: {row.get('interaction_type', '')}
                    Ngày: {row.get('interaction_date', '')}
                    Bình luận: {row.get('comment', '')}
                    Độ khó: {row.get('difficulty', '')}
                    Bữa ăn: {row.get('meal_time', '')}
                    Loại dinh dưỡng: {row.get('nutrition_category', '')}
                    """
                    
                    documents.append(interaction_text)
                    metadatas.append({
                        'customer_id': str(row.get('customer_id', '')),
                        'recipe_name': str(row.get('recipe_name', '')),
                        'rating': float(row.get('rating', 0)),
                        'interaction_type': str(row.get('interaction_type', '')),
                        'interaction_date': str(row.get('interaction_date', '')),
                        'comment': str(row.get('comment', '')),
                        'difficulty': str(row.get('difficulty', '')),
                        'meal_time': str(row.get('meal_time', '')),
                        'nutrition_category': str(row.get('nutrition_category', '')),
                        'data_type': 'interaction'
                    })
                    ids.append(f"interaction_{idx}")
                
                # Generate embeddings
                print(f"🧠 Generating embeddings for interactions...")
                embeddings = self.embedding_model.encode(
                    documents,
                    batch_size=32,
                    show_progress_bar=True,
                    convert_to_tensor=False
                ).tolist()
                
                # Add to ChromaDB
                self.collections['interactions'].add(
                    documents=documents,
                    metadatas=metadatas,
                    embeddings=embeddings,
                    ids=ids
                )
                
                print(f"✅ Added interaction batch {i//batch_size + 1} to ChromaDB")
            
            print(f"🎉 Successfully added {len(df)} interactions to ChromaDB")
            
        except Exception as e:
            print(f"❌ Error adding interactions from CSV: {str(e)}")
            raise
    
    def add_nutrition_knowledge(self, knowledge_data: List[Dict]):
        """Add nutrition knowledge base to ChromaDB"""
        try:
            documents = []
            metadatas = []
            ids = []
            
            for idx, knowledge in enumerate(knowledge_data):
                # Create comprehensive text
                knowledge_text = f"""
                Chủ đề: {knowledge.get('topic', '')}
                Nội dung: {knowledge.get('content', '')}
                Loại: {knowledge.get('category', '')}
                Thông tin bổ sung: {knowledge.get('additional_info', '')}
                """
                
                # Chunk the knowledge text
                chunks = self.chunk_text(knowledge_text)
                
                for chunk_idx, chunk in enumerate(chunks):
                    documents.append(chunk)
                    metadatas.append({
                        'topic': str(knowledge.get('topic', '')),
                        'category': str(knowledge.get('category', '')),
                        'content': str(knowledge.get('content', '')),
                        'additional_info': str(knowledge.get('additional_info', '')),
                        'chunk_index': chunk_idx,
                        'total_chunks': len(chunks),
                        'data_type': 'nutrition_knowledge'
                    })
                    ids.append(f"nutrition_{idx}_{chunk_idx}")
            
            # Generate embeddings
            print(f"🧠 Generating embeddings for nutrition knowledge...")
            embeddings = self.embedding_model.encode(
                documents,
                batch_size=32,
                show_progress_bar=True,
                convert_to_tensor=False
            ).tolist()
            
            # Add to ChromaDB
            self.collections['nutrition'].add(
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
                ids=ids
            )
            
            print(f"🎉 Successfully added {len(knowledge_data)} nutrition knowledge entries")
            
        except Exception as e:
            print(f"❌ Error adding nutrition knowledge: {str(e)}")
            raise
    
    def search_similar(self, query: str, collection_name: str = 'recipes', n_results: int = 10) -> Dict:
        """Search for similar documents using vector similarity"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()[0]
            
            # Search in specified collection
            results = self.collections[collection_name].query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching similar documents: {str(e)}")
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
    
    def get_collection_stats(self):
        """Get statistics about the collections"""
        stats = {}
        
        try:
            for name, collection in self.collections.items():
                count = collection.count()
                stats[name] = {
                    'document_count': count,
                    'collection_name': name
                }
            
            stats['gpu_enabled'] = self.use_gpu
            stats['device'] = 'cuda' if self.use_gpu else 'cpu'
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting collection stats: {str(e)}")
            return {}

def setup_nutrition_knowledge():
    """Setup basic nutrition knowledge base"""
    knowledge_data = [
        {
            'topic': 'Giảm cân',
            'category': 'weight_management',
            'content': 'Để giảm cân hiệu quả, cần tạo ra thâm hụt calo bằng cách ăn ít calo hơn và tăng vận động. Nên chọn thực phẩm ít calo nhưng giàu chất dinh dưỡng như rau xanh, trái cây, protein nạc.',
            'additional_info': 'Nên giảm 0.5-1kg/tuần. Tránh các chế độ ăn quá khắt nghiệt.'
        },
        {
            'topic': 'Tăng cân',
            'category': 'weight_management',
            'content': 'Để tăng cân lành mạnh, cần tăng lượng calo nạp vào với thực phẩm giàu dinh dưỡng. Chọn protein chất lượng cao, carbohydrate phức tạp, và chất béo lành mạnh.',
            'additional_info': 'Nên ăn nhiều bữa nhỏ trong ngày. Kết hợp với tập luyện để tăng cơ bắp.'
        },
        {
            'topic': 'Tiểu đường',
            'category': 'medical_condition',
            'content': 'Người bị tiểu đường cần kiểm soát lượng đường và carbohydrate. Nên chọn thực phẩm có chỉ số đường huyết thấp, nhiều chất xơ.',
            'additional_info': 'Ăn đều đặn, tránh nhịn ăn. Theo dõi lượng đường huyết thường xuyên.'
        },
        {
            'topic': 'Cao huyết áp',
            'category': 'medical_condition',
            'content': 'Người cao huyết áp cần hạn chế muối và natri. Tăng cường thực phẩm giàu kali như chuối, rau xanh.',
            'additional_info': 'Hạn chế thực phẩm chế biến sẵn. Tăng cường omega-3 từ cá.'
        },
        {
            'topic': 'Bà bầu',
            'category': 'pregnancy',
            'content': 'Phụ nữ mang thai cần bổ sung acid folic, sắt, canxi. Tránh rượu bia, cà phê quá nhiều, thực phẩm sống.',
            'additional_info': 'Cần thêm 300-500 calo/ngày. Ăn nhiều bữa nhỏ để tránh buồn nôn.'
        },
        {
            'topic': 'Ăn chay',
            'category': 'dietary_preference',
            'content': 'Người ăn chay cần chú ý bổ sung protein từ đậu, hạt, vitamin B12, sắt, kẽm.',
            'additional_info': 'Kết hợp nhiều loại protein thực vật để có amino acid đầy đủ.'
        },
        {
            'topic': 'Trẻ em',
            'category': 'age_group',
            'content': 'Trẻ em cần dinh dưỡng đầy đủ để phát triển. Protein, canxi, vitamin D rất quan trọng.',
            'additional_info': 'Hạn chế đồ ngọt, đồ chiên. Khuyến khích ăn rau quả đa dạng.'
        },
        {
            'topic': 'Tập gym',
            'category': 'fitness',
            'content': 'Người tập gym cần nhiều protein để xây dựng cơ bắp. Carbohydrate trước tập, protein sau tập.',
            'additional_info': 'Nhu cầu protein: 1.6-2.2g/kg thể trọng. Uống đủ nước.'
        }
    ]
    
    return knowledge_data

def main():
    """Main function to setup RAG vector database"""
    print("🚀 Setting up RAG Vector Database with ChromaDB and GPU acceleration...")
    
    # Initialize RAG database
    rag_db = RAGVectorDatabase(use_gpu=True)
    
    # Add nutrition knowledge
    print("\n📚 Adding nutrition knowledge base...")
    knowledge_data = setup_nutrition_knowledge()
    rag_db.add_nutrition_knowledge(knowledge_data)
    
    # Check for existing CSV files
    csv_files = [
        'customers_data.csv',
        'interactions_encoded.csv',
        'food_recipes.csv'  # You might need to create this or use existing data
    ]
    
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            print(f"\n📁 Processing {csv_file}...")
            if 'customer' in csv_file.lower():
                print(f"⏭️ Skipping customer data (will process interactions)")
            elif 'interaction' in csv_file.lower():
                rag_db.add_interactions_from_csv(csv_file)
            elif 'recipe' in csv_file.lower() or 'food' in csv_file.lower():
                rag_db.add_recipes_from_csv(csv_file)
        else:
            print(f"⚠️ File {csv_file} not found, skipping...")
    
    # Display statistics
    print("\n📊 Database Statistics:")
    stats = rag_db.get_collection_stats()
    for collection_name, collection_stats in stats.items():
        if isinstance(collection_stats, dict) and 'document_count' in collection_stats:
            print(f"  {collection_name}: {collection_stats['document_count']} documents")
    
    print(f"\n🔥 GPU Enabled: {stats.get('gpu_enabled', False)}")
    print(f"🖥️ Device: {stats.get('device', 'cpu')}")
    
    # Test search
    print("\n🔍 Testing search functionality...")
    test_query = "món ăn giảm cân ít calo"
    results = rag_db.search_similar(test_query, 'recipes', n_results=3)
    
    if results['documents'][0]:
        print(f"Search results for '{test_query}':")
        for i, (doc, meta) in enumerate(zip(results['documents'][0][:3], results['metadatas'][0][:3])):
            print(f"  {i+1}. {meta.get('recipe_name', 'Unknown')}")
    
    print("\n✅ RAG Vector Database setup complete!")
    
    return rag_db

if __name__ == "__main__":
    main()
