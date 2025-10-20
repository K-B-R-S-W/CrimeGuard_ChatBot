"""
Debug Test: Check TwiML Generation
This script will show exactly what TwiML is being generated
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_twiml_generation():
    """Test TwiML generation with user message"""
    
    # Simulate the exact code from twilio_service.py
    emergency_type = "police"
    user_message = "Help! There is a robbery at 123 Main Street!"
    language = "en"
    
    print("\n" + "="*70)
    print("TESTING TWIML GENERATION")
    print("="*70 + "\n")
    
    print(f"Emergency Type: {emergency_type}")
    print(f"User Message: {user_message}")
    print(f"Language: {language}")
    print()
    
    # Check if message exists
    if user_message and len(user_message.strip()) > 0:
        print("✅ User message exists and is not empty")
        print(f"   Length: {len(user_message)} characters")
        print()
        
        # Base intro message
        intro = f"""This is an emergency call from Crime Guard Chat Bot. 
A user has requested {emergency_type} assistance."""
        
        # Truncate message if too long
        safe_message = user_message[:200] if len(user_message) > 200 else user_message
        
        # Escape special XML characters
        safe_message = safe_message.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        print(f"Safe message (after truncation/escaping): {safe_message}")
        print()
        
        # Create TwiML with user message
        twiml = f'''
                <Response>
                    <Say voice="Polly.Aditi" language="en-IN">
                        {intro}
                    </Say>
                    <Pause length="1"/>
                    <Say voice="Polly.Aditi" language="en-IN">
                        The user's message is: {safe_message}
                    </Say>
                    <Pause length="1"/>
                    <Say voice="Polly.Aditi" language="en-IN">
                        Please assist immediately.
                    </Say>
                    <Pause length="2"/>
                </Response>
                '''
        
        print("="*70)
        print("GENERATED TWIML:")
        print("="*70)
        print(twiml)
        print("="*70)
        
    else:
        print("❌ User message is empty or None")
    
    print("\n")

if __name__ == "__main__":
    test_twiml_generation()
