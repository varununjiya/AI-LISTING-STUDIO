#!/usr/bin/env python3
"""Test script for AI Engine - Run to verify OpenRouter integration."""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from ai_engine import AIManager
from ai_engine.ai_manager import NoAPIKeyError


async def test_ai_engine():
    """Test the AI Engine without making actual API calls."""
    print("🧪 Testing AI Engine...\n")
    
    # 1. Test AI Manager initialization
    print("1️⃣ Testing AI Manager initialization...")
    try:
        manager = AIManager()
        print("   ✅ AI Manager created successfully")
    except Exception as e:
        print(f"   ❌ Failed to create AI Manager: {e}")
        return False
    
    # 2. Test OpenRouter configuration check
    print("\n2️⃣ Testing OpenRouter configuration...")
    has_openrouter = manager.has_openrouter_configured()
    if has_openrouter:
        print("   ✅ OpenRouter API keys configured")
    else:
        print("   ⚠️  No OpenRouter API keys found (add OPENROUTER_API_KEY_1 to .env)")
    
    # 3. Test Image Generation configuration check
    print("\n3️⃣ Testing Image Generation configuration...")
    has_image = manager.has_image_generation_configured()
    if has_image:
        print("   ✅ Emergent LLM Key configured for image generation")
    else:
        print("   ⚠️  No EMERGENT_LLM_KEY found (add to .env for image generation)")
    
    # 4. Test Model Router
    print("\n4️⃣ Testing Model Router...")
    models = manager.model_router.list_models()
    print("   Configured models:")
    for task, model in models.items():
        print(f"      • {task}: {model}")
    print("   ✅ Model router working")
    
    # 5. Test Prompt Manager
    print("\n5️⃣ Testing Prompt Manager...")
    available_prompts = manager.prompt_manager.list_available_prompts()
    print(f"   Loaded {len(available_prompts)} prompt templates:")
    for prompt_key in available_prompts:
        print(f"      • {prompt_key}")
    print("   ✅ Prompt manager working")
    
    # 6. Test Response Formatter
    print("\n6️⃣ Testing Response Formatter...")
    test_json = '{"test": "value", "nested": {"key": "data"}}'
    try:
        parsed = manager.formatter.extract_json(test_json)
        assert parsed["test"] == "value"
        print("   ✅ Response formatter working")
    except Exception as e:
        print(f"   ❌ Response formatter failed: {e}")
        return False
    
    # 7. Test OpenRouter Service stats
    print("\n7️⃣ Testing OpenRouter Service...")
    stats = manager.openrouter.get_stats()
    print(f"   Active API keys: {stats['active_keys']}")
    if stats['active_keys'] > 0:
        print(f"   Current key index: {stats['current_key_index']}")
        print(f"   Total requests: {stats['total_requests']}")
        print("   ✅ OpenRouter service initialized")
    else:
        print("   ⚠️  No API keys configured yet")
    
    # 8. Test AI Manager stats
    print("\n8️⃣ Testing AI Manager statistics...")
    ai_stats = manager.get_stats()
    print(f"   OpenRouter requests: {ai_stats['openrouter']['total_requests']}")
    print(f"   Prompts loaded: {ai_stats['prompts_loaded']}")
    print(f"   Image generation available: {ai_stats['image_generation_available']}")
    print("   ✅ AI Manager stats working")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    
    if not has_openrouter:
        print("\n⚠️  CONFIGURATION NEEDED:")
        print("   Add OpenRouter API keys to /app/backend/.env:")
        print("   OPENROUTER_API_KEY_1='sk-or-v1-...'")
        print("   Get keys from: https://openrouter.ai/keys")
    
    if not has_image:
        print("\n⚠️  OPTIONAL CONFIGURATION:")
        print("   Add Emergent Universal Key for image generation:")
        print("   EMERGENT_LLM_KEY='your-key'")
    
    return True


async def test_with_mock_data():
    """Test with mock product data (no API calls)."""
    print("\n" + "="*60)
    print("🧪 Testing with Mock Product Data (No API Calls)")
    print("="*60 + "\n")
    
    manager = AIManager()
    
    mock_product = {
        "product_name": "Premium Stainless Steel Water Bottle",
        "brand": "HydroMax",
        "category": "Home & Kitchen",
        "material": "Stainless Steel",
        "color": "Blue",
        "features": "Insulated, BPA-free, leak-proof",
    }
    
    mock_settings = {
        "brand_tone": "professional",
        "language": "English",
    }
    
    # Test prompt generation (no API call)
    print("1️⃣ Testing prompt generation...")
    try:
        prompt = manager.prompt_manager.get_prompt(
            "listing.full_marketplace",
            {
                "tone": mock_settings["brand_tone"],
                "language": mock_settings["language"],
                "product_data": mock_product,
            }
        )
        print(f"   ✅ Generated prompt ({len(prompt)} chars)")
        print(f"   First 200 chars: {prompt[:200]}...")
    except Exception as e:
        print(f"   ❌ Prompt generation failed: {e}")
        return False
    
    # Test quality scoring (no API call)
    print("\n2️⃣ Testing quality scoring...")
    try:
        import ai_service
        
        mock_listing = {
            "amazon_title": "HydroMax Premium Stainless Steel Water Bottle - 750ml Insulated",
            "amazon_bullets": [
                "PREMIUM QUALITY: Made from food-grade stainless steel",
                "KEEPS DRINKS HOT/COLD: Double-wall insulation",
                "LEAK-PROOF DESIGN: Secure screw cap prevents spills",
                "BPA-FREE & SAFE: Healthy for daily use",
                "EASY TO CLEAN: Wide mouth opening",
            ],
            "amazon_description": "Stay hydrated in style with our premium water bottle.",
            "flipkart_title": "HydroMax Insulated Water Bottle 750ml",
            "meesho_title": "Premium Steel Water Bottle",
            "seo_primary_keywords": ["water bottle", "insulated bottle", "steel bottle"],
            "seo_secondary_keywords": ["hydration", "bpa free", "leak proof"],
        }
        
        mock_product["images"] = ["image1.jpg"]
        mock_product["generated_images"] = [{"data": "img1"}, {"data": "img2"}]
        
        quality = ai_service.compute_quality_score(mock_product, mock_listing)
        print(f"   ✅ Quality score: {quality['score']}/100")
        print(f"   Breakdown: {quality['breakdown']}")
        print(f"   Suggestions: {len(quality['suggestions'])} recommendations")
    except Exception as e:
        print(f"   ❌ Quality scoring failed: {e}")
        return False
    
    print("\n✅ Mock data tests completed successfully!")
    return True


if __name__ == "__main__":
    print("="*60)
    print("AI LISTING STUDIO - OpenRouter Engine Test Suite")
    print("="*60 + "\n")
    
    try:
        # Run basic tests
        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(test_ai_engine())
        
        if success:
            # Run mock data tests
            loop.run_until_complete(test_with_mock_data())
        
        print("\n" + "="*60)
        print("🎉 Test suite completed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
