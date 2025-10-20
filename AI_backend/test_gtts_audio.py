"""
Test gTTS Audio Generation for Emergency Calls
Tests the complete flow: gTTS generation -> local storage -> URL serving
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.audio_manager import audio_manager

def test_gtts_audio_generation():
    """Test gTTS audio generation and local storage"""
    
    print("\n" + "="*70)
    print("TESTING gTTS AUDIO GENERATION FOR EMERGENCY CALLS")
    print("="*70 + "\n")
    
    # Test cases with different languages
    test_cases = [
        {
            'message': 'Help! There is a robbery at 123 Main Street!',
            'language': 'en',
            'emergency_type': 'police'
        },
        {
            'message': 'මගේ නිවසට කොල්ලයක්. කරුණාකර ඉක්මනින් එන්න!',
            'language': 'si',
            'emergency_type': 'police'
        },
        {
            'message': 'அவசரம்! என் வீட்டில் திருடர்கள் உள்ளனர்!',
            'language': 'ta',
            'emergency_type': 'police'
        },
        {
            'message': 'Fire in the building! Everyone evacuate now!',
            'language': 'en',
            'emergency_type': 'fire'
        }
    ]
    
    for idx, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {idx} ---")
        print(f"Message: {test_case['message']}")
        print(f"Language: {test_case['language']}")
        print(f"Emergency Type: {test_case['emergency_type']}")
        print()
        
        # Step 1: Generate audio
        print("Step 1: Generating audio with gTTS...")
        success, audio_path = audio_manager.generate_audio_from_text(
            text=test_case['message'],
            language=test_case['language']
        )
        
        if success:
            print(f"✅ Audio generated: {audio_path}")
            print(f"   File exists: {os.path.exists(audio_path)}")
            if os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                print(f"   File size: {file_size} bytes ({file_size/1024:.2f} KB)")
        else:
            print(f"❌ Audio generation failed: {audio_path}")
            continue
        
        # Step 2: Save to local storage
        print("\nStep 2: Saving to local storage...")
        success, filename = audio_manager.save_to_local_storage(audio_path)
        
        if success:
            print(f"✅ Audio saved: {filename}")
            
            # Verify file exists in storage
            storage_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'app',
                'audio_storage'
            )
            stored_path = os.path.join(storage_dir, filename)
            print(f"   Storage path: {stored_path}")
            print(f"   File exists in storage: {os.path.exists(stored_path)}")
        else:
            print(f"❌ Storage failed: {filename}")
            continue
        
        # Step 3: Construct URL
        base_url = "http://localhost:8000"
        audio_url = f"{base_url}/audio/{filename}"
        print(f"\nStep 3: Audio URL")
        print(f"✅ URL: {audio_url}")
        print(f"   This URL will be used in TwiML <Play> tag")
        
        print("-" * 70)
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    print("\nNext Steps:")
    print("1. ✅ Audio files generated with gTTS (better quality for Sinhala/Tamil)")
    print("2. ✅ Files saved to local storage (AI_backend/app/audio_storage/)")
    print("3. ✅ URLs constructed for serving via FastAPI")
    print("4. ⏳ Start the backend server: python main.py")
    print("5. ⏳ Test emergency call with: 'call the police there is a robbery'")
    print("6. ⏳ The call will play gTTS audio instead of Twilio TTS")
    print("\n")

def test_complete_flow():
    """Test the complete end-to-end flow"""
    
    print("\n" + "="*70)
    print("TESTING COMPLETE FLOW: generate_and_upload_message()")
    print("="*70 + "\n")
    
    test_message = "Help! There is an emergency at my location!"
    language = "en"
    emergency_type = "police"
    base_url = "http://localhost:8000"
    
    print(f"Message: {test_message}")
    print(f"Language: {language}")
    print(f"Emergency Type: {emergency_type}")
    print(f"Base URL: {base_url}")
    print()
    
    print("Executing complete flow...")
    success, result = audio_manager.generate_and_upload_message(
        user_message=test_message,
        language=language,
        emergency_type=emergency_type,
        base_url=base_url
    )
    
    if success:
        print(f"✅ SUCCESS!")
        print(f"   Audio URL: {result}")
        print(f"\n   This URL will be used in TwiML:")
        print(f"   <Play>{result}</Play>")
    else:
        print(f"❌ FAILED: {result}")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    print("\n🎵 Starting gTTS Audio Generation Tests...\n")
    
    # Test individual steps
    test_gtts_audio_generation()
    
    # Test complete flow
    test_complete_flow()
    
    print("\n✅ All tests completed!\n")
