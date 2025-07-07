from langchain.schema import Document
from langchain.vectorstores.base import VectorStore
from langchain.embeddings.base import Embeddings
from langchain.schema.retriever import BaseRetriever
from langchain.schema import BaseRetriever as LangChainBaseRetriever
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.schema.document import Document
from typing import List, Dict, Any, Optional
from rag_vector_db import RAGVectorDatabase
import numpy as np

class ChromaDBEmbeddings(Embeddings):
    """Custom embeddings class for ChromaDB integration with LangChain"""
    
    def __init__(self, rag_db: RAGVectorDatabase):
        self.rag_db = rag_db
        self.embedding_model = rag_db.embedding_model
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        return self.embedding_model.encode(texts, convert_to_tensor=False).tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        return self.embedding_model.encode([text], convert_to_tensor=False)[0].tolist()

class ChromaDBRetriever(LangChainBaseRetriever):
    """Custom retriever for ChromaDB integration with LangChain"""
    
    def __init__(self, rag_db: RAGVectorDatabase, collection_name: str = 'recipes', k: int = 10):
        super().__init__()
        self._rag_db = rag_db
        self._collection_name = collection_name
        self._k = k
    
    def _get_relevant_documents(
        self, 
        query: str, 
        *, 
        run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Retrieve relevant documents for a query"""
        try:
            # Search using RAG database
            results = self._rag_db.search_similar(
                query=query, 
                collection_name=self._collection_name, 
                n_results=self._k
            )
            
            documents = []
            
            if results['documents'][0]:
                for doc, metadata, distance in zip(
                    results['documents'][0], 
                    results['metadatas'][0], 
                    results.get('distances', [[]] * len(results['documents'][0]))[0]
                ):
                    # Add distance to metadata
                    metadata['similarity_score'] = 1 - distance if distance else 1.0
                    
                    # Create LangChain Document
                    documents.append(Document(
                        page_content=doc,
                        metadata=metadata
                    ))
            
            return documents
            
        except Exception as e:
            print(f"❌ Error retrieving documents: {str(e)}")
            return []

class RAGChain:
    """RAG Chain combining retrieval and generation using LangChain and OpenAI"""
    
    def __init__(self, rag_db: RAGVectorDatabase, openai_api_key: str = None):
        self.rag_db = rag_db
        self.openai_api_key = openai_api_key
        
        # Initialize retrievers for different collections
        self.retrievers = {
            'recipes': ChromaDBRetriever(rag_db, 'recipes', k=5),
            'interactions': ChromaDBRetriever(rag_db, 'interactions', k=3),
            'nutrition': ChromaDBRetriever(rag_db, 'nutrition', k=4)
        }
        
        # Setup LangChain components
        self._setup_langchain()
    
    def _setup_langchain(self):
        """Setup LangChain components"""
        try:
            from langchain.chat_models import ChatOpenAI
            from langchain.prompts import ChatPromptTemplate
            from langchain.schema.runnable import RunnablePassthrough
            from langchain.schema.output_parser import StrOutputParser
            
            # Initialize OpenAI LLM
            if self.openai_api_key:
                self.llm = ChatOpenAI(
                    temperature=0.7,
                    model_name="gpt-3.5-turbo",
                    openai_api_key=self.openai_api_key
                )
            else:
                print("⚠️ OpenAI API key not provided, using fallback responses")
                self.llm = None
            
            # Create comprehensive prompt template
            self.prompt = ChatPromptTemplate.from_template("""
            Bạn là một chuyên gia tư vấn ẩm thực và dinh dưỡng chuyên nghiệp. Sử dụng thông tin dưới đây để đưa ra lời tư vấn chi tiết và hữu ích.

            THÔNG TIN TỪ CƠ SỞ DỮ LIỆU:
            {context}

            CÂU HỎI CỦA NGƯỜI DÙNG:
            {question}

            HƯỚNG DẪN TRẢ LỜI:
            1. Phân tích nhu cầu của người dùng
            2. Đưa ra gợi ý món ăn cụ thể dựa trên thông tin đã có
            3. Giải thích lý do tại sao những món này phù hợp
            4. Đưa ra lời khuyên về dinh dưỡng và cách chế biến
            5. Nếu có thông tin về tương tác khách hàng, hãy tham khảo để đưa ra gợi ý phù hợp

            TRẢ LỜI:
            """)
            
            print("✅ LangChain components initialized successfully")
            
        except ImportError as e:
            print(f"⚠️ LangChain import error: {str(e)}")
            self.llm = None
            self.prompt = None
        except Exception as e:
            print(f"❌ Error setting up LangChain: {str(e)}")
            self.llm = None
            self.prompt = None
    
    def retrieve_context(self, query: str, include_collections: List[str] = None) -> str:
        """Retrieve relevant context from multiple collections"""
        if include_collections is None:
            include_collections = ['recipes', 'nutrition', 'interactions']
        
        all_context = []
        
        for collection_name in include_collections:
            if collection_name in self.retrievers:
                try:
                    docs = self.retrievers[collection_name]._get_relevant_documents(
                        query, run_manager=None
                    )
                    
                    if docs:
                        context_section = f"\n=== THÔNG TIN TỪ {collection_name.upper()} ===\n"
                        for i, doc in enumerate(docs[:3]):  # Limit to top 3 results per collection
                            context_section += f"{i+1}. {doc.page_content}\n"
                            if doc.metadata.get('recipe_name'):
                                context_section += f"   Món: {doc.metadata['recipe_name']}\n"
                            if doc.metadata.get('similarity_score'):
                                context_section += f"   Độ tương đồng: {doc.metadata['similarity_score']:.2f}\n"
                            context_section += "\n"
                        
                        all_context.append(context_section)
                        
                except Exception as e:
                    print(f"⚠️ Error retrieving from {collection_name}: {str(e)}")
        
        return "\n".join(all_context) if all_context else "Không tìm thấy thông tin liên quan."
    
    def query(self, question: str, include_collections: List[str] = None) -> Dict[str, Any]:
        """Query the RAG system with a question"""
        try:
            # Retrieve relevant context
            context = self.retrieve_context(question, include_collections)
            
            if self.llm and self.prompt:
                # Use LangChain with OpenAI
                try:
                    from langchain.schema.runnable import RunnablePassthrough
                    from langchain.schema.output_parser import StrOutputParser
                    
                    # Create the chain
                    chain = (
                        {"context": lambda x: context, "question": RunnablePassthrough()}
                        | self.prompt
                        | self.llm
                        | StrOutputParser()
                    )
                    
                    # Generate response
                    response = chain.invoke(question)
                    
                    return {
                        'answer': response,
                        'context': context,
                        'source': 'langchain_openai',
                        'success': True
                    }
                    
                except Exception as e:
                    print(f"⚠️ LangChain error, using fallback: {str(e)}")
                    return self._generate_fallback_response(question, context)
            else:
                return self._generate_fallback_response(question, context)
                
        except Exception as e:
            print(f"❌ Error in RAG query: {str(e)}")
            return {
                'answer': 'Xin lỗi, đã có lỗi xảy ra khi xử lý câu hỏi của bạn.',
                'context': '',
                'source': 'error',
                'success': False,
                'error': str(e)
            }
    
    def _generate_fallback_response(self, question: str, context: str) -> Dict[str, Any]:
        """Generate fallback response when OpenAI is not available"""
        
        # Simple keyword-based response generation
        question_lower = question.lower()
        
        fallback_response = "Dựa trên thông tin có sẵn:\n\n"
        
        if "giảm cân" in question_lower:
            fallback_response += "🏃‍♀️ Để giảm cân hiệu quả:\n"
            fallback_response += "• Chọn món ăn ít calo, nhiều chất xơ\n"
            fallback_response += "• Tăng cường rau xanh, protein nạc\n"
            fallback_response += "• Hạn chế đồ chiên, ngọt\n\n"
        
        elif "tăng cân" in question_lower:
            fallback_response += "💪 Để tăng cân lành mạnh:\n"
            fallback_response += "• Tăng lượng calo với thực phẩm bổ dưỡng\n"
            fallback_response += "• Nhiều protein, carbohydrate phức tạp\n"
            fallback_response += "• Ăn nhiều bữa nhỏ trong ngày\n\n"
        
        elif "tiểu đường" in question_lower:
            fallback_response += "🩺 Cho người tiểu đường:\n"
            fallback_response += "• Chọn thực phẩm chỉ số đường huyết thấp\n"
            fallback_response += "• Hạn chế đường, carbohydrate đơn giản\n"
            fallback_response += "• Tăng chất xơ từ rau quả\n\n"
        
        elif "cao huyết áp" in question_lower:
            fallback_response += "❤️ Cho người cao huyết áp:\n"
            fallback_response += "• Hạn chế muối và natri\n"
            fallback_response += "• Tăng thực phẩm giàu kali\n"
            fallback_response += "• Chọn thực phẩm tươi, hạn chế chế biến sẵn\n\n"
        
        elif any(word in question_lower for word in ["mang thai", "bà bầu", "thai kỳ"]):
            fallback_response += "🤱 Cho phụ nữ mang thai:\n"
            fallback_response += "• Bổ sung acid folic, sắt, canxi\n"
            fallback_response += "• Tránh thực phẩm sống, rượu bia\n"
            fallback_response += "• Ăn nhiều bữa nhỏ\n\n"
        
        elif "chay" in question_lower:
            fallback_response += "🌱 Cho người ăn chay:\n"
            fallback_response += "• Đa dạng nguồn protein thực vật\n"
            fallback_response += "• Bổ sung vitamin B12, sắt, kẽm\n"
            fallback_response += "• Kết hợp đậu, hạt, ngũ cốc\n\n"
        
        elif any(word in question_lower for word in ["trẻ em", "trẻ con", "bé"]):
            fallback_response += "👶 Cho trẻ em:\n"
            fallback_response += "• Đầy đủ protein, canxi, vitamin D\n"
            fallback_response += "• Hạn chế đồ ngọt, đồ chiên\n"
            fallback_response += "• Khuyến khích ăn rau quả đa dạng\n\n"
        
        elif any(word in question_lower for word in ["gym", "tập luyện", "thể hình"]):
            fallback_response += "🏋️‍♂️ Cho người tập luyện:\n"
            fallback_response += "• Tăng protein: 1.6-2.2g/kg thể trọng\n"
            fallback_response += "• Carbohydrate trước tập, protein sau tập\n"
            fallback_response += "• Uống đủ nước\n\n"
        
        else:
            fallback_response += "🍽️ Gợi ý chung:\n"
            fallback_response += "• Ăn đa dạng các nhóm thực phẩm\n"
            fallback_response += "• Cân bằng protein, carbohydrate, chất béo\n"
            fallback_response += "• Tăng rau xanh, trái cây\n\n"
        
        if context and "món" in context.lower():
            fallback_response += "📋 Dựa trên dữ liệu có sẵn, hệ thống tìm thấy một số món ăn phù hợp trong cơ sở dữ liệu.\n"
        
        fallback_response += "\n💡 Để có tư vấn chi tiết hơn, vui lòng cung cấp OpenAI API key."
        
        return {
            'answer': fallback_response,
            'context': context,
            'source': 'fallback',
            'success': True
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        stats = self.rag_db.get_collection_stats()
        stats['langchain_enabled'] = self.llm is not None
        stats['openai_enabled'] = self.openai_api_key is not None
        
        return stats

def main():
    """Main function to test RAG LangChain integration"""
    print("🚀 Testing RAG LangChain Integration...")
    
    # Initialize RAG database
    from rag_vector_db import RAGVectorDatabase
    rag_db = RAGVectorDatabase(use_gpu=True)
    
    # Initialize RAG Chain
    rag_chain = RAGChain(rag_db)
    
    # Test queries
    test_queries = [
        "Tôi muốn giảm cân, gợi ý món ăn ít calo",
        "Người tiểu đường nên ăn gì?",
        "Món ăn tăng cân cho người gầy",
        "Thực đơn cho bà bầu",
        "Món chay giàu protein"
    ]
    
    print("\n🔍 Testing RAG queries...")
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        result = rag_chain.query(query)
        print(f"✅ Answer: {result['answer'][:200]}...")
        print(f"📊 Source: {result['source']}")
    
    # Display stats
    print("\n📊 RAG System Statistics:")
    stats = rag_chain.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n✅ RAG LangChain integration test complete!")

if __name__ == "__main__":
    main()
