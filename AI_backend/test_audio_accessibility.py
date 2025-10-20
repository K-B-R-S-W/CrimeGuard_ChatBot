"""
Test Audio File Generation and Accessibility
Checks if Twilio can access the audio files we generate
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.audio_manager import audio_manager
import requests

def test_audio_generation_and_accessibility():
    """Test complete audio flow"""
    
    print("\n" + "="*70)
    print("AUDIO GENERATION AND ACCESSIBILITY TEST")
    print("="*70 + "\n")
    
    # Test message
    test_message = "Help! There is an emergency at my location!"
    language = "en"
    
    print(f"Test Message: {test_message}")
    print(f"Language: {language}")
    print()
    
    # Step 1: Generate audio
    print("Step 1: Generating audio with gTTS...")
    success, audio_path = audio_manager.generate_audio_from_text(
        text=test_message,
        language=language
    )
    
    if not success:
        print(f"❌ Failed: {audio_path}")
        return
    
    print(f"✅ Audio generated: {audio_path}")
    
    # Check file properties
    if os.path.exists(audio_path):
        file_size = os.path.getsize(audio_path)
        print(f"   File size: {file_size} bytes ({file_size/1024:.2f} KB)")
        
        # Check file format
        with open(audio_path, 'rb') as f:
            header = f.read(12)
            print(f"   File header: {header[:4]}")
            
            # MP3 files should start with ID3 or 0xFF 0xFB
            if header.startswith(b'ID3') or (header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
                print(f"   ✅ Valid MP3 file")
            else:
                print(f"   ⚠️ File format might not be MP3")
    
    # Step 2: Save to local storage
    print("\nStep 2: Saving to local storage...")
    success, filename = audio_manager.save_to_local_storage(audio_path)
    
    if not success:
        print(f"❌ Failed: {filename}")
        return
    
    print(f"✅ Saved: {filename}")
    
    # Check storage location
    storage_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'app',
        'audio_storage'
    )
    stored_path = os.path.join(storage_dir, filename)
    print(f"   Path: {stored_path}")
    print(f"   Exists: {os.path.exists(stored_path)}")
    
    # Step 3: Construct URL
    base_url = "http://localhost:8000"
    audio_url = f"{base_url}/audio/{filename}"
    print(f"\nStep 3: Audio URL")
    print(f"   URL: {audio_url}")
    
    # Step 4: Check if URL is accessible (requires server to be running)
    print(f"\nStep 4: Testing URL accessibility...")
    print(f"   ⚠️ Note: Backend server must be running for this test")
    
    try:
        response = requests.head(audio_url, timeout=2)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ URL is accessible!")
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"   Content-Length: {response.headers.get('content-length', 'N/A')} bytes")
        else:
            print(f"   ❌ URL returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"   ⚠️ Backend server is not running")
        print(f"   Start server with: python main.py")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Step 5: Test what Twilio sees
    print(f"\nStep 5: Twilio Audio Requirements")
    print(f"   Twilio accepts: MP3, WAV, and other formats")
    print(f"   Supported codecs: MP3, WAV (ulaw, alaw, PCM)")
    print(f"   Max file size: 5 MB")
    print(f"   Recommended bitrate: 64 kbps")
    print(f"   ✅ Our file: MP3 format from gTTS")
    
    print(f"\nStep 6: TwiML that will be used:")
    twiml = f'''<Response>
    <Say voice="Polly.Aditi" language="en-IN">
        This is an emergency call from Crime Guard Chat Bot.
        A user has requested assistance.
    </Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" language="en-IN">The user's message follows:</Say>
    <Pause length="1"/>
    <Play>{audio_url}</Play>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" language="en-IN">Please assist immediately.</Say>
</Response>'''
    
    print(twiml)
    
    print("\n" + "="*70)
    print("KEY FINDINGS:")
    print("="*70)
    print()
    
    # Check if using localhost
    if 'localhost' in audio_url or '127.0.0.1' in audio_url:
        print("⚠️ CRITICAL ISSUE: Using localhost URL!")
        print()
        print("   Problem: Twilio CANNOT access 'localhost' URLs")
        print("   'localhost' refers to YOUR computer, not Twilio's servers")
        print()
        print("   Solutions:")
        print("   1. Use ngrok to create a public tunnel:")
        print("      - Install: https://ngrok.com/download")
        print("      - Run: ngrok http 8000")
        print("      - Update BASE_URL in .env to ngrok URL")
        print()
        print("   2. Deploy to a public server (Heroku, AWS, etc.)")
        print()
        print("   3. For testing: Use Twilio TTS fallback (already implemented)")
        print("      - The <Say> tag will work without external URLs")
        print()
    else:
        print("✅ Using non-localhost URL - should work!")
    
    print()

if __name__ == "__main__":
    test_audio_generation_and_accessibility()
