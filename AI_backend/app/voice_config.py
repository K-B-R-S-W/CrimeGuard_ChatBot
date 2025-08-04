from gtts import gTTS
from openai import OpenAI
from io import BytesIO
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup basic logging
logger = logging.getLogger(__name__)

# Set up OpenAI client for voice transcription
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def speech_to_text(file_content, temp_path):
    """Transcribes audio file using OpenAI's Whisper API."""
    logger.info("Starting audio transcription...")
    try:
        with open(temp_path, "rb") as audio_file_to_transcribe:
            transcription = openai_client.audio.transcriptions.create(
                file=audio_file_to_transcribe,
                model="whisper-1",
                response_format="text"
            )
        logger.info(f"Transcription successful: '{transcription}'")
        if not transcription or transcription.strip() == "":
            logger.warning("Transcription resulted in empty text.")
            return "I didn't catch that. Could you please speak clearly?"
        return transcription
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
