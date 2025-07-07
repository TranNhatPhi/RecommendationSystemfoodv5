import openai
import json
import requests
from typing import Dict, List, Optional
import pandas as pd
import os
from datetime import datetime

# Import RAG components
try:
    from rag_vector_db import RAGVectorDatabase
    from rag_langchain_integration import RAGChain
    RAG_AVAILABLE = True
    print("✅ RAG components available")
except ImportError as e:
    RAG_AVAILABLE = False
    print(f"⚠️ RAG components not available: {str(e)}")

# Import cache manager
try:
    from cache_manager import cached, cache_manager
    CACHING_ENABLED = True
except ImportError:
    CACHING_ENABLED = False
    print("⚠️ Cache manager not available - running without caching")

    # Fallback decorator
    def cached(expire_hours: int = 24):
        def decorator(func):
            return func
        return decorator


class EnhancedRAGAgent:
    def __init__(self, openai_api_key: str = None, use_gpu: bool = True):
        """Initialize Enhanced RAG AI Agent with ChromaDB and LangChain"""
        
        # Set OpenAI API key
        if openai_api_key:
            openai.api_key = openai_api_key
            self.openai_api_key = openai_api_key
        elif os.getenv('OPENAI_API_KEY'):
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
        else:
            print("⚠️ Warning: OpenAI API key not provided. RAG will use fallback responses.")
            self.openai_api_key = None

        # Initialize RAG system
        self.rag_enabled = False
        if RAG_AVAILABLE:
            try:
                print("🚀 Initializing RAG Vector Database...")
                self.rag_db = RAGVectorDatabase(use_gpu=use_gpu)
                
                print("🔗 Initializing RAG Chain...")
                self.rag_chain = RAGChain(self.rag_db, self.openai_api_key)
                
                self.rag_enabled = True
                print("✅ RAG system initialized successfully")
                
                # Load data if not already loaded
                self._initialize_rag_data()
                
            except Exception as e:
                print(f"❌ Error initializing RAG system: {str(e)}")
                self.rag_enabled = False
        
        # Initialize fallback database (for compatibility)
        try:
            from simple_food_db import SimpleFoodRecommendationDB
            self.fallback_db = SimpleFoodRecommendationDB()
        except ImportError:
            self.fallback_db = None
            print("⚠️ Fallback database not available")

        # System prompt for traditional AI mode
        self.system_prompt = """
        Bạn là một chuyên gia tư vấn ẩm thực và dinh dưỡng chuyên nghiệp với khả năng truy xuất thông tin từ cơ sở dữ liệu món ăn và tương tác khách hàng.

        MỤC TIÊU CHÍNH:
        - Giúp người tiêu dùng lựa chọn thực đơn vừa ngon miệng, vừa đảm bảo sức khỏe
        - Ưu tiên an toàn thực phẩm và vệ sinh dinh dưỡng  
        - Tư vấn phù hợp với từng nhóm đối tượng (trẻ em, người già, người bệnh, v.v.)
        - Sử dụng thông tin từ cơ sở dữ liệu để đưa ra gợi ý cụ thể và chính xác

        PHONG CÁCH TƯ VẤN:
        - Thân thiện, nhiệt tình và dễ hiểu
        - Dựa trên dữ liệu thực tế từ hệ thống
        - Đưa ra gợi ý món ăn cụ thể khi có thể
        - Giải thích rõ ràng lý do đằng sau mỗi lời khuyên
        """

    def _initialize_rag_data(self):
        """Initialize RAG data from CSV files"""
        if not self.rag_enabled:
            return
        
        try:
            print("📊 Checking RAG database content...")
            stats = self.rag_db.get_collection_stats()
            
            # Check if data is already loaded
            has_data = any(
                collection_data.get('document_count', 0) > 0 
                for collection_data in stats.values() 
                if isinstance(collection_data, dict)
            )
            
            if has_data:
                print("✅ RAG database already contains data")
                return
            
            print("📁 Loading data into RAG database...")
            
            # Load interactions data
            if os.path.exists('interactions_encoded.csv'):
                print("📋 Loading customer interactions...")
                self.rag_db.add_interactions_from_csv('interactions_encoded.csv')
            
            # Load customer data as recipe data if available
            if os.path.exists('customers_data.csv'):
                print("👥 Processing customer preferences...")
                # Convert customer data to searchable format
                self._load_customer_preferences()
            
            # Add nutrition knowledge
            from rag_langchain_integration import setup_nutrition_knowledge
            knowledge_data = setup_nutrition_knowledge()
            self.rag_db.add_nutrition_knowledge(knowledge_data)
            
            print("✅ RAG data initialization complete")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize RAG data: {str(e)}")

    def _load_customer_preferences(self):
        """Load customer preferences as searchable content"""
        try:
            df = pd.read_csv('customers_data.csv')
            
            # Create synthetic recipe preferences based on customer data
            preference_docs = []
            
            for _, customer in df.iterrows():
                # Create preference document
                pref_text = f"""
                Khách hàng {customer.get('customer_id', '')} từ {customer.get('region', '')}
                Giới tính: {customer.get('gender', '')}
                Nhóm tuổi: {customer.get('age_group', '')}
                """
                
                preference_docs.append({
                    'topic': f'Khách hàng {customer.get("customer_id", "")}',
                    'category': 'customer_preference',
                    'content': pref_text,
                    'additional_info': f'Khu vực: {customer.get("region", "")}'
                })
            
            if preference_docs:
                self.rag_db.add_nutrition_knowledge(preference_docs)
                print(f"✅ Added {len(preference_docs)} customer preference documents")
                
        except Exception as e:
            print(f"⚠️ Error loading customer preferences: {str(e)}")

    @cached(expire_hours=1)
    def process_user_request(self, user_query: str, user_id: str = None, location: str = None) -> Dict:
        """Process user request using RAG system"""
        try:
            start_time = datetime.now()
            
            if self.rag_enabled:
                # Use RAG system
                print("🧠 Processing query with RAG system...")
                
                # Determine which collections to search based on query
                collections = ['nutrition', 'recipes']
                
                # Add interactions if user_id is provided
                if user_id:
                    collections.append('interactions')
                
                # Query RAG system
                rag_result = self.rag_chain.query(user_query, include_collections=collections)
                
                # Extract recommended recipes from context
                recommended_recipes = self._extract_recipes_from_context(rag_result.get('context', ''))
                
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return {
                    "ai_response": rag_result['answer'],
                    "recommended_recipes": recommended_recipes,
                    "customer_info": {"user_id": user_id, "location": location},
                    "nearby_restaurants": [],
                    "timestamp": datetime.now().isoformat(),
                    "processing_time_ms": processing_time,
                    "rag_enabled": True,
                    "source": rag_result.get('source', 'rag'),
                    "context_used": rag_result.get('context', '')[:500] + "..." if len(rag_result.get('context', '')) > 500 else rag_result.get('context', '')
                }
            
            else:
                # Fallback to traditional method
                print("🔄 Using fallback AI agent...")
                return self._process_fallback_request(user_query, user_id, location)
                
        except Exception as e:
            print(f"❌ Error processing user request: {str(e)}")
            return self._generate_error_response(str(e))

    def _extract_recipes_from_context(self, context: str) -> List[Dict]:
        """Extract recipe information from RAG context"""
        recipes = []
        
        try:
            lines = context.split('\n')
            for line in lines:
                if 'Món:' in line:
                    recipe_name = line.split('Món:')[1].strip()
                    if recipe_name and recipe_name not in [r.get('recipe_name', '') for r in recipes]:
                        recipes.append({
                            'recipe_name': recipe_name,
                            'source': 'rag_retrieval'
                        })
        except Exception as e:
            print(f"⚠️ Error extracting recipes: {str(e)}")
        
        return recipes[:5]  # Limit to 5 recipes

    def _process_fallback_request(self, user_query: str, user_id: str = None, location: str = None) -> Dict:
        """Process request using fallback method"""
        try:
            # Try OpenAI API first
            if hasattr(openai, 'api_key') and openai.api_key:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_query}
                    ],
                    max_tokens=1000,
                    temperature=0.7
                )
                ai_response = response['choices'][0]['message']['content']
            else:
                ai_response = self._generate_simple_fallback(user_query)
            
            # Get some recommended recipes from fallback database
            recommended_recipes = []
            if self.fallback_db:
                try:
                    search_results = self.fallback_db.search_recipes(user_query, n_results=3)
                    if search_results and search_results.get('metadatas'):
                        for metadata in search_results['metadatas'][0]:
                            recommended_recipes.append({
                                'recipe_name': metadata.get('recipe_name', 'Unknown'),
                                'source': 'fallback_db'
                            })
                except Exception as e:
                    print(f"⚠️ Error getting fallback recipes: {str(e)}")
            
            return {
                "ai_response": ai_response,
                "recommended_recipes": recommended_recipes,
                "customer_info": {"user_id": user_id, "location": location},
                "nearby_restaurants": [],
                "timestamp": datetime.now().isoformat(),
                "rag_enabled": False,
                "source": "fallback"
            }
            
        except Exception as e:
            return self._generate_error_response(str(e))

    def _generate_simple_fallback(self, user_query: str) -> str:
        """Generate simple fallback response"""
        query_lower = user_query.lower()
        
        if "giảm cân" in query_lower:
            return """
🏃‍♀️ Để giảm cân hiệu quả, tôi khuyên bạn:

1. **Món ăn ít calo, nhiều chất xơ:**
   - Salad rau xanh với protein nạc
   - Canh rau củ
   - Cơm gạo lức với thịt nạc

2. **Nguyên tắc ăn uống:**
   - Ăn nhiều bữa nhỏ (5-6 bữa/ngày)
   - Uống đủ nước (2-3 lít/ngày)
   - Hạn chế đồ chiên, ngọt, fast food

3. **Gợi ý thực đơn:**
   - Sáng: Yến mạch + trái cây
   - Trưa: Cơm gạo lức + rau + cá
   - Tối: Salad + protein nạc

💡 Kết hợp với vận động 30 phút/ngày để đạt hiệu quả tốt nhất!
"""
        
        elif "tăng cân" in query_lower:
            return """
💪 Để tăng cân lành mạnh, bạn nên:

1. **Tăng calo với thực phẩm bổ dưỡng:**
   - Hạt, các loại nut
   - Avocado, chuối
   - Thịt, cá, trứng

2. **Ăn thường xuyên:**
   - 6-8 bữa nhỏ/ngày
   - Thêm snack giữa các bữa chính
   - Uống sữa, sinh tố

3. **Món ăn gợi ý:**
   - Cháo thịt, cháo cá
   - Bánh mì với topping đầy đủ
   - Cơm với nhiều món phụ

🎯 Mục tiêu: Tăng 0.5-1kg/tháng một cách an toàn!
"""
        
        else:
            return """
🍽️ Cảm ơn bạn đã sử dụng dịch vụ tư vấn dinh dưỡng!

Để được tư vấn chính xác nhất, bạn có thể chia sẻ:
- Mục tiêu của bạn (giảm cân, tăng cân, khỏe mạnh)
- Tình trạng sức khỏe hiện tại
- Sở thích ăn uống
- Ngân sách và thời gian

💡 Tôi sẽ đưa ra lời khuyên phù hợp và gợi ý món ăn cụ thể!
"""

    def _generate_error_response(self, error_message: str) -> Dict:
        """Generate error response"""
        return {
            "ai_response": f"Xin lỗi, đã có lỗi xảy ra khi xử lý yêu cầu của bạn: {error_message}. Vui lòng thử lại sau.",
            "recommended_recipes": [],
            "customer_info": {},
            "nearby_restaurants": [],
            "timestamp": datetime.now().isoformat(),
            "rag_enabled": self.rag_enabled,
            "source": "error",
            "error": error_message
        }

    def get_system_stats(self) -> Dict:
        """Get comprehensive system statistics"""
        stats = {
            "rag_enabled": self.rag_enabled,
            "openai_enabled": self.openai_api_key is not None,
            "caching_enabled": CACHING_ENABLED,
            "timestamp": datetime.now().isoformat()
        }
        
        if self.rag_enabled:
            try:
                rag_stats = self.rag_chain.get_stats()
                stats.update(rag_stats)
            except Exception as e:
                stats["rag_error"] = str(e)
        
        if self.fallback_db:
            try:
                fallback_stats = self.fallback_db.get_collection_stats()
                stats["fallback_db"] = fallback_stats
            except Exception as e:
                stats["fallback_db_error"] = str(e)
        
        return stats

def get_enhanced_rag_agent(openai_api_key: str = None, use_gpu: bool = True) -> EnhancedRAGAgent:
    """Factory function to get Enhanced RAG Agent instance"""
    return EnhancedRAGAgent(openai_api_key=openai_api_key, use_gpu=use_gpu)

def main():
    """Main function to test Enhanced RAG Agent"""
    print("🚀 Testing Enhanced RAG Agent...")
    
    # Initialize agent
    agent = EnhancedRAGAgent(use_gpu=True)
    
    # Test queries
    test_queries = [
        "Tôi muốn giảm cân, gợi ý món ăn phù hợp",
        "Người tiểu đường nên ăn những món gì?",
        "Thực đơn tăng cân cho người gầy",
        "Món ăn bổ dưỡng cho bà bầu",
        "Món chay giàu protein cho người tập gym"
    ]
    
    print("\n🔍 Testing queries...")
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        result = agent.process_user_request(query, user_id="test_user")
        print(f"✅ Response: {result['ai_response'][:200]}...")
        print(f"📊 Source: {result.get('source', 'unknown')}")
        print(f"🍽️ Recipes found: {len(result.get('recommended_recipes', []))}")
    
    # Display stats
    print("\n📊 System Statistics:")
    stats = agent.get_system_stats()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key}: {sub_value}")
        else:
            print(f"  {key}: {value}")
    
    print("\n✅ Enhanced RAG Agent test complete!")

if __name__ == "__main__":
    main()
