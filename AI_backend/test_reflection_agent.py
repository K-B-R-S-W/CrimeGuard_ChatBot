"""
Test script for Reflection & Recovery Agent
Tests autonomous monitoring, failure analysis, and retry logic
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.reflection_agent import reflection_agent, ReflectionRecoveryAgent
from dotenv import load_dotenv

load_dotenv()

def test_agent_initialization():
    """Test 1: Verify agent initializes correctly"""
    print("\n" + "="*70)
    print("TEST 1: Agent Initialization")
    print("="*70)
    
    agent = ReflectionRecoveryAgent()
    
    print(f"✅ Agent initialized successfully")
    print(f"   Max Attempts: {agent.max_attempts}")
    print(f"   Wait Time: {agent.wait_time_seconds} seconds")
    print(f"   Monitoring Interval: {agent.monitoring_interval} seconds")
    
    # Check emergency contacts
    for service_type, contacts in agent.EMERGENCY_CONTACTS.items():
        print(f"\n📋 {service_type.upper()} Contacts:")
        for contact in contacts:
            print(f"   {contact['priority']}. {contact['name']}")
            print(f"      Number: {contact['number']}")
            print(f"      Description: {contact['description']}")

def test_emergency_contacts_configuration():
    """Test 2: Verify emergency backup numbers are configured"""
    print("\n" + "="*70)
    print("TEST 2: Emergency Contacts Configuration")
    print("="*70)
    
    agent = ReflectionRecoveryAgent()
    
    # Verify each service has backup contacts
    required_services = ["police", "ambulance", "fire"]
    
    for service in required_services:
        contacts = agent.EMERGENCY_CONTACTS.get(service, [])
        print(f"\n🚨 {service.upper()} Service:")
        print(f"   Total Backup Contacts: {len(contacts)}")
        
        if len(contacts) == 0:
            print("   ❌ ERROR: No contacts configured!")
        elif len(contacts) < 2:
            print("   ⚠️  WARNING: Less than 2 backup contacts")
        else:
            print("   ✅ PASS: Multiple backup contacts available")
        
        # Check if all numbers are from .env
        for i, contact in enumerate(contacts, 1):
            if contact["number"]:
                print(f"   {i}. {contact['name']}: {contact['number']} ✅")
            else:
                print(f"   {i}. {contact['name']}: NOT CONFIGURED ❌")

def test_llm_failure_analysis():
    """Test 3: Test LLM-based failure analysis (if OpenAI key available)"""
    print("\n" + "="*70)
    print("TEST 3: LLM Failure Analysis")
    print("="*70)
    
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  SKIPPED: OPENAI_API_KEY not found in .env")
        return
    
    agent = ReflectionRecoveryAgent()
    
    # Test scenario: First attempt "no-answer"
    print("\n🧪 Test Scenario: First attempt 'no-answer' on Police Emergency")
    
    current_contact = agent.EMERGENCY_CONTACTS["police"][0]
    remaining_contacts = agent.EMERGENCY_CONTACTS["police"][1:]
    
    try:
        decision = agent._analyze_failure_and_decide(
            call_status="no-answer",
            emergency_type="police",
            attempt=1,
            current_contact=current_contact,
            remaining_contacts=remaining_contacts,
            user_message="Someone is breaking into my house!"
        )
        
        print("\n🧠 LLM Decision:")
        print(f"   Should Retry: {decision.get('should_retry', 'N/A')}")
        print(f"   Try Next Contact: {decision.get('try_next_contact', 'N/A')}")
        print(f"   Success Probability: {decision.get('success_probability', 'N/A')}")
        print(f"   Reasoning: {decision.get('reasoning', 'N/A')}")
        
        if decision.get('should_retry'):
            print("\n✅ PASS: Agent decided to retry (expected for first attempt)")
        else:
            print("\n⚠️  UNEXPECTED: Agent decided NOT to retry on first attempt")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

def test_monitoring_logic():
    """Test 4: Verify monitoring logic structure"""
    print("\n" + "="*70)
    print("TEST 4: Monitoring Logic Structure")
    print("="*70)
    
    agent = ReflectionRecoveryAgent()
    
    # Verify method exists
    if hasattr(agent, 'monitor_and_recover'):
        print("✅ monitor_and_recover() method exists")
    else:
        print("❌ ERROR: monitor_and_recover() method missing!")
        return
    
    # Verify helper methods
    helper_methods = [
        '_check_call_status',
        '_analyze_failure_and_decide',
        '_retry_emergency_call'
    ]
    
    for method in helper_methods:
        if hasattr(agent, method):
            print(f"✅ {method}() helper method exists")
        else:
            print(f"❌ ERROR: {method}() helper method missing!")

def test_agent_parameters():
    """Test 5: Verify agent parameters match requirements"""
    print("\n" + "="*70)
    print("TEST 5: Agent Parameters Validation")
    print("="*70)
    
    agent = ReflectionRecoveryAgent()
    
    # Check wait time is 5 seconds as required
    if agent.wait_time_seconds == 5:
        print("✅ PASS: Wait time is 5 seconds (as required)")
    else:
        print(f"❌ FAIL: Wait time is {agent.wait_time_seconds}s (should be 5s)")
    
    # Check max attempts
    if agent.max_attempts >= 4:
        print(f"✅ PASS: Max attempts is {agent.max_attempts} (≥4)")
    else:
        print(f"⚠️  WARNING: Max attempts is {agent.max_attempts} (<4)")
    
    # Check monitoring interval
    if agent.monitoring_interval == 5:
        print(f"✅ PASS: Monitoring interval is 5 seconds")
    else:
        print(f"⚠️  INFO: Monitoring interval is {agent.monitoring_interval}s")

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("🤖 REFLECTION & RECOVERY AGENT - TEST SUITE")
    print("="*70)
    print("Testing autonomous call monitoring and recovery system")
    print("="*70)
    
    try:
        test_agent_initialization()
        test_emergency_contacts_configuration()
        test_monitoring_logic()
        test_agent_parameters()
        test_llm_failure_analysis()  # Run last (requires API key)
        
        print("\n" + "="*70)
        print("✅ TEST SUITE COMPLETED")
        print("="*70)
        print("\nNOTE: To test actual call monitoring, make a real emergency")
        print("      call and the agent will automatically activate.")
        print("\n⚠️  IMPORTANT: Verify all emergency numbers in Twilio Console")
        print("   https://console.twilio.com/us1/develop/phone-numbers/manage/verified")
        
    except Exception as e:
        print("\n" + "="*70)
        print(f"❌ TEST SUITE FAILED: {e}")
        print("="*70)

if __name__ == "__main__":
    run_all_tests()
