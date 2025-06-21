#!/usr/bin/env python3
"""
Make Real Call - Using Twilio with Gemini Intelligence
Makes actual phone calls with AI-powered conversation
"""

import os
import json
import time
from datetime import datetime

# Import Twilio (install with: pip install twilio==9.6.0)
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    print("❌ Twilio not installed. Installing...")
    import subprocess
    subprocess.run(["pip", "install", "twilio==9.6.0", "--force-reinstall"], check=True)
    from twilio.rest import Client
    TWILIO_AVAILABLE = True

def make_real_intelligent_call(phone_number, vendor_name="Test Vendor"):
    """Make a real call using Twilio + Gemini intelligence"""
    
    print("📞 MAKING REAL INTELLIGENT CALL")
    print("=" * 60)
    
    # Get Twilio credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER', '+14323484517')
    
    if not account_sid or not auth_token:
        print("❌ Twilio credentials not found!")
        print("💡 Please set environment variables:")
        print("   $env:TWILIO_ACCOUNT_SID='your_sid'")
        print("   $env:TWILIO_AUTH_TOKEN='your_token'")
        print("   $env:TWILIO_FROM_NUMBER='+14323484517'")
        return False
    
    print(f"✅ Twilio credentials configured")
    print(f"📱 From: {from_number}")
    print(f"📞 To: {phone_number} ({vendor_name})")
    
    # Initialize Twilio client
    try:
        client = Client(account_sid, auth_token)
        print(f"✅ Twilio client initialized")
    except Exception as e:
        print(f"❌ Twilio initialization failed: {e}")
        return False
    
    # Webhook URL (your server)
    webhook_url = os.getenv('WEBHOOK_URL', 'http://localhost:5000')
    voice_webhook = f"{webhook_url}/webhook/voice"
    status_webhook = f"{webhook_url}/webhook/status"
    
    print(f"🌐 Voice webhook: {voice_webhook}")
    print(f"📊 Status webhook: {status_webhook}")
    
    # Make the call
    try:
        print(f"\n📞 INITIATING CALL...")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        call = client.calls.create(
            url=voice_webhook,
            to=phone_number,
            from_=from_number,
            status_callback=status_webhook,
            status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
            status_callback_method='POST',
            record=True,  # Record for analysis
            timeout=30,   # Ring for 30 seconds
            machine_detection='Enable'  # Detect answering machines
        )
        
        print(f"✅ CALL INITIATED SUCCESSFULLY!")
        print(f"🆔 Call SID: {call.sid}")
        print(f"📊 Initial Status: {call.status}")
        print(f"📱 From: {call.from_}")
        print(f"📞 To: {call.to}")
        
        # Monitor call status
        print(f"\n📊 MONITORING CALL STATUS...")
        for i in range(60):  # Monitor for 1 minute
            try:
                updated_call = client.calls(call.sid).fetch()
                current_status = updated_call.status
                
                print(f"⏰ [{i+1:02d}s] Status: {current_status}")
                
                if current_status in ['completed', 'failed', 'busy', 'no-answer']:
                    print(f"\n📋 CALL COMPLETED")
                    print(f"📊 Final Status: {current_status}")
                    print(f"⏱️  Duration: {updated_call.duration} seconds")
                    print(f"💰 Price: {updated_call.price} {updated_call.price_unit}")
                    break
                    
                elif current_status == 'in-progress':
                    print(f"🎤 Call is active - conversation in progress...")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Status check failed: {e}")
                break
        
        # Show call details
        print(f"\n📋 CALL DETAILS:")
        print(f"   🆔 SID: {call.sid}")
        print(f"   📞 Direction: Outbound")
        print(f"   📱 From: {from_number}")
        print(f"   📞 To: {phone_number}")
        print(f"   🎯 Purpose: Laboratory supplies procurement")
        print(f"   🤖 AI: Gemini-enhanced conversation")
        
        return call.sid
        
    except Exception as e:
        print(f"❌ CALL FAILED: {e}")
        
        # Show specific error guidance
        if "authentication" in str(e).lower():
            print("💡 Authentication error - check your Twilio credentials")
        elif "phone number" in str(e).lower():
            print("💡 Phone number error - check format (+1234567890)")
        elif "balance" in str(e).lower():
            print("💡 Insufficient balance - add funds to Twilio account")
        elif "webhook" in str(e).lower():
            print("💡 Webhook error - make sure your server is running")
        
        return False

def test_twilio_setup():
    """Test Twilio configuration"""
    print("🧪 TESTING TWILIO SETUP")
    print("=" * 40)
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER')
    
    print(f"📋 Configuration:")
    print(f"   Account SID: {'✅ Set' if account_sid else '❌ Missing'}")
    print(f"   Auth Token: {'✅ Set' if auth_token else '❌ Missing'}")
    print(f"   From Number: {from_number if from_number else '❌ Missing'}")
    
    if not account_sid or not auth_token:
        return False
    
    try:
        client = Client(account_sid, auth_token)
        
        # Test account details
        account = client.api.accounts(account_sid).fetch()
        print(f"✅ Account verified: {account.friendly_name}")
        
        # Test phone number
        if from_number:
            try:
                phone_number = client.incoming_phone_numbers.list(
                    phone_number=from_number
                )[0]
                print(f"✅ Phone number verified: {phone_number.friendly_name}")
            except:
                print(f"⚠️  Phone number not found in account")
        
        return True
        
    except Exception as e:
        print(f"❌ Twilio test failed: {e}")
        return False

def main():
    """Main function"""
    print("🤖 REAL INTELLIGENT CALLING SYSTEM")
    print("=" * 70)
    
    # Test setup first
    if not test_twilio_setup():
        print("\n❌ Setup failed. Please configure Twilio credentials.")
        return
    
    print(f"\n🎯 READY TO MAKE REAL CALLS!")
    
    # Default test numbers (you can modify these)
    test_calls = [
        {
            "name": "Your Phone (Test Call)",
            "phone": "+1234567890",  # Replace with your phone number
            "description": "Test call to verify system"
        },
        # Add real vendor numbers here
        # {
        #     "name": "ABC Medical Supplies", 
        #     "phone": "+91-9876543210",
        #     "description": "Procurement call for lab supplies"
        # }
    ]
    
    print(f"\n📞 AVAILABLE CALLS:")
    for i, call_info in enumerate(test_calls):
        print(f"   {i+1}. {call_info['name']} ({call_info['phone']})")
        print(f"      {call_info['description']}")
    
    try:
        choice = input(f"\nSelect call to make (1-{len(test_calls)}) or enter phone number: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(test_calls):
            # Selected from list
            selected = test_calls[int(choice)-1]
            phone = selected['phone']
            name = selected['name']
        elif choice.startswith('+') or choice.isdigit():
            # Manual phone number entry
            phone = choice if choice.startswith('+') else f"+{choice}"
            name = input("Enter vendor name (optional): ").strip() or "Unknown Vendor"
        else:
            print("❌ Invalid selection")
            return
        
        # Confirmation
        print(f"\n📞 About to call:")
        print(f"   Name: {name}")
        print(f"   Phone: {phone}")
        print(f"   Purpose: Laboratory supplies procurement")
        print(f"   AI: Gemini-enhanced conversation")
        
        confirm = input(f"\nProceed with call? (y/N): ").strip().lower()
        
        if confirm == 'y':
            result = make_real_intelligent_call(phone, name)
            
            if result:
                print(f"\n🎉 SUCCESS! Call initiated with SID: {result}")
                print(f"💡 Check your webhook server logs for conversation details")
                print(f"📊 Monitor call status in Twilio Console")
            else:
                print(f"\n❌ Call failed. Check error messages above.")
        else:
            print(f"📞 Call cancelled")
    
    except KeyboardInterrupt:
        print(f"\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main() 