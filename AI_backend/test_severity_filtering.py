"""
Test Severity Filtering for Emergency Detection

This script tests the severity assessment to ensure:
1. Minor issues (small injuries, first aid questions) -> No emergency call
2. Severe emergencies (life-threatening, unconscious) -> Emergency call

Example that should NOT trigger call:
"මගේ කකුලෙ පොඩි තුවාලයක්. චුට්ටක් ලේ යනව. මට මේක නවත්වන්න මොකද්ද කරන්න පුළුවන් කියලා කියන්න"
(My leg has a small injury. A little blood is coming. Tell me what I can do to stop this)

Expected: severity=minor, no emergency call, provide first aid advice
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.twilio_service import TwilioCallService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_severity_filtering():
    """Test severity assessment with various scenarios"""
    
    print("=" * 80)
    print("🔍 TESTING SEVERITY FILTERING")
    print("=" * 80)
    
    # Initialize TwilioCallService
    twilio_service = TwilioCallService()
    
    # Test cases: (message, expected_severity, should_call_emergency)
    test_cases = [
        # 🟢 MINOR - Should NOT call emergency
        (
            "මගේ කකුලෙ පොඩි තුවාලයක්. චුට්ටක් ලේ යනව. මට මේක නවත්වන්න මොකද්ද කරන්න පුළුවන් කියලා කියන්න",
            "minor",
            False,
            "Sinhala: Small leg injury with minor bleeding - asking for advice"
        ),
        (
            "I have a small cut on my finger. It's bleeding a little. What should I do?",
            "minor",
            False,
            "English: Minor cut with slight bleeding - asking for advice"
        ),
        (
            "My child has a small bruise on the knee. Should I be worried?",
            "minor",
            False,
            "English: Minor bruise - parent asking for advice"
        ),
        (
            "මගේ හිසේ වේදනාවක් තියෙනවා. මොකද්ද කරන්න ඕනේ?",
            "minor",
            False,
            "Sinhala: Headache - asking for advice"
        ),
        (
            "I have a mild fever. What medicine should I take?",
            "minor",
            False,
            "English: Mild fever - asking for medication advice"
        ),
        (
            "My child scraped their elbow playing. It's a small scrape. First aid tips?",
            "minor",
            False,
            "English: Small scrape - first aid question"
        ),
        (
            "පොඩි පිලිස්සුමක් තියෙනවා. වතුර දැම්මා. තව මොනවද කරන්න ඕනේ?",
            "minor",
            False,
            "Sinhala: Small burn with water applied - asking for next steps"
        ),
        (
            "I twisted my finger. It hurts a bit but I can move it. Should I ice it?",
            "minor",
            False,
            "English: Minor finger twist - asking for treatment advice"
        ),
        (
            "What are the symptoms of food poisoning?",
            "minor",
            False,
            "English: General question about symptoms - not reporting emergency"
        ),
        (
            "My nose is bleeding a little. How do I stop it?",
            "minor",
            False,
            "English: Minor nosebleed - asking for first aid"
        ),
        
        # 🟡 MODERATE - Should NOT call emergency (provide urgent advice)
        (
            "මගේ අතට ගැඹුරු කැපුමක් තිබෙනවා. ලේ නැවැත්තුවේ නැහැ. මොකද කරන්න ඕනේ?",
            "moderate",
            False,
            "Sinhala: Deep cut, won't stop bleeding - needs advice but not life-threatening"
        ),
        (
            "I fell and twisted my ankle badly. It's swollen and hurts a lot.",
            "moderate",
            False,
            "English: Sprained ankle - painful but not life-threatening"
        ),
        (
            "My child fell off the bike. They're crying but conscious. Scraped knees badly.",
            "moderate",
            False,
            "English: Bike fall with scrapes - child conscious and responsive"
        ),
        (
            "I have a bad toothache that won't go away. Can't sleep.",
            "moderate",
            False,
            "English: Severe toothache - painful but not emergency"
        ),
        (
            "බඩ රිදෙනවා ගොඩක් වැඩියි. වමනේ වෙනවා. මොකද කරන්න ඕනේ?",
            "moderate",
            False,
            "Sinhala: Severe stomach pain and vomiting - needs advice"
        ),
        
        # 🔴 SEVERE - Should call emergency
        (
            "මගේ මිතුරා හුස්ම ගන්න බැරි වෙලා ඉන්නවා. වැටිලා සිහිය නැති වෙලා",
            "severe",
            True,
            "Sinhala: Friend unconscious and can't breathe - SEVERE emergency"
        ),
        (
            "Someone broke into my house! They have a weapon! Help!",
            "severe",
            True,
            "English: Active crime with weapon - SEVERE emergency"
        ),
        (
            "My chest hurts really bad. I can't breathe properly. It feels like pressure.",
            "severe",
            True,
            "English: Chest pain, breathing difficulty - possible heart attack"
        ),
        (
            "ගින්නක් හටගෙන ඉන්නවා! උදව්වක් කරන්න!",
            "severe",
            True,
            "Sinhala: Fire emergency - SEVERE"
        ),
        (
            "My baby is not breathing! Please help!",
            "severe",
            True,
            "English: Baby not breathing - life-threatening emergency"
        ),
        (
            "මට රත්තරං වමනේ වෙනවා. ගොඩක් ලේ බහිනවා",
            "severe",
            True,
            "Sinhala: Vomiting blood - severe medical emergency"
        ),
        (
            "Car accident! Multiple people injured! Send ambulance!",
            "severe",
            True,
            "English: Car accident with injuries - SEVERE emergency"
        ),
        (
            "Someone is having a seizure! They're shaking uncontrollably!",
            "severe",
            True,
            "English: Seizure in progress - medical emergency"
        ),
        (
            "මගේ අම්මා බිම වැටිලා. හිස බොරලෙන් ලේ යනවා. කතා කරන්නේ නැහැ",
            "severe",
            True,
            "Sinhala: Mother fell, head bleeding heavily, unresponsive - SEVERE"
        ),
        (
            "I drank poison by mistake! What do I do?",
            "severe",
            True,
            "English: Poisoning - life-threatening emergency"
        ),
        (
            "කෙනෙක් මගේ පස්සෙන් එනවා. තර්ජනය කරනවා. බයයි",
            "severe",
            True,
            "Sinhala: Being followed and threatened - safety emergency"
        ),
        (
            "Domestic violence happening right now! Please send police!",
            "severe",
            True,
            "English: Active domestic violence - police emergency"
        ),
        (
            "Gas leak! I can smell gas everywhere! House might explode!",
            "severe",
            True,
            "English: Gas leak - fire/explosion danger"
        ),
        (
            "හුස්ම ගන්න අමාරුයි. පපුව තද වෙනවා. හදවතේ වේදනාවක් වගේ",
            "severe",
            True,
            "Sinhala: Difficulty breathing, chest tightness, heart pain - cardiac emergency"
        ),
        (
            "My friend overdosed on pills! They're barely conscious!",
            "severe",
            True,
            "English: Drug overdose - medical emergency"
        )
    ]
    
    print("\n📋 Running Test Cases:\n")
    
    passed = 0
    failed = 0
    
    for i, (message, expected_severity, should_call, description) in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test Case {i}: {description}")
        print(f"{'='*80}")
        print(f"📝 Message: {message}")
        print(f"🎯 Expected: severity={expected_severity}, call_emergency={should_call}")
        
        # Detect emergency intent
        result = twilio_service.detect_emergency_intent(message)
        
        if result:
            actual_severity = result.get('severity', 'unknown')
            actual_type = result.get('type', 'none')
            actual_confidence = result.get('confidence', 0.0)
            actual_reasoning = result.get('reasoning', '')
            
            print(f"\n🤖 AI Response:")
            print(f"   Severity: {actual_severity}")
            print(f"   Type: {actual_type}")
            print(f"   Confidence: {actual_confidence:.2f}")
            print(f"   Will Call: YES ✅")
            print(f"   Reasoning: {actual_reasoning}")
            
            # Check if it matches expectations
            if should_call and actual_severity == expected_severity:
                print(f"\n✅ PASS: Correctly identified as {expected_severity} emergency")
                passed += 1
            elif should_call and actual_severity != expected_severity:
                print(f"\n❌ FAIL: Expected {expected_severity}, got {actual_severity}")
                failed += 1
            elif not should_call:
                print(f"\n❌ FAIL: Should NOT have called emergency for {expected_severity} issue")
                failed += 1
        else:
            print(f"\n🤖 AI Response: No emergency detected (will provide advice only)")
            
            # Check if it matches expectations
            if not should_call:
                print(f"\n✅ PASS: Correctly identified as non-emergency (advice only)")
                passed += 1
            else:
                print(f"\n❌ FAIL: Should have called emergency for {expected_severity} issue")
                failed += 1
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"✅ Passed: {passed}/{len(test_cases)}")
    print(f"❌ Failed: {failed}/{len(test_cases)}")
    print(f"📈 Success Rate: {(passed/len(test_cases)*100):.1f}%")
    print("="*80)
    
    if failed == 0:
        print("\n🎉 All tests passed! Severity filtering is working correctly.")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Review the AI reasoning above.")
    
    return passed, failed


if __name__ == "__main__":
    print("\n🚀 Starting Severity Filtering Tests...\n")
    passed, failed = test_severity_filtering()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)
