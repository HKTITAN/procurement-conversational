#!/usr/bin/env python3
"""
Ngrok-enabled Call Script
Use this after setting up ngrok tunnel
"""

import os
import requests
import base64
import sys

def make_ngrok_call():
    """Make a call using ngrok webhook URL"""
    
    # Get ngrok URL from user
    print("🌐 NGROK SPEECH RECOGNITION CALL")
    print("=" * 40)
    print("1. Start: python interactive_vendor_call.py")
    print("2. Start: ngrok http 5000")
    print("3. Copy the ngrok URL (e.g., https://abc123.ngrok.io)")
    print()
    
    ngrok_url = input("Enter your ngrok URL: ").strip()
    if not ngrok_url:
        print("❌ Need ngrok URL!")
        return
    
    if not ngrok_url.startswith('http'):
        ngrok_url = f"https://{ngrok_url}"
    
    if ngrok_url.endswith('/'):
        ngrok_url = ngrok_url[:-1]
    
    phone = input("Phone number (+918800000488): ").strip()
    if not phone:
        phone = "+918800000488"
    
    # Twilio credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER', '+14323484517')
    
    if not account_sid or not auth_token:
        print("❌ Missing Twilio credentials!")
        return
    
    # Webhook URLs using ngrok
    voice_webhook = f"{ngrok_url}/webhook/voice"
    speech_webhook = f"{ngrok_url}/webhook/speech"
    status_webhook = f"{ngrok_url}/webhook/status"
    
    print(f"📞 Making call with speech recognition:")
    print(f"   Voice Webhook: {voice_webhook}")
    print(f"   Speech Webhook: {speech_webhook}")
    print(f"   Phone: {phone}")
    
    # Make the call
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"
    auth = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'From': from_number,
        'To': phone,
        'Url': voice_webhook,
        'Method': 'POST',
        'StatusCallback': status_webhook,
        'StatusCallbackEvent': ['initiated', 'ringing', 'answered', 'completed'],
        'StatusCallbackMethod': 'POST',
        'Record': 'true',
        'Timeout': '30'
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 201:
            call_data = response.json()
            print(f"✅ SPEECH RECOGNITION CALL STARTED!")
            print(f"🆔 Call SID: {call_data['sid']}")
            print(f"🎤 Speak when prompted - AI will understand and respond!")
        else:
            print(f"❌ Call failed: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    make_ngrok_call()
