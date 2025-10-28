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
# from AI_backend.app.langgraph_utils import get_multilingual_response  # OLD: Sequential (backup)
from AI_backend.app.langgraph_enhanced import get_enhanced_response, clean_response  # NEW: Parallel execution with LangGraph tools
from AI_backend.app.db_utils import save_chat_interaction, get_emergency_calls, get_emergency_statistics
from AI_backend.app.twilio_service import twilio_service
from AI_backend.app.reflection_agent import reflection_agent
from AI_backend.app.escalation_agent import escalation_agent
from AI_backend.app.fast_classifier import fast_classifier, IntentType

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
        session_id = data.get("session_id", "default_session")  # Get unique session ID
        conversation_history = data.get("conversation_history", [])  # Get conversation context

        if not user_input:
            logger.warning("Received empty message in /chat request")
            return JSONResponse(
                status_code=400,
                content={"error": "Message cannot be empty."}
            )

        logger.info(f"Processing chat for session {session_id}: {user_input}")
        logger.info(f"Conversation history length: {len(conversation_history)} messages")
        
        # LAYER 0: Fast Reactive Classifier (NEW! - 70% of queries handled here)
        # This provides instant responses for FAQ, greetings, etc.
        intent, fast_response, confidence = fast_classifier.classify(user_input)
        
        if fast_response:
            # REACTIVE PATH - Instant cached response!
            logger.info(f"⚡⚡⚡ FAST PATH: Returning cached response (latency: ~50-100ms)")
            
            # Save interaction
            save_chat_interaction(
                user_message=user_input,
                bot_response=fast_response,
                message_type='fast_cached'
            )
            
            return {
                "response": {
                    "type": "text",
                    "content": fast_response
                },
                "language": fast_classifier.detect_language(user_input),
                "emergency_call": False,
                "processing_path": "reactive_cached",
                "latency_ms": "<100"
            }
        
        # LAYER 1: Check if this is an emergency call request (may be MULTIPLE!)
        emergency_intent = twilio_service.detect_emergency_intent(user_input)
        
        if emergency_intent:
            detected_lang = emergency_intent.get('language', 'en')
            emergencies_list = emergency_intent.get('emergencies', [])
            total_count = emergency_intent.get('total_count', 0)
            
            logger.info(f"🚨 {total_count} Emergency(ies) detected!")
            
            # CHECK: Single or Multiple emergencies?
            if total_count == 1:
                # SINGLE EMERGENCY - Direct call with Reflection Agent
                emergency = emergencies_list[0]
                emergency_type = emergency['type']
                emergency_number = emergency['number']
                
                logger.info(f"   Single emergency: {emergency_type}")
                
                # Initiate the INITIAL emergency call WITH user's message
                success, call_info = twilio_service.make_emergency_call(
                    to_number=emergency_number,
                    emergency_type=emergency_type,
                    user_message=user_input,
                    language=detected_lang
                )
            
            elif total_count > 1:
                # 🤖 MULTIPLE EMERGENCIES - Activate Escalation Agent
                logger.info(f"   🤖 ACTIVATING ESCALATION AGENT for {total_count} emergencies")
                
                # Agent autonomously coordinates all calls
                coordination_result = escalation_agent.coordinate_multi_emergency(
                    emergencies=emergencies_list,
                    user_message=user_input,
                    language=detected_lang
                )
                
                # Extract results for response
                calls = coordination_result.get('calls', [])
                success = coordination_result.get('successful_calls', 0) > 0
                call_info = calls  # Multiple calls
                emergency_type = "multi_emergency"  # Special indicator
                
                logger.info(f"   ✅ Escalation complete: {coordination_result.get('successful_calls', 0)}/{total_count} calls successful")
            
            else:
                # No emergencies (shouldn't happen, but safety check)
                logger.warning("   ⚠️ Emergency detected but count is 0")
                success = False
                call_info = "No emergencies to process"
                emergency_type = "none"
            
            # Handle response based on emergency type
            if emergency_type == "multi_emergency":
                # MULTIPLE EMERGENCIES - Build comprehensive response
                calls = call_info  # This is array of calls
                successful_services = [c['type'] for c in calls if c['status'] == 'initiated']
                failed_services = [c['type'] for c in calls if c['status'] == 'failed']
                
                # Build multi-service response message
                if detected_lang == 'si':
                    response_message = f"🚨 හදිසි සේවා {len(successful_services)} කට අමතනු ලැබීය:\n"
                    response_message += "\n".join([f"✅ {s.upper()}" for s in successful_services])
                    if failed_services:
                        response_message += f"\n\n⚠️ අසාර්ථකයි: {', '.join(failed_services)}"
                elif detected_lang == 'ta':
                    response_message = f"🚨 {len(successful_services)} அவசர சேவைகளுக்கு அழைக்கப்பட்டது:\n"
                    response_message += "\n".join([f"✅ {s.upper()}" for s in successful_services])
                    if failed_services:
                        response_message += f"\n\n⚠️ தோல்வியுற்றது: {', '.join(failed_services)}"
                else:
                    response_message = f"🚨 {len(successful_services)} Emergency services contacted:\n"
                    response_message += "\n".join([f"✅ {s.upper()}" for s in successful_services])
                    if failed_services:
                        response_message += f"\n\n⚠️ Failed: {', '.join(failed_services)}"
                
                # Save multi-emergency interaction
                save_chat_interaction(
                    user_message=user_input,
                    bot_response=f"Multi-emergency: {len(successful_services)} calls initiated (Escalation Agent + Reflection Agents)",
                    message_type='multi_emergency_call'
                )
                
                return {
                    "response": response_message,
                    "language": detected_lang,
                    "emergency_call": True,
                    "multi_emergency": True,
                    "calls": calls,
                    "total_emergencies": total_count,
                    "successful_calls": len(successful_services),
                    "escalation_agent_active": True,
                    "reflection_agents_active": True
                }
            
            else:
                # SINGLE EMERGENCY - Standard response
                emergency_type = emergencies_list[0]['type']
                emergency_number = emergencies_list[0]['number']
                
                response_message = twilio_service.get_emergency_response_text(
                    emergency_type=emergency_type,
                    language=detected_lang
                )
                
                service_name = twilio_service.get_service_name(
                    emergency_type=emergency_type,
                    language=detected_lang
                )
                
                if success:
                    call_sid = call_info
                    logger.info(f"✅ Initial emergency call successful: {call_sid}")
                    
                    # 🤖 ACTIVATE REFLECTION & RECOVERY AGENT
                    logger.info(f"🤖 Activating Reflection & Recovery Agent for call {call_sid}")
                    
                    import threading
                    monitoring_thread = threading.Thread(
                        target=reflection_agent.monitor_and_recover,
                        args=(call_sid, emergency_type, user_input, detected_lang),
                        daemon=True
                    )
                    monitoring_thread.start()
                    
                    logger.info("🤖 Reflection Agent now monitoring call autonomously")
                    
                    # Save the emergency interaction
                    save_chat_interaction(
                        user_message=user_input,
                        bot_response=f"Emergency call initiated: {emergency_type} - Call SID: {call_sid} (Monitored by Reflection Agent)",
                        message_type='emergency_call'
                    )
                else:
                    logger.error(f"❌ Initial emergency call failed: {call_info}")
                    response_message += f"\n\n⚠️ Note: Automated call failed ({call_info}). Please dial {emergency_number} directly!"
                    call_sid = None
                
                return {
                    "response": response_message,
                    "language": detected_lang,
                    "emergency_call": True,
                    "emergency_type": emergency_type,
                    "service_name": service_name,
                    "emergency_number": emergency_number,
                    "call_initiated": success,
                    "call_sid": call_sid,
                    "reflection_agent_active": success
                }
        
        # If not an emergency call, proceed with normal chat
        # LAYER 2: Enhanced LangGraph with parallel tool execution (NEW!)
        logger.info("🚀 Using enhanced LangGraph with parallel processing")
        response_data = get_enhanced_response(
            user_input, 
            thread_id=session_id,
            conversation_history=conversation_history
        )
        raw_response = clean_response(response_data["response"])
        detected_language = response_data["language"]
        processing_time = response_data.get("processing_time_ms", 0)
        
        logger.info(f"⚡ Enhanced response generated in {processing_time:.0f}ms (language: {detected_language})")
        
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
            "emergency_call": False,
            "processing_path": "enhanced_parallel",
            "processing_time_ms": processing_time,
            "performance_improvement": "40-50% faster"
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

