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
    get_ai_response,
    text_to_speech,
    format_response_as_list,
    graph,
)
from langchain_core.messages import HumanMessage

# Setup logging
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.post("/voice_chat")
async def voice_chat(file: UploadFile = File(...)):
    logger.info("Received request for /voice_chat")
    temp_audio_path = None
    try:
        # Create temporary file for audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            audio_content = file.file.read()
            temp_audio.write(audio_content)
            temp_audio_path = temp_audio.name

        # Process the audio file and get response
        transcription = speech_to_text(audio_content, temp_audio_path)
        # Get AI response
        text_response = get_ai_response(transcription)

        # Return only the text response as JSON
        return JSONResponse({"text_response": text_response})
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

        if not user_input:
            logger.warning("Received empty message in /chat request")
            return JSONResponse(
                status_code=400,
                content={"error": "Message cannot be empty."}
            )

        logger.info(f"Invoking LangGraph for text chat: {user_input}")
        config = {"configurable": {"thread_id": "text_conversation"}}
        response = graph.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config
        )
        raw_response = response["messages"][-1].content
        logger.info(f"Raw response from graph: {raw_response}")
        formatted_response = format_response_as_list(raw_response)
        logger.info(f"Formatted response for /chat: {formatted_response}")

        return {"response": formatted_response}

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