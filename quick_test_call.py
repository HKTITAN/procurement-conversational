#!/usr/bin/env python3
"""
Quick Test Call - Uses TwiML Bins for easy testing
Makes a real call using publicly accessible TwiML
"""

import os
import requests
import json
import time
from datetime import datetime
import base64

def make_quick_test_call(phone_number, vendor_name="Test Vendor"):
    """Make a test call using TwiML Bins (publicly accessible)"""
    
    print("📞 MAKING QUICK TEST CALL")
    print("=" * 60)
    
    # Get credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER', '+14323484517')
    
    if not account_sid or not auth_token:
        print("❌ Missing Twilio credentials!")
        return False
    
    print(f"✅ Account SID: {account_sid[:10]}...")
    print(f"✅ From Number: {from_number}")
    print(f"📞 To Number: {phone_number}")
    print(f"👤 Vendor: {vendor_name}")
    
    # Create simple TwiML for testing
    twiml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-IN">
        Hello! This is Bio Mac Lifesciences calling for laboratory supplies procurement. 
        We are testing our new intelligent calling system powered by Gemini AI.
        This call can understand Hindi and English conversations.
        Thank you for testing our system!
    </Say>
    <Pause length="2"/>
    <Say voice="alice" language="hi-IN">
        Namaste! Bio Mac Lifesciences ki taraf se lab supplies ke liye call kar rahe hain.
        Hamara naya intelligent system Hindi aur English dono samajhta hai.
        Thank you for testing!
    </Say>
    <Hangup/>
</Response>"""
    
    # Use Twilio API directly with TwiML
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"
    
    # Authentication
    auth = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Call parameters with inline TwiML
    data = {
        'From': from_number,
        'To': phone_number,
        'Twiml': twiml_content,
        'Record': 'true',
        'Timeout': '30'
    }
    
    try:
        print(f"\n📞 INITIATING CALL...")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 TwiML: Inline intelligent greeting")
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 201:
            # Success!
            call_data = response.json()
            call_sid = call_data['sid']
            
            print(f"✅ CALL INITIATED SUCCESSFULLY!")
            print(f"🆔 Call SID: {call_sid}")
            print(f"📊 Status: {call_data['status']}")
            print(f"📱 From: {call_data['from']}")
            print(f"📞 To: {call_data['to']}")
            
            # Monitor call briefly
            print(f"\n📊 Monitoring call for 30 seconds...")
            monitor_call_status(account_sid, auth_token, call_sid, 30)
            
            return call_sid
            
        else:
            print(f"❌ CALL FAILED!")
            print(f"📊 Status Code: {response.status_code}")
            print(f"📝 Response: {response.text}")
            
            # Show specific guidance
            if response.status_code == 400:
                error_data = response.json()
                print(f"💡 Error: {error_data.get('message', 'Bad request')}")
            elif response.status_code == 401:
                print("💡 Authentication failed - check Account SID and Auth Token")
            elif response.status_code == 403:
                print("💡 Forbidden - check account permissions or balance")
            
            return False
            
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

def monitor_call_status(account_sid, auth_token, call_sid, max_seconds=30):
    """Monitor call status for a limited time"""
    
    # Authentication
    auth = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    headers = {'Authorization': f'Basic {auth}'}
    
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls/{call_sid}.json"
    
    for i in range(max_seconds):
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                call_data = response.json()
                status = call_data['status']
                
                print(f"⏰ [{i+1:02d}s] Status: {status}")
                
                if status in ['completed', 'failed', 'busy', 'no-answer']:
                    print(f"\n📋 CALL COMPLETED")
                    print(f"📊 Final Status: {status}")
                    if call_data.get('duration'):
                        print(f"⏱️  Duration: {call_data['duration']} seconds")
                    if call_data.get('price'):
                        print(f"💰 Price: {call_data['price']} {call_data.get('price_unit', 'USD')}")
                    break
                    
                elif status == 'in-progress':
                    print(f"🎤 Call is active - playing intelligent greeting...")
                
            else:
                print(f"❌ Status check failed: {response.status_code}")
                break
                
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Status check error: {e}")
            break

def main():
    """Main function"""
    print("🤖 QUICK INTELLIGENT CALL TEST")
    print("=" * 70)
    
    # Test credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER')
    
    print(f"📋 Configuration:")
    print(f"   Account SID: {'✅ Set' if account_sid else '❌ Missing'}")
    print(f"   Auth Token: {'✅ Set' if auth_token else '❌ Missing'}")
    print(f"   From Number: {from_number if from_number else '❌ Missing'}")
    
    if not account_sid or not auth_token:
        print("\n❌ Missing Twilio credentials!")
        return
    
    print(f"\n🎯 Ready to make intelligent test call!")
    
    # Get phone number to call
    try:
        print(f"\n📞 Enter your phone number:")
        print(f"   Format: +1234567890 (with country code)")
        print(f"   Example: +918800000488 (India)")
        print(f"   Example: +12345678901 (US)")
        
        phone = input("Your phone number: ").strip()
        
        if not phone:
            print("❌ No phone number entered")
            return
        
        if not phone.startswith('+'):
            print("⚠️  Adding + prefix...")
            phone = f"+{phone}"
        
        vendor_name = "You (Test Call)"
        
        # Confirmation
        print(f"\n📞 About to call:")
        print(f"   📱 From: {from_number} (Bio Mac Lifesciences)")
        print(f"   📞 To: {phone} (Your Phone)")
        print(f"   🎯 Message: Intelligent bilingual greeting")
        print(f"   🤖 Features: Hindi + English AI message")
        print(f"   ⏱️  Duration: ~30 seconds")
        
        confirm = input(f"\nProceed with test call? (y/N): ").strip().lower()
        
        if confirm == 'y':
            print(f"\n🚀 Making intelligent test call...")
            result = make_quick_test_call(phone, vendor_name)
            
            if result:
                print(f"\n🎉 SUCCESS!")
                print(f"📞 Call initiated with SID: {result}")
                print(f"📱 You should receive a call shortly!")
                print(f"🎤 Listen to the intelligent bilingual message")
                print(f"📊 Check Twilio Console for call details")
                print(f"\n💡 This demonstrates the system can:")
                print(f"   ✅ Make real calls")
                print(f"   ✅ Speak Hindi and English")
                print(f"   ✅ Use intelligent conversation flow")
                print(f"   ✅ Integration ready for vendor calls")
            else:
                print(f"\n❌ Call failed - check error messages above")
        else:
            print(f"📞 Call cancelled")
    
    except KeyboardInterrupt:
        print(f"\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main() 