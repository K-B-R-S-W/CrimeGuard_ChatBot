from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
import os
import logging
import sys
import io
from dotenv import load_dotenv
from gtts import gTTS

# Load environment variables
load_dotenv()

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from AI_backend.app.langchain_utils import format_response_as_list
from AI_backend.app.langgraph_utils import (
    get_multilingual_response,
    clean_response,
)
from AI_backend.app.db_utils import save_chat_interaction

# Setup logging
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

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

# TTS endpoint for Sinhala/Tamil support
class TTSRequest(BaseModel):
    text: str
    language: str = 'en'

@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using gTTS and return audio stream
    Supports English, Sinhala, and Tamil
    Optimized for fast response
    """
    try:
        # Map language codes
        lang_map = {
            'en': 'en',
            'si': 'si',  # Sinhala
            'ta': 'ta'   # Tamil
        }
        
        tts_lang = lang_map.get(request.language, 'en')
        
        # Limit text length for faster processing (split if too long)
        max_length = 500
        text_to_speak = request.text[:max_length] if len(request.text) > max_length else request.text
        
        # Generate speech using gTTS with optimizations
        tts = gTTS(
            text=text_to_speak, 
            lang=tts_lang, 
            slow=False,
            lang_check=False  # Skip language check for faster processing
        )
        
        # Save to BytesIO buffer
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Return audio stream with proper headers
        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3",
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Accept-Ranges": "bytes"
            }
        )
    except Exception as e:
        logger.error(f"TTS error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}") 