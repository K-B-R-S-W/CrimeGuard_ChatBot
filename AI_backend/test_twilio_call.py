"""
Twilio Call Diagnostic Test
Tests if Twilio can make a call to your number
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twilio.rest import Client

def test_twilio_configuration():
    """Test Twilio configuration and credentials"""
    
    print("\n" + "="*70)
    print("TWILIO CONFIGURATION TEST")
    print("="*70 + "\n")
    
    # Check environment variables
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_PHONE_NUMBER')
    to_number = os.getenv('EMERGENCY_POLICE_NUMBER')
    
    print("Environment Variables:")
    print(f"  TWILIO_ACCOUNT_SID: {account_sid[:10]}... (masked)" if account_sid else "  TWILIO_ACCOUNT_SID: ❌ NOT SET")
    print(f"  TWILIO_AUTH_TOKEN: {auth_token[:10]}... (masked)" if auth_token else "  TWILIO_AUTH_TOKEN: ❌ NOT SET")
    print(f"  TWILIO_PHONE_NUMBER: {from_number}")
    print(f"  EMERGENCY_POLICE_NUMBER: {to_number}")
    print()
    
    if not account_sid or not auth_token:
        print("❌ Twilio credentials are missing!")
        return False
    
    try:
        # Initialize Twilio client
        print("Initializing Twilio client...")
        client = Client(account_sid, auth_token)
        print("✅ Client initialized successfully")
        print()
        
        # Fetch account info
        print("Fetching account information...")
        account = client.api.accounts(account_sid).fetch()
        print(f"✅ Account Status: {account.status}")
        print(f"   Account Type: {account.type}")
        print(f"   Friendly Name: {account.friendly_name}")
        print()
        
        # Check phone number
        print("Checking Twilio phone number...")
        incoming_numbers = client.incoming_phone_numbers.list(limit=10)
        
        if incoming_numbers:
            print(f"✅ Found {len(incoming_numbers)} phone number(s):")
            for number in incoming_numbers:
                print(f"   - {number.phone_number} ({number.friendly_name})")
                if number.phone_number == from_number:
                    print(f"     ✅ This is your configured number!")
        else:
            print("⚠️ No phone numbers found on this account")
        print()
        
        # Check verified numbers (for trial accounts)
        if account.type.lower() == 'trial':
            print("⚠️ This is a TRIAL account. Checking verified numbers...")
            try:
                verified_numbers = client.outgoing_caller_ids.list(limit=20)
                if verified_numbers:
                    print(f"✅ Found {len(verified_numbers)} verified number(s):")
                    for num in verified_numbers:
                        print(f"   - {num.phone_number} ({num.friendly_name})")
                        if num.phone_number == to_number:
                            print(f"     ✅ Your test number {to_number} is VERIFIED!")
                else:
                    print("❌ No verified numbers found!")
                    print("   You need to verify your number at: https://console.twilio.com/us1/develop/phone-numbers/manage/verified")
            except Exception as e:
                print(f"⚠️ Could not fetch verified numbers: {e}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_simple_call():
    """Test making a simple call"""
    
    print("\n" + "="*70)
    print("SIMPLE CALL TEST")
    print("="*70 + "\n")
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_PHONE_NUMBER')
    to_number = os.getenv('EMERGENCY_POLICE_NUMBER')
    
    print(f"From: {from_number}")
    print(f"To: {to_number}")
    print()
    
    try:
        client = Client(account_sid, auth_token)
        
        # Simple TwiML
        twiml = '''<Response>
    <Say voice="Polly.Aditi" language="en-IN">
        Hello! This is a test call from Crime Guard Chat Bot. 
        If you can hear this message, the Twilio integration is working correctly.
        This call will end in 3 seconds.
    </Say>
    <Pause length="3"/>
    <Hangup/>
</Response>'''
        
        print("Making test call...")
        print("TwiML:")
        print(twiml)
        print()
        
        call = client.calls.create(
            twiml=twiml,
            to=to_number,
            from_=from_number
        )
        
        print(f"✅ Call initiated successfully!")
        print(f"   Call SID: {call.sid}")
        print(f"   Status: {call.status}")
        print(f"   To: {call.to}")
        print(f"   From: {call.from_formatted}")
        print()
        print("📞 You should receive a call now!")
        print("   If you don't receive a call, check:")
        print("   1. Your number is verified in Twilio (for trial accounts)")
        print("   2. Your phone has good signal")
        print("   3. Check Twilio console for call logs")
        print()
        
        # Wait and check call status
        import time
        print("Waiting 10 seconds to check call status...")
        time.sleep(10)
        
        updated_call = client.calls(call.sid).fetch()
        print(f"Call Status Update: {updated_call.status}")
        print(f"Duration: {updated_call.duration} seconds")
        
        if updated_call.status in ['completed', 'in-progress']:
            print("✅ Call was successful!")
        elif updated_call.status == 'failed':
            print("❌ Call failed!")
        elif updated_call.status == 'busy':
            print("⚠️ Number was busy")
        elif updated_call.status == 'no-answer':
            print("⚠️ No answer")
        
        return True
        
    except Exception as e:
        print(f"❌ Call failed: {e}")
        print()
        print("Common issues:")
        print("1. Trial account: Number not verified")
        print("2. Invalid phone number format (should be +94779421552)")
        print("3. Insufficient Twilio balance")
        print("4. Number is not capable of receiving calls")
        return False

if __name__ == "__main__":
    print("\n🔧 Twilio Diagnostic Test\n")
    
    # Test configuration
    config_ok = test_twilio_configuration()
    
    if config_ok:
        # Ask user if they want to make a test call
        print("\n" + "="*70)
        response = input("\n⚠️  Do you want to make a TEST CALL to your number? (yes/no): ")
        
        if response.lower() in ['yes', 'y']:
            test_simple_call()
        else:
            print("\nTest call skipped.")
    
    print("\n✅ Diagnostic complete!\n")
