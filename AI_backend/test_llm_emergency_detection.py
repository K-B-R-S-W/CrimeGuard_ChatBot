"""
Test LLM-based Emergency Detection
Tests the new intelligent emergency detection system
"""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app.twilio_service import twilio_service

def test_emergency_detection():
    """Test various messages with LLM-based detection"""
    
    print("=" * 80)
    print("🤖 LLM-BASED EMERGENCY DETECTION TEST")
    print("=" * 80)
    print()
    
    # Test cases with different scenarios
    test_cases = [
        # TRUE EMERGENCIES - English
        ("call police there's a robbery at Main Street", True, "police", "en"),
        ("I need ambulance someone is unconscious", True, "ambulance", "en"),
        ("fire in my house call fire department urgently", True, "fire", "en"),
        ("help me call the police now there's an intruder", True, "police", "en"),
        
        # TRUE EMERGENCIES - Sinhala
        ("පොලිසියට කතා කරන්න මා ගෙදර සොරකම් කරනවා", True, "police", "si"),
        ("ගිලන් රථයට කතා කරන්න කෙනෙක් අසනීප", True, "ambulance", "si"),
        ("ගිනි නිවීමට කතා කරන්න ගිනි ගත්තා", True, "fire", "si"),
        
        # TRUE EMERGENCIES - Tamil
        ("காவல்துறையை அழைக்கவும் திருடர்கள் வந்தனர்", True, "police", "ta"),
        ("ஆம்புலன்ஸை அழைக்கவும் விபத்து நடந்தது", True, "ambulance", "ta"),
        ("தீயணைப்பு அழைக்க தீ விபத்து", True, "fire", "ta"),
        
        # NOT EMERGENCIES - Just questions
        ("what is the police number?", False, None, "en"),
        ("how do I call an ambulance?", False, None, "en"),
        ("tell me about fire safety", False, None, "en"),
        ("where is the nearest police station?", False, None, "en"),
        
        # NOT EMERGENCIES - Sinhala questions
        ("පොලිස් අංකය කීයද?", False, None, "si"),
        ("ගිලන් රථ සේවාව ගැන කියන්න", False, None, "si"),
        
        # NOT EMERGENCIES - General chat
        ("hello how are you?", False, None, "en"),
        ("what can you help me with?", False, None, "en"),
        ("හෙලෝ", False, None, "si"),
    ]
    
    passed = 0
    failed = 0
    
    for i, (message, expected_emergency, expected_type, expected_lang) in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"Test {i}/{len(test_cases)}")
        print(f"{'─' * 80}")
        print(f"📝 Message: {message}")
        print(f"📋 Expected: Emergency={expected_emergency}, Type={expected_type}, Lang={expected_lang}")
        print()
        
        # Detect emergency
        result = twilio_service.detect_emergency_intent(message)
        
        # Analyze result
        is_emergency = result is not None
        emergency_type = result.get('type') if result else None
        detected_lang = result.get('language') if result else None
        confidence = result.get('confidence', 0) if result else 0
        reasoning = result.get('reasoning', 'N/A') if result else 'Not an emergency'
        
        print(f"🔍 LLM Analysis:")
        print(f"   Is Emergency: {is_emergency}")
        print(f"   Type: {emergency_type}")
        print(f"   Language: {detected_lang}")
        print(f"   Confidence: {confidence:.2f}")
        print(f"   Reasoning: {reasoning}")
        print()
        
        # Check if test passed
        if is_emergency == expected_emergency:
            if expected_emergency:
                # For emergencies, also check type and language
                if emergency_type == expected_type and detected_lang == expected_lang:
                    print("✅ TEST PASSED")
                    passed += 1
                else:
                    print(f"❌ TEST FAILED - Wrong type/language")
                    print(f"   Expected: {expected_type}/{expected_lang}")
                    print(f"   Got: {emergency_type}/{detected_lang}")
                    failed += 1
            else:
                # For non-emergencies, just check it wasn't detected as emergency
                print("✅ TEST PASSED")
                passed += 1
        else:
            print(f"❌ TEST FAILED")
            print(f"   Expected emergency: {expected_emergency}")
            print(f"   Got: {is_emergency}")
            failed += 1
    
    # Summary
    print(f"\n{'=' * 80}")
    print("📊 TEST SUMMARY")
    print(f"{'=' * 80}")
    print(f"✅ Passed: {passed}/{len(test_cases)}")
    print(f"❌ Failed: {failed}/{len(test_cases)}")
    print(f"📈 Success Rate: {(passed/len(test_cases)*100):.1f}%")
    print()
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! LLM-based detection is working perfectly!")
    else:
        print(f"⚠️ {failed} test(s) failed. Review the LLM reasoning above.")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    print()
    print("🚀 Starting LLM-based Emergency Detection Test...")
    print()
    
    # Check if LLM is initialized
    if not twilio_service.emergency_llm:
        print("❌ ERROR: Emergency detection LLM not initialized")
        print("   Make sure OPENAI_API_KEY is set in .env file")
        sys.exit(1)
    
    test_emergency_detection()
