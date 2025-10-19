"""
Twilio Voice Call Service for Emergency Situations
Detects emergency keywords and initiates voice calls to appropriate authorities
"""
import os
import logging
from typing import Dict, Optional, Tuple
from twilio.rest import Client
from dotenv import load_dotenv
import re

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

# Emergency Keywords - Multi-language support
EMERGENCY_KEYWORDS = {
    'police': {
        'en': [
            r'\bcall\s+(the\s+)?police\b',           # "call police" or "call the police"
            r'\bpolice\b.*\bcall\b',                 # "police" followed by "call"
            r'\bcall.*police\b',                     # "call" followed by "police" (catches "call help police")
            r'\bdial\s+119\b',                       # "dial 119"
            r'\bcontact\s+(the\s+)?police\b',        # "contact police" or "contact the police"
            r'\breport\s+(to\s+)?crime\b',           # "report crime"
            r'\bemergency\s+police\b',               # "emergency police"
            r'\bneed\s+police\b',                    # "need police"
            r'\bhelp.*police\b',                     # "help police" or "help me call police"
            r'\bpolice.*help\b',                     # "police help"
            r'\bpolice.*urgent\b',                   # "police urgent"
            r'\bpolice.*emergency\b',                # "police emergency"
        ],
        'si': [
            r'පොලිස්',                              # "police"
            r'පොලිසියට',                            # "to police"
            r'පොලිසිය',                             # "the police"
            r'පොලීස්',                              # alternate spelling
            r'119',                                  # emergency number
            r'කතා\s*කරන්න.*පොලිස්',                 # "call police" (any order)
            r'පොලිස්.*කතා\s*කරන්න',                # "police call"
            r'අමතන්න.*පොලිස්',                     # "contact police"
            r'පොලිස්.*අමතන්න',                     # "police contact"
            r'උදව්.*පොලිස්',                        # "help police"
            r'පොලිස්.*උදව්',                        # "police help"
            r'හදිසි.*පොලිස්',                       # "emergency police"
            r'පොලිස්.*හදිසි',                       # "police emergency"
        ],
        'ta': [
            r'காவல்துறை',                           # "police department"
            r'காவல்துறையை',                        # "to police department"
            r'போலீஸ்',                              # "police"
            r'போலீஸை',                              # "to police"
            r'119',                                  # emergency number
            r'அழைக்க.*காவல்',                      # "call police" (any order)
            r'காவல்.*அழைக்க',                      # "police call"
            r'தொடர்பு.*காவல்',                     # "contact police"
            r'உதவி.*காவல்',                        # "help police"
            r'காவல்.*உதவி',                        # "police help"
            r'அவசர.*காவல்',                        # "emergency police"
        ]
    },
    'fire': {
        'en': [
            r'\bcall\s+(the\s+)?fire\b',             # "call fire" or "call the fire"
            r'\bfire\s+truck\b',                     # "fire truck"
            r'\bfire\s+department\b',                # "fire department"
            r'\bfire\s+brigade\b',                   # "fire brigade"
            r'\bfire.*emergency\b',                  # "fire emergency"
            r'\bdial\s+110\b',                       # "dial 110"
            r'\bfire\s+service\b',                   # "fire service"
            r'\bcall.*fire\b',                       # "call help fire" or "call the fire"
            r'\bneed.*fire\b',                       # "need fire department"
            r'\bhelp.*fire\b',                       # "help fire"
            r'\bfire.*help\b',                       # "fire help"
            r'\bfire.*urgent\b',                     # "fire urgent"
        ],
        'si': [
            r'ගිනි',                                # "fire"
            r'ගින්න',                               # "fire" (colloquial)
            r'ගිනි\s+නිවීම',                        # "fire extinguishing"
            r'ගිනි\s+නිවන',                         # "fire fighting"
            r'ගිනි\s+හමුදාව',                       # "fire brigade"
            r'ගිනි.*සේවාව',                        # "fire service"
            r'110',                                  # emergency number
            r'කතා\s*කරන්න.*ගිනි',                  # "call fire"
            r'ගිනි.*කතා\s*කරන්න',                  # "fire call"
            r'අමතන්න.*ගිනි',                      # "contact fire"
            r'ගිනි.*අමතන්න',                       # "fire contact"
            r'උදව්.*ගිනි',                         # "help fire"
            r'ගිනි.*උදව්',                         # "fire help"
            r'හදිසි.*ගිනි',                        # "emergency fire"
            r'ගිනි.*හදිසි',                        # "fire emergency"
        ],
        'ta': [
            r'தீ',                                   # "fire"
            r'தீயணைப்பு',                           # "fire fighting"
            r'தீயணைப்பு\s+துறை',                   # "fire department"
            r'தீயணைப்பு\s+சேவை',                   # "fire service"
            r'110',                                  # emergency number
            r'அழைக்க.*தீ',                         # "call fire"
            r'தீ.*அழைக்க',                         # "fire call"
            r'தொடர்பு.*தீ',                        # "contact fire"
            r'உதவி.*தீ',                           # "help fire"
            r'தீ.*உதவி',                           # "fire help"
            r'அவசர.*தீ',                           # "emergency fire"
        ]
    },
    'ambulance': {
        'en': [
            r'\bcall\s+(the\s+|an\s+)?ambulance\b',  # "call ambulance" or "call the ambulance" or "call an ambulance"
            r'\bambulance\b.*\bcall\b',              # "ambulance" followed by "call"
            r'\bcall.*ambulance\b',                  # "call" followed by "ambulance"
            r'\bmedical\s+emergency\b',              # "medical emergency"
            r'\bdial\s+1990\b',                      # "dial 1990"
            r'\bsuwa\s+seriya\b',                    # "suwa seriya"
            r'\bemergency\s+medical\b',              # "emergency medical"
            r'\bhealth\s+emergency\b',               # "health emergency"
            r'\bneed.*ambulance\b',                  # "need ambulance"
            r'\bhelp.*ambulance\b',                  # "help ambulance"
            r'\bambulance.*help\b',                  # "ambulance help"
            r'\bambulance.*urgent\b',                # "ambulance urgent"
            r'\bmedical.*help\b',                    # "medical help"
        ],
        'si': [
            r'ගිලන්\s*රථ',                         # "ambulance"
            r'ගිලන්රථය',                           # "the ambulance"
            r'ඇම්බියුලන්ස්',                        # "ambulance" (English word)
            r'සුව\s+සැරිය',                         # "Suwa Seriya"
            r'සුව\s*සැරිය',                         # "Suwa Seriya" (no space)
            r'1990',                                 # emergency number
            r'කතා\s*කරන්න.*ගිලන්',                 # "call ambulance"
            r'ගිලන්.*කතා\s*කරන්න',                 # "ambulance call"
            r'කතා\s*කරන්න.*ඇම්බියුලන්ස්',          # "call ambulance" (English word)
            r'අමතන්න.*ගිලන්',                     # "contact ambulance"
            r'ගිලන්.*අමතන්න',                      # "ambulance contact"
            r'උදව්.*ගිලන්',                        # "help ambulance"
            r'ගිලන්.*උදව්',                        # "ambulance help"
            r'වෛද්‍ය.*උදව්',                       # "medical help"
            r'හදිසි.*වෛද්‍ය',                      # "emergency medical"
            r'අසනීප',                              # "sick/unwell"
        ],
        'ta': [
            r'ஆம்புலன்ஸ்',                          # "ambulance"
            r'ஆம்புலன்ஸை',                         # "to ambulance"
            r'மருத்துவ',                            # "medical"
            r'அவசர\s+மருத்துவம்',                   # "emergency medical"
            r'சுவ\s+செரியா',                        # "Suwa Seriya"
            r'1990',                                 # emergency number
            r'அழைக்க.*ஆம்புலன்ஸ்',                # "call ambulance"
            r'ஆம்புலன்ஸ்.*அழைக்க',                # "ambulance call"
            r'தொடர்பு.*ஆம்புலன்ஸ்',               # "contact ambulance"
            r'உதவி.*ஆம்புலன்ஸ்',                  # "help ambulance"
            r'ஆம்புலன்ஸ்.*உதவி',                  # "ambulance help"
            r'மருத்துவ.*உதவி',                     # "medical help"
            r'அவசர.*மருத்துவ',                     # "emergency medical"
            r'நோய்',                                 # "sick/illness"
        ]
    }
}


class TwilioCallService:
    """Service to handle emergency voice calls via Twilio"""
    
    def __init__(self):
        """Initialize Twilio client"""
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
    
    def detect_emergency_intent(self, message: str) -> Optional[Dict[str, str]]:
        """
        Detect if the message contains emergency call keywords
        
        Args:
            message: User's message to analyze
            
        Returns:
            Dict with emergency type and number if detected, None otherwise
        """
        message_lower = message.lower()
        
        # Check each emergency type
        for emergency_type, languages in EMERGENCY_KEYWORDS.items():
            for lang, patterns in languages.items():
                for pattern in patterns:
                    if re.search(pattern, message, re.IGNORECASE):
                        logger.info(f"Emergency detected: {emergency_type} (language: {lang})")
                        return {
                            'type': emergency_type,
                            'number': EMERGENCY_NUMBERS[emergency_type],
                            'language': lang,
                            'pattern_matched': pattern
                        }
        
        return None
    
    def make_emergency_call(self, to_number: str, emergency_type: str) -> Tuple[bool, str]:
        """
        Initiate a voice call to emergency services
        
        Args:
            to_number: Emergency service number to call
            emergency_type: Type of emergency (police, fire, ambulance)
            
        Returns:
            Tuple of (success, message/call_sid)
        """
        if not self.client:
            logger.error("Twilio client not initialized")
            return False, "Twilio service not configured"
        
        try:
            # Create TwiML for the call
            twiml = f'''
            <Response>
                <Say voice="Polly.Aditi" language="en-IN">
                    This is an emergency call from Crime Guard Chat Bot. 
                    A user has requested {emergency_type} assistance. 
                    Please standby for connection.
                </Say>
                <Pause length="2"/>
            </Response>
            '''
            
            # Make the call
            call = self.client.calls.create(
                twiml=twiml,
                to=to_number,
                from_=TWILIO_PHONE_NUMBER
            )
            
            logger.info(f"Emergency call initiated: SID={call.sid}, Type={emergency_type}, To={to_number}")
            return True, call.sid
            
        except Exception as e:
            logger.error(f"Failed to make emergency call: {e}", exc_info=True)
            return False, str(e)
    
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
