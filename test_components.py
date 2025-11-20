"""
Component Testing Script
Test each component independently before running the full bot
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_imports():
    """Test if all required packages are installed"""
    print("\n" + "="*50)
    print("Testing Package Imports")
    print("="*50)
    
    packages = [
        ('telegram', 'python-telegram-bot'),
        ('sentence_transformers', 'sentence-transformers'),
        ('chromadb', 'chromadb'),
        ('ollama', 'ollama'),
        ('transformers', 'transformers'),
        ('torch', 'torch'),
        ('PIL', 'Pillow'),
    ]
    
    failed = []
    for package, name in packages:
        try:
            __import__(package)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} - MISSING")
            failed.append(name)
    
    if failed:
        print(f"\n❌ Missing packages: {', '.join(failed)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✅ All packages installed!")
    return True

def test_ollama():
    """Test Ollama connection"""
    print("\n" + "="*50)
    print("Testing Ollama Connection")
    print("="*50)
    
    try:
        import ollama
        
        # List models
        models = ollama.list()
        print(f"✓ Connected to Ollama")
        print(f"Available models: {[m['name'] for m in models.get('models', [])]}")
        
        # Test inference
        model_name = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        print(f"\nTesting inference with {model_name}...")
        
        response = ollama.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': 'Say "Hello, I am working!"'}]
        )
        
        print(f"Response: {response['message']['content']}")
        print("\n✅ Ollama is working!")
        return True
        
    except Exception as e:
        print(f"\n❌ Ollama error: {e}")
        print("\nTroubleshooting:")
        print("1. Start Ollama: ollama serve")
        print("2. Pull model: ollama pull llama3.2:3b")
        return False

def test_embeddings():
    """Test embedding model"""
    print("\n" + "="*50)
    print("Testing Embedding Model")
    print("="*50)
    
    try:
        from sentence_transformers import SentenceTransformer
        
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        print(f"Loading {model_name}...")
        
        model = SentenceTransformer(model_name)
        
        # Test embedding
        text = "This is a test sentence."
        embedding = model.encode(text)
        
        print(f"✓ Model loaded")
        print(f"Embedding dimension: {len(embedding)}")
        print(f"Sample embedding values: {embedding[:5]}")
        
        print("\n✅ Embeddings working!")
        return True
        
    except Exception as e:
        print(f"\n❌ Embedding error: {e}")
        return False

def test_vector_store():
    """Test ChromaDB and vector store"""
    print("\n" + "="*50)
    print("Testing Vector Store")
    print("="*50)
    
    try:
        from vector_store import VectorStore
        
        print("Initializing vector store...")
        vs = VectorStore()
        
        stats = vs.get_stats()
        print(f"✓ Vector store initialized")
        print(f"Documents: {stats['total_documents']}")
        print(f"Embedding dimensions: {stats['embedding_model']}")
        
        # Test search
        print("\nTesting search...")
        results = vs.search("What is Python?", k=2)
        
        print(f"✓ Search returned {len(results)} results")
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"  Source: {result['source']}")
            print(f"  Distance: {result['distance']:.4f}")
            print(f"  Text preview: {result['text'][:100]}...")
        
        print("\n✅ Vector store working!")
        return True
        
    except Exception as e:
        print(f"\n❌ Vector store error: {e}")
        return False

def test_vision():
    """Test vision model"""
    print("\n" + "="*50)
    print("Testing Vision Model")
    print("="*50)
    
    try:
        from vision_manager import VisionManager
        from PIL import Image
        import io
        
        print("Loading vision model (this may take a moment)...")
        vm = VisionManager()
        
        print(f"✓ Model loaded: {vm.model_name}")
        print(f"Device: {vm.device}")
        
        # Create a simple test image
        print("\nCreating test image...")
        img = Image.new('RGB', (224, 224), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes = img_bytes.getvalue()
        
        print("Generating caption...")
        caption = vm.generate_caption(img_bytes)
        
        print(f"✓ Caption: {caption}")
        
        print("\n✅ Vision model working!")
        return True
        
    except Exception as e:
        print(f"\n❌ Vision error: {e}")
        print("\nNote: First run downloads ~1GB model")
        return False

def test_telegram_token():
    """Test if Telegram token is configured"""
    print("\n" + "="*50)
    print("Testing Telegram Configuration")
    print("="*50)
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not set in .env")
        print("\nGet token from: https://t.me/botfather")
        return False
    
    if token == "your_telegram_bot_token_here":
        print("❌ TELEGRAM_BOT_TOKEN not configured")
        print("Please edit .env and add your real token")
        return False
    
    print(f"✓ Token configured: {token[:10]}...")
    print("\n✅ Telegram configured!")
    return True

def main():
    """Run all tests"""
    print("\n" + "="*50)
    print("Telegram RAG Bot - Component Tests")
    print("="*50)
    
    tests = [
        ("Package Imports", test_imports),
        ("Ollama LLM", test_ollama),
        ("Embeddings", test_embeddings),
        ("Vector Store", test_vector_store),
        ("Vision Model", test_vision),
        ("Telegram Config", test_telegram_token),
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ {name} failed with exception: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print("\n" + "="*50)
    print(f"Results: {passed_count}/{total_count} tests passed")
    print("="*50)
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Ready to run the bot.")
        print("\nRun: python bot.py")
    else:
        print("\n⚠️ Some tests failed. Please fix issues above.")
    
    return passed_count == total_count

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)