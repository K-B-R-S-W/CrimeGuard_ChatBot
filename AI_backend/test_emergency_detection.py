"""
Test script to verify emergency keyword detection
Run this to test the Twilio service without making actual calls
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.twilio_service import twilio_service

def test_emergency_detection():
    """Test emergency keyword detection with various inputs"""
    
    test_cases = [
        # English - Police (various phrasings)
        ("please call police", "police"),
        ("call the police", "police"),
        ("i need help call the police", "police"),  # User's exact phrase
        ("I need police", "police"),
        ("help me police", "police"),
        ("police help urgent", "police"),
        ("I need to dial 119", "police"),
        ("contact police now", "police"),
        
        # English - Fire
        ("call fire department", "fire"),
        ("i need help call the fire department", "fire"),
        ("we need the fire truck", "fire"),
        ("dial 110 please", "fire"),
        ("help fire emergency", "fire"),
        
        # English - Ambulance
        ("call ambulance immediately", "ambulance"),
        ("i need help call an ambulance", "ambulance"),
        ("need medical emergency help", "ambulance"),
        ("dial 1990", "ambulance"),
        ("help ambulance urgent", "ambulance"),
        
        # Sinhala - Police
        ("පොලිස්", "police"),
        ("පොලිසියට කතා කරන්න", "police"),
        ("මට උදව් පොලිසියට කතා කරන්න", "police"),
        ("හදිසි පොලිස් අමතන්න", "police"),
        
        # Sinhala - Fire
        ("ගිනි නිවීම", "fire"),
        ("ගිනි නිවන හමුදාව කතා කරන්න", "fire"),
        ("මට උදව් ගිනි", "fire"),
        ("හදිසි ගිනි සේවාව", "fire"),
        
        # Sinhala - Ambulance
        ("ගිලන් රථයට කතා කරන්න", "ambulance"),
        ("සුව සැරිය", "ambulance"),
        ("මට උදව් ඇම්බියුලන්ස් කතා කරන්න", "ambulance"),
        ("වෛද්‍ය උදව්", "ambulance"),
        
        # Tamil - Police
        ("காவல்துறையை அழைக்கவும்", "police"),
        ("உதவி காவல்துறை", "police"),
        ("அவசர காவல்துறை", "police"),
        
        # Tamil - Fire
        ("தீயணைப்பு துறை", "fire"),
        ("தீ உதவி அழைக்க", "fire"),
        ("அவசர தீயணைப்பு", "fire"),
        
        # Tamil - Ambulance
        ("ஆம்புலன்ஸ்", "ambulance"),
        ("மருத்துவ உதவி", "ambulance"),
        ("அவசர மருத்துவம்", "ambulance"),
        
        # Non-emergency messages
        ("Hello, how are you?", None),
        ("What's the weather like?", None),
        ("Tell me about safety tips", None),
    ]
    
    print("=" * 80)
    print("TESTING EMERGENCY KEYWORD DETECTION")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for message, expected_type in test_cases:
        result = twilio_service.detect_emergency_intent(message)
        
        if expected_type is None:
            # Should NOT detect emergency
            if result is None:
                print(f"✓ PASS: '{message}' - No emergency detected")
                passed += 1
            else:
                print(f"✗ FAIL: '{message}' - Incorrectly detected as {result['type']}")
                failed += 1
        else:
            # SHOULD detect emergency
            if result and result['type'] == expected_type:
                print(f"✓ PASS: '{message}' - Detected as {result['type']}")
                passed += 1
            elif result:
                print(f"✗ FAIL: '{message}' - Expected {expected_type}, got {result['type']}")
                failed += 1
            else:
                print(f"✗ FAIL: '{message}' - Expected {expected_type}, got None")
                failed += 1
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)
    
    if failed == 0:
        print("\n✓ All tests passed! Emergency detection is working correctly.")
    else:
        print(f"\n✗ {failed} test(s) failed. Please review the patterns in twilio_service.py")
    
    return failed == 0


def test_response_generation():
    """Test emergency response message generation"""
    
    print("\n" + "=" * 80)
    print("TESTING RESPONSE MESSAGE GENERATION")
    print("=" * 80)
    
    test_cases = [
        ("police", "en"),
        ("fire", "en"),
        ("ambulance", "en"),
        ("police", "si"),
        ("fire", "si"),
        ("ambulance", "si"),
        ("police", "ta"),
        ("fire", "ta"),
        ("ambulance", "ta"),
    ]
    
    for emergency_type, language in test_cases:
        response = twilio_service.get_emergency_response_text(emergency_type, language)
        print(f"\n{emergency_type.upper()} ({language}):")
        print(response[:150] + "..." if len(response) > 150 else response)
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n🔍 Testing Twilio Emergency Service\n")
    
    # Test keyword detection
    detection_passed = test_emergency_detection()
    
    # Test response generation
    test_response_generation()
    
    print("\n✅ Testing complete!\n")
    
    if not detection_passed:
        sys.exit(1)
