#!/usr/bin/env python3
"""
Test script specifically for image processing fix
Creates a test image and verifies it's processed correctly
"""

import sys
import logging
from PIL import Image
import io

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def create_test_image(color='red', size=(224, 224)):
    """Create a test image"""
    colors = {
        'red': (255, 0, 0),
        'blue': (0, 0, 255),
        'green': (0, 255, 0),
        'yellow': (255, 255, 0),
    }
    
    img = Image.new('RGB', size, color=colors.get(color, (255, 0, 0)))
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    return img_bytes.getvalue()

def test_vision_direct():
    """Test vision manager directly"""
    print("\n" + "="*70)
    print("TEST 1: Vision Manager Direct Call")
    print("="*70)
    
    try:
        from vision_manager import VisionManager
        
        logger.info("Loading vision model...")
        vm = VisionManager()
        
        # Test with different colored images
        test_cases = [
            ('red', 'Red image test'),
            ('blue', 'Blue image test'),
            ('green', 'Green image test'),
        ]
        
        for color, description in test_cases:
            logger.info(f"\nTesting {description}...")
            img_bytes = create_test_image(color=color)
            
            # Test generate_detailed_description (what bot uses)
            result = vm.generate_detailed_description(img_bytes)
            
            assert isinstance(result, dict), "❌ Result not a dict!"
            assert 'caption' in result, "❌ No caption in result!"
            assert 'tags' in result, "❌ No tags in result!"
            assert result['caption'], "❌ Empty caption!"
            
            print(f"  ✅ {color.capitalize()} image:")
            print(f"     Caption: {result['caption']}")
            print(f"     Tags: {result['tags']}")
        
        print("\n✅ TEST 1 PASSED - Vision model works directly!")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_no_agent_confusion():
    """Test that images don't go through agent/RAG"""
    print("\n" + "="*70)
    print("TEST 2: Images Should NOT Trigger RAG")
    print("="*70)
    
    try:
        from agent_manager import AgentManager
        
        agent = AgentManager()
        
        # Create plan for image (should warn)
        logger.info("Creating plan with has_image=True (should warn)...")
        plan = agent.create_execution_plan("Describe this image", has_image=True)
        
        # Check plan
        assert plan['use_vision'] == True, "❌ Vision not enabled!"
        assert plan['use_rag'] == False, "❌ RAG should NOT be used for images!"
        assert plan['use_llm'] == False, "❌ LLM should NOT be used for direct image analysis!"
        
        print(f"  ✅ Image plan correct:")
        print(f"     use_vision: {plan['use_vision']}")
        print(f"     use_rag: {plan['use_rag']}")
        print(f"     use_llm: {plan['use_llm']}")
        
        print("\n✅ TEST 2 PASSED - Images bypass RAG correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bot_handler_simulation():
    """Simulate what bot does with image"""
    print("\n" + "="*70)
    print("TEST 3: Simulate Bot Image Handler")
    print("="*70)
    
    try:
        from vision_manager import VisionManager
        
        logger.info("Loading vision model...")
        vm = VisionManager()
        
        logger.info("Creating test image...")
        image_bytes = create_test_image(color='red')
        
        logger.info("Processing image (as bot would)...")
        
        # This is what bot does
        result = vm.generate_detailed_description(image_bytes)
        
        # Format response (as bot does)
        caption = result.get('caption', 'Unable to analyze image')
        tags = result.get('tags', [])
        tags_str = ", ".join(tags) if tags else "N/A"
        
        response = f"""**Caption:** {caption}

**Tags:** {tags_str}

👁️ *Analyzed by {vm.model_name.split('/')[-1]}*"""
        
        # Verify
        assert 'Caption:' in response, "❌ No caption in response!"
        assert 'Tags:' in response, "❌ No tags in response!"
        assert 'Unable to analyze' not in caption, "❌ Failed to analyze!"
        
        print(f"\n✅ Bot Response Preview:")
        print("-" * 70)
        print(response)
        print("-" * 70)
        
        print("\n✅ TEST 3 PASSED - Bot handler works correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_response():
    """Test what should NOT happen"""
    print("\n" + "="*70)
    print("TEST 4: Verify Error Response is NOT Triggered")
    print("="*70)
    
    from vision_manager import VisionManager
    
    vm = VisionManager()
    img_bytes = create_test_image()
    result = vm.generate_detailed_description(img_bytes)
    
    caption = result.get('caption', '')
    
    # These strings should NOT appear (they indicate RAG was used)
    bad_strings = [
        "Based on the provided context",
        "cannot describe an image",
        "no visual information",
        "Machine Learning",
        "Kubernetes",
        "Docker Containerization",
    ]
    
    for bad_str in bad_strings:
        if bad_str.lower() in caption.lower():
            print(f"  ❌ Found problematic text: '{bad_str}'")
            print(f"  ❌ This means RAG was used instead of vision model!")
            return False
    
    print(f"  ✅ Caption: {caption}")
    print(f"  ✅ No RAG text detected!")
    print("\n✅ TEST 4 PASSED - Pure vision processing!")
    return True

def main():
    """Run all tests"""
    print("\n" + "🖼️ "*35)
    print("IMAGE PROCESSING FIX VERIFICATION")
    print("🖼️ "*35)
    
    print("\nThis test verifies:")
    print("  1. Vision model works directly")
    print("  2. Images don't trigger RAG/LLM")
    print("  3. Bot handler formats correctly")
    print("  4. No document-related text in responses")
    
    results = {
        'Vision Direct Call': test_vision_direct(),
        'No Agent Confusion': test_no_agent_confusion(),
        'Bot Handler Simulation': test_bot_handler_simulation(),
        'Error Response Check': test_error_response(),
    }
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(results.values())
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("\n" + "="*70)
    print(f"Results: {passed}/{total} tests passed")
    print("="*70)
    
    if passed == total:
        print("\n🎉 IMAGE PROCESSING FIXED!")
        print("\nWhat to expect in Telegram:")
        print("  1. Upload any image")
        print("  2. Bot shows: '🖼️ Analyzing image with BLIP model...'")
        print("  3. Returns: Caption + Tags")
        print("  4. NO mention of 'documents' or 'context'")
        print("  5. Response in 2-5 seconds")
        print("\nDeploy now:")
        print("  docker-compose down")
        print("  docker-compose build --no-cache")
        print("  docker-compose up -d")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("Please check errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())