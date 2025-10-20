"""
Make a test call and monitor it in real-time
"""
import sys
import os
from dotenv import load_dotenv
import time
from datetime import datetime

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twilio.rest import Client

def make_test_call_with_monitoring():
    """Make a test call and monitor it"""
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_PHONE_NUMBER')
    to_number = os.getenv('EMERGENCY_POLICE_NUMBER')
    
    print("\n" + "="*70)
    print("MAKING TEST CALL WITH REAL-TIME MONITORING")
    print("="*70)
    
    print(f"\nFrom: {from_number}")
    print(f"To: {to_number}")
    print()
    
    # Simple test message
    test_message = "Hello! This is a test call. If you can hear this message, everything is working correctly."
    
    twiml = f'''<Response>
    <Say voice="Polly.Aditi" language="en-IN">
        {test_message}
    </Say>
    <Pause length="2"/>
    <Say voice="Polly.Aditi" language="en-IN">
        This call will now end. Thank you.
    </Say>
    <Hangup/>
</Response>'''
    
    try:
        client = Client(account_sid, auth_token)
        
        print("🚀 Initiating call...")
        print("📱 GET READY TO ANSWER YOUR PHONE!")
        print()
        
        # Make the call
        call = client.calls.create(
            twiml=twiml,
            to=to_number,
            from_=from_number
        )
        
        print(f"✅ Call initiated!")
        print(f"   Call SID: {call.sid}")
        print()
        
        # Monitor in real-time
        print("📊 Real-time Status:")
        print("-" * 70)
        
        previous_status = None
        start_time = time.time()
        max_duration = 60  # Monitor for 60 seconds
        
        while time.time() - start_time < max_duration:
            try:
                call_status = client.calls(call.sid).fetch()
                current_status = call_status.status
                
                if current_status != previous_status:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    if current_status == 'queued':
                        print(f"[{timestamp}] ⏳ QUEUED - Call is waiting to be processed")
                    elif current_status == 'initiated':
                        print(f"[{timestamp}] 🔄 INITIATED - Call is being set up")
                    elif current_status == 'ringing':
                        print(f"[{timestamp}] 📞 RINGING - YOUR PHONE SHOULD BE RINGING NOW!")
                        print(f"            🎯 ANSWER YOUR PHONE TO HEAR THE MESSAGE!")
                    elif current_status == 'in-progress':
                        print(f"[{timestamp}] ✅ IN-PROGRESS - Call connected! You answered!")
                        print(f"            🔊 You should be hearing the message now...")
                    elif current_status == 'completed':
                        print(f"[{timestamp}] ✅ COMPLETED - Call finished")
                        print(f"            Duration: {call_status.duration} seconds")
                        
                        if call_status.duration and int(call_status.duration) < 5:
                            print(f"            ⚠️ Very short duration - might have gone to voicemail")
                        elif call_status.duration and int(call_status.duration) > 10:
                            print(f"            ✅ Good duration - likely you heard the message!")
                        break
                    elif current_status == 'failed':
                        print(f"[{timestamp}] ❌ FAILED - Call failed to connect")
                        break
                    elif current_status == 'busy':
                        print(f"[{timestamp}] ⚠️ BUSY - Phone was busy")
                        break
                    elif current_status == 'no-answer':
                        print(f"[{timestamp}] ⚠️ NO ANSWER - Phone rang but wasn't answered")
                        break
                    elif current_status == 'canceled':
                        print(f"[{timestamp}] 🚫 CANCELED - Call was canceled")
                        break
                    
                    previous_status = current_status
                
                time.sleep(0.5)  # Check every 500ms
                
            except KeyboardInterrupt:
                print("\n\n⚠️ Monitoring interrupted by user")
                break
            except Exception as e:
                print(f"Error: {e}")
                break
        
        print("-" * 70)
        print()
        
        # Final summary
        final_call = client.calls(call.sid).fetch()
        print("📋 FINAL SUMMARY:")
        print(f"   Status: {final_call.status}")
        print(f"   Duration: {final_call.duration} seconds" if final_call.duration else "   Duration: N/A")
        
        if final_call.status == 'completed':
            if final_call.duration and int(final_call.duration) < 8:
                print("\n⚠️ ANALYSIS:")
                print("   Duration is very short (< 8 seconds)")
                print("   This suggests the call went to VOICEMAIL")
                print("   Check your voicemail to confirm!")
            else:
                print("\n✅ ANALYSIS:")
                print("   Duration suggests you likely answered and heard the message!")
                print("   Did you hear the test message?")
        
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("\n⚠️  IMPORTANT: Be ready to answer your phone!")
    print("   The call will be made in 3 seconds...\n")
    time.sleep(3)
    
    make_test_call_with_monitoring()
