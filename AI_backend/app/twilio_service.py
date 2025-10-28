"""
Twilio Voice Call Service for Emergency Situations
Uses LLM to intelligently detect emergencies and initiate voice calls to appropriate authorities
"""
import os
import logging
from typing import Dict, Optional, Tuple
from twilio.rest import Client
from dotenv import load_dotenv
import json
from app.db_utils import save_emergency_call, update_call_status

load_dotenv()

logger = logging.getLogger(__name__)

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '+15673721765')

# Emergency Service Numbers in Sri Lanka (configurable via .env)
EMERGENCY_NUMBERS = {
    'police': os.getenv('EMERGENCY_POLICE_NUMBER', '+94119'),        # Default: Sri Lanka Police
    'fire': os.getenv('EMERGENCY_FIRE_NUMBER', '+94110'),            # Default: Fire & Rescue
    'ambulance': os.getenv('EMERGENCY_AMBULANCE_NUMBER', '+941990')  # Default: Suwa Seriya Ambulance
}

# Emergency detection prompt for LLM
EMERGENCY_DETECTION_PROMPT = """You are an emergency detection AI assistant for Sri Lanka. Your job is to analyze user messages and determine if they require an emergency call to authorities.

⚠️ IMPORTANT: A user message may contain MULTIPLE emergencies (e.g., "Fire AND people injured!"). Detect ALL emergencies present.

Available Emergency Services in Sri Lanka:
1. Police (119) - For crimes, threats, violence, robberies, assaults, suspicious activities
2. Fire Department (110) - For fires, gas leaks, building collapses, explosions
3. Ambulance/Medical (1990 - Suwa Seriya) - For medical emergencies, injuries, accidents, health issues

Analyze the following user message and determine:
1. Is this an ACTUAL emergency requiring immediate authority contact? (not just a question or minor issue)
2. What is the SEVERITY level?
3. Which emergency service(s) should be called? (MAY BE MULTIPLE!)
4. What is the detected language? (en for English, si for Sinhala, ta for Tamil)

CRITICAL SEVERITY ASSESSMENT RULES:

🟢 MINOR ISSUES (DO NOT CALL):
- Small cuts, minor bleeding, minor bruises
- Minor burns (first-degree)
- Common cold, mild fever, headache
- Asking for first aid advice
- Minor household problems
- Questions about symptoms or treatment
- Examples: "small cut bleeding", "minor injury", "first aid tips", "පොඩි තුවාලයක්", "සුළු තුවාලය"

🔴 SEVERE EMERGENCIES (CALL IMMEDIATELY):
- Life-threatening injuries (heavy bleeding, unconsciousness, chest pain)
- Serious accidents (vehicle collision, fall from height, drowning)
- Severe medical conditions (heart attack, stroke, difficulty breathing, severe burns)
- Active crimes (robbery in progress, assault happening now, intruder present)
- Active fires or explosions
- Someone in immediate danger
- Examples: "someone unconscious", "can't breathe", "chest pain", "robbery happening", "house on fire"

IMPORTANT DECISION RULES:
- If user asks "how to stop bleeding" or "what should I do" → NOT an emergency (just advice needed)
- If user says "call ambulance" or "need help now" → Check severity first
- Minor injuries + asking for advice → NOT an emergency
- Severe injuries + urgent situation → IS an emergency
- Questions about emergency services → NOT an emergency
- When in doubt about severity → It's NOT an emergency (be conservative)

User Message: "{message}"

Respond ONLY with valid JSON in this exact format (no extra text):

FOR SINGLE EMERGENCY:
{{
    "is_emergency": true/false,
    "emergencies": [
        {{
            "type": "police/fire/ambulance",
            "severity": "minor/moderate/severe",
            "confidence": 0.0-1.0,
            "reasoning": "why this service is needed"
        }}
    ],
    "language": "en/si/ta",
    "total_count": 1
}}

FOR MULTIPLE EMERGENCIES:
{{
    "is_emergency": true,
    "emergencies": [
        {{
            "type": "fire",
            "severity": "severe",
            "confidence": 0.95,
            "reasoning": "building on fire"
        }},
        {{
            "type": "ambulance",
            "severity": "severe",
            "confidence": 0.90,
            "reasoning": "people injured/trapped"
        }}
    ],
    "language": "en",
    "total_count": 2
}}

EXAMPLES:
- "Fire in building!" → 1 emergency (fire only)
- "Fire AND people injured!" → 2 emergencies (fire + ambulance)
- "Car accident with injuries" → 2 emergencies (police + ambulance)
- "Robbery in progress" → 1 emergency (police only)
- "Someone breaking in and I'm hurt" → 2 emergencies (police + ambulance)"""


class TwilioCallService:
    """Service to handle emergency voice calls via Twilio"""
    
    def __init__(self):
        """Initialize Twilio client and LLM for emergency detection"""
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            logger.warning("Twilio credentials not configured. Call service will not work.")
            self.client = None
        else:
            try:
                self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.client = None
        
        # Initialize LLM for emergency detection
        try:
            from langchain_openai import ChatOpenAI
            self.emergency_llm = ChatOpenAI(
                model="gpt-4o-mini",  # Fast and cost-effective for classification
                temperature=0.1,  # Low temperature for consistent detection
                max_tokens=200
            )
            logger.info("Emergency detection LLM initialized (GPT-4o-mini)")
        except Exception as e:
            logger.error(f"Failed to initialize emergency detection LLM: {e}")
            self.emergency_llm = None
    
    def detect_emergency_intent(self, message: str) -> Optional[Dict]:
        """
        Use LLM to intelligently detect if the message requires emergency call(s)
        
        NOW SUPPORTS MULTIPLE EMERGENCIES (e.g., "Fire AND people injured!")
        
        Args:
            message: User's message to analyze
            
        Returns:
            Dict with emergencies array (may contain multiple), or None if no emergency
            Example: {
                'emergencies': [
                    {'type': 'fire', 'severity': 'severe', 'confidence': 0.95},
                    {'type': 'ambulance', 'severity': 'severe', 'confidence': 0.90}
                ],
                'language': 'en',
                'total_count': 2
            }
        """
        if not self.emergency_llm:
            logger.error("Emergency detection LLM not initialized")
            return None
        
        try:
            # Create the detection prompt
            prompt = EMERGENCY_DETECTION_PROMPT.format(message=message)
            
            logger.info(f"🔍 Analyzing message for emergency: {message[:100]}...")
            
            # Get LLM response
            response = self.emergency_llm.invoke(prompt)
            response_text = response.content.strip()
            
            logger.debug(f"LLM Response: {response_text}")
            
            # Parse JSON response
            try:
                # Extract JSON from response (in case there's extra text)
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    result = json.loads(json_str)
                else:
                    logger.error("No JSON found in LLM response")
                    return None
                
                # Check if it's an emergency
                is_emergency = result.get('is_emergency', False)
                emergencies_list = result.get('emergencies', [])
                language = result.get('language', 'en')
                total_count = result.get('total_count', 0)
                
                if not is_emergency or not emergencies_list:
                    logger.info(f"ℹ️ Not an emergency")
                    return None
                
                # Filter severe emergencies with high confidence
                severe_emergencies = []
                for emerg in emergencies_list:
                    emerg_type = emerg.get('type', 'none')
                    severity = emerg.get('severity', 'minor')
                    confidence = emerg.get('confidence', 0.0)
                    reasoning = emerg.get('reasoning', '')
                    
                    logger.info(f"📊 Emergency #{len(severe_emergencies) + 1}:")
                    logger.info(f"   Type: {emerg_type}")
                    logger.info(f"   Severity: {severity}")
                    logger.info(f"   Confidence: {confidence}")
                    logger.info(f"   Reasoning: {reasoning}")
                    
                    # Only include severe emergencies with high confidence
                    if (severity == 'severe' and 
                        confidence >= 0.7 and 
                        emerg_type in EMERGENCY_NUMBERS):
                        severe_emergencies.append({
                            'type': emerg_type,
                            'number': EMERGENCY_NUMBERS[emerg_type],
                            'severity': severity,
                            'confidence': confidence,
                            'reasoning': reasoning
                        })
                        logger.info(f"   ✅ SEVERE emergency - will call {emerg_type}")
                    elif severity in ['minor', 'moderate']:
                        logger.info(f"   ℹ️ {severity.upper()} issue - providing advice only")
                    else:
                        logger.info(f"   ⚠️ Filtered out (low confidence or invalid type)")
                
                # Return result
                if severe_emergencies:
                    logger.info(f"✅ {len(severe_emergencies)} SEVERE emergencies detected (language: {language})")
                    return {
                        'emergencies': severe_emergencies,
                        'language': language,
                        'total_count': len(severe_emergencies)
                    }
                else:
                    logger.info(f"ℹ️ No severe emergencies detected")
                    return None
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}")
                logger.error(f"Response was: {response_text}")
                return None
                
        except Exception as e:
            logger.error(f"Error in emergency detection: {e}", exc_info=True)
            return None
    
    def make_emergency_call(
        self, 
        to_number: str, 
        emergency_type: str,
        user_message: Optional[str] = None,
        language: str = 'en',
        user_phone: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Initiate a voice call to emergency services with conference bridge
        Creates a 3-way call: Bot -> User -> Emergency Service
        
        Args:
            to_number: Emergency service number to call
            emergency_type: Type of emergency (police, fire, ambulance)
            user_message: Optional user message to include in call
            language: Language of user message (en, si, ta)
            user_phone: User's phone number to call (for 3-way conference)
            
        Returns:
            Tuple of (success, message/call_sid)
        """
        if not self.client:
            logger.error("Twilio client not initialized")
            return False, "Twilio service not configured"
        
        try:
            # Import audio manager
            from .audio_manager import audio_manager
            
            # Base intro message
            intro = f"""This is an emergency call from Crime Guard Emergency Assistant. 
A user has requested {emergency_type} assistance."""
            
            # Generate audio URL if user message is provided
            audio_url = None
            if user_message and len(user_message.strip()) > 0:
                logger.info(f"✅ USER MESSAGE DETECTED: {user_message[:100]}...")
                
                # Get base URL for audio serving (use environment variable or default)
                base_url = os.getenv('BASE_URL', 'http://localhost:8000')
                
                # Check if base_url is localhost (Twilio can't access localhost)
                is_localhost = 'localhost' in base_url or '127.0.0.1' in base_url
                
                if is_localhost:
                    logger.warning(f"⚠️ BASE_URL is localhost - Twilio cannot access it. Using Twilio TTS fallback.")
                    logger.info(f"💡 To use gTTS audio, set BASE_URL in .env to a public URL (e.g., ngrok)")
                    audio_url = None  # Force fallback to Twilio TTS
                else:
                    logger.info(f"🎵 Generating gTTS audio in language: {language}")
                    
                    # Generate audio with gTTS
                    success, result = audio_manager.generate_and_upload_message(
                        user_message=user_message,
                        language=language,
                        emergency_type=emergency_type,
                        base_url=base_url
                    )
                    
                    if success:
                        audio_url = result
                        logger.info(f"✅ Audio generated successfully: {audio_url}")
                    else:
                        logger.error(f"❌ Audio generation failed: {result}")
                        # Will fallback to text-based TTS
            
            # Create TwiML
            if audio_url:
                # Use gTTS audio with <Play> tag
                logger.info(f"🎤 Using gTTS audio playback")
                twiml = f'''<Response>
    <Say voice="Polly.Aditi" language="en-IN">{intro}</Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" language="en-IN">The user's message follows:</Say>
    <Pause length="1"/>
    <Play>{audio_url}</Play>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" language="en-IN">Please assist immediately.</Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" language="en-IN">Playing message again:</Say>
    <Play>{audio_url}</Play>
    <Pause length="2"/>
    <Hangup/>
</Response>'''
            elif user_message and len(user_message.strip()) > 0:
                # Fallback: Use Twilio TTS if gTTS failed
                logger.warning(f"⚠️ Falling back to Twilio TTS")
                safe_message = user_message[:200] if len(user_message) > 200 else user_message
                safe_message = safe_message.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                
                twiml = f'''<Response>
    <Say voice="Polly.Aditi" language="en-IN">{intro}</Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" language="en-IN">The user said: {safe_message}</Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" language="en-IN">Please assist immediately.</Say>
    <Pause length="2"/>
    <Say voice="Polly.Aditi" language="en-IN">Repeating: {safe_message}</Say>
    <Pause length="2"/>
    <Hangup/>
</Response>'''
            else:
                # No user message
                logger.info(f"ℹ️ No user message provided")
                twiml = f'''<Response>
    <Say voice="Polly.Aditi" language="en-IN">{intro} Please assist immediately.</Say>
    <Pause length="2"/>
    <Hangup/>
</Response>'''
            
            logger.info(f"📞 Making emergency call to {to_number}...")
            logger.debug(f"TwiML: {twiml}")
            
            # Make the call directly to emergency number
            # The person answering the call will hear the TwiML
            call = self.client.calls.create(
                twiml=twiml,
                to=to_number,
                from_=TWILIO_PHONE_NUMBER,
                record=True,  # Record for logging purposes
                recording_status_callback=None  # Can add URL for recording notification
            )
            
            logger.info(f"✅ Emergency call initiated: SID={call.sid}")
            logger.info(f"   Type: {emergency_type}")
            logger.info(f"   To: {to_number}")
            logger.info(f"   User message: {bool(user_message)}")
            logger.info(f"   gTTS audio URL: {audio_url if audio_url else 'Not used'}")
            
            # Save emergency call record to MongoDB with multi-language support
            try:
                # Get emergency detection result for logging
                emergency_info = self.detect_emergency_intent(user_message) if user_message else {}
                confidence = emergency_info.get('confidence', 0.95) if emergency_info else 0.95
                reasoning = emergency_info.get('reasoning', f'Emergency call to {emergency_type}') if emergency_info else f'Emergency call to {emergency_type}'
                severity = emergency_info.get('severity', 'severe') if emergency_info else 'severe'
                
                save_emergency_call(
                    user_message=user_message or f"Emergency {emergency_type} call",
                    emergency_type=emergency_type,
                    phone_number=to_number,
                    call_sid=call.sid,
                    language=language,
                    confidence=confidence,
                    reasoning=reasoning,
                    severity=severity,
                    audio_url=audio_url,
                    user_phone=user_phone,
                    call_status='initiated'
                )
                logger.info(f"📊 Emergency call record saved to MongoDB")
            except Exception as db_error:
                logger.error(f"⚠️ Failed to save emergency call to MongoDB: {db_error}")
                # Don't fail the call if DB save fails
            
            return True, call.sid
            
        except Exception as e:
            logger.error(f"Failed to make emergency call: {e}", exc_info=True)
            return False, str(e)
    
    def cancel_emergency_call(self, call_sid: str) -> Tuple[bool, str]:
        """
        Cancel an ongoing emergency call
        
        Args:
            call_sid: Twilio call SID to cancel
            
        Returns:
            Tuple of (success, message)
        """
        if not self.client:
            logger.error("Twilio client not initialized")
            return False, "Twilio service not configured"
        
        try:
            # Update the call to cancel it
            call = self.client.calls(call_sid).update(status='canceled')
            
            logger.info(f"Emergency call canceled: SID={call_sid}")
            
            # Update MongoDB record
            try:
                update_call_status(call_sid, 'canceled')
                logger.info(f"📊 Call status updated to 'canceled' in MongoDB")
            except Exception as db_error:
                logger.error(f"⚠️ Failed to update call status in MongoDB: {db_error}")
            
            return True, f"Call {call_sid} canceled successfully"
            
        except Exception as e:
            logger.error(f"Failed to cancel emergency call: {e}", exc_info=True)
            return False, str(e)
    
    def get_call_status(self, call_sid: str) -> Tuple[bool, str]:
        """
        Get the status of an emergency call and update MongoDB
        
        Args:
            call_sid: Twilio call SID to check
            
        Returns:
            Tuple of (success, status)
        """
        if not self.client:
            logger.error("Twilio client not initialized")
            return False, "Twilio service not configured"
        
        try:
            call = self.client.calls(call_sid).fetch()
            
            logger.info(f"Call status for {call_sid}: {call.status}")
            
            # Update MongoDB with latest status and duration
            try:
                duration = int(call.duration) if call.duration else None
                update_call_status(call_sid, call.status, duration)
                logger.info(f"📊 Call status '{call.status}' updated in MongoDB")
            except Exception as db_error:
                logger.error(f"⚠️ Failed to update call status in MongoDB: {db_error}")
            
            return True, call.status
            
        except Exception as e:
            logger.error(f"Failed to get call status: {e}", exc_info=True)
            return False, str(e)
    
    def get_service_name(self, emergency_type: str, language: str = 'en') -> str:
        """
        Get the service name in the user's preferred language
        
        Args:
            emergency_type: Type of emergency (police, fire, ambulance)
            language: Language for the service name
            
        Returns:
            Service name in appropriate language
        """
        service_names = {
            'police': {
                'en': 'Police',
                'si': 'පොලිසිය',
                'ta': 'காவல்துறை'
            },
            'fire': {
                'en': 'Fire Department',
                'si': 'ගිනි නිවීමේ සේවාව',
                'ta': 'தீயணைப்பு துறை'
            },
            'ambulance': {
                'en': 'Ambulance',
                'si': 'ගිලන් රථ සේවාව',
                'ta': 'ஆம்புலன்ஸ்'
            }
        }
        
        return service_names.get(emergency_type, {}).get(language, service_names.get(emergency_type, {}).get('en', emergency_type))
    
    def get_emergency_response_text(self, emergency_type: str, language: str = 'en') -> str:
        """
        Get appropriate response text when emergency call is triggered
        
        Args:
            emergency_type: Type of emergency detected
            language: Language for the response
            
        Returns:
            Response message in appropriate language
        """
        responses = {
            'police': {
                'en': f"🚨 EMERGENCY CALL INITIATED 🚨\n\nI'm calling the Police (119) on your behalf right now. Please stay on the line and speak with the authorities when they answer.\n\nDirect Number: 119\nService: Sri Lanka Police",
                'si': f"🚨 හදිසි ඇමතුම ආරම්භ කර ඇත 🚨\n\nමම දැන් ඔබ වෙනුවෙන් පොලිසියට (119) ඇමතුම් කරමින් සිටිමි. කරුණාකර රැඳී සිටින්න.\n\nසෘජු අංකය: 119\nසේවාව: ශ්‍රී ලංකා පොලිසිය",
                'ta': f"🚨 அவசர அழைப்பு தொடங்கப்பட்டது 🚨\n\nநான் இப்போது உங்கள் சார்பாக காவல்துறையை (119) அழைக்கிறேன். தயவுசெய்து காத்திருங்கள்.\n\nநேரடி எண்: 119\nசேவை: இலங்கை காவல்துறை"
            },
            'fire': {
                'en': f"🚨 EMERGENCY CALL INITIATED 🚨\n\nI'm calling the Fire & Rescue Service (110) on your behalf right now. Please evacuate to safety immediately if possible.\n\nDirect Number: 110\nService: Sri Lanka Fire & Rescue",
                'si': f"🚨 හදිසි ඇමතුම ආරම්භ කර ඇත 🚨\n\nමම දැන් ඔබ වෙනුවෙන් ගිනි නිවීමේ සේවාවට (110) ඇමතුම් කරමින් සිටිමි. හැකි නම් වහාම ආරක්ෂිත ස්ථානයකට යන්න.\n\nසෘජු අංකය: 110\nසේවාව: ශ්‍රී ලංකා ගිනි නිවීමේ සේවාව",
                'ta': f"🚨 அவசர அழைப்பு தொடங்கப்பட்டது 🚨\n\nநான் இப்போது உங்கள் சார்பாக தீயணைப்பு சேவையை (110) அழைக்கிறேன். உடனடியாக பாதுகாப்பான இடத்திற்கு செல்லவும்.\n\nநேரடி எண்: 110\nசேவை: இலங்கை தீயணைப்பு சேவை"
            },
            'ambulance': {
                'en': f"🚨 EMERGENCY CALL INITIATED 🚨\n\nI'm calling the Ambulance Service - Suwa Seriya (1990) on your behalf right now. Medical help is on the way.\n\nDirect Number: 1990\nService: Suwa Seriya Ambulance",
                'si': f"🚨 හදිසි ඇමතුම ආරම්භ කර ඇත 🚨\n\nමම දැන් ඔබ වෙනුවෙන් ගිලන් රථ සේවාව - සුව සැරිය (1990) ඇමතුම් කරමින් සිටිමි. වෛද්‍ය ආධාර එළඹෙමින් පවතී.\n\nසෘජු අංකය: 1990\nසේවාව: සුව සැරිය ගිලන් රථ සේවාව",
                'ta': f"🚨 அவசர அழைப்பு தொடங்கப்பட்டது 🚨\n\nநான் இப்போது உங்கள் சார்பாக ஆம்புலன்ஸ் சேவை - சுவ செரியாவை (1990) அழைக்கிறேன். மருத்துவ உதவி வருகிறது.\n\nநேரடி எண்: 1990\nசேவை: சுவ செரியா ஆம்புலன்ஸ்"
            }
        }
        
        return responses.get(emergency_type, {}).get(language, responses.get(emergency_type, {}).get('en', ''))


# Singleton instance
twilio_service = TwilioCallService()
