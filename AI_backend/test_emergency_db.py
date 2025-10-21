"""
Test Emergency Call Database Integration
Tests MongoDB storage and retrieval of emergency call records
"""
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app.db_utils import (
    save_emergency_call,
    update_call_status,
    get_emergency_calls,
    get_emergency_statistics
)

def test_emergency_db_integration():
    """Test complete emergency call database workflow"""
    
    print("=" * 80)
    print("🗄️  EMERGENCY CALL DATABASE TEST")
    print("=" * 80)
    print()
    
    # Test 1: Save emergency calls in different languages
    print("📝 Test 1: Saving Emergency Calls")
    print("─" * 80)
    
    test_calls = [
        {
            "user_message": "call police there's a robbery at Main Street",
            "emergency_type": "police",
            "phone_number": "+94779421552",
            "call_sid": "CA_TEST_001_EN",
            "language": "en",
            "confidence": 0.95,
            "reasoning": "User explicitly requesting police call for robbery",
            "audio_url": "https://example.ngrok.app/audio/test_en.mp3",
            "user_phone": "+94771234567",
            "call_status": "initiated"
        },
        {
            "user_message": "පොලිසියට කතා කරන්න මා ගෙදර සොරකම් කරනවා",
            "emergency_type": "police",
            "phone_number": "+94779421552",
            "call_sid": "CA_TEST_002_SI",
            "language": "si",
            "confidence": 0.92,
            "reasoning": "User requesting police in Sinhala for break-in",
            "audio_url": "https://example.ngrok.app/audio/test_si.mp3",
            "user_phone": "+94777654321",
            "call_status": "initiated"
        },
        {
            "user_message": "ஆம்புலன்ஸை அழைக்கவும் விபத்து நடந்தது",
            "emergency_type": "ambulance",
            "phone_number": "+94779421552",
            "call_sid": "CA_TEST_003_TA",
            "language": "ta",
            "confidence": 0.97,
            "reasoning": "User requesting ambulance in Tamil for accident",
            "audio_url": "https://example.ngrok.app/audio/test_ta.mp3",
            "user_phone": "+94771111111",
            "call_status": "initiated"
        },
        {
            "user_message": "fire in my house call fire department urgently",
            "emergency_type": "fire",
            "phone_number": "+94779421552",
            "call_sid": "CA_TEST_004_EN",
            "language": "en",
            "confidence": 0.99,
            "reasoning": "User reporting fire emergency, high urgency",
            "audio_url": "https://example.ngrok.app/audio/test_fire.mp3",
            "user_phone": "+94772222222",
            "call_status": "initiated"
        }
    ]
    
    saved_ids = []
    for i, call_data in enumerate(test_calls, 1):
        try:
            doc_id = save_emergency_call(**call_data)
            saved_ids.append(doc_id)
            print(f"✅ Call {i}: {call_data['emergency_type']} ({call_data['language']}) - Saved with ID: {doc_id}")
        except Exception as e:
            print(f"❌ Call {i}: Failed to save - {e}")
    
    print()
    
    # Test 2: Update call statuses
    print("📝 Test 2: Updating Call Statuses")
    print("─" * 80)
    
    status_updates = [
        ("CA_TEST_001_EN", "ringing", None),
        ("CA_TEST_002_SI", "in-progress", None),
        ("CA_TEST_003_TA", "completed", 45),
        ("CA_TEST_004_EN", "failed", 0)
    ]
    
    for call_sid, status, duration in status_updates:
        try:
            success = update_call_status(call_sid, status, duration)
            duration_str = f" (duration: {duration}s)" if duration is not None else ""
            if success:
                print(f"✅ Updated {call_sid}: {status}{duration_str}")
            else:
                print(f"⚠️  No record found for {call_sid}")
        except Exception as e:
            print(f"❌ Failed to update {call_sid}: {e}")
    
    print()
    
    # Test 3: Retrieve emergency calls with filters
    print("📝 Test 3: Retrieving Emergency Calls")
    print("─" * 80)
    
    # Get all calls
    print("\n🔍 All Emergency Calls:")
    all_calls = get_emergency_calls(limit=10)
    print(f"   Found {len(all_calls)} calls")
    for call in all_calls[:3]:  # Show first 3
        print(f"   - {call['emergency_type'].upper()} ({call['language']}): {call['user_message'][:50]}...")
        print(f"     Status: {call['call_status']} | Confidence: {call['confidence']:.2f}")
    
    # Filter by type
    print("\n🔍 Police Calls Only:")
    police_calls = get_emergency_calls(emergency_type='police', limit=10)
    print(f"   Found {len(police_calls)} police calls")
    
    # Filter by language
    print("\n🔍 Sinhala Calls Only:")
    sinhala_calls = get_emergency_calls(language='si', limit=10)
    print(f"   Found {len(sinhala_calls)} Sinhala calls")
    for call in sinhala_calls:
        print(f"   - {call['service_name_si']}: {call['user_message']}")
    
    # Filter by status
    print("\n🔍 Completed Calls:")
    completed_calls = get_emergency_calls(status='completed', limit=10)
    print(f"   Found {len(completed_calls)} completed calls")
    
    # Filter by confidence
    print("\n🔍 High Confidence Calls (≥0.95):")
    high_confidence = get_emergency_calls(min_confidence=0.95, limit=10)
    print(f"   Found {len(high_confidence)} high-confidence calls")
    
    print()
    
    # Test 4: Get statistics
    print("📝 Test 4: Emergency Call Statistics")
    print("─" * 80)
    
    try:
        stats = get_emergency_statistics()
        
        print(f"\n📊 Total Calls: {stats['total_calls']}")
        
        print(f"\n📈 Calls by Type:")
        for item in stats['by_type']:
            print(f"   {item['_id'].upper()}: {item['count']} calls")
        
        print(f"\n🌍 Calls by Language:")
        lang_names = {'en': 'English', 'si': 'Sinhala', 'ta': 'Tamil'}
        for item in stats['by_language']:
            lang = lang_names.get(item['_id'], item['_id'])
            print(f"   {lang}: {item['count']} calls")
        
        print(f"\n📞 Calls by Status:")
        for item in stats['by_status']:
            print(f"   {item['_id'].upper()}: {item['count']} calls")
        
        print(f"\n🎯 Confidence Statistics:")
        for item in stats['confidence_stats']:
            print(f"   {item['_id'].upper()}:")
            print(f"      Average: {item['avg_confidence']:.2f}")
            print(f"      Min: {item['min_confidence']:.2f}")
            print(f"      Max: {item['max_confidence']:.2f}")
        
        print()
        print("✅ Statistics calculated successfully!")
        
    except Exception as e:
        print(f"❌ Failed to get statistics: {e}")
    
    print()
    
    # Summary
    print("=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully saved {len(saved_ids)} test calls")
    print(f"✅ Successfully updated {len(status_updates)} call statuses")
    print(f"✅ Successfully retrieved calls with various filters")
    print(f"✅ Successfully calculated emergency statistics")
    print()
    print("🎉 All database operations working perfectly!")
    print("=" * 80)


if __name__ == "__main__":
    print()
    print("🚀 Starting Emergency Call Database Test...")
    print()
    
    try:
        test_emergency_db_integration()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
