from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from groq import Groq, APIError
from gtts import gTTS
from io import BytesIO
import tempfile
import logging
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup basic logging
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
logger = logging.getLogger(__name__)

# Set up Groq API key
groq_api_key = os.getenv('GROQ_API_KEY')
if not groq_api_key:
    logger.error("GROQ_API_KEY not set in environment variables.")
    raise ValueError("GROQ_API_KEY environment variable is required")

# Initialize Groq clients
try:
    groq_client = Groq(api_key=groq_api_key)
    model = ChatGroq(
        model=os.getenv('MODEL_NAME', 'meta-llama/llama-4-scout-17b-16e-instruct'),
        groq_api_key=groq_api_key
    )
except Exception as e:
    logger.error(f"Failed to initialize Groq clients: {e}")
    raise

# Define the system prompt
system_prompt = """You are CrimeGuard, an AI Emergency Assistant for Sri Lanka. Your primary goal is to provide immediate, clear, and actionable guidance in emergency situations.

Prioritize Safety: Always remind the user to contact official emergency services first if they are in immediate danger or require urgent help. Provide the correct Sri Lankan numbers clearly.
Police Emergency Hotline: 119
Fire & Rescue Services: 110
Ambulance (Suwa Seriya): 1990

Gather Information (If Safe): If the situation allows, gently ask for key details:
What is happening? (Nature of emergency)
Where are you located? (Be specific if possible - city, area, landmarks)
Is anyone injured or in immediate danger?

Provide Clear Instructions: Give step-by-step instructions relevant to the situation described. Use numbered lists. Be concise and easy to understand.

Sri Lanka Context: Be aware of Sri Lankan context (e.g., specific emergency numbers, common situations). Relevant numbers:
Electricity Emergency (CEB): 1987
Gas Leak Emergency (Litro): 1311
Disaster Management Centre: 117
Tourist Police: 011-2421052 (Corrected number)
Child & Women Bureau: 011-2444444

Tone: Remain calm, empathetic, and authoritative. Reassure the user while providing clear guidance.

Formatting:
Use numbered lists for steps (e.g., "1. Do this.", "2. Do that.").
Do NOT use Markdown bold (`**`). Use plain text.
Keep responses focused and avoid unnecessary conversation.

Example Interaction:
User: My house is on fire!
Assistant: Okay, stay calm. 1. If you haven't already, evacuate everyone immediately. 2. Call the Fire & Rescue Services at 110 right away. 3. Close doors behind you as you leave to slow the fire, but only if it's safe. 4. Do not go back inside for any reason. 5. Where are you located? I need your address for the fire department.

If the user asks a general question, answer it concisely based on Sri Lankan emergency procedures. If the query is unclear or not an emergency, gently guide them or state you primarily handle emergencies.
"""

# LangGraph State and Workflow
class VoiceAppState(MessagesState):
    pass

def call_model(state: VoiceAppState):
    logger.info(f"Calling model with messages: {state['messages']}")
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    try:
        response = model.invoke(messages)
        logger.info(f"Model response received: {response.content}")
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"Error invoking the language model: {e}")
        error_message = "Sorry, I encountered an error trying to process that. Please try again."
        return {"messages": [SystemMessage(content=error_message)]}

# Initialize workflow
workflow = StateGraph(VoiceAppState)
workflow.add_node("model", call_model)
workflow.set_entry_point("model")
workflow.set_finish_point("model")

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)

# Helper Functions
def clean_response(text):
    """Remove Markdown bold markers (**) and potential unwanted artifacts."""
    return text.replace("**", "").strip()

def format_response_as_list(response_text):
    """Analyzes response text and formats it appropriately (steps or plain text)."""
    cleaned_text = clean_response(response_text)
    step_pattern = r'^\s*(\d+\.|Step\s*\d+\s*[:-]?)\s+'
    lines = cleaned_text.split('\n')
    steps = []
    is_list_format = False

    for line in lines:
        line = line.strip()
        if re.match(step_pattern, line):
            is_list_format = True
            step_text = re.sub(step_pattern, '', line)
            if step_text:
                steps.append(step_text)
        elif is_list_format and line:
            steps.append(line)
        elif line:
            steps.append(line)

    if is_list_format and len(steps) > 1:
        steps = [s.strip() for s in steps if s.strip()]
        return {"type": "steps", "content": steps}
    else:
        final_text = "\n".join(steps).strip()
        if not final_text:
            return {"type": "text", "content": "..."}
        return {"type": "text", "content": final_text}

def speech_to_text(file_content, temp_path):
    """Transcribes audio file using Groq Whisper API."""
    logger.info("Starting audio transcription...")
    try:
        with open(temp_path, "rb") as audio_file_to_transcribe:
            transcription_response = groq_client.audio.transcriptions.create(
                file=(temp_path, audio_file_to_transcribe.read()),
                model="whisper-large-v3",
                response_format="text"
            )
        transcription = transcription_response
        logger.info(f"Transcription successful: '{transcription}'")
        if not transcription or transcription.strip() == "":
            logger.warning("Transcription resulted in empty text.")
            return "I didn't catch that. Could you please speak clearly?"
        return transcription
    except APIError as e:
        logger.error(f"Groq API Error during transcription: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error during transcription: {e}", exc_info=True)
        raise

def get_ai_response(transcription: str):
    """Gets AI response from LangGraph based on transcription."""
    logger.info(f"Invoking LangGraph with transcription: '{transcription}'")
    config = {"configurable": {"thread_id": "voice_conversation"}}
    try:
        graph_response = graph.invoke(
            {"messages": [HumanMessage(content=transcription)]},
            config=config
        )
        raw_response = graph_response["messages"][-1].content
        logger.info(f"Raw response from graph: '{raw_response}'")
        response_text = clean_response(raw_response)
        logger.info(f"Cleaned text for TTS: '{response_text}'")
        if not response_text or response_text.strip() == "":
            logger.warning("LLM response was empty.")
            return "I received your message but have no specific instructions."
        return response_text
    except Exception as e:
        logger.error(f"Error invoking LangGraph: {e}", exc_info=True)
        raise

def text_to_speech(text: str):
    """Converts text to speech using gTTS and returns audio bytes."""
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