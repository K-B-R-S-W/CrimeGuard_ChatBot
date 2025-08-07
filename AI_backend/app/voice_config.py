from gtts import gTTS
from openai import OpenAI
from io import BytesIO
import logging
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup basic logging
logger = logging.getLogger(__name__)

# Set up OpenAI client for voice transcription
if not os.getenv('OPENAI_API_KEY'):
    logger.error("OPENAI_API_KEY not set in environment variables")
    raise ValueError("OPENAI_API_KEY environment variable is required")

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def speech_to_text(file_content, temp_path):
    """Transcribes audio file using OpenAI's Whisper API."""
    logger.info("Starting audio transcription...")
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

        # Attempt transcription with enhanced parameters
        with open(temp_path, "rb") as audio_file:
            try:
                logger.info("Starting transcription process...")
                
                # First attempt with whisper-1 model
                transcription = openai_client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-1",
                    language="en",
                    temperature=0.0,
                    response_format="text"
                )
                
                logger.debug(f"Raw API response: {transcription}")
                text = str(transcription).strip()
                logger.info(f"First attempt result: '{text}'")

                # If needed, try again with different parameters
                if not text or text.lower() in ["you", "for more un videos visit www.un.org", "transcribe what the person is saying"] or len(text) < 3:
                    logger.info("First attempt unclear, trying with different parameters...")
                    audio_file.seek(0)
                    
                    # Second attempt with adjusted parameters
                    transcription = openai_client.audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-1",
                        language="en",
                        temperature=0.2,
                        response_format="text"
                    )
                    
                    text = str(transcription).strip()
                    logger.info(f"Second attempt result: '{text}'")

                    # If still unclear, try one final time
                    if not text or text.lower() in ["you", "for more un videos visit www.un.org", "transcribe what the person is saying"] or len(text) < 3:
                        logger.info("Second attempt unclear, trying final attempt...")
                        audio_file.seek(0)
                        
                        # Third attempt with different parameters
                        transcription = openai_client.audio.transcriptions.create(
                            file=audio_file,
                            model="whisper-1",
                            language="en",
                            temperature=0.4,
                            response_format="text"
                        )
                        
                        text = str(transcription).strip()
                        logger.info(f"Final attempt result: '{text}'")

                # Final validation
                if not text or text.lower() in ["you", "for more un videos visit www.un.org", "transcribe what the person is saying"] or len(text) < 3:
                    logger.error("All transcription attempts failed to get clear result")
                    return "I couldn't understand that clearly. Please speak again."                # Remove any UN-related prefixes/suffixes
                text = re.sub(r'for more un videos visit.*$', '', text, flags=re.IGNORECASE).strip()
                text = re.sub(r'^.*un videos?:?\s*', '', text, flags=re.IGNORECASE).strip()
                
                logger.info(f"Final cleaned transcription: '{text}'")
                return text

                # Clean the transcription
                text = str(transcription).strip()
                
                # If we got "you" or very short text, try again with different parameters
                if not text or text.lower() == "you" or len(text) < 3:
                    audio_file.seek(0)  # Reset file pointer
                    transcription = openai_client.audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-1",
                        language="en",
                        temperature=0.2,  # Slightly higher temperature
                        prompt="The person is asking for help or describing a situation."
                    )
                    text = str(transcription).strip()

                # Final validation
                if not text or text.lower() == "you" or len(text) < 3:
                    logger.warning("Failed to get clear transcription after retries")
                    return "I couldn't understand that clearly. Please speak again."

                logger.info(f"Successful transcription: '{text}'")
                return text

            except Exception as e:
                logger.error(f"Transcription error: {e}")
                return "There was an error processing your speech. Please try again."

    except Exception as e:
        logger.error(f"OpenAI API Error during transcription: {e}", exc_info=True)
        raise

def text_to_speech(text: str):
    """Converts text to speech using Google TTS (gTTS) and returns audio bytes."""
    logger.info(f"Generating TTS audio for: '{text}'")
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        logger.info("TTS audio generated successfully.")
        return audio_buffer.read()
    except Exception as e:
        logger.error(f"Error during TTS generation: {e}", exc_info=True)
        raise

# Voice configuration settings
VOICE_CONFIG = {
    "speech_to_text": {
        "model": "whisper-1",
        "response_format": "text",
    },
    "text_to_speech": {
        "language": "en",
        "slow": False,
    }
}