"""
Simple RAG demo with manual data
"""
import chromadb
from sentence_transformers import SentenceTransformer
import pandas as pd
import os

def create_simple_rag_demo():
    """Create a simple RAG demo with manual data"""
    print("🚀 Creating Simple RAG Demo...")
    
    # Initialize components
    model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
    client = chromadb.PersistentClient(path="./simple_rag_demo")
    
    # Create collections
    recipes_collection = client.get_or_create_collection(name="recipes_demo")
    nutrition_collection = client.get_or_create_collection(name="nutrition_demo")
    
    # Manual recipe data
    recipe_data = [
        {
            "text": "Salad rau xanh với ức gà nướng - món ăn ít calo, giàu protein, tốt cho việc giảm cân. Cung cấp vitamin và khoáng chất thiết yếu.",
            "name": "Salad ức gà",
            "category": "giảm cân",
            "calories": "250"
        },
        {
            "text": "Cháo yến mạch với trái cây - bữa sáng bổ dưỡng, giàu chất xơ, giúp no lâu và kiểm soát cân nặng hiệu quả.",
            "name": "Cháo yến mạch trái cây", 
            "category": "giảm cân",
            "calories": "200"
        },
        {
            "text": "Cơm gạo lức với thịt bò nướng và rau củ - món ăn cân bằng dinh dưỡng, giàu protein và carbohydrate phức tạp.",
            "name": "Cơm gạo lức thịt bò",
            "category": "tăng cân",
            "calories": "450"
        },
        {
            "text": "Sinh tố bơ chuối với sữa hạt - đồ uống giàu calo lành mạnh, protein và chất béo tốt, phù hợp cho người gầy.",
            "name": "Sinh tố bơ chuối",
            "category": "tăng cân", 
            "calories": "350"
        },
        {
            "text": "Canh rau củ thanh đạm - ít natrium, nhiều kali, phù hợp cho người cao huyết áp, không chứa MSG.",
            "name": "Canh rau củ",
            "category": "cao huyết áp",
            "calories": "80"
        }
    ]
    
    # Nutrition knowledge data
    nutrition_data = [
        {
            "text": "Để giảm cân hiệu quả, cần tạo thâm hụt calo 500-750 calo/ngày. Ăn nhiều rau xanh, protein nạc, hạn chế carbohydrate tinh chế.",
            "topic": "Giảm cân",
            "category": "weight_management"
        },
        {
            "text": "Người tăng cân cần ăn thặng dư calo 300-500 calo/ngày. Tập trung vào protein chất lượng cao và carbohydrate phức tạp.",
            "topic": "Tăng cân",
            "category": "weight_management"
        },
        {
            "text": "Người cao huyết áp nên hạn chế muối dưới 2g/ngày, tăng kali từ rau quả, tránh thực phẩm chế biến sẵn.",
            "topic": "Cao huyết áp",
            "category": "medical_condition"
        },
        {
            "text": "Người tiểu đường type 2 nên ăn thực phẩm chỉ số đường huyết thấp, kiểm soát carbohydrate, tăng chất xơ.",
            "topic": "Tiểu đường",
            "category": "medical_condition"
        }
    ]
    
    # Add recipes to collection
    print("📋 Adding recipes to collection...")
    recipe_texts = [item["text"] for item in recipe_data]
    recipe_embeddings = model.encode(recipe_texts)
    
    recipes_collection.add(
        documents=recipe_texts,
        metadatas=[{"name": item["name"], "category": item["category"], "calories": item["calories"]} for item in recipe_data],
        ids=[f"recipe_{i}" for i in range(len(recipe_data))],
        embeddings=recipe_embeddings.tolist()
    )
    
    # Add nutrition knowledge to collection
    print("📚 Adding nutrition knowledge to collection...")
    nutrition_texts = [item["text"] for item in nutrition_data]
    nutrition_embeddings = model.encode(nutrition_texts)
    
    nutrition_collection.add(
        documents=nutrition_texts,
        metadatas=[{"topic": item["topic"], "category": item["category"]} for item in nutrition_data],
        ids=[f"nutrition_{i}" for i in range(len(nutrition_data))],
        embeddings=nutrition_embeddings.tolist()
    )
    
    print("✅ Data added successfully!")
    
    return model, recipes_collection, nutrition_collection

def test_rag_queries(model, recipes_collection, nutrition_collection):
    """Test RAG queries"""
    print("\n🔍 Testing RAG Queries...")
    
    test_queries = [
        "Tôi muốn giảm cân, gợi ý món ăn ít calo",
        "Món ăn cho người tăng cân", 
        "Thực phẩm cho người cao huyết áp",
        "Lời khuyên về dinh dưỡng cho người tiểu đường"
    ]
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        
        # Generate query embedding
        query_embedding = model.encode([query])
        
        # Search recipes
        recipe_results = recipes_collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=2
        )
        
        # Search nutrition knowledge
        nutrition_results = nutrition_collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=2
        )
        
        print("🍽️ Recipe Results:")
        if recipe_results['documents'][0]:
            for i, (doc, meta) in enumerate(zip(recipe_results['documents'][0], recipe_results['metadatas'][0])):
                print(f"  {i+1}. {meta['name']} ({meta['calories']} calo)")
                print(f"     {doc[:100]}...")
        else:
            print("  No recipes found")
        
        print("📚 Nutrition Knowledge:")
        if nutrition_results['documents'][0]:
            for i, (doc, meta) in enumerate(zip(nutrition_results['documents'][0], nutrition_results['metadatas'][0])):
                print(f"  {i+1}. {meta['topic']}")
                print(f"     {doc[:100]}...")
        else:
            print("  No nutrition knowledge found")

def generate_rag_response(query, model, recipes_collection, nutrition_collection):
    """Generate comprehensive response using RAG"""
    print(f"\n🤖 Generating RAG Response for: {query}")
    
    # Get context from both collections
    query_embedding = model.encode([query])
    
    recipe_results = recipes_collection.query(query_embeddings=query_embedding.tolist(), n_results=3)
    nutrition_results = nutrition_collection.query(query_embeddings=query_embedding.tolist(), n_results=2)
    
    # Build context
    context = "THÔNG TIN TỪ CƠ SỞ DỮ LIỆU:\n\n"
    
    if recipe_results['documents'][0]:
        context += "MÓN ĂN GỢI Ý:\n"
        for doc, meta in zip(recipe_results['documents'][0], recipe_results['metadatas'][0]):
            context += f"- {meta['name']}: {doc}\n"
        context += "\n"
    
    if nutrition_results['documents'][0]:
        context += "KIẾN THỨC DINH DƯỠNG:\n"
        for doc, meta in zip(nutrition_results['documents'][0], nutrition_results['metadatas'][0]):
            context += f"- {meta['topic']}: {doc}\n"
    
    # Simple response generation (without OpenAI for demo)
    response = f"""
Dựa trên câu hỏi "{query}", tôi có những gợi ý sau:

{context}

💡 Lời khuyên: Kết hợp các món ăn phù hợp với lời khuyên dinh dưỡng để đạt mục tiêu sức khỏe của bạn.
"""
    
    print(response)
    return response

def main():
    """Main demo function"""
    print("🚀 RAG System Demo - Manual Data")
    
    # Create RAG system
    model, recipes_collection, nutrition_collection = create_simple_rag_demo()
    
    # Test queries
    test_rag_queries(model, recipes_collection, nutrition_collection)
    
    # Generate sample responses
    print("\n" + "="*50)
    print("🤖 RAG RESPONSE GENERATION DEMO")
    print("="*50)
    
    demo_queries = [
        "Tôi muốn giảm cân, gợi ý món ăn",
        "Món ăn cho người cao huyết áp"
    ]
    
    for query in demo_queries:
        generate_rag_response(query, model, recipes_collection, nutrition_collection)
    
    print("\n✅ RAG Demo completed successfully!")
    print("💡 This demonstrates how RAG retrieves relevant information and generates responses.")

if __name__ == "__main__":
    main()
