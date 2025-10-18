from io import BytesIO
import logging
import os
import re
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from gtts import gTTS
import requests

# Load environment variables
load_dotenv()

# Setup basic logging
logger = logging.getLogger(__name__)

# Set up ElevenLabs client for voice transcription
if not os.getenv('ELEVENLABS_API_KEY'):
    logger.error("ELEVENLABS_API_KEY not set in environment variables")
    raise ValueError("ELEVENLABS_API_KEY environment variable is required")

elevenlabs_client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))

def speech_to_text(file_content, temp_path):
    """Transcribes audio file using ElevenLabs Speech-to-Text API with support for English, Tamil, and Sinhala."""
    logger.info("Starting audio transcription with ElevenLabs...")
    try:
        # Log and validate file details
        file_size = os.path.getsize(temp_path)
        file_extension = os.path.splitext(temp_path)[1].lower()
        logger.info(f"Audio file size: {file_size} bytes, format: {file_extension}")

        # Debug: Print file content details
        logger.debug(f"File content length: {len(file_content)} bytes")
        logger.debug(f"Temp file path: {temp_path}")

        # Validate file size - adjusted thresholds
        if file_size < 1024:  # Minimum 1KB
            logger.warning(f"Audio file too small: {file_size} bytes")
            return "Please speak longer and more clearly."

        if file_size > 25 * 1024 * 1024:  # Max 25MB
            logger.warning("Audio file too large")
            return "Recording too long. Please keep it under 30 seconds."

        # Validate audio format
        if file_extension not in ['.mp3', '.webm', '.wav', '.m4a', '.ogg']:
            logger.warning(f"Unsupported audio format: {file_extension}")
            return "Unsupported audio format. Please try again."

        # Attempt transcription with ElevenLabs
        try:
            logger.info("Starting ElevenLabs transcription process...")
            
            # Use the temp file directly for better compatibility
            logger.info("First attempt: Auto-detecting language...")
            
            # Open the file and pass it directly - ElevenLabs will auto-detect language
            with open(temp_path, 'rb') as audio_file:
                # Let ElevenLabs auto-detect the language by only passing required params
                transcription = elevenlabs_client.speech_to_text.convert(
                    file=audio_file,
                    model_id="scribe_v1",
                )
            
            # Extract text from transcription result
            text = ""
            if hasattr(transcription, 'text'):
                text = transcription.text.strip()
            elif isinstance(transcription, dict) and 'text' in transcription:
                text = transcription['text'].strip()
            else:
                text = str(transcription).strip()
            
            logger.debug(f"Raw API response: {transcription}")
            logger.info(f"Transcription result: '{text}'")

            # Validate transcription quality
            if not text or len(text) < 2:
                logger.warning("Transcription resulted in empty or very short text")
                
                # Try again with specific language codes
                logger.info("Attempting with specific language hints...")
                
                # Try with English first
                try:
                    with open(temp_path, 'rb') as audio_file:
                        transcription = elevenlabs_client.speech_to_text.convert(
                            file=audio_file,
                            model_id="scribe_v1",
                            language_code="eng",
                        )
                    text = transcription.text.strip() if hasattr(transcription, 'text') else str(transcription).strip()
                    logger.info(f"English attempt result: '{text}'")
                except Exception as e:
                    logger.warning(f"English language attempt failed: {e}")
                
                # If still no good result, try Sinhala
                if not text or len(text) < 2:
                    try:
                        with open(temp_path, 'rb') as audio_file:
                            transcription = elevenlabs_client.speech_to_text.convert(
                                file=audio_file,
                                model_id="scribe_v1",
                                language_code="sin",
                            )
                        text = transcription.text.strip() if hasattr(transcription, 'text') else str(transcription).strip()
                        logger.info(f"Sinhala attempt result: '{text}'")
                    except Exception as e:
                        logger.warning(f"Sinhala language attempt failed: {e}")
                
                # If still no good result, try Tamil
                if not text or len(text) < 2:
                    try:
                        with open(temp_path, 'rb') as audio_file:
                            transcription = elevenlabs_client.speech_to_text.convert(
                                file=audio_file,
                                model_id="scribe_v1",
                                language_code="tam",
                            )
                        text = transcription.text.strip() if hasattr(transcription, 'text') else str(transcription).strip()
                        logger.info(f"Tamil attempt result: '{text}'")
                    except Exception as e:
                        logger.warning(f"Tamil language attempt failed: {e}")

            # Final validation
            if not text or len(text) < 2:
                logger.error("All transcription attempts failed to get clear result")
                return "I couldn't understand that clearly. Please speak again."
            
            # Clean up any unwanted artifacts
            text = text.strip()
            
            logger.info(f"Final transcription: '{text}'")
            return text

        except Exception as e:
            logger.error(f"ElevenLabs transcription error: {e}", exc_info=True)
            return "There was an error processing your speech. Please try again."

    except Exception as e:
        logger.error(f"ElevenLabs API Error during transcription: {e}", exc_info=True)
        raise

def text_to_speech(text: str, language: str = "en", speed: float = 1.3):
    """
    Converts text to speech using Google Text-to-Speech (gTTS).
    Supports multiple languages including English, Sinhala, and Tamil.
    
    Args:
        text: The text to convert to speech
        language: Language code ('en', 'si', 'ta') - defaults to 'en'
        speed: Speed multiplier for playback (1.0 = normal, 1.3 = 30% faster, 0.8 = 20% slower)
               Note: gTTS doesn't directly support speed, so we use the 'slow' parameter
               and note that actual speed control happens on playback
    
    Returns:
        Audio bytes in MP3 format
    """
    logger.info(f"Generating TTS audio for language '{language}' at speed {speed}x: '{text[:50]}...'")
    try:
        # Map language codes to gTTS language codes
        # 'en' -> 'en', 'si' -> 'si', 'ta' -> 'ta'
        gtts_lang = language
        
        # Determine if we should use slow speech (speed < 1.0 means slower)
        use_slow = speed < 1.0
        
        # Generate speech using gTTS
        # Note: gTTS has limited speed control (only slow=True/False)
        # For better speed control, we'll rely on audio playback speed adjustment
        tts = gTTS(text=text, lang=gtts_lang, slow=use_slow)
        
        # Save to BytesIO buffer
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        audio_bytes = audio_buffer.read()
        logger.info(f"TTS audio generated successfully using gTTS. Size: {len(audio_bytes)} bytes, Speed: {speed}x")
        return audio_bytes
        
    except Exception as e:
        logger.error(f"Error during gTTS generation: {e}", exc_info=True)
        # Fallback to English if language fails
        try:
            logger.warning(f"Falling back to English TTS")
            tts = gTTS(text=text, lang='en', slow=False)
            audio_buffer = BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            return audio_buffer.read()
        except Exception as fallback_error:
            logger.error(f"Fallback TTS also failed: {fallback_error}")
            raise

# Voice configuration settings
VOICE_CONFIG = {
    "speech_to_text": {
        "model": "scribe_v1",  # ElevenLabs model
        "supported_languages": ["eng", "sin", "tam"],  # English, Sinhala, Tamil
        "tag_audio_events": True,
        "diarize": False,
    },
    "text_to_speech": {
        "engine": "gTTS",  # Google Text-to-Speech (free)
        "supported_languages": ["en", "si", "ta"],  # English, Sinhala, Tamil
        "speed": 1.3,  # Default speed multiplier (1.0 = normal, 1.3 = 30% faster)
        "slow": False,
    }
}