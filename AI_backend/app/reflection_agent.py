"""
Reflection & Recovery Agent - Autonomous Emergency Call Monitoring and Recovery
=====================================================================
This agent autonomously ensures emergency calls succeed through:
1. Continuous call status monitoring
2. LLM-based failure analysis and reasoning
3. Adaptive retry strategies (same number vs alternative services)
4. Pre-configured emergency service backup numbers (Twilio trail compatible)

Agentic Characteristics:
- ✅ Autonomy: Makes all decisions independently without user intervention
- ✅ Goal-Oriented: Pursues single goal "Ensure emergency services are notified"
- ✅ Reasoning: Uses GPT-4o-mini for intelligent failure analysis
- ✅ Reactivity: Responds to call status changes in real-time
- ✅ Persistence: Retries up to 4 times with adaptive strategies
- ✅ Self-Monitoring: Tracks own progress and success rates
"""

import os
import time
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI
import json
from twilio.rest import Client

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize OpenAI client for LLM reasoning
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize Twilio client
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


class ReflectionRecoveryAgent:
    """
    Autonomous agent that ensures emergency calls succeed through intelligent monitoring and recovery
    """
    
    # Pre-verified emergency service numbers (Twilio trail compatible)
    # All numbers must be verified in Twilio Console before use
    EMERGENCY_CONTACTS = {
        "police": [
            {
                "number": os.getenv('EMERGENCY_POLICE_PRIMARY', '+94119'),
                "name": "Police Emergency Hotline",
                "priority": 1,
                "description": "Primary police emergency line (119)"
            },
            {
                "number": os.getenv('EMERGENCY_POLICE_ACCIDENT', '+94118'),
                "name": "Accident Service",
                "priority": 2,
                "description": "Also handles police emergencies (118)"
            },
            {
                "number": os.getenv('EMERGENCY_POLICE_COMMAND', '+94112433333'),
                "name": "Colombo Police Command Center",
                "priority": 3,
                "description": "Direct line to central command (011-2433333)"
            }
        ],
        "ambulance": [
            {
                "number": os.getenv('EMERGENCY_AMBULANCE_PRIMARY', '+941990'),
                "name": "Suwa Sariya Ambulance",
                "priority": 1,
                "description": "Primary ambulance service (1990)"
            },
            {
                "number": os.getenv('EMERGENCY_AMBULANCE_SERVICE', '+94110'),
                "name": "Government Ambulance Service",
                "priority": 2,
                "description": "Alternative ambulance service (110)"
            },
            {
                "number": os.getenv('EMERGENCY_AMBULANCE_HOSPITAL', '+94112691111'),
                "name": "National Hospital Colombo",
                "priority": 3,
                "description": "Direct hospital emergency line (011-2691111)"
            }
        ],
        "fire": [
            {
                "number": os.getenv('EMERGENCY_FIRE_PRIMARY', '+94110'),
                "name": "Fire & Rescue Service",
                "priority": 1,
                "description": "Primary fire emergency line (110)"
            },
            {
                "number": os.getenv('EMERGENCY_FIRE_COLOMBO', '+94112422222'),
                "name": "Colombo Fire Department",
                "priority": 2,
                "description": "Direct Colombo fire station (011-2422222)"
            }
        ]
    }
    
    def __init__(self):
        """Initialize the Reflection & Recovery Agent"""
        self.max_attempts = 4  # Maximum retry attempts
        self.wait_time_seconds = 5  # Fixed 5-second wait between attempts
        self.monitoring_interval = 5  # Check call status every 5 seconds
        logger.info("Reflection & Recovery Agent initialized")
    
    def monitor_and_recover(
        self,
        initial_call_sid: str,
        emergency_type: str,
        user_message: str,
        language: str = "en"
    ) -> Dict:
        """
        Autonomously monitor emergency call and recover from failures
        
        This is the main agentic loop that pursues the goal: "Ensure emergency services are notified"
        
        Args:
            initial_call_sid: Twilio Call SID from initial attempt
            emergency_type: Type of emergency (police/ambulance/fire)
            user_message: Original user emergency message
            language: User's language (en/si/ta)
        
        Returns:
            Dict with success status, attempts made, and recovery details
        """
        logger.info(f"🤖 Reflection Agent: Starting autonomous monitoring for call {initial_call_sid}")
        logger.info(f"   Goal: Ensure {emergency_type} services are notified")
        
        # Get available contacts for this emergency type
        contacts = self.EMERGENCY_CONTACTS.get(emergency_type, [])
        if not contacts:
            logger.error(f"No emergency contacts configured for type: {emergency_type}")
            return {
                "success": False,
                "error": "No emergency contacts available",
                "attempts": 0
            }
        
        current_call_sid = initial_call_sid
        current_contact_index = 0
        attempt = 1
        
        # Main agentic loop - autonomous goal pursuit
        while attempt <= self.max_attempts:
            logger.info(f"🔍 Attempt {attempt}/{self.max_attempts}: Monitoring call {current_call_sid}")
            
            # AUTONOMOUS ACTION 1: Self-Monitor call status
            call_status = self._check_call_status(current_call_sid)
            current_contact = contacts[current_contact_index]
            
            logger.info(f"   Status: {call_status} | Contact: {current_contact['name']}")
            
            # SUCCESS - Goal achieved!
            if call_status == "completed":
                logger.info(f"✅ SUCCESS! Emergency call completed after {attempt} attempts")
                return {
                    "success": True,
                    "attempts": attempt,
                    "final_contact": current_contact,
                    "call_sid": current_call_sid,
                    "message": f"Emergency services successfully notified via {current_contact['name']}"
                }
            
            # IN PROGRESS - Continue monitoring
            elif call_status in ["queued", "ringing", "in-progress"]:
                logger.info(f"   Call in progress, waiting {self.monitoring_interval}s before next check...")
                time.sleep(self.monitoring_interval)
                continue
            
            # FAILURE - Autonomous recovery needed
            elif call_status in ["failed", "busy", "no-answer", "canceled"]:
                logger.warning(f"⚠️  Call failed with status: {call_status}")
                
                # AUTONOMOUS ACTION 2: LLM-based failure analysis and decision making
                recovery_decision = self._analyze_failure_and_decide(
                    call_status=call_status,
                    emergency_type=emergency_type,
                    attempt=attempt,
                    current_contact=current_contact,
                    remaining_contacts=contacts[current_contact_index + 1:],
                    user_message=user_message
                )
                
                logger.info(f"🧠 LLM Decision: {recovery_decision.get('reasoning', 'No reasoning provided')}")
                
                # Should we give up?
                if not recovery_decision.get("should_retry", False):
                    logger.error(f"❌ Agent decided to stop after {attempt} attempts")
                    return {
                        "success": False,
                        "attempts": attempt,
                        "reason": recovery_decision.get("reasoning"),
                        "message": "Agent exhausted all recovery strategies"
                    }
                
                # AUTONOMOUS ACTION 3: Decide retry strategy
                if recovery_decision.get("try_next_contact", False):
                    # Move to next backup contact
                    current_contact_index += 1
                    if current_contact_index >= len(contacts):
                        logger.error(f"❌ No more backup contacts available")
                        return {
                            "success": False,
                            "attempts": attempt,
                            "reason": "All emergency contacts exhausted",
                            "message": f"Tried all {len(contacts)} available contacts"
                        }
                    
                    current_contact = contacts[current_contact_index]
                    logger.info(f"🔄 Switching to backup: {current_contact['name']}")
                else:
                    # Retry same contact (might be temporary issue)
                    logger.info(f"🔄 Retrying same contact: {current_contact['name']}")
                
                # Wait before retry (fixed 5 seconds)
                logger.info(f"⏳ Waiting {self.wait_time_seconds} seconds before retry...")
                time.sleep(self.wait_time_seconds)
                
                # AUTONOMOUS ACTION 4: Execute retry
                current_call_sid = self._retry_emergency_call(
                    to_number=current_contact["number"],
                    emergency_type=emergency_type,
                    user_message=user_message,
                    language=language,
                    contact_name=current_contact["name"]
                )
                
                if not current_call_sid:
                    logger.error("❌ Failed to initiate retry call")
                    return {
                        "success": False,
                        "attempts": attempt,
                        "reason": "Retry call initiation failed",
                        "message": "Could not create new Twilio call"
                    }
                
                attempt += 1
            
            else:
                # Unknown status
                logger.warning(f"⚠️  Unknown call status: {call_status}, waiting...")
                time.sleep(self.monitoring_interval)
        
        # Max attempts reached
        logger.error(f"❌ Max attempts ({self.max_attempts}) reached without success")
        return {
            "success": False,
            "attempts": attempt - 1,
            "reason": "Maximum retry attempts exceeded",
            "message": f"Failed after {self.max_attempts} attempts across {current_contact_index + 1} contacts"
        }
    
    def _check_call_status(self, call_sid: str) -> str:
        """
        Autonomous monitoring: Check current status of Twilio call
        
        Args:
            call_sid: Twilio Call SID
        
        Returns:
            Call status string (completed/failed/busy/no-answer/in-progress/etc)
        """
        try:
            call = twilio_client.calls(call_sid).fetch()
            return call.status
        except Exception as e:
            logger.error(f"Error checking call status: {e}")
            return "failed"
    
    def _analyze_failure_and_decide(
        self,
        call_status: str,
        emergency_type: str,
        attempt: int,
        current_contact: Dict,
        remaining_contacts: List[Dict],
        user_message: str
    ) -> Dict:
        """
        LLM-based reasoning: Analyze why call failed and decide recovery strategy
        
        This is the "brain" of the agent - uses GPT-4o-mini to autonomously reason about:
        1. Why did the call fail?
        2. Should we retry?
        3. Retry same number or try backup contact?
        4. What's the probability of success?
        
        Args:
            call_status: Failed call status
            emergency_type: Type of emergency
            attempt: Current attempt number
            current_contact: Contact that just failed
            remaining_contacts: Backup contacts available
            user_message: Original emergency message
        
        Returns:
            Dict with retry decision and reasoning
        """
        # Format remaining contacts for LLM
        remaining_list = [f"{c['name']} ({c['description']})" for c in remaining_contacts]
        remaining_text = "\n".join(remaining_list) if remaining_list else "None (last contact)"
        
        prompt = f"""You are an autonomous Reflection & Recovery Agent monitoring an emergency call.

SITUATION:
- Emergency Type: {emergency_type}
- User Message: "{user_message}"
- Current Attempt: {attempt}/{self.max_attempts}
- Failed Contact: {current_contact['name']} ({current_contact['description']})
- Failure Status: {call_status}
- Remaining Backup Contacts:
{remaining_text}

FAILURE STATUS MEANINGS:
- "failed": Technical error (network/system issue)
- "busy": Number is busy/engaged
- "no-answer": Rang but nobody picked up
- "canceled": Call was canceled

YOUR TASK:
Analyze this failure and decide the optimal recovery strategy. Consider:
1. Is this emergency life-threatening? (affects retry priority)
2. Was failure likely temporary (network glitch) or persistent (line busy)?
3. Should we retry SAME contact (if temporary) or NEXT contact (if persistent)?
4. What's the probability of success if we retry?
5. Should we continue trying or give up?

RESPONSE FORMAT (JSON):
{{
    "should_retry": true/false,  ← SET TRUE TO CONTINUE RECOVERY (same OR next contact), FALSE TO STOP ENTIRELY
    "try_next_contact": true/false,  ← true = skip to next contact, false = retry same contact
    "reasoning": "Brief explanation of your decision",
    "success_probability": 0.0-1.0
}}

⚠️ CRITICAL RULES:
- Set should_retry=true if you want to CONTINUE trying ANY contact (same or next)
- Set should_retry=false ONLY if you want to GIVE UP completely (e.g., exhausted all options)
- Set try_next_contact=true if current contact is persistently failing (busy/failed)
- Set try_next_contact=false if failure was likely temporary (retry same contact)

EXAMPLES:
- If "no-answer" on attempt 1 → should_retry=true, try_next_contact=false (retry same)
- If "busy" on attempt 1 → should_retry=true, try_next_contact=true (skip to next contact)
- If "failed" → should_retry=true, try_next_contact=true (technical issue, try next)
- If attempt 4 and all failed → should_retry=false, try_next_contact=false (give up)

Analyze and decide:"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an autonomous emergency call recovery agent. Make intelligent decisions to ensure emergency services are notified."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent decisions
                max_tokens=200
            )
            
            decision_text = response.choices[0].message.content.strip()
            
            # Log raw LLM response for debugging
            logger.debug(f"🧠 Raw LLM Response: {decision_text[:500]}")
            
            # Parse JSON response
            # Handle markdown code blocks if present
            if "```json" in decision_text:
                decision_text = decision_text.split("```json")[1].split("```")[0].strip()
            elif "```" in decision_text:
                decision_text = decision_text.split("```")[1].split("```")[0].strip()
            
            decision = json.loads(decision_text)
            
            # Log the full decision for debugging
            logger.info(f"🧠 LLM Analysis: {decision.get('reasoning', 'No reasoning')}")
            logger.info(f"🧠 LLM Decision Details: should_retry={decision.get('should_retry')}, try_next_contact={decision.get('try_next_contact')}, success_prob={decision.get('success_probability')}")
            return decision
            
        except Exception as e:
            logger.error(f"Error in LLM failure analysis: {e}")
            # Fallback: Simple rule-based decision
            return {
                "should_retry": attempt < self.max_attempts,
                "try_next_contact": attempt > 1,  # Try backup after first failure
                "reasoning": f"LLM unavailable, using fallback logic (attempt {attempt})",
                "success_probability": 0.5
            }
    
    def _retry_emergency_call(
        self,
        to_number: str,
        emergency_type: str,
        user_message: str,
        language: str,
        contact_name: str
    ) -> Optional[str]:
        """
        Autonomous action: Execute retry call to emergency services
        
        Args:
            to_number: Emergency service number to call
            emergency_type: Type of emergency
            user_message: Original emergency message
            language: User's language
            contact_name: Name of contact being called
        
        Returns:
            New Call SID or None if failed
        """
        try:
            logger.info(f"📞 Initiating retry call to {contact_name} ({to_number})")
            
            # Import twilio_service to create call
            from app.twilio_service import twilio_service
            
            # Use existing make_emergency_call method (returns tuple: success, call_info)
            success, call_info = twilio_service.make_emergency_call(
                to_number=to_number,
                emergency_type=emergency_type,
                user_message=user_message,
                language=language
            )
            
            if success:
                new_call_sid = call_info  # call_info is call_sid when success=True
                logger.info(f"✅ Retry call initiated: {new_call_sid}")
                return new_call_sid
            else:
                error_msg = call_info  # call_info is error message when success=False
                logger.error(f"❌ Retry call failed: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"Error initiating retry call: {e}")
            return None


# Global singleton instance
reflection_agent = ReflectionRecoveryAgent()
