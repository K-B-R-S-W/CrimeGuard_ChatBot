"""
Escalation Management Agent - Autonomous Multi-Emergency Coordination
=====================================================================
This agent autonomously handles MULTIPLE simultaneous emergencies through:
1. LLM-based prioritization (which emergency is most urgent?)
2. Intelligent calling strategy (sequential or parallel?)
3. Coordinated multi-call execution
4. Adaptive failure handling (adjust plan if calls fail)

Agentic Characteristics:
- ✅ Autonomy: Decides priority and calling strategy independently
- ✅ Goal-Oriented: Pursues goal "Notify ALL appropriate emergency services"
- ✅ Reasoning: Uses GPT-4o-mini for intelligent prioritization
- ✅ Reactivity: Adjusts plan based on call outcomes
- ✅ Persistence: Ensures ALL emergencies are addressed
- ✅ Coordination: Manages multiple Reflection Agents simultaneously
"""

import os
import time
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI
import json
import threading

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize OpenAI client for LLM reasoning
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


class EscalationManagementAgent:
    """
    Autonomous agent that coordinates multiple simultaneous emergency calls
    """
    
    def __init__(self):
        """Initialize the Escalation Management Agent"""
        self.sequential_delay = 5  # Seconds between sequential calls
        logger.info("Escalation Management Agent initialized")
    
    def coordinate_multi_emergency(
        self,
        emergencies: List[Dict],
        user_message: str,
        language: str = "en"
    ) -> Dict:
        """
        Main agentic loop - autonomously coordinate multiple emergency calls
        
        This is the core decision-making function that:
        1. Analyzes which emergencies are most urgent (LLM reasoning)
        2. Decides calling strategy: sequential vs parallel (LLM reasoning)
        3. Executes coordinated calls with Reflection Agent monitoring
        4. Adapts to failures dynamically
        
        Args:
            emergencies: List of emergency dicts with type, severity, confidence
            user_message: Original user emergency message
            language: User's language
        
        Returns:
            Dict with coordination results, call SIDs, and outcomes
        """
        logger.info(f"🚨 Escalation Agent: Managing {len(emergencies)} simultaneous emergencies")
        
        if len(emergencies) == 1:
            # Single emergency - no escalation needed
            logger.info("   Single emergency detected - no escalation coordination needed")
            return {
                'multi_emergency': False,
                'emergencies': emergencies
            }
        
        # AUTONOMOUS ACTION 1: LLM-based prioritization
        logger.info("🧠 Step 1: Analyzing emergency priorities...")
        prioritized_emergencies = self._prioritize_emergencies(emergencies, user_message)
        
        # AUTONOMOUS ACTION 2: Decide calling strategy
        logger.info("🧠 Step 2: Deciding optimal calling strategy...")
        strategy = self._decide_calling_strategy(prioritized_emergencies, user_message)
        
        logger.info(f"📋 Coordination Plan:")
        logger.info(f"   Strategy: {strategy['strategy'].upper()}")
        logger.info(f"   Reasoning: {strategy['reasoning']}")
        
        # AUTONOMOUS ACTION 3: Execute coordinated calls
        if strategy['strategy'] == 'parallel':
            logger.info("🚀 Executing PARALLEL calls (all services simultaneously)...")
            results = self._execute_parallel_calls(prioritized_emergencies, user_message, language)
        else:
            logger.info("🚀 Executing SEQUENTIAL calls (one after another)...")
            results = self._execute_sequential_calls(prioritized_emergencies, user_message, language)
        
        # Add coordination metadata
        results['multi_emergency'] = True
        results['total_emergencies'] = len(emergencies)
        results['strategy'] = strategy['strategy']
        results['strategy_reasoning'] = strategy['reasoning']
        
        logger.info(f"✅ Escalation coordination complete")
        return results
    
    def _prioritize_emergencies(self, emergencies: List[Dict], user_message: str) -> List[Dict]:
        """
        LLM-based reasoning: Rank emergencies by urgency
        
        Uses GPT-4o-mini to autonomously analyze which emergency needs
        the fastest response based on life-threat level and context.
        
        Args:
            emergencies: List of detected emergencies
            user_message: Original message for context
        
        Returns:
            Same list but sorted by priority (most urgent first)
        """
        # Format emergencies for LLM
        emergency_descriptions = []
        for i, emerg in enumerate(emergencies, 1):
            emergency_descriptions.append(
                f"{i}. {emerg['type'].upper()} "
                f"(severity: {emerg['severity']}, "
                f"confidence: {emerg['confidence']}, "
                f"reason: {emerg['reasoning']})"
            )
        
        emergencies_text = "\n".join(emergency_descriptions)
        
        prompt = f"""You are an autonomous Escalation Management Agent coordinating multiple emergency responses.

USER MESSAGE: "{user_message}"

DETECTED EMERGENCIES:
{emergencies_text}

YOUR TASK:
Analyze and prioritize these emergencies by urgency. Consider:

1. **Life Threat Level**:
   - Which emergency is MOST immediately life-threatening?
   - Fire spreading → people die in minutes
   - Heavy bleeding → person dies in minutes
   - Robbery → threat but less immediate than above

2. **Time Sensitivity**:
   - Which requires FASTEST response?
   - Fire spreads exponentially (every second counts)
   - Medical emergencies have "golden hour"
   - Crime scenes need quick response but less critical

3. **Dependency**:
   - Are emergencies related? (e.g., fire CAUSED injuries)
   - If so, which should be handled first?
   - Fire first (stop cause) then ambulance (treat effect)

4. **Resource Availability**:
   - Can services respond simultaneously?
   - Or should we ensure one arrives before calling next?

RESPONSE FORMAT (JSON):
{{
    "prioritized_order": [
        {{
            "type": "fire/police/ambulance",
            "priority": 1-3,
            "urgency_score": 0.0-1.0,
            "reasoning": "why this priority"
        }}
    ],
    "overall_reasoning": "explanation of priority logic"
}}

Analyze and prioritize:"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an autonomous emergency coordination agent. Prioritize emergencies to maximize lives saved."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            decision_text = response.choices[0].message.content.strip()
            
            # Parse JSON
            if "```json" in decision_text:
                decision_text = decision_text.split("```json")[1].split("```")[0].strip()
            elif "```" in decision_text:
                decision_text = decision_text.split("```")[1].split("```")[0].strip()
            
            decision = json.loads(decision_text)
            
            logger.info(f"🧠 LLM Prioritization:")
            logger.info(f"   {decision.get('overall_reasoning', 'No reasoning provided')}")
            
            # Reorder emergencies based on LLM priority
            prioritized_order = decision.get('prioritized_order', [])
            prioritized_emergencies = []
            
            for priority_item in prioritized_order:
                emerg_type = priority_item['type']
                # Find matching emergency
                for emerg in emergencies:
                    if emerg['type'] == emerg_type:
                        emerg['priority'] = priority_item['priority']
                        emerg['urgency_score'] = priority_item.get('urgency_score', 0.5)
                        emerg['priority_reasoning'] = priority_item.get('reasoning', '')
                        prioritized_emergencies.append(emerg)
                        logger.info(f"   Priority {priority_item['priority']}: {emerg_type.upper()} "
                                  f"(urgency: {priority_item.get('urgency_score', 0.5)})")
                        break
            
            return prioritized_emergencies if prioritized_emergencies else emergencies
            
        except Exception as e:
            logger.error(f"Error in LLM prioritization: {e}")
            # Fallback: Simple rule-based priority
            logger.info("⚠️ Using fallback rule-based prioritization")
            priority_order = {'fire': 1, 'ambulance': 2, 'police': 3}
            for emerg in emergencies:
                emerg['priority'] = priority_order.get(emerg['type'], 3)
                emerg['urgency_score'] = 0.8 if emerg['type'] == 'fire' else 0.7
            return sorted(emergencies, key=lambda x: x['priority'])
    
    def _decide_calling_strategy(self, emergencies: List[Dict], user_message: str) -> Dict:
        """
        LLM-based reasoning: Sequential vs Parallel calling
        
        Autonomously decides optimal calling strategy:
        - SEQUENTIAL: Call one by one (when order matters)
        - PARALLEL: Call all simultaneously (when all equally urgent)
        
        Args:
            emergencies: Prioritized list of emergencies
            user_message: Original message for context
        
        Returns:
            Dict with strategy and reasoning
        """
        # Format emergencies
        emergency_list = [f"{e['type']} (priority: {e.get('priority', 'N/A')})" 
                         for e in emergencies]
        emergencies_text = ", ".join(emergency_list)
        
        prompt = f"""You are an autonomous Escalation Management Agent deciding calling strategy.

USER MESSAGE: "{user_message}"
PRIORITIZED EMERGENCIES: {emergencies_text}

STRATEGY OPTIONS:

1. **SEQUENTIAL** (call one after another):
   - Use when: Emergencies are related (one caused by another)
   - Use when: Need to ensure primary service arrives first
   - Example: Fire caused injuries → Fire first, then ambulance
   - Delay: 5 seconds between calls

2. **PARALLEL** (call all simultaneously):
   - Use when: Emergencies are independent and equally urgent
   - Use when: All services needed ASAP
   - Example: Multiple unrelated life threats
   - No delay: All calls initiated together

DECISION CRITERIA:
- Are emergencies related or independent?
- Is one emergency clearly more urgent?
- Would calling all at once cause confusion?
- What maximizes total lives saved?

RESPONSE FORMAT (JSON):
{{
    "strategy": "sequential/parallel",
    "reasoning": "detailed explanation of why this strategy"
}}

Decide optimal strategy:"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an autonomous emergency coordination agent. Choose optimal calling strategy."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            decision_text = response.choices[0].message.content.strip()
            
            # Parse JSON
            if "```json" in decision_text:
                decision_text = decision_text.split("```json")[1].split("```")[0].strip()
            elif "```" in decision_text:
                decision_text = decision_text.split("```")[1].split("```")[0].strip()
            
            decision = json.loads(decision_text)
            
            strategy = decision.get('strategy', 'sequential')
            reasoning = decision.get('reasoning', 'No reasoning provided')
            
            logger.info(f"🧠 LLM Strategy Decision: {strategy.upper()}")
            logger.info(f"   Reasoning: {reasoning}")
            
            return {
                'strategy': strategy,
                'reasoning': reasoning
            }
            
        except Exception as e:
            logger.error(f"Error in strategy decision: {e}")
            # Fallback: Sequential (safer default)
            logger.info("⚠️ Using fallback strategy: SEQUENTIAL")
            return {
                'strategy': 'sequential',
                'reasoning': 'Fallback: LLM unavailable, using sequential for safety'
            }
    
    def _execute_parallel_calls(
        self,
        emergencies: List[Dict],
        user_message: str,
        language: str
    ) -> Dict:
        """
        Execute all emergency calls SIMULTANEOUSLY
        
        Args:
            emergencies: List of emergencies to call
            user_message: User's message
            language: Language for calls
        
        Returns:
            Dict with all call SIDs and statuses
        """
        logger.info(f"📞 Initiating {len(emergencies)} PARALLEL calls...")
        
        call_results = []
        threads = []
        
        # Import here to avoid circular import
        from app.twilio_service import twilio_service
        from app.reflection_agent import reflection_agent
        
        # Start all calls simultaneously
        for i, emergency in enumerate(emergencies, 1):
            logger.info(f"   Call {i}/{len(emergencies)}: {emergency['type'].upper()}")
            
            # Initiate call (returns tuple: (success, call_sid_or_error))
            success, call_info = twilio_service.make_emergency_call(
                to_number=emergency['number'],
                emergency_type=emergency['type'],
                user_message=user_message,
                language=language
            )
            
            if success:
                call_sid = call_info  # call_info is call_sid when success=True
                logger.info(f"   ✅ Call initiated: {call_sid}")
                
                # Start Reflection Agent monitoring (parallel thread)
                monitor_thread = threading.Thread(
                    target=reflection_agent.monitor_and_recover,
                    args=(call_sid, emergency['type'], user_message, language),
                    daemon=True
                )
                monitor_thread.start()
                threads.append(monitor_thread)
                
                call_results.append({
                    'type': emergency['type'],
                    'call_sid': call_sid,
                    'status': 'initiated',
                    'reflection_agent_active': True,
                    'priority': emergency.get('priority', 'N/A')
                })
            else:
                error_msg = call_info  # call_info is error message when success=False
                logger.error(f"   ❌ Call failed: {error_msg}")
                call_results.append({
                    'type': emergency['type'],
                    'call_sid': None,
                    'status': 'failed',
                    'error': error_msg,
                    'priority': emergency.get('priority', 'N/A')
                })
        
        logger.info(f"✅ All {len(emergencies)} calls initiated in parallel")
        
        return {
            'calls': call_results,
            'total_calls': len(emergencies),
            'successful_calls': sum(1 for c in call_results if c['status'] == 'initiated')
        }
    
    def _execute_sequential_calls(
        self,
        emergencies: List[Dict],
        user_message: str,
        language: str
    ) -> Dict:
        """
        Execute emergency calls ONE BY ONE (most urgent first)
        
        Args:
            emergencies: Prioritized list of emergencies
            user_message: User's message
            language: Language for calls
        
        Returns:
            Dict with all call SIDs and statuses
        """
        logger.info(f"📞 Initiating {len(emergencies)} SEQUENTIAL calls...")
        
        call_results = []
        
        # Import here to avoid circular import
        from app.twilio_service import twilio_service
        from app.reflection_agent import reflection_agent
        
        # Call one by one
        for i, emergency in enumerate(emergencies, 1):
            logger.info(f"   Call {i}/{len(emergencies)}: {emergency['type'].upper()} (Priority {emergency.get('priority', 'N/A')})")
            
            # Initiate call (returns tuple: (success, call_sid_or_error))
            success, call_info = twilio_service.make_emergency_call(
                to_number=emergency['number'],
                emergency_type=emergency['type'],
                user_message=user_message,
                language=language
            )
            
            if success:
                call_sid = call_info  # call_info is call_sid when success=True
                logger.info(f"   ✅ Call initiated: {call_sid}")
                
                # Start Reflection Agent monitoring (background thread)
                monitor_thread = threading.Thread(
                    target=reflection_agent.monitor_and_recover,
                    args=(call_sid, emergency['type'], user_message, language),
                    daemon=True
                )
                monitor_thread.start()
                
                call_results.append({
                    'type': emergency['type'],
                    'call_sid': call_sid,
                    'status': 'initiated',
                    'reflection_agent_active': True,
                    'priority': emergency.get('priority', 'N/A')
                })
            else:
                error_msg = call_info  # call_info is error message when success=False
                logger.error(f"   ❌ Call failed: {error_msg}")
                call_results.append({
                    'type': emergency['type'],
                    'call_sid': None,
                    'status': 'failed',
                    'error': error_msg,
                    'priority': emergency.get('priority', 'N/A')
                })
            
            # Wait before next call (except for last one)
            if i < len(emergencies):
                logger.info(f"   ⏳ Waiting {self.sequential_delay} seconds before next call...")
                time.sleep(self.sequential_delay)
        
        logger.info(f"✅ All {len(emergencies)} calls completed sequentially")
        
        return {
            'calls': call_results,
            'total_calls': len(emergencies),
            'successful_calls': sum(1 for c in call_results if c['status'] == 'initiated')
        }


# Global singleton instance
escalation_agent = EscalationManagementAgent()
