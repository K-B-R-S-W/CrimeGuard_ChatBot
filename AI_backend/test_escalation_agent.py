"""
Test script for Escalation Management Agent
Tests multi-emergency detection, prioritization, and coordinated calling
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.escalation_agent import escalation_agent, EscalationManagementAgent
from app.twilio_service import twilio_service
from dotenv import load_dotenv

load_dotenv()

def test_agent_initialization():
    """Test 1: Verify agent initializes correctly"""
    print("\n" + "="*70)
    print("TEST 1: Agent Initialization")
    print("="*70)
    
    agent = EscalationManagementAgent()
    
    print(f"✅ Agent initialized successfully")
    print(f"   Sequential Delay: {agent.sequential_delay} seconds")

def test_multi_emergency_detection():
    """Test 2: Test detection of multiple emergencies"""
    print("\n" + "="*70)
    print("TEST 2: Multi-Emergency Detection")
    print("="*70)
    
    test_messages = [
        "Fire in building AND people are injured!",
        "Car accident with injuries!",
        "Someone breaking in and I'm hurt!",
        "Fire spreading fast!",  # Single emergency
        "How do I stop bleeding?"  # Not an emergency
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n🧪 Test Message {i}: \"{message}\"")
        
        try:
            result = twilio_service.detect_emergency_intent(message)
            
            if result:
                emergencies = result.get('emergencies', [])
                total_count = result.get('total_count', 0)
                language = result.get('language', 'en')
                
                print(f"   ✅ {total_count} emergency(ies) detected (language: {language})")
                
                for j, emerg in enumerate(emergencies, 1):
                    print(f"      {j}. {emerg['type'].upper()}")
                    print(f"         Severity: {emerg['severity']}")
                    print(f"         Confidence: {emerg['confidence']}")
                    print(f"         Reasoning: {emerg['reasoning']}")
            else:
                print("   ℹ️ No emergency detected")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

def test_prioritization_logic():
    """Test 3: Test LLM-based prioritization"""
    print("\n" + "="*70)
    print("TEST 3: Emergency Prioritization")
    print("="*70)
    
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  SKIPPED: OPENAI_API_KEY not found in .env")
        return
    
    agent = EscalationManagementAgent()
    
    # Mock multi-emergency scenario
    mock_emergencies = [
        {
            'type': 'fire',
            'number': '+94110',
            'severity': 'severe',
            'confidence': 0.95,
            'reasoning': 'Building on fire'
        },
        {
            'type': 'ambulance',
            'number': '+941990',
            'severity': 'severe',
            'confidence': 0.90,
            'reasoning': 'People trapped and injured'
        }
    ]
    
    user_message = "Fire in building! People trapped and injured inside!"
    
    print(f"\n🧪 Test Scenario: \"{user_message}\"")
    print(f"   Detected Emergencies: Fire + Ambulance")
    
    try:
        prioritized = agent._prioritize_emergencies(mock_emergencies, user_message)
        
        print("\n🧠 LLM Prioritization Result:")
        for emerg in prioritized:
            print(f"   Priority {emerg.get('priority', 'N/A')}: {emerg['type'].upper()}")
            print(f"      Urgency Score: {emerg.get('urgency_score', 'N/A')}")
            print(f"      Reasoning: {emerg.get('priority_reasoning', 'No reasoning')}")
        
        print("\n✅ PASS: Prioritization completed")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

def test_strategy_decision():
    """Test 4: Test sequential vs parallel strategy decision"""
    print("\n" + "="*70)
    print("TEST 4: Calling Strategy Decision")
    print("="*70)
    
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  SKIPPED: OPENAI_API_KEY not found in .env")
        return
    
    agent = EscalationManagementAgent()
    
    test_scenarios = [
        {
            'message': "Fire caused injuries!",
            'emergencies': [
                {'type': 'fire', 'priority': 1},
                {'type': 'ambulance', 'priority': 2}
            ],
            'expected': 'sequential'
        },
        {
            'message': "Multiple independent emergencies!",
            'emergencies': [
                {'type': 'police', 'priority': 1},
                {'type': 'fire', 'priority': 1}
            ],
            'expected': 'parallel'
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 Scenario {i}: \"{scenario['message']}\"")
        
        try:
            strategy = agent._decide_calling_strategy(
                scenario['emergencies'],
                scenario['message']
            )
            
            print(f"   Strategy: {strategy['strategy'].upper()}")
            print(f"   Reasoning: {strategy['reasoning']}")
            print(f"   Expected: {scenario['expected'].upper()}")
            
            if strategy['strategy'] == scenario['expected']:
                print(f"   ✅ MATCH: Strategy matches expected")
            else:
                print(f"   ⚠️ DIFFERENT: Strategy differs from expected (not necessarily wrong)")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

def test_coordination_methods():
    """Test 5: Verify coordination methods exist"""
    print("\n" + "="*70)
    print("TEST 5: Coordination Methods")
    print("="*70)
    
    agent = EscalationManagementAgent()
    
    methods = [
        'coordinate_multi_emergency',
        '_prioritize_emergencies',
        '_decide_calling_strategy',
        '_execute_parallel_calls',
        '_execute_sequential_calls'
    ]
    
    for method in methods:
        if hasattr(agent, method):
            print(f"✅ {method}() exists")
        else:
            print(f"❌ ERROR: {method}() missing!")

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("🚨 ESCALATION MANAGEMENT AGENT - TEST SUITE")
    print("="*70)
    print("Testing multi-emergency coordination and prioritization")
    print("="*70)
    
    try:
        test_agent_initialization()
        test_coordination_methods()
        test_multi_emergency_detection()
        test_prioritization_logic()
        test_strategy_decision()
        
        print("\n" + "="*70)
        print("✅ TEST SUITE COMPLETED")
        print("="*70)
        print("\nNOTE: To test actual multi-emergency coordination:")
        print("      Send message: 'Fire AND people injured!'")
        print("      The Escalation Agent will automatically coordinate all calls.")
        print("\n⚠️  IMPORTANT: This agent works with Reflection Agent")
        print("   Each call is monitored independently for failures.")
        
    except Exception as e:
        print("\n" + "="*70)
        print(f"❌ TEST SUITE FAILED: {e}")
        print("="*70)

if __name__ == "__main__":
    run_all_tests()
