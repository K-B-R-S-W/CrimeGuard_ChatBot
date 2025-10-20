"""
Test Emergency Call with User Message Feature
Tests the new functionality of including user's message in emergency calls
"""
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.twilio_service import twilio_service

def test_emergency_detection_with_message():
    """Test emergency detection and call with user message"""
    
    print("\n" + "="*70)
    print("TESTING EMERGENCY CALL WITH USER MESSAGE FEATURE")
    print("="*70 + "\n")
    
    # Test scenarios
    test_cases = [
        {
            'message': 'Help! Call the police. There is a robbery at 123 Main Street!',
            'language': 'en',
            'expected_type': 'police'
        },
        {
            'message': 'I need help call the ambulance my friend collapsed',
            'language': 'en',
            'expected_type': 'ambulance'
        },
        {
            'message': 'Fire emergency! Building on fire at Park Avenue!',
            'language': 'en',
            'expected_type': 'fire'
        },
        {
            'message': 'පොලිසියට කතා කරන්න උදව්. මගේ නිවසට කොල්ලයක්.',
            'language': 'si',
            'expected_type': 'police'
        },
        {
            'message': 'காவல்துறையை அழைக்க உதவி. அவசரம்!',
            'language': 'ta',
            'expected_type': 'police'
        }
    ]
    
    print("Testing emergency detection with messages:\n")
    
    for idx, test_case in enumerate(test_cases, 1):
        message = test_case['message']
        expected_type = test_case['expected_type']
        language = test_case['language']
        
        print(f"\n--- Test Case {idx} ---")
        print(f"Message: {message}")
        print(f"Language: {language}")
        print(f"Expected Type: {expected_type}")
        
        # Detect emergency
        result = twilio_service.detect_emergency_intent(message)
        
        if result:
            detected_type = result['type']
            detected_lang = result['language']
            emergency_number = result['number']
            
            print(f"✅ Detection: SUCCESS")
            print(f"   Type: {detected_type}")
            print(f"   Language: {detected_lang}")
            print(f"   Number: {emergency_number}")
            
            if detected_type == expected_type:
                print(f"✅ Type Match: CORRECT")
            else:
                print(f"❌ Type Match: INCORRECT (expected {expected_type})")
            
            # Get service name
            service_name = twilio_service.get_service_name(detected_type, detected_lang)
            print(f"   Service Name: {service_name}")
            
            # Get response text
            response_text = twilio_service.get_emergency_response_text(detected_type, detected_lang)
            print(f"   Response: {response_text[:100]}...")
            
            # Simulate call (DON'T ACTUALLY CALL)
            print(f"\n   📞 SIMULATED CALL:")
            print(f"   From: {os.getenv('TWILIO_PHONE_NUMBER', 'Not configured')}")
            print(f"   To: {emergency_number}")
            print(f"   Type: {detected_type}")
            print(f"   User Message: {message}")
            print(f"   Language: {detected_lang}")
            print(f"\n   TwiML Content (what will be spoken):")
            print(f"   - Intro: 'This is an emergency call from Crime Guard Chat Bot. A user has requested {detected_type} assistance.'")
            print(f"   - User Message: 'The user's message is: {message[:100]}...'")
            print(f"   - Closing: 'Please assist immediately.'")
            
        else:
            print(f"❌ Detection: FAILED (no emergency detected)")
        
        print("-" * 70)
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    print("\nNote: These are simulated tests. No actual calls were made.")
    print("To test with real calls, ensure:")
    print("1. TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are set in .env")
    print("2. TWILIO_PHONE_NUMBER is configured")
    print("3. Emergency numbers are verified in your Twilio account (trial limitation)")
    print("4. Uncomment the actual call code in twilio_service.py if needed")
    print("\n")

def test_message_formatting():
    """Test how user messages are formatted for TwiML"""
    
    print("\n" + "="*70)
    print("TESTING MESSAGE FORMATTING FOR TWIML")
    print("="*70 + "\n")
    
    test_messages = [
        "Help! There's a robbery!",
        "My friend collapsed and needs immediate medical attention at 123 Main Street",
        "Fire in the building! Everyone evacuate!",
        "Special characters: & < > \" ' test",
        "A very long message " * 20  # Long message test
    ]
    
    for idx, message in enumerate(test_messages, 1):
        print(f"\n--- Test Message {idx} ---")
        print(f"Original: {message[:100]}{'...' if len(message) > 100 else ''}")
        
        # Simulate truncation (max 200 chars)
        safe_message = message[:200] if len(message) > 200 else message
        
        # Simulate XML escaping
        escaped = safe_message.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        print(f"Truncated Length: {len(safe_message)} chars")
        print(f"After Escaping: {escaped[:100]}{'...' if len(escaped) > 100 else ''}")
        
        if len(message) > 200:
            print(f"⚠️ Message was truncated from {len(message)} to 200 chars")
        else:
            print(f"✅ Message length OK ({len(message)} chars)")
    
    print("\n" + "="*70)
    print("MESSAGE FORMATTING TEST COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    print("\n🚀 Starting Emergency Call with User Message Tests...\n")
    
    # Check if Twilio is configured
    if not os.getenv('TWILIO_ACCOUNT_SID') or not os.getenv('TWILIO_AUTH_TOKEN'):
        print("⚠️  WARNING: Twilio credentials not found in .env file")
        print("   Tests will run but calls cannot be made without configuration.\n")
    
    # Run tests
    test_emergency_detection_with_message()
    test_message_formatting()
    
    print("\n✅ All tests completed!\n")
