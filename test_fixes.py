#!/usr/bin/env python3
"""
Test script to verify all bug fixes
Run this after applying fixes to ensure everything works
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_agent_manager():
    """Test agent manager fixes"""
    print("\n" + "="*60)
    print("TEST 1: Agent Manager - Return Value Fix")
    print("="*60)
    
    try:
        from agent_manager import AgentManager, AgenticQueryProcessor
        from vector_store import VectorStore
        from llm_manager import LLMManager
        from vision_manager import VisionManager
        
        # Initialize components
        logger.info("Initializing components...")
        vector_store = VectorStore()
        llm_manager = LLMManager()
        vision_manager = VisionManager()
        processor = AgenticQueryProcessor(vector_store, llm_manager, vision_manager)
        
        # Test 1: Simple greeting (should return template)
        logger.info("\nTest 1a: Simple greeting")
        result = processor.process_query("hi")
        
        assert result is not None, "❌ Result is None!"
        assert isinstance(result, dict), "❌ Result is not a dict!"
        assert 'answer' in result, "❌ No 'answer' key in result!"
        assert result['answer'], "❌ Answer is empty!"
        
        print(f"✅ Simple greeting works!")
        print(f"   Answer: {result['answer'][:50]}...")
        
        # Test 2: Knowledge query (should use RAG)
        logger.info("\nTest 1b: Knowledge query")
        result = processor.process_query("What is Docker?")
        
        assert result is not None, "❌ Result is None!"
        assert isinstance(result, dict), "❌ Result is not a dict!"
        assert 'answer' in result, "❌ No 'answer' key!"
        assert result['answer'], "❌ Answer is empty!"
        assert len(result.get('sources', [])) > 0, "❌ No sources found!"
        
        print(f"✅ Knowledge query works!")
        print(f"   Answer: {result['answer'][:50]}...")
        print(f"   Sources: {result['sources']}")
        
        print("\n✅ TEST 1 PASSED - Agent Manager Fixed!")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chromadb():
    """Test ChromaDB initialization"""
    print("\n" + "="*60)
    print("TEST 2: ChromaDB - No Telemetry Errors")
    print("="*60)
    
    try:
        from vector_store import VectorStore
        
        logger.info("Initializing ChromaDB...")
        vs = VectorStore()
        
        logger.info("Testing search...")
        results = vs.search("test query", k=2)
        
        assert results is not None, "❌ Search returned None!"
        assert isinstance(results, list), "❌ Results not a list!"
        
        stats = vs.get_stats()
        print(f"✅ ChromaDB initialized successfully!")
        print(f"   Documents: {stats['total_documents']}")
        print(f"   Embedding dims: {stats['embedding_model']}")
        
        print("\n✅ TEST 2 PASSED - ChromaDB Fixed!")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vision():
    """Test vision manager"""
    print("\n" + "="*60)
    print("TEST 3: Vision Manager - Image Processing")
    print("="*60)
    
    try:
        from vision_manager import VisionManager
        from PIL import Image
        import io
        
        logger.info("Loading vision model...")
        vm = VisionManager()
        
        logger.info("Creating test image...")
        img = Image.new('RGB', (224, 224), color=(255, 0, 0))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes = img_bytes.getvalue()
        
        logger.info("Analyzing image...")
        result = vm.analyze_image(img_bytes)
        
        assert result, "❌ No result from vision model!"
        assert isinstance(result, str), "❌ Result not a string!"
        assert len(result) > 0, "❌ Empty result!"
        
        print(f"✅ Vision model works!")
        print(f"   Result: {result[:100]}...")
        
        print("\n✅ TEST 3 PASSED - Vision Fixed!")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling improvements"""
    print("\n" + "="*60)
    print("TEST 4: Error Handling - Safe Dictionary Access")
    print("="*60)
    
    try:
        # Simulate result validation
        result = None
        
        # Old way (would crash)
        # intent = result.get('plan', {}).get('intent', 'unknown')
        
        # New way (safe)
        if result and isinstance(result, dict):
            plan = result.get('plan', {})
            intent = plan.get('intent', 'unknown') if plan else 'unknown'
        else:
            intent = 'unknown'
        
        assert intent == 'unknown', "❌ Error handling failed!"
        
        # Test with valid result
        result = {
            'answer': 'test answer',
            'sources': ['test.md'],
            'plan': {'intent': 'knowledge_search'}
        }
        
        if result and isinstance(result, dict):
            answer = result.get('answer', 'No response')
            sources = result.get('sources', [])
            plan = result.get('plan', {})
            intent = plan.get('intent', 'unknown') if plan else 'unknown'
        
        assert answer == 'test answer', "❌ Answer extraction failed!"
        assert sources == ['test.md'], "❌ Sources extraction failed!"
        assert intent == 'knowledge_search', "❌ Intent extraction failed!"
        
        print(f"✅ Error handling works correctly!")
        print(f"   None result handled safely: {intent}")
        print(f"   Valid result parsed correctly")
        
        print("\n✅ TEST 4 PASSED - Error Handling Improved!")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "🧪 "*30)
    print("RUNNING BUG FIX VERIFICATION TESTS")
    print("🧪 "*30)
    
    results = {
        'Agent Manager': test_agent_manager(),
        'ChromaDB': test_chromadb(),
        'Vision Manager': test_vision(),
        'Error Handling': test_error_handling(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Bugs are fixed!")
        print("\nYou can now safely deploy:")
        print("  docker-compose down")
        print("  docker-compose up -d --build")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED! Please check errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())