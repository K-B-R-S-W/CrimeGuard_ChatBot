"""
Audio Manager for Emergency Calls
Generates audio from user messages and uploads to Twilio Assets
"""
import os
import logging
import tempfile
import hashlib
from typing import Tuple, Optional
from gtts import gTTS
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')


class AudioManager:
    """Manages audio generation and upload for emergency calls"""
    
    def __init__(self):
        """Initialize Twilio client for asset upload"""
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            logger.warning("Twilio credentials not configured. Audio upload will not work.")
            self.client = None
        else:
            try:
                self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                logger.info("Audio Manager initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Audio Manager: {e}")
                self.client = None
    
    def generate_audio_from_text(
        self, 
        text: str, 
        language: str = 'en'
    ) -> Tuple[bool, Optional[str]]:
        """
        Generate audio file from text using gTTS
        
        Args:
            text: Text to convert to speech
            language: Language code (en, si, ta)
            
        Returns:
            Tuple of (success, audio_file_path or error_message)
        """
        try:
            # Map language codes
            lang_map = {
                'en': 'en',
                'si': 'si',  # Sinhala
                'ta': 'ta'   # Tamil
            }
            
            tts_lang = lang_map.get(language, 'en')
            
            # Generate unique filename based on content hash
            text_hash = hashlib.md5(text.encode()).hexdigest()[:10]
            filename = f"emergency_{text_hash}_{tts_lang}.mp3"
            
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            audio_path = os.path.join(temp_dir, filename)
            
            logger.info(f"Generating audio for text: {text[:50]}... in language: {tts_lang}")
            
            # Generate speech using gTTS
            tts = gTTS(
                text=text,
                lang=tts_lang,
                slow=False,
                lang_check=False
            )
            
            # Save to file
            tts.save(audio_path)
            
            logger.info(f"Audio generated successfully: {audio_path}")
            return True, audio_path
            
        except Exception as e:
            logger.error(f"Failed to generate audio: {e}", exc_info=True)
            return False, str(e)
    
    def save_to_local_storage(
        self, 
        audio_path: str,
        storage_dir: str = None
    ) -> Tuple[bool, str]:
        """
        Save audio file to local storage directory for serving via FastAPI
        
        Args:
            audio_path: Path to the temporary audio file
            storage_dir: Directory to store audio files (default: audio_storage in app)
            
        Returns:
            Tuple of (success, filename or error_message)
        """
        try:
            if storage_dir is None:
                # Use a directory relative to the app folder
                storage_dir = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'audio_storage'
                )
            
            # Create storage directory if it doesn't exist
            os.makedirs(storage_dir, exist_ok=True)
            
            # Generate unique filename
            filename = os.path.basename(audio_path)
            destination_path = os.path.join(storage_dir, filename)
            
            # Copy file to storage (or move if temp)
            import shutil
            shutil.copy2(audio_path, destination_path)
            
            logger.info(f"Audio saved to local storage: {destination_path}")
            return True, filename
            
        except Exception as e:
            logger.error(f"Failed to save audio to local storage: {e}", exc_info=True)
            return False, str(e)
    
    def generate_and_upload_message(
        self,
        user_message: str,
        language: str = 'en',
        emergency_type: str = "emergency",
        base_url: str = "http://localhost:8000"
    ) -> Tuple[bool, str]:
        """
        Complete workflow: Generate audio from message and save to local storage
        
        Args:
            user_message: User's emergency message
            language: Language code
            emergency_type: Type of emergency (for context)
            base_url: Base URL of the FastAPI server (for constructing audio URL)
            
        Returns:
            Tuple of (success, public_url or error_message)
        """
        try:
            # Prepare the message for TTS
            # Just use the raw message - keep it simple for emergency services
            full_message = user_message
            
            # Step 1: Generate audio
            success, result = self.generate_audio_from_text(full_message, language)
            
            if not success:
                logger.error(f"Audio generation failed: {result}")
                return False, result
            
            audio_path = result
            
            # Step 2: Save to local storage
            success, filename = self.save_to_local_storage(audio_path)
            
            if not success:
                logger.error(f"Failed to save audio: {filename}")
                return False, filename
            
            # Step 3: Construct public URL
            # This will be served by FastAPI
            public_url = f"{base_url}/audio/{filename}"
            
            logger.info(f"Audio file ready at: {public_url}")
            
            return True, public_url
            
        except Exception as e:
            logger.error(f"Failed to generate and upload message: {e}", exc_info=True)
            return False, str(e)
    
    def create_emergency_twiml_with_audio(
        self,
        emergency_type: str,
        user_message: str,
        language: str = 'en',
        audio_url: Optional[str] = None
    ) -> str:
        """
        Create TwiML that includes user's message
        
        Args:
            emergency_type: Type of emergency
            user_message: User's message text
            language: Language of the message
            audio_url: Optional URL to audio file (if uploaded)
            
        Returns:
            TwiML XML string
        """
        # Intro message (always in English for emergency services)
        intro = f"""This is an emergency call from Crime Guard Chat Bot. 
A user has requested {emergency_type} assistance."""
        
        # If we have audio URL, play it
        if audio_url and audio_url.startswith('http'):
            twiml = f'''
            <Response>
                <Say voice="Polly.Aditi" language="en-IN">
                    {intro}
                </Say>
                <Pause length="1"/>
                <Say voice="Polly.Aditi" language="en-IN">
                    The user's message follows:
                </Say>
                <Play>{audio_url}</Play>
                <Pause length="1"/>
                <Say voice="Polly.Aditi" language="en-IN">
                    Please assist immediately.
                </Say>
                <Pause length="2"/>
            </Response>
            '''
        else:
            # Fallback: Use <Say> with text (works for English, okay for others)
            # Truncate message if too long (Twilio has 250 char limit per Say)
            safe_message = user_message[:200] if len(user_message) > 200 else user_message
            
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
        
        return twiml
    
    def cleanup_audio_file(self, audio_path: str) -> bool:
        """
        Clean up temporary audio file
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Success status
        """
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
                logger.info(f"Cleaned up audio file: {audio_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to cleanup audio file: {e}")
            return False


# Singleton instance
audio_manager = AudioManager()
