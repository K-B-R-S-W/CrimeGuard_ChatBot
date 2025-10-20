"""
Real-time Call Status Checker
Checks the status of emergency calls in real-time
"""
import sys
import os
from dotenv import load_dotenv
from datetime import datetime
import time

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twilio.rest import Client

def monitor_call_status(call_sid, duration=30):
    """Monitor a call's status in real-time"""
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    try:
        client = Client(account_sid, auth_token)
        
        print(f"\n📞 Monitoring Call: {call_sid}")
        print("=" * 70)
        
        previous_status = None
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                call = client.calls(call_sid).fetch()
                current_status = call.status
                
                if current_status != previous_status:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] Status: {current_status.upper()}")
                    
                    # Explain status
                    if current_status == 'queued':
                        print("           → Call is queued, waiting to be initiated")
                    elif current_status == 'initiated':
                        print("           → Call is being set up")
                    elif current_status == 'ringing':
                        print("           → 📱 Your phone should be ringing now!")
                    elif current_status == 'in-progress':
                        print("           → ✅ Call connected! You answered the phone")
                    elif current_status == 'completed':
                        print("           → ✅ Call completed successfully")
                        print(f"           → Duration: {call.duration} seconds")
                        break
                    elif current_status == 'failed':
                        print("           → ❌ Call failed")
                        break
                    elif current_status == 'busy':
                        print("           → ⚠️ Phone was busy")
                        break
                    elif current_status == 'no-answer':
                        print("           → ⚠️ No answer (phone rang but wasn't picked up)")
                        break
                    elif current_status == 'canceled':
                        print("           → 🚫 Call was canceled")
                        break
                    
                    previous_status = current_status
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"Error fetching call status: {e}")
                break
        
        # Final status
        print("\n" + "=" * 70)
        call = client.calls(call_sid).fetch()
        print(f"Final Status: {call.status.upper()}")
        
        if call.duration:
            print(f"Duration: {call.duration} seconds")
        
        if call.price:
            print(f"Cost: ${abs(float(call.price))} {call.price_unit}")
        
        # Get detailed info if failed
        if call.status in ['failed', 'busy', 'no-answer']:
            print("\n⚠️ Possible Reasons:")
            if call.status == 'failed':
                print("  - Network issues")
                print("  - Invalid phone number")
                print("  - Twilio account issue")
                print("  - Audio URL not accessible")
            elif call.status == 'busy':
                print("  - Phone was on another call")
                print("  - Call waiting disabled")
            elif call.status == 'no-answer':
                print("  - Phone rang but wasn't answered")
                print("  - Phone was in silent/DND mode")
                print("  - Poor signal strength")
        
        return call.status
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def check_last_call():
    """Check the status of the most recent call"""
    
    print("\n" + "=" * 70)
    print("CHECKING LAST EMERGENCY CALL")
    print("=" * 70)
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    your_number = os.getenv('EMERGENCY_POLICE_NUMBER')
    
    try:
        client = Client(account_sid, auth_token)
        
        # Get last call to your number
        calls = client.calls.list(to=your_number, limit=1)
        
        if not calls:
            print(f"\n❌ No calls found to {your_number}")
            return
        
        call = calls[0]
        
        print(f"\nLast Call Details:")
        print(f"  SID: {call.sid}")
        print(f"  To: {call.to}")
        print(f"  Status: {call.status}")
        print(f"  Direction: {call.direction}")
        print(f"  Start Time: {call.start_time}")
        
        if call.duration:
            print(f"  Duration: {call.duration} seconds")
        
        if call.status == 'completed':
            print("\n✅ Last call was successful!")
        elif call.status == 'no-answer':
            print("\n⚠️ Last call: Phone rang but wasn't answered")
        elif call.status == 'failed':
            print("\n❌ Last call failed")
        elif call.status == 'busy':
            print("\n⚠️ Last call: Phone was busy")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Monitor specific call SID
        call_sid = sys.argv[1]
        monitor_call_status(call_sid, duration=60)
    else:
        # Check last call
        check_last_call()
        
        print("\n💡 Usage:")
        print("  python monitor_call.py                    # Check last call")
        print("  python monitor_call.py CA123abc...        # Monitor specific call")
