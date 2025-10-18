from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
import tempfile
import os
import base64
import logging
import sys
from dotenv import load_dotenv
from io import BytesIO

# Load environment variables
load_dotenv()

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from AI_backend.app.langchain_utils import (
    speech_to_text,
    text_to_speech,
    format_response_as_list,
)
from AI_backend.app.langgraph_utils import (
    get_multilingual_response,
    clean_response,
    detect_language
)
from AI_backend.app.db_utils import save_chat_interaction
from langchain_core.messages import HumanMessage

# Setup logging
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.post("/voice_chat")
async def voice_chat(file: UploadFile = File(...)):
    logger.info("=== Starting new voice chat request ===")
    logger.info(f"Received file: {file.filename}, Content-Type: {file.content_type}")
    
    temp_audio_path = None
    try:
        # Determine correct file extension and mime type
        content_type = file.content_type.lower()
        if "webm" in content_type:
            extension = ".webm"
        elif "mp3" in content_type:
            extension = ".mp3"
        elif "wav" in content_type:
            extension = ".wav"
        else:
            extension = ".webm"  # Default to webm
        
        logger.debug(f"Using file extension: {extension}")
        
        # Create temporary file with proper extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_audio:
            audio_content = await file.read()  # Use await for proper async file reading
            
            # Detailed logging of audio file
            logger.info(f"Audio file details:")
            logger.info(f"- Size: {len(audio_content)} bytes")
            logger.info(f"- Content type: {content_type}")
            logger.info(f"- Temp path: {temp_audio.name}")
            
            # Enhanced audio content validation
            if len(audio_content) < 1024:  # If less than 1KB
                logger.warning("Received audio file is very small, might be empty or corrupted")
                return JSONResponse(
                    status_code=400,
                    content={"error": "The recording is too short. Please speak for at least 1-2 seconds."}
                )
            
            if len(audio_content) > 25 * 1024 * 1024:  # If larger than 25MB
                logger.warning("Received audio file is too large")
                return JSONResponse(
                    status_code=400,
                    content={"error": "The recording is too long. Please keep it under 30 seconds."}
                )
                
            temp_audio.write(audio_content)
            temp_audio_path = temp_audio.name

        # Validate content type
        if not file.content_type.startswith('audio/'):
            logger.warning(f"Invalid content type received: {file.content_type}")
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid audio format. Please try again."}
            )

        # Process the audio file and get response
        logger.info("Starting speech to text processing...")
        transcription = speech_to_text(audio_content, temp_audio_path)
        
        # Detailed logging of transcription results
        logger.info("----- Transcription Results -----")
        logger.info(f"Raw transcription: {transcription}")
        logger.debug(f"Transcription type: {type(transcription)}")
        logger.debug(f"Transcription length: {len(str(transcription))}")
        
        # Enhanced error handling and validation
        if not transcription:
            logger.error("Received empty transcription")
            return JSONResponse(
                status_code=400,
                content={"error": "No speech detected. Please try again."}
            )
        
        # Handle error messages from speech_to_text
        if isinstance(transcription, str) and transcription.startswith(
            ("Audio too short", "Unsupported audio format", "I didn't catch that", "Please speak")
        ):
            logger.warning(f"Received error message from speech_to_text: {transcription}")
            return JSONResponse(
                status_code=400,
                content={"error": transcription}
            )
        
        # Ensure transcription is properly formatted
        if not transcription or transcription.isspace():
            logger.warning("Empty or whitespace-only transcription received")
            return JSONResponse(
                status_code=400,
                content={"error": "Could not understand the audio. Please speak clearly and try again."}
            )
            
        # Get AI response using the new multilingual LangGraph
        logger.info("Getting multilingual response for voice chat")
        response_data = get_multilingual_response(transcription, thread_id="voice_conversation")
        text_response = clean_response(response_data["response"])
        detected_language = response_data["language"]
        
        logger.info(f"Voice response generated in {detected_language}: {text_response[:100]}...")

        # Save the voice interaction to MongoDB
        try:
            save_chat_interaction(
                user_message=transcription,
                bot_response=text_response,
                message_type='voice'
            )
            logger.info("Voice interaction saved to MongoDB")
        except Exception as e:
            logger.error(f"Failed to save voice interaction to MongoDB: {e}")

        # Generate audio response using gTTS with configurable speed
        logger.info(f"Generating audio response for language: {detected_language}")
        try:
            # Get speed from environment or use default (1.3 = 30% faster)
            tts_speed = float(os.getenv('TTS_SPEED', '1.3'))
            
            # Map language codes: 'en', 'si', 'ta'
            audio_bytes = text_to_speech(text_response, language=detected_language, speed=tts_speed)
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            logger.info(f"Audio generated successfully. Size: {len(audio_bytes)} bytes, Speed: {tts_speed}x")
        except Exception as e:
            logger.error(f"Failed to generate TTS audio: {e}")
            audio_base64 = None

        # Return transcription, text response, audio, speed, and language as JSON
        return JSONResponse({
            "transcription": transcription,
            "text_response": text_response,
            "audio": audio_base64,  # Base64 encoded audio
            "speed": tts_speed,  # Playback speed multiplier
            "language": detected_language
        })
    except Exception as e:
        logger.error(f"Error during voice chat processing: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "An internal error occurred processing the voice message."}
        )
    finally:
        # Clean up temporary file
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
                logger.info(f"Temporary audio file {temp_audio_path} deleted.")
            except Exception as e:
                logger.error(f"Error deleting temporary file {temp_audio_path}: {e}")

@router.post("/chat")
async def chat(request: Request):
    logger.info("Received request for /chat")
    try:
        data = await request.json()
        user_input = data.get("message")
        language = data.get("language")  # Get language from frontend (optional)

        if not user_input:
            logger.warning("Received empty message in /chat request")
            return JSONResponse(
                status_code=400,
                content={"error": "Message cannot be empty."}
            )

        logger.info(f"Processing text chat: {user_input}")
        
        # Use the new multilingual LangGraph
        response_data = get_multilingual_response(user_input, thread_id="text_conversation")
        raw_response = clean_response(response_data["response"])
        detected_language = response_data["language"]
        
        logger.info(f"Chat response generated in {detected_language}: {raw_response[:100]}...")
        
        # Format the response
        formatted_response = format_response_as_list(raw_response)
        logger.info(f"Formatted response for /chat: {formatted_response}")

        # Save the interaction to MongoDB
        save_chat_interaction(
            user_message=user_input,
            bot_response=raw_response,
            message_type='text'
        )

        return {
            "response": formatted_response,
            "language": detected_language
        }

    except Exception as e:
        logger.error(f"Error during chat processing: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "An internal error occurred during chat processing."}
        )

@router.get("/", response_class=HTMLResponse)
async def read_root():
    logger.info("Serving index copy 2.html")
    try:
        # Update the path to look in the parent directory
        html_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "index copy 2.html")
        if not os.path.exists(html_file_path):
            logger.error(f"{html_file_path} not found.")
            return HTMLResponse(
                content="<html><body><h1>Error: Frontend file not found.</h1></body></html>",
                status_code=404
            )
        with open(html_file_path, encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"Error reading HTML file: {e}", exc_info=True)
        return HTMLResponse(
            content="<html><body><h1>Internal Server Error reading page.</h1></body></html>",
            status_code=500
        ) 