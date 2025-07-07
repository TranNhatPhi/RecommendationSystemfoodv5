#!/usr/bin/env python3
"""
RTX 3050 Ti RAG Setup and Test Script
Automated installation and testing for 3GB GPU
"""

import subprocess
import sys
import os
import torch
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_gpu():
    """Check GPU availability and specifications"""
    logger.info("🎮 Checking GPU availability...")
    
    if torch.cuda.is_available():
        gpu_count = torch.cuda.device_count()
        logger.info(f"✅ Found {gpu_count} GPU(s)")
        
        for i in range(gpu_count):
            gpu_name = torch.cuda.get_device_name(i)
            gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
            logger.info(f"   GPU {i}: {gpu_name} ({gpu_memory:.1f}GB)")
            
            # Check if RTX 3050 Ti
            if "3050" in gpu_name:
                logger.info("🎯 RTX 3050 Ti detected - optimizations will be applied")
                return True, gpu_memory
        
        return True, gpu_memory
    else:
        logger.warning("⚠️ No GPU detected - will use CPU mode")
        return False, 0

def install_requirements():
    """Install required packages"""
    logger.info("📦 Installing requirements...")
    
    try:
        # Install PyTorch with CUDA support
        logger.info("Installing PyTorch with CUDA 11.8...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "torch", "torchvision", "torchaudio", 
            "--index-url", "https://download.pytorch.org/whl/cu118"
        ])
        
        # Install other requirements
        logger.info("Installing other requirements...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "rtx3050_requirements.txt"
        ])
        
        logger.info("✅ All packages installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Installation failed: {e}")
        return False

def test_basic_imports():
    """Test if all required packages can be imported"""
    logger.info("🧪 Testing basic imports...")
    
    imports_to_test = [
        ('torch', 'PyTorch'),
        ('chromadb', 'ChromaDB'),
        ('sentence_transformers', 'SentenceTransformers'),
        ('pandas', 'Pandas'),
        ('numpy', 'NumPy'),
        ('transformers', 'Transformers'),
        ('langchain', 'LangChain')
    ]
    
    failed_imports = []
    
    for module, name in imports_to_test:
        try:
            __import__(module)
            logger.info(f"   ✅ {name}")
        except ImportError as e:
            logger.error(f"   ❌ {name}: {e}")
            failed_imports.append(name)
    
    if failed_imports:
        logger.error(f"❌ Failed imports: {', '.join(failed_imports)}")
        return False
    else:
        logger.info("✅ All imports successful")
        return True

def test_gpu_torch():
    """Test PyTorch GPU functionality"""
    logger.info("🎮 Testing PyTorch GPU functionality...")
    
    try:
        if torch.cuda.is_available():
            # Test tensor creation on GPU
            device = torch.device('cuda')
            test_tensor = torch.randn(100, 100).to(device)
            result = torch.matmul(test_tensor, test_tensor.T)
            
            logger.info("   ✅ GPU tensor operations working")
            
            # Test memory management
            torch.cuda.empty_cache()
            allocated = torch.cuda.memory_allocated() / 1024**2
            reserved = torch.cuda.memory_reserved() / 1024**2
            
            logger.info(f"   📊 GPU Memory - Allocated: {allocated:.1f}MB, Reserved: {reserved:.1f}MB")
            return True
        else:
            logger.warning("   ⚠️ No GPU available for testing")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ GPU test failed: {e}")
        return False

def test_chromadb():
    """Test ChromaDB functionality"""
    logger.info("🗃️ Testing ChromaDB...")
    
    try:
        import chromadb
        
        # Create test client
        client = chromadb.Client()
        
        # Create test collection
        collection = client.create_collection("test_collection")
        
        # Add test data
        collection.add(
            embeddings=[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
            documents=["Test document 1", "Test document 2"],
            metadatas=[{"source": "test1"}, {"source": "test2"}],
            ids=["id1", "id2"]
        )
        
        # Test query
        results = collection.query(
            query_embeddings=[[1.1, 2.1, 3.1]],
            n_results=1
        )
        
        if results['documents'][0]:
            logger.info("   ✅ ChromaDB working correctly")
            
            # Cleanup
            client.delete_collection("test_collection")
            return True
        else:
            logger.error("   ❌ ChromaDB query returned empty results")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ ChromaDB test failed: {e}")
        return False

def test_sentence_transformers():
    """Test SentenceTransformers with GPU"""
    logger.info("🔤 Testing SentenceTransformers...")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # Test with CPU first
        model_cpu = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        embeddings_cpu = model_cpu.encode(["Test sentence"], show_progress_bar=False)
        logger.info(f"   ✅ CPU embeddings shape: {embeddings_cpu.shape}")
        
        # Test with GPU if available
        if torch.cuda.is_available():
            model_gpu = SentenceTransformer('all-MiniLM-L6-v2', device='cuda')
            embeddings_gpu = model_gpu.encode(["Test sentence"], show_progress_bar=False)
            logger.info(f"   ✅ GPU embeddings shape: {embeddings_gpu.shape}")
            
            # Memory cleanup
            del model_gpu
            torch.cuda.empty_cache()
        
        return True
        
    except Exception as e:
        logger.error(f"   ❌ SentenceTransformers test failed: {e}")
        return False

def check_data_files():
    """Check if required data files exist"""
    logger.info("📁 Checking data files...")
    
    required_files = [
        './rag_features/recipes.csv',
        './rag_features/nutrition_info.csv',
        './rag_features/customer_profiles.csv',
        './rag_features/interactions.csv'
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / 1024  # KB
            logger.info(f"   ✅ {file_path} ({file_size:.1f}KB)")
            existing_files.append(file_path)
        else:
            logger.warning(f"   ❌ Missing: {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        logger.warning("⚠️ Some data files are missing. Run feature_splitter.py first.")
        return False, existing_files
    else:
        logger.info("✅ All required data files found")
        return True, existing_files

def run_quick_rag_test():
    """Run a quick RAG system test"""
    logger.info("🚀 Running quick RAG system test...")
    
    try:
        # Import our optimized RAG system
        sys.path.append('.')
        from rtx3050_optimized_rag import RTX3050RAGSystem
        
        # Initialize system
        rag_system = RTX3050RAGSystem(use_gpu=torch.cuda.is_available())
        
        # Try to load one feature
        success = rag_system.load_feature_optimized(
            'test_recipes', 
            'recipes.csv', 
            'name', 
            max_records=50
        )
        
        if success:
            # Test search
            results = rag_system.search_optimized('test_recipes', 'chicken recipe', n_results=3)
            
            if results and results['documents']:
                logger.info(f"   ✅ RAG test successful - found {len(results['documents'])} results")
                logger.info(f"   📝 Sample result: {results['documents'][0][:100]}...")
                return True
            else:
                logger.error("   ❌ RAG search returned no results")
                return False
        else:
            logger.error("   ❌ Failed to load test feature")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ RAG test failed: {e}")
        return False

def main():
    """Main setup and test function"""
    logger.info("🎯 RTX 3050 Ti RAG System Setup & Test")
    logger.info("=" * 60)
    
    # Step 1: Check GPU
    has_gpu, gpu_memory = check_gpu()
    
    # Step 2: Install requirements
    if not install_requirements():
        logger.error("❌ Installation failed. Please check errors above.")
        return False
    
    # Step 3: Test basic imports
    if not test_basic_imports():
        logger.error("❌ Import tests failed. Please check installation.")
        return False
    
    # Step 4: Test GPU functionality
    if has_gpu:
        test_gpu_torch()
    
    # Step 5: Test ChromaDB
    if not test_chromadb():
        logger.error("❌ ChromaDB test failed.")
        return False
    
    # Step 6: Test SentenceTransformers
    if not test_sentence_transformers():
        logger.error("❌ SentenceTransformers test failed.")
        return False
    
    # Step 7: Check data files
    data_ok, existing_files = check_data_files()
    
    # Step 8: Run RAG system test if data is available
    if data_ok:
        if run_quick_rag_test():
            logger.info("🎉 All tests passed! RTX 3050 Ti RAG system is ready!")
        else:
            logger.warning("⚠️ RAG test failed, but basic components work.")
    else:
        logger.info("ℹ️ Skipping RAG test due to missing data files.")
        logger.info("   Run feature_splitter.py first to prepare data files.")
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("🎯 Setup Summary:")
    logger.info(f"   GPU Available: {'Yes' if has_gpu else 'No'}")
    if has_gpu:
        logger.info(f"   GPU Memory: {gpu_memory:.1f}GB")
    logger.info(f"   Data Files: {'Ready' if data_ok else 'Missing - run feature_splitter.py'}")
    logger.info("   Core Libraries: ✅ Working")
    
    if data_ok:
        logger.info("\n🚀 You can now run:")
        logger.info("   python rtx3050_optimized_rag.py")
        logger.info("   python advanced_langchain_rag.py")
    else:
        logger.info("\n📋 Next steps:")
        logger.info("   1. Run: python feature_splitter.py")
        logger.info("   2. Then run: python rtx3050_optimized_rag.py")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
