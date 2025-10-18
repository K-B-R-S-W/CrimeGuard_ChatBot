"""
LangGraph utilities for multilingual emergency response with proper language routing.
Uses LangGraph's state management and conditional routing for language-specific responses.
Sinhala requests use Google Gemini, English and Tamil use OpenAI.
"""

from typing import Literal, TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
logger = logging.getLogger(__name__)

# Set up OpenAI API key for English and Tamil
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    logger.error("OPENAI_API_KEY not set in environment variables.")
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Set up Gemini API key for Sinhala
gemini_api_key = os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    logger.error("GEMINI_API_KEY not set in environment variables.")
    raise ValueError("GEMINI_API_KEY environment variable is required for Sinhala language support")

# Initialize OpenAI model for English and Tamil
openai_model = ChatOpenAI(
    model=os.getenv('MODEL_NAME', 'gpt-3.5-turbo'),
    openai_api_key=openai_api_key
)

# Initialize Gemini model for Sinhala
gemini_model = ChatGoogleGenerativeAI(
    model=os.getenv('GEMINI_MODEL_NAME', 'gemini-2.5-flash'),
    google_api_key=gemini_api_key,
    temperature=0.7,
    convert_system_message_to_human=True  # Gemini requires this for system messages
)

logger.info("Initialized OpenAI model for English and Tamil")
logger.info("Initialized Gemini model for Sinhala")


# System prompts for each language
SYSTEM_PROMPTS = {
    'en': """You are CrimeGuard, an AI Emergency Assistant for Sri Lanka. Your primary goal is to provide immediate, clear, and actionable guidance in emergency situations.

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
Tourist Police: 011-2421052
Child & Women Bureau: 011-2444444

Tone: Remain calm, empathetic, and authoritative. Reassure the user while providing clear guidance.

Formatting:
Use numbered lists for steps (e.g., "1. Do this.", "2. Do that.").
Do NOT use Markdown bold (`**`). Use plain text.
Keep responses focused and avoid unnecessary conversation.

CRITICAL: You MUST respond ONLY in English language. Do not translate or use any other language.""",

    'si': """ඔබ CrimeGuard, ශ්‍රී ලංකාව සඳහා AI හදිසි සහායකයෙකි. ඔබේ ප්‍රධාන ඉලක්කය හදිසි අවස්ථාවන්හිදී ක්ෂණික, පැහැදිලි සහ ක්‍රියාත්මක කළ හැකි මග පෙන්වීමක් සැපයීමයි.

ආරක්ෂාවට ප්‍රමුඛත්වය: ඔවුන් ක්ෂණික අනතුරක හෝ හදිසි සහාය අවශ්‍ය නම්, පළමුව නිල හදිසි සේවා අමතන්න. ශ්‍රී ලංකා අංක පැහැදිලිව සපයන්න.
පොලිස් හදිසි අංකය: 119
ගිනි නිවීමේ හා ගලවා ගැනීමේ සේවා: 110
ගිලන් රථ (සුව සැරිය): 1990

තොරතුරු රැස් කරන්න (ආරක්ෂිත නම්): තත්වය ඉඩ දෙන්නේ නම්, ප්‍රධාන විස්තර මෘදු ලෙස විමසන්න:
සිදුවන්නේ කුමක්ද? (හදිසි අවස්ථාවේ ස්වභාවය)
ඔබ පිහිටා සිටින්නේ කොහිද? (හැකි නම් නිශ්චිත - නගරය, ප්‍රදේශය, සලකුණු)
කිසිවෙකු තුවාල ලබා හෝ ක්ෂණික අනතුරක සිටීද?

පැහැදිලි උපදෙස් සපයන්න: විස්තර කර ඇති තත්වයට අදාළ පියවරෙන් පියවර උපදෙස් දෙන්න. අංකිත ලැයිස්තු භාවිතා කරන්න. සංක්ෂිප්ත සහ තේරුම් ගත හැකි වන්න.

ශ්‍රී ලංකා සන්දර්භය: අදාළ අංක:
විදුලිය හදිසි (CEB): 1987
ගෑස් කාන්දු හදිසි (Litro): 1311
ආපදා කළමනාකරණ මධ්‍යස්ථානය: 117
සංචාරක පොලිසිය: 011-2421052
ළමා සහ කාන්තා කාර්යාංශය: 011-2444444

ස්වරය: සන්සුන්, සංවේදී සහ අධිකාරී වන්න. පැහැදිලි මග පෙන්වීමක් සපයන අතරම පරිශීලකයා සන්සුන් කරන්න.

ආකෘතිකරණය:
පියවර සඳහා අංකිත ලැයිස්තු භාවිතා කරන්න (උදා: "1. මෙය කරන්න.", "2. එය කරන්න.").
Markdown bold (`**`) භාවිතා නොකරන්න. සරල පෙළ භාවිතා කරන්න.

ඉතාම වැදගත්: ඔබ අනිවාර්යයෙන්ම සිංහල භාෂාවෙන් පමණක් ප්‍රතිචාර දැක්විය යුතුයි. වෙනත් කිසිදු භාෂාවක් භාවිතා නොකරන්න.""",

    'ta': """நீங்கள் CrimeGuard, இலங்கைக்கான AI அவசர உதவியாளர். உங்கள் முக்கிய நோக்கம் அவசரநிலைகளில் உடனடி, தெளிவான மற்றும் செயல்படக்கூடிய வழிகாட்டுதலை வழங்குவது.

பாதுகாப்புக்கு முன்னுரிமை: அவர்கள் உடனடி ஆபத்தில் அல்லது அவசர உதவி தேவைப்பட்டால், முதலில் உத்தியோகபூர்வ அவசர சேவைகளை தொடர்பு கொள்ளுமாறு பயனரை நினைவூட்டவும். இலங்கை எண்களை தெளிவாக வழங்கவும்.
காவல்துறை அவசர எண்: 119
தீயணைப்பு & மீட்பு சேவைகள்: 110
ஆம்புலன்ஸ் (சுவ செரிய): 1990

தகவல்களை சேகரிக்கவும் (பாதுகாப்பானதாக இருந்தால்): நிலைமை அனுமதித்தால், முக்கிய விவரங்களை மென்மையாக கேளுங்கள்:
என்ன நடக்கிறது? (அவசரநிலையின் தன்மை)
நீங்கள் எங்கு இருக்கிறீர்கள்? (முடிந்தால் குறிப்பாக - நகரம், பகுதி, இடங்கள்)
யாரேனும் காயமடைந்துள்ளனரா அல்லது உடனடி ஆபத்தில் உள்ளனரா?

தெளிவான வழிமுறைகளை வழங்கவும்: விவரிக்கப்பட்ட நிலைமைக்கு தொடர்புடைய படிப்படியான வழிமுறைகளை வழங்கவும். எண்ணிடப்பட்ட பட்டியல்களைப் பயன்படுத்தவும். சுருக்கமாகவும் புரிந்துகொள்ள எளிதாகவும் இருங்கள்.

இலங்கை சூழல்: தொடர்புடைய எண்கள்:
மின்சார அவசரம் (CEB): 1987
எரிவாயு கசிவு அவசரம் (Litro): 1311
பேரிடர் மேலாண்மை மையம்: 117
சுற்றுலா காவல்துறை: 011-2421052
குழந்தைகள் மற்றும் பெண்கள் பணியகம்: 011-2444444

தொனி: அமைதியாகவும், அனுதாபமாகவும், அதிகாரபூர்வமாகவும் இருங்கள். தெளிவான வழிகாட்டுதலை வழங்கும் போது பயனரை உறுதியளிக்கவும்.

வடிவமைப்பு:
படிகளுக்கு எண்ணிடப்பட்ட பட்டியல்களைப் பயன்படுத்தவும் (எ.கா: "1. இதை செய்யுங்கள்.", "2. அதை செய்யுங்கள்.").
Markdown bold (`**`) பயன்படுத்த வேண்டாம். எளிய உரையைப் பயன்படுத்தவும்.

மிக முக்கியம்: நீங்கள் கட்டாயமாக தமிழ் மொழியில் மட்டுமே பதிலளிக்க வேண்டும். வேறு எந்த மொழியையும் பயன்படுத்த வேண்டாம்."""
}


# Define the State
class MultilingualState(TypedDict):
    messages: list[BaseMessage]
    language: str
    detected_language: str


def detect_language(text: str) -> str:
    """
    Detects if the text is in Sinhala, Tamil, or English.
    Returns 'si' for Sinhala, 'ta' for Tamil, 'en' for English.
    """
    # Check for Sinhala characters (Unicode range: 0D80-0DFF)
    sinhala_chars = len([c for c in text if '\u0D80' <= c <= '\u0DFF'])
    # Check for Tamil characters (Unicode range: 0B80-0BFF)
    tamil_chars = len([c for c in text if '\u0B80' <= c <= '\u0BFF'])
    # Check for English/Latin characters
    english_chars = len([c for c in text if c.isalpha() and ord(c) < 128])
    
    total_chars = sinhala_chars + tamil_chars + english_chars
    
    logger.info(f"Language detection - Sinhala: {sinhala_chars}, Tamil: {tamil_chars}, English: {english_chars}")
    
    if total_chars == 0:
        return 'en'  # Default to English if no alphabet characters
    
    # Determine the dominant language with higher threshold
    sinhala_ratio = sinhala_chars / total_chars if total_chars > 0 else 0
    tamil_ratio = tamil_chars / total_chars if total_chars > 0 else 0
    english_ratio = english_chars / total_chars if total_chars > 0 else 0
    
    logger.info(f"Language ratios - Sinhala: {sinhala_ratio:.2f}, Tamil: {tamil_ratio:.2f}, English: {english_ratio:.2f}")
    
    # Need at least 30% of the language to consider it
    if sinhala_ratio > 0.3 and sinhala_ratio >= tamil_ratio and sinhala_ratio >= english_ratio:
        return 'si'
    elif tamil_ratio > 0.3 and tamil_ratio >= sinhala_ratio and tamil_ratio >= english_ratio:
        return 'ta'
    else:
        return 'en'


# Node: Detect Language
def detect_language_node(state: MultilingualState) -> MultilingualState:
    """Node to detect the language from the user's message."""
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage):
        detected_lang = detect_language(last_message.content)
        logger.info(f"Detected language: {detected_lang} from message: {last_message.content[:50]}...")
        return {
            **state,
            "detected_language": detected_lang,
            "language": detected_lang  # Set the language to detected
        }
    return state


# Node: Route to appropriate language model
def route_by_language(state: MultilingualState) -> Literal["english_model", "sinhala_model", "tamil_model"]:
    """Conditional edge function to route based on detected language."""
    language = state.get("detected_language", "en")
    logger.info(f"Routing to language: {language}")
    
    if language == "si":
        return "sinhala_model"
    elif language == "ta":
        return "tamil_model"
    else:
        return "english_model"


# Node: English Model (uses OpenAI)
def english_model_node(state: MultilingualState) -> MultilingualState:
    """Process the message with English prompt using OpenAI."""
    logger.info("Processing with English model (OpenAI)")
    system_message = SystemMessage(content=SYSTEM_PROMPTS['en'])
    messages = [system_message] + state["messages"]
    
    try:
        response = openai_model.invoke(messages)
        logger.info(f"English model response: {response.content[:100]}...")
        return {
            **state,
            "messages": state["messages"] + [response]
        }
    except Exception as e:
        logger.error(f"Error in English model: {e}", exc_info=True)
        error_msg = SystemMessage(content="Sorry, I encountered an error. Please try again.")
        return {
            **state,
            "messages": state["messages"] + [error_msg]
        }


# Node: Sinhala Model (uses Google Gemini)
def sinhala_model_node(state: MultilingualState) -> MultilingualState:
    """Process the message with Sinhala prompt using Google Gemini."""
    logger.info("Processing with Sinhala model (Google Gemini)")
    system_message = SystemMessage(content=SYSTEM_PROMPTS['si'])
    messages = [system_message] + state["messages"]
    
    try:
        response = gemini_model.invoke(messages)
        logger.info(f"Sinhala model (Gemini) response: {response.content[:100]}...")
        return {
            **state,
            "messages": state["messages"] + [response]
        }
    except Exception as e:
        logger.error(f"Error in Sinhala model (Gemini): {e}", exc_info=True)
        error_msg = SystemMessage(content="සමාවන්න, දෝෂයක් ඇතිවිය. කරුණාකර නැවත උත්සාහ කරන්න.")
        return {
            **state,
            "messages": state["messages"] + [error_msg]
        }


# Node: Tamil Model (uses OpenAI)
def tamil_model_node(state: MultilingualState) -> MultilingualState:
    """Process the message with Tamil prompt using OpenAI."""
    logger.info("Processing with Tamil model (OpenAI)")
    system_message = SystemMessage(content=SYSTEM_PROMPTS['ta'])
    messages = [system_message] + state["messages"]
    
    try:
        response = openai_model.invoke(messages)
        logger.info(f"Tamil model response: {response.content[:100]}...")
        return {
            **state,
            "messages": state["messages"] + [response]
        }
    except Exception as e:
        logger.error(f"Error in Tamil model: {e}", exc_info=True)
        error_msg = SystemMessage(content="மன்னிக்கவும், பிழை ஏற்பட்டது. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.")
        return {
            **state,
            "messages": state["messages"] + [error_msg]
        }


# Build the LangGraph
def create_multilingual_graph():
    """Create and compile the multilingual LangGraph."""
    workflow = StateGraph(MultilingualState)
    
    # Add nodes
    workflow.add_node("detect_language", detect_language_node)
    workflow.add_node("english_model", english_model_node)
    workflow.add_node("sinhala_model", sinhala_model_node)
    workflow.add_node("tamil_model", tamil_model_node)
    
    # Add edges
    workflow.add_edge(START, "detect_language")
    
    # Add conditional edges based on language
    workflow.add_conditional_edges(
        "detect_language",
        route_by_language,
        {
            "english_model": "english_model",
            "sinhala_model": "sinhala_model",
            "tamil_model": "tamil_model"
        }
    )
    
    # All models end after processing
    workflow.add_edge("english_model", END)
    workflow.add_edge("sinhala_model", END)
    workflow.add_edge("tamil_model", END)
    
    # Compile with memory
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# Create the global graph instance
multilingual_graph = create_multilingual_graph()


# Helper function to get response
def get_multilingual_response(user_message: str, thread_id: str = "default") -> dict:
    """
    Get a response from the multilingual graph.
    
    Args:
        user_message: The user's message
        thread_id: Thread ID for conversation memory
        
    Returns:
        dict with 'response' (text) and 'language' (detected language)
    """
    try:
        config = {"configurable": {"thread_id": thread_id}}
        
        # Invoke the graph
        result = multilingual_graph.invoke(
            {
                "messages": [HumanMessage(content=user_message)],
                "language": "",
                "detected_language": ""
            },
            config=config
        )
        
        # Extract the response
        response_message = result["messages"][-1]
        detected_lang = result.get("detected_language", "en")
        
        logger.info(f"Final response in {detected_lang}: {response_message.content[:100]}...")
        
        return {
            "response": response_message.content,
            "language": detected_lang
        }
        
    except Exception as e:
        logger.error(f"Error getting multilingual response: {e}", exc_info=True)
        return {
            "response": "An error occurred. Please try again.",
            "language": "en"
        }


def clean_response(text: str) -> str:
    """Remove Markdown bold markers (**) and potential unwanted artifacts."""
    return text.replace("**", "").strip()
