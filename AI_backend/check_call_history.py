"""
Check Status of Recent Twilio Calls
"""
import sys
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twilio.rest import Client

def check_recent_calls():
    """Check recent call history"""
    
    print("\n" + "="*70)
    print("RECENT CALL HISTORY")
    print("="*70 + "\n")
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    try:
        client = Client(account_sid, auth_token)
        
        # Get calls from the last hour
        after_time = datetime.utcnow() - timedelta(hours=1)
        
        calls = client.calls.list(
            start_time_after=after_time,
            limit=10
        )
        
        if not calls:
            print("❌ No calls found in the last hour")
            print("   This might mean:")
            print("   1. Calls are not being initiated")
            print("   2. There's an error before the call is made")
            return
        
        print(f"Found {len(calls)} call(s) in the last hour:\n")
        
        for idx, call in enumerate(calls, 1):
            print(f"--- Call {idx} ---")
            print(f"SID: {call.sid}")
            print(f"From: {call.from_formatted}")
            print(f"To: {call.to_formatted}")
            print(f"Status: {call.status}")
            print(f"Direction: {call.direction}")
            print(f"Start Time: {call.start_time}")
            print(f"Duration: {call.duration} seconds" if call.duration else "Duration: N/A")
            
            # Explain status
            if call.status == 'completed':
                print("✅ Call completed successfully!")
            elif call.status == 'in-progress':
                print("📞 Call is currently in progress")
            elif call.status == 'queued':
                print("⏳ Call is queued (waiting to connect)")
            elif call.status == 'ringing':
                print("📱 Phone is ringing...")
            elif call.status == 'failed':
                print("❌ Call failed")
                # Try to get more details
                try:
                    call_details = client.calls(call.sid).fetch()
                    if hasattr(call_details, 'error_code') and call_details.error_code:
                        print(f"   Error Code: {call_details.error_code}")
                        print(f"   Error Message: {call_details.error_message}")
                except:
                    pass
            elif call.status == 'busy':
                print("⚠️ Number was busy")
            elif call.status == 'no-answer':
                print("⚠️ No answer - phone rang but wasn't picked up")
            elif call.status == 'canceled':
                print("🚫 Call was canceled")
            
            print()
        
        # Check specifically for your test number
        your_number = os.getenv('EMERGENCY_POLICE_NUMBER')
        calls_to_you = [c for c in calls if c.to == your_number or c.to_formatted == your_number]
        
        if calls_to_you:
            print(f"\n✅ Found {len(calls_to_you)} call(s) to your number ({your_number})")
            latest = calls_to_you[0]
            print(f"\nLatest call to you:")
            print(f"  Status: {latest.status}")
            print(f"  Time: {latest.start_time}")
            
            if latest.status == 'no-answer':
                print("\n💡 The call reached your phone but wasn't answered!")
                print("   Make sure to answer when you test!")
            elif latest.status == 'completed':
                print("\n✅ Call was completed - you should have heard the message!")
            elif latest.status == 'failed':
                print("\n❌ Call failed to connect")
        else:
            print(f"\n⚠️ No calls found to your number ({your_number})")
            print("   This might mean the emergency detection isn't triggering")
        
    except Exception as e:
        print(f"❌ Error checking calls: {e}")

if __name__ == "__main__":
    check_recent_calls()
