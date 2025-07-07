#!/usr/bin/env python3
"""
Advanced RAG with LangChain for RTX 3050 Ti
Food Recommendation System with intelligent GPU memory management
"""

import os
import gc
import torch
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np
import time
import logging
from typing import List, Dict, Optional, Any
import json

# LangChain imports
try:
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.vectorstores import Chroma
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
    from langchain.chains import RetrievalQA
    from langchain.llms import HuggingFacePipeline
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain not available. Install with: pip install langchain transformers")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedRAGSystem:
    def __init__(self, features_dir: str = "./rag_features", use_gpu: bool = True, use_langchain: bool = True):
        """
        Advanced RAG System optimized for RTX 3050 Ti with LangChain integration
        """
        self.features_dir = features_dir
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.use_langchain = use_langchain and LANGCHAIN_AVAILABLE
        self.device = 'cuda' if self.use_gpu else 'cpu'
        
        logger.info("🚀 Advanced RAG System for Food Recommendations")
        logger.info(f"🔧 Device: {self.device}")
        logger.info(f"🔗 LangChain: {'Enabled' if self.use_langchain else 'Disabled'}")
        
        self._setup_gpu_optimization()
        self._initialize_components()
        
    def _setup_gpu_optimization(self):
        """Setup GPU optimization for RTX 3050 Ti"""
        if self.use_gpu:
            torch.cuda.empty_cache()
            
            # Get GPU info
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            logger.info(f"🎮 GPU: {gpu_name}")
            logger.info(f"🎮 VRAM: {gpu_memory:.1f}GB")
            
            # RTX 3050 Ti specific optimizations
            if "3050" in gpu_name:
                self.batch_size = 8  # Conservative for 3GB
                self.max_length = 256  # Shorter sequences
                self.embedding_dim = 384  # Smaller embeddings
                logger.info("🎯 RTX 3050 Ti optimizations applied")
            else:
                self.batch_size = 16
                self.max_length = 512
                self.embedding_dim = 768
        else:
            self.batch_size = 16
            self.max_length = 512
            self.embedding_dim = 384
    
    def _initialize_components(self):
        """Initialize embedding models and vector stores"""
        try:
            logger.info("1️⃣ Initializing embedding model...")
            
            if self.use_langchain:
                # LangChain embeddings
                self.embeddings = HuggingFaceEmbeddings(
                    model_name='all-MiniLM-L6-v2',
                    model_kwargs={'device': self.device},
                    encode_kwargs={'batch_size': self.batch_size}
                )
                logger.info("   ✅ LangChain embeddings loaded")
            else:
                # Direct SentenceTransformer
                self.model = SentenceTransformer(
                    'all-MiniLM-L6-v2',
                    device=self.device
                )
                logger.info("   ✅ SentenceTransformer loaded")
            
            # Initialize ChromaDB
            logger.info("2️⃣ Setting up vector stores...")
            self.chroma_client = chromadb.Client()
            self.vector_stores = {}
            self.collections = {}
            
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=300,  # Smaller chunks for 3GB GPU
                chunk_overlap=50,
                length_function=len
            )
            
            logger.info("   ✅ Vector stores ready")
            
            # Initialize LLM for Q&A (optional)
            if self.use_langchain and self.use_gpu:
                self._initialize_llm()
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            # Fallback to CPU
            if self.use_gpu:
                logger.info("🔄 Falling back to CPU...")
                self.use_gpu = False
                self.device = 'cpu'
                self._initialize_components()
            else:
                raise
    
    def _initialize_llm(self):
        """Initialize small LLM for Q&A (RTX 3050 Ti compatible)"""
        try:
            logger.info("3️⃣ Loading small LLM for Q&A...")
            
            # Use a small, efficient model for 3GB GPU
            model_name = "microsoft/DialoGPT-small"
            
            # Check available GPU memory
            if torch.cuda.is_available():
                free_memory = torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated()
                free_gb = free_memory / 1024**3
                
                if free_gb > 1.5:  # Only load if enough memory
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    model = AutoModelForCausalLM.from_pretrained(
                        model_name,
                        torch_dtype=torch.float16,  # Use half precision
                        device_map="auto"
                    )
                    
                    text_generator = pipeline(
                        "text-generation",
                        model=model,
                        tokenizer=tokenizer,
                        max_new_tokens=100,
                        do_sample=True,
                        temperature=0.7,
                        device=0
                    )
                    
                    self.llm = HuggingFacePipeline(pipeline=text_generator)
                    logger.info("   ✅ Small LLM loaded")
                else:
                    logger.warning("   ⚠️ Insufficient GPU memory for LLM, skipping...")
                    self.llm = None
            else:
                self.llm = None
                
        except Exception as e:
            logger.warning(f"⚠️ LLM initialization failed: {e}")
            self.llm = None
    
    def _create_documents_from_csv(self, csv_file: str, text_column: str, metadata_columns: List[str] = None) -> List[Document]:
        """Create LangChain documents from CSV"""
        csv_path = os.path.join(self.features_dir, csv_file)
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        df = pd.read_csv(csv_path)
        documents = []
        
        # Limit records for GPU memory
        max_records = 1000 if self.use_gpu else 2000
        df = df.head(max_records)
        
        for idx, row in df.iterrows():
            text = str(row[text_column]) if pd.notna(row[text_column]) else ""
            
            if len(text.strip()) > 5:
                # Create metadata
                metadata = {'source': csv_file, 'row_id': idx}
                
                if metadata_columns:
                    for col in metadata_columns:
                        if col in df.columns and pd.notna(row[col]):
                            metadata[col] = str(row[col])[:100]
                
                # Create document
                doc = Document(
                    page_content=text[:400],  # Limit length
                    metadata=metadata
                )
                documents.append(doc)
        
        logger.info(f"   📄 Created {len(documents)} documents from {csv_file}")
        return documents
    
    def load_feature_with_langchain(self, feature_name: str, csv_file: str, text_column: str, metadata_columns: List[str] = None):
        """Load feature using LangChain"""
        logger.info(f"\n📊 Loading feature with LangChain: {feature_name}")
        
        try:
            # Create documents
            documents = self._create_documents_from_csv(csv_file, text_column, metadata_columns)
            
            if not documents:
                logger.warning(f"⚠️ No documents created for {feature_name}")
                return False
            
            # Split documents
            split_docs = self.text_splitter.split_documents(documents)
            logger.info(f"   📝 Split into {len(split_docs)} chunks")
            
            # Create vector store
            collection_name = f"langchain_{feature_name}"
            
            # Clear GPU cache before vector store creation
            if self.use_gpu:
                torch.cuda.empty_cache()
            
            vector_store = Chroma.from_documents(
                documents=split_docs,
                embedding=self.embeddings,
                collection_name=collection_name,
                persist_directory=f"./chroma_db_{feature_name}"
            )
            
            self.vector_stores[feature_name] = vector_store
            
            logger.info(f"✅ Feature '{feature_name}' loaded with LangChain")
            
            # Memory cleanup
            if self.use_gpu:
                torch.cuda.empty_cache()
            gc.collect()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load {feature_name} with LangChain: {e}")
            return False
    
    def create_qa_chain(self, feature_name: str):
        """Create Q&A chain for a specific feature"""
        if feature_name not in self.vector_stores:
            logger.error(f"❌ Vector store for '{feature_name}' not found")
            return None
        
        if not self.llm:
            logger.warning("⚠️ LLM not available for Q&A")
            return None
        
        try:
            retriever = self.vector_stores[feature_name].as_retriever(
                search_kwargs={"k": 3}  # Limit results for memory
            )
            
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True
            )
            
            logger.info(f"✅ Q&A chain created for '{feature_name}'")
            return qa_chain
            
        except Exception as e:
            logger.error(f"❌ Failed to create Q&A chain: {e}")
            return None
    
    def search_with_langchain(self, feature_name: str, query: str, k: int = 5):
        """Search using LangChain vector store"""
        if feature_name not in self.vector_stores:
            logger.error(f"❌ Vector store for '{feature_name}' not found")
            return None
        
        try:
            logger.info(f"🔍 LangChain search in '{feature_name}': '{query[:50]}...'")
            
            # Similarity search
            results = self.vector_stores[feature_name].similarity_search_with_score(
                query, k=k
            )
            
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'similarity_score': 1 - score  # Convert distance to similarity
                })
            
            logger.info(f"✅ Found {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ LangChain search failed: {e}")
            return None
    
    def ask_question(self, feature_name: str, question: str):
        """Ask a question using the Q&A chain"""
        qa_chain = self.create_qa_chain(feature_name)
        
        if not qa_chain:
            logger.warning("⚠️ Q&A chain not available, falling back to search")
            return self.search_with_langchain(feature_name, question)
        
        try:
            logger.info(f"❓ Asking question: '{question}'")
            
            # Clear GPU cache before inference
            if self.use_gpu:
                torch.cuda.empty_cache()
            
            response = qa_chain({"query": question})
            
            result = {
                'answer': response['result'],
                'source_documents': [
                    {
                        'content': doc.page_content,
                        'metadata': doc.metadata
                    }
                    for doc in response.get('source_documents', [])
                ]
            }
            
            logger.info("✅ Question answered")
            return result
            
        except Exception as e:
            logger.error(f"❌ Question answering failed: {e}")
            return None
    
    def load_all_features_advanced(self):
        """Load all features with advanced LangChain processing"""
        features_config = [
            {
                'name': 'recipes',
                'csv': 'recipes.csv',
                'text_column': 'name',
                'metadata_columns': ['category', 'cuisine', 'cooking_time']
            },
            {
                'name': 'nutrition',
                'csv': 'nutrition_info.csv',
                'text_column': 'food_name',
                'metadata_columns': ['calories', 'protein', 'carbs']
            },
            {
                'name': 'customers',
                'csv': 'customer_profiles.csv',
                'text_column': 'dietary_restrictions',
                'metadata_columns': ['age', 'health_conditions', 'preferences']
            }
        ]
        
        logger.info("🎯 Loading all features with advanced LangChain processing...")
        
        success_count = 0
        for config in features_config:
            if self.use_langchain:
                success = self.load_feature_with_langchain(
                    config['name'],
                    config['csv'],
                    config['text_column'],
                    config.get('metadata_columns')
                )
            else:
                # Fallback to basic loading
                success = self.load_feature_basic(
                    config['name'],
                    config['csv'],
                    config['text_column']
                )
            
            if success:
                success_count += 1
            
            # Memory management between features
            if self.use_gpu:
                torch.cuda.empty_cache()
            gc.collect()
            time.sleep(2)  # Pause between features
        
        logger.info(f"✅ Successfully loaded {success_count}/{len(features_config)} features")
        return success_count == len(features_config)
    
    def demo_advanced_search(self):
        """Demo advanced search and Q&A functionality"""
        logger.info("\n🔍 Demo: Advanced RAG Search & Q&A")
        
        test_queries = [
            "What are some healthy chicken recipes?",
            "Show me vegetarian high-protein foods",
            "What breakfast options are good for diabetics?",
            "Find low-sodium meal ideas"
        ]
        
        for query in test_queries:
            logger.info(f"\n🔎 Query: '{query}'")
            
            for feature_name in self.vector_stores.keys():
                logger.info(f"  📚 Searching in {feature_name}...")
                
                # Try Q&A first
                if self.llm:
                    answer = self.ask_question(feature_name, query)
                    if answer:
                        logger.info(f"    💬 Answer: {answer['answer'][:100]}...")
                        continue
                
                # Fallback to search
                results = self.search_with_langchain(feature_name, query, k=2)
                if results:
                    for i, result in enumerate(results[:2]):
                        score = result['similarity_score']
                        content = result['content'][:80]
                        logger.info(f"    {i+1}. {content}... (score: {score:.3f})")

def main():
    """Main function to run Advanced RAG System"""
    try:
        # Initialize advanced RAG system
        rag_system = AdvancedRAGSystem(
            use_gpu=True,
            use_langchain=True
        )
        
        # Load all features
        success = rag_system.load_all_features_advanced()
        
        if success:
            logger.info("🎉 Advanced RAG System ready!")
            
            # Demo functionality
            rag_system.demo_advanced_search()
            
            logger.info("\n✅ Advanced RAG System with LangChain ready for production!")
        else:
            logger.warning("⚠️ Some features failed to load")
        
    except Exception as e:
        logger.error(f"❌ System failed: {e}")
        raise

if __name__ == "__main__":
    main()
