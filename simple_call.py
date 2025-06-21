#!/usr/bin/env python3
"""
Simple Twilio call script for Likwid.AI Procurement Automation
Makes a direct call without complex dependencies
"""

import json
import sys
from datetime import datetime

# Twilio configuration
TWILIO_ACCOUNT_SID = "AC820daae89092e30fee3487e80162d2e2"
TWILIO_AUTH_TOKEN = "690636dcdd752868f4e77648dc0d49eb"
TWILIO_PHONE_NUMBER = "+14323484517"

# Vendor details
VENDOR_NAME = "Harshit Khemani"
VENDOR_PHONE = "+918800000488"
CLIENT_NAME = "Bio Mac Lifesciences"

# Your ngrok webhook URL
WEBHOOK_BASE_URL = "https://543a-2401-4900-1c30-31b1-c11a-e61b-78b3-ce01.ngrok-free.app"

def make_simple_call():
    """Make a simple call using requests library instead of Twilio SDK"""
    import requests
    from requests.auth import HTTPBasicAuth
    
    print("📞 Making REAL call to Harshit Khemani...")
    print(f"   From: {TWILIO_PHONE_NUMBER}")
    print(f"   To: {VENDOR_PHONE}")
    print(f"   Webhook: {WEBHOOK_BASE_URL}")
    print()
    
    # Twilio API endpoint
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Calls.json"
    
    # Call parameters
    data = {
        'From': TWILIO_PHONE_NUMBER,
        'To': VENDOR_PHONE,
        'Url': f"{WEBHOOK_BASE_URL}/webhook/voice",
        'Method': 'POST',
        'StatusCallback': f"{WEBHOOK_BASE_URL}/webhook/status",
        'StatusCallbackMethod': 'POST'
    }
    
    # Make the API call
    try:
        auth = HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        response = requests.post(url, data=data, auth=auth, timeout=30)
        
        if response.status_code == 201:
            call_data = response.json()
            call_sid = call_data.get('sid')
            
            print("✅ Call initiated successfully!")
            print(f"   Call SID: {call_sid}")
            print(f"   Status: {call_data.get('status')}")
            print(f"   Duration: {call_data.get('duration')} seconds")
            print()
            print("📱 The call is now connecting to Harshit Khemani...")
            print("🤖 AI will start conversation about procurement items")
            print("💾 Quotes will be logged via webhooks")
            print()
            print("ℹ️  You can monitor the call status in your Twilio Console:")
            print(f"   https://console.twilio.com/us1/develop/phone-numbers/manage/calls/{call_sid}")
            
            return True
            
        else:
            print(f"❌ Call failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error making call: {e}")
        return False

def create_twiml_response():
    """Create TwiML response for handling the call"""
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">
        Hi, this is an AI assistant calling on behalf of {CLIENT_NAME}. 
        I'm reaching out to get quotes for some laboratory supplies we need to order. 
        Is this a good time to discuss pricing for a few items?
    </Say>
    <Gather input="speech" timeout="10" speechTimeout="5" action="{WEBHOOK_BASE_URL}/webhook/gather" method="POST">
        <Say voice="alice">Please let me know if you're available to provide quotes.</Say>
    </Gather>
    <Say voice="alice">Thank you for your time. We'll call back later.</Say>
</Response>"""
    
    print("\n📋 TwiML Response Template Created:")
    print("   This will be used to handle the voice conversation")
    print("   The AI will introduce itself and ask for quotes")
    
    return twiml

def main():
    print("🚀 LIKWID.AI PROCUREMENT AUTOMATION - DIRECT CALL")
    print("="*60)
    print(f"Client: {CLIENT_NAME}")
    print(f"Vendor: {VENDOR_NAME}")
    print(f"Phone: {VENDOR_PHONE}")
    print(f"Webhook Base: {WEBHOOK_BASE_URL}")
    print("="*60)
    
    # Confirm with user
    confirm = input("\n⚠️  This will make a REAL phone call. Continue? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Call cancelled by user")
        return False
    
    # Create TwiML response
    twiml = create_twiml_response()
    
    # Make the call
    success = make_simple_call()
    
    if success:
        print("\n" + "="*60)
        print("🎉 CALL PROCESS COMPLETED!")
        print()
        print("📞 What happens next:")
        print("1. Harshit will receive the call")
        print("2. AI will introduce Bio Mac Lifesciences")  
        print("3. Conversation about lab supply quotes will begin")
        print("4. Responses will be processed via webhooks")
        print("5. Check your Twilio Console for call logs")
        print()
        print("💡 Webhook endpoints that will handle responses:")
        print(f"   • {WEBHOOK_BASE_URL}/webhook/voice")
        print(f"   • {WEBHOOK_BASE_URL}/webhook/gather")
        print(f"   • {WEBHOOK_BASE_URL}/webhook/status")
        print("="*60)
    
    return success

if __name__ == "__main__":
    try:
        # Check if requests is available
        import requests
        main()
    except ImportError:
        print("❌ 'requests' library not found")
        print("Please install it: pip install requests")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(1) 