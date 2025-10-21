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
from AI_backend.app.db_utils import save_chat_interaction, get_emergency_calls, get_emergency_statistics
from AI_backend.app.twilio_service import twilio_service

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
        
        # FIRST: Check if this is an emergency call request
        emergency_intent = twilio_service.detect_emergency_intent(user_input)
        
        if emergency_intent:
            emergency_type = emergency_intent['type']
            emergency_number = emergency_intent['number']
            detected_lang = emergency_intent.get('language', 'en')
            
            logger.info(f"Emergency call detected: {emergency_type}")
            
            # Initiate the emergency call WITH user's message
            success, call_info = twilio_service.make_emergency_call(
                to_number=emergency_number,
                emergency_type=emergency_type,
                user_message=user_input,  # Pass user's message to be spoken in call
                language=detected_lang
            )
            
            # Get appropriate response message
            response_message = twilio_service.get_emergency_response_text(
                emergency_type=emergency_type,
                language=detected_lang
            )
            
            # Get service name in user's language
            service_name = twilio_service.get_service_name(
                emergency_type=emergency_type,
                language=detected_lang
            )
            
            if success:
                logger.info(f"Emergency call successful: {call_info}")
                # Save the emergency interaction
                save_chat_interaction(
                    user_message=user_input,
                    bot_response=f"Emergency call initiated: {emergency_type} - Call SID: {call_info}",
                    message_type='emergency_call'
                )
            else:
                logger.error(f"Emergency call failed: {call_info}")
                response_message += f"\n\n⚠️ Note: Automated call failed ({call_info}). Please dial {emergency_number} directly!"
            
            return {
                "response": response_message,
                "language": detected_lang,
                "emergency_call": True,
                "emergency_type": emergency_type,
                "service_name": service_name,
                "emergency_number": emergency_number,
                "call_initiated": success,
                "call_sid": call_info if success else None
            }
        
        # If not an emergency call, proceed with normal chat
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
            "language": detected_language,
            "emergency_call": False
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

# Emergency call management endpoints
class CancelCallRequest(BaseModel):
    call_sid: str

@router.post("/cancel_call")
async def cancel_emergency_call(request: CancelCallRequest):
    """
    Cancel an ongoing emergency call
    """
    try:
        call_sid = request.call_sid
        
        if not call_sid:
            return JSONResponse(
                status_code=400,
                content={"error": "Call SID is required"}
            )
        
        logger.info(f"Canceling call: {call_sid}")
        
        success, message = twilio_service.cancel_emergency_call(call_sid)
        
        if success:
            return {
                "success": True,
                "message": message
            }
        else:
            return JSONResponse(
                status_code=500,
                content={"error": message}
            )
    
    except Exception as e:
        logger.error(f"Error canceling call: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.get("/call_status/{call_sid}")
async def get_call_status(call_sid: str):
    """
    Get the status of an emergency call
    """
    try:
        logger.info(f"Getting status for call: {call_sid}")
        
        success, status = twilio_service.get_call_status(call_sid)
        
        if success:
            return {
                "success": True,
                "status": status,
                "call_sid": call_sid
            }
        else:
            return JSONResponse(
                status_code=500,
                content={"error": status}
            )
    
    except Exception as e:
        logger.error(f"Error getting call status: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# Audio file serving endpoint
@router.get("/audio/{filename}")
async def serve_audio_file(filename: str):
    """
    Serve audio files for emergency calls
    """
    try:
        # Get audio storage directory
        audio_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'audio_storage'
        )
        
        # Construct full file path
        file_path = os.path.join(audio_dir, filename)
        
        # Security check: ensure file is within audio_storage directory
        if not os.path.abspath(file_path).startswith(os.path.abspath(audio_dir)):
            logger.warning(f"Attempted path traversal: {filename}")
            return JSONResponse(
                status_code=403,
                content={"error": "Access denied"}
            )
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"Audio file not found: {file_path}")
            return JSONResponse(
                status_code=404,
                content={"error": "Audio file not found"}
            )
        
        # Serve the file
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            media_type="audio/mpeg",
            filename=filename
        )
    
    except Exception as e:
        logger.error(f"Error serving audio file: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@router.get("/emergency_calls")
async def get_emergency_call_history(
    limit: int = 100,
    emergency_type: str = None,
    language: str = None,
    status: str = None,
    min_confidence: float = None
):
    """
    Get emergency call history with optional filters
    
    Query Parameters:
    - limit: Maximum number of records (default: 100)
    - emergency_type: Filter by service (police/fire/ambulance)
    - language: Filter by language (en/si/ta)
    - status: Filter by call status (initiated/ringing/in-progress/completed/failed/canceled)
    - min_confidence: Minimum AI confidence threshold (0.0-1.0)
    """
    try:
        logger.info(f"Retrieving emergency calls with filters: type={emergency_type}, lang={language}, status={status}, min_conf={min_confidence}")
        
        calls = get_emergency_calls(
            limit=limit,
            emergency_type=emergency_type,
            language=language,
            status=status,
            min_confidence=min_confidence
        )
        
        return JSONResponse(content={
            "success": True,
            "count": len(calls),
            "calls": calls
        })
    
    except Exception as e:
        logger.error(f"Error retrieving emergency calls: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@router.get("/emergency_statistics")
async def get_emergency_call_statistics():
    """
    Get comprehensive statistics about emergency calls
    
    Returns:
    - Total call count
    - Breakdown by emergency type (police/fire/ambulance)
    - Breakdown by language (English/Sinhala/Tamil)
    - Breakdown by call status
    - Average/min/max confidence scores
    """
    try:
        logger.info("Calculating emergency call statistics")
        
        stats = get_emergency_statistics()
        
        return JSONResponse(content={
            "success": True,
            "statistics": stats
        })
    
    except Exception as e:
        logger.error(f"Error getting emergency statistics: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

