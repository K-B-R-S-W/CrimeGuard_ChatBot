"""
Comprehensive Emergency Detection Test Suite
Tests various emergency phrases to identify potential classification issues
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.fast_classifier import fast_classifier, IntentType
from app.twilio_service import twilio_service
import logging

logging.basicConfig(level=logging.WARNING)  # Reduce noise, show only warnings
logger = logging.getLogger(__name__)

# Test cases covering various emergency scenarios
EMERGENCY_TEST_CASES = [
    # Medical Emergencies
    {
        "message": "im bleeding heavily help me im at nuwara eliya town",
        "expected_type": "ambulance",
        "expected_severity": "severe",
        "category": "Medical - Heavy Bleeding"
    },
    {
        "message": "help my father is having a heart attack",
        "expected_type": "ambulance",
        "expected_severity": "severe",
        "category": "Medical - Heart Attack"
    },
    {
        "message": "someone is unconscious and not breathing",
        "expected_type": "ambulance",
        "expected_severity": "severe",
        "category": "Medical - Unconscious"
    },
    {
        "message": "i cant breathe help me please",
        "expected_type": "ambulance",
        "expected_severity": "severe",
        "category": "Medical - Breathing Problem"
    },
    {
        "message": "chest pain urgent help needed",
        "expected_type": "ambulance",
        "expected_severity": "severe",
        "category": "Medical - Chest Pain"
    },
    {
        "message": "car accident people injured badly",
        "expected_type": "ambulance",
        "expected_severity": "severe",
        "category": "Medical - Accident"
    },
    {
        "message": "my mother fell and hurt her head bleeding",
        "expected_type": "ambulance",
        "expected_severity": "severe",
        "category": "Medical - Head Injury"
    },
    
    # Police Emergencies
    {
        "message": "help theres a robbery happening right now",
        "expected_type": "police",
        "expected_severity": "severe",
        "category": "Police - Robbery"
    },
    {
        "message": "someone is breaking into my house help",
        "expected_type": "police",
        "expected_severity": "severe",
        "category": "Police - Break-in"
    },
    {
        "message": "im being attacked please help urgent",
        "expected_type": "police",
        "expected_severity": "severe",
        "category": "Police - Assault"
    },
    {
        "message": "theres a fight and someone has a weapon",
        "expected_type": "police",
        "expected_severity": "severe",
        "category": "Police - Armed Threat"
    },
    {
        "message": "suspicious person trying to break in help",
        "expected_type": "police",
        "expected_severity": "severe",
        "category": "Police - Intruder"
    },
    
    # Fire Emergencies
    {
        "message": "help my house is on fire",
        "expected_type": "fire",
        "expected_severity": "severe",
        "category": "Fire - House Fire"
    },
    {
        "message": "theres smoke everywhere and flames spreading",
        "expected_type": "fire",
        "expected_severity": "severe",
        "category": "Fire - Spreading"
    },
    {
        "message": "gas leak i smell gas help urgent",
        "expected_type": "fire",
        "expected_severity": "severe",
        "category": "Fire - Gas Leak"
    },
    {
        "message": "explosion in the kitchen fire starting",
        "expected_type": "fire",
        "expected_severity": "severe",
        "category": "Fire - Explosion"
    },
    
    # Multi-language Emergencies
    {
        "message": "හදිසි උදව් අවශ්‍යයි මට තුවාලයක්",
        "expected_type": "ambulance",
        "expected_severity": "severe",
        "category": "Sinhala - Injury"
    },
    {
        "message": "ගින්නක් උදව් කරන්න",
        "expected_type": "fire",
        "expected_severity": "severe",
        "category": "Sinhala - Fire"
    },
    {
        "message": "அவசர உதவி வேண்டும் விபத்து",
        "expected_type": "ambulance",
        "expected_severity": "severe",
        "category": "Tamil - Accident"
    },
    
    # Edge Cases - Problematic Phrases
    {
        "message": "help i need assistance with emergency",
        "expected_type": "help",  # Should NOT trigger emergency
        "expected_severity": "none",
        "category": "Edge Case - Help Request (not emergency)"
    },
    {
        "message": "can you help me understand how to call ambulance",
        "expected_type": "help",  # Information request
        "expected_severity": "none",
        "category": "Edge Case - Information Request"
    },
    {
        "message": "what should i do if someone is bleeding",
        "expected_type": "help",  # Advice request
        "expected_severity": "none",
        "category": "Edge Case - Advice Request"
    }
]

def test_single_emergency(test_case):
    """Test a single emergency phrase"""
    message = test_case["message"]
    expected_type = test_case["expected_type"]
    expected_severity = test_case["expected_severity"]
    category = test_case["category"]
    
    print(f"\n{'='*80}")
    print(f"TEST: {category}")
    print(f"{'='*80}")
    print(f"Message: \"{message}\"")
    print(f"Expected: {expected_type} / {expected_severity}")
    print(f"{'-'*80}")
    
    # Step 1: Fast Classifier
    intent, fast_response, confidence = fast_classifier.classify(message)
    
    print(f"Fast Classifier: {intent.value}")
    
    if fast_response:
        print(f"❌ PROBLEM: Returned cached response instead of escalating!")
        print(f"Response preview: {fast_response[:100]}...")
        return {
            "category": category,
            "message": message,
            "status": "FAILED",
            "reason": "Fast classifier returned cached response",
            "expected": expected_type,
            "actual": "cached_response"
        }
    
    # Step 2: Emergency Detection (only if expected to be emergency)
    if expected_type in ['ambulance', 'police', 'fire']:
        print(f"✅ Fast classifier escalated to LLM")
        
        emergency_intent = twilio_service.detect_emergency_intent(message)
        
        if not emergency_intent:
            print(f"❌ FAILED: LLM did not detect emergency!")
            return {
                "category": category,
                "message": message,
                "status": "FAILED",
                "reason": "LLM did not detect emergency",
                "expected": expected_type,
                "actual": "none"
            }
        
        # Check detected emergency
        emergencies = emergency_intent.get('emergencies', [])
        if not emergencies:
            print(f"❌ FAILED: Empty emergencies list!")
            return {
                "category": category,
                "message": message,
                "status": "FAILED",
                "reason": "Empty emergencies list",
                "expected": expected_type,
                "actual": "none"
            }
        
        first_emerg = emergencies[0]
        actual_type = first_emerg.get('type')
        actual_severity = first_emerg.get('severity')
        confidence = first_emerg.get('confidence')
        reasoning = first_emerg.get('reasoning', '')
        
        print(f"Detected: {actual_type} / {actual_severity} (confidence: {confidence})")
        print(f"Reasoning: {reasoning}")
        
        # Verify type and severity
        if actual_type != expected_type:
            print(f"⚠️  WARNING: Type mismatch! Expected '{expected_type}', got '{actual_type}'")
            return {
                "category": category,
                "message": message,
                "status": "WARNING",
                "reason": f"Type mismatch: expected {expected_type}, got {actual_type}",
                "expected": expected_type,
                "actual": actual_type
            }
        
        if actual_severity != expected_severity:
            print(f"⚠️  WARNING: Severity mismatch! Expected '{expected_severity}', got '{actual_severity}'")
            return {
                "category": category,
                "message": message,
                "status": "WARNING",
                "reason": f"Severity mismatch: expected {expected_severity}, got {actual_severity}",
                "expected": expected_severity,
                "actual": actual_severity
            }
        
        print(f"✅ PASSED: Correctly detected as {actual_type} / {actual_severity}")
        return {
            "category": category,
            "message": message,
            "status": "PASSED",
            "expected": expected_type,
            "actual": actual_type
        }
    
    else:
        # Expected to be information/help request (not emergency)
        print(f"✅ Correctly handled as non-emergency")
        return {
            "category": category,
            "message": message,
            "status": "PASSED",
            "expected": expected_type,
            "actual": "non_emergency"
        }

def run_all_tests():
    """Run all emergency detection tests"""
    print("\n" + "="*80)
    print("EMERGENCY DETECTION TEST SUITE")
    print("="*80)
    print(f"Total test cases: {len(EMERGENCY_TEST_CASES)}")
    
    results = []
    for test_case in EMERGENCY_TEST_CASES:
        result = test_single_emergency(test_case)
        results.append(result)
    
    # Summary
    print("\n\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = [r for r in results if r["status"] == "PASSED"]
    failed = [r for r in results if r["status"] == "FAILED"]
    warnings = [r for r in results if r["status"] == "WARNING"]
    
    print(f"\n✅ PASSED: {len(passed)}/{len(results)}")
    print(f"⚠️  WARNINGS: {len(warnings)}/{len(results)}")
    print(f"❌ FAILED: {len(failed)}/{len(results)}")
    
    if failed:
        print("\n" + "="*80)
        print("FAILED TESTS (CRITICAL ISSUES)")
        print("="*80)
        for r in failed:
            print(f"\n❌ {r['category']}")
            print(f"   Message: \"{r['message'][:60]}...\"")
            print(f"   Reason: {r['reason']}")
            print(f"   Expected: {r['expected']}, Actual: {r['actual']}")
    
    if warnings:
        print("\n" + "="*80)
        print("WARNINGS (MINOR ISSUES)")
        print("="*80)
        for r in warnings:
            print(f"\n⚠️  {r['category']}")
            print(f"   Message: \"{r['message'][:60]}...\"")
            print(f"   Reason: {r['reason']}")
            print(f"   Expected: {r['expected']}, Actual: {r['actual']}")
    
    print("\n" + "="*80)
    if len(failed) == 0 and len(warnings) == 0:
        print("✅✅✅ ALL TESTS PASSED! ✅✅✅")
    elif len(failed) == 0:
        print("✅ ALL CRITICAL TESTS PASSED (some warnings)")
    else:
        print("❌ SOME TESTS FAILED - REVIEW NEEDED")
    print("="*80 + "\n")
    
    return results

if __name__ == "__main__":
    results = run_all_tests()
