#!/usr/bin/env python3
"""
Direct Ngrok Call - Real speech recognition with your ngrok URL
Uses: https://59b6-2401-4900-1c66-9039-5c24-977c-347-d277.ngrok-free.app
"""

import os
import requests
import base64
from datetime import datetime

def make_speech_recognition_call():
    """Make a call with real speech recognition using ngrok URL"""
    
    print("🌐 REAL SPEECH RECOGNITION CALL")
    print("Using your ngrok URL: https://59b6-2401-4900-1c66-9039-5c24-977c-347-d277.ngrok-free.app")
    print("=" * 80)
    
    # Your ngrok URL
    ngrok_url = "https://59b6-2401-4900-1c66-9039-5c24-977c-347-d277.ngrok-free.app"
    
    # Phone number
    phone = "+918800000488"
    
    # Twilio credentials
    account_sid = "AC820daae89092e30fee3487e80162d2e2"
    auth_token = "690636dcdd752868f4e77648dc0d49eb"
    from_number = "+14323484517"
    
    # Webhook URLs using your ngrok tunnel
    voice_webhook = f"{ngrok_url}/webhook/voice"
    speech_webhook = f"{ngrok_url}/webhook/speech"
    status_webhook = f"{ngrok_url}/webhook/status"
    
    print(f"📞 Making call with REAL speech recognition:")
    print(f"   📱 From: {from_number}")
    print(f"   📞 To: {phone}")
    print(f"   🌐 Voice Webhook: {voice_webhook}")
    print(f"   🎤 Speech Webhook: {speech_webhook}")
    print(f"   📊 Status Webhook: {status_webhook}")
    print(f"   🧠 AI: Gemini-powered responses")
    
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
        print(f"\n🚀 INITIATING SPEECH RECOGNITION CALL...")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 201:
            call_data = response.json()
            print(f"✅ SPEECH RECOGNITION CALL STARTED!")
            print(f"🆔 Call SID: {call_data['sid']}")
            print(f"📊 Status: {call_data['status']}")
            
            print(f"\n🎭 WHAT WILL HAPPEN:")
            print(f"   1. 📞 Call will connect to {phone}")
            print(f"   2. 🎤 AI will introduce Bio Mac Lifesciences")
            print(f"   3. 🗣️ AI will ask for laboratory supplies pricing")
            print(f"   4. 🎧 When you speak, Twilio will recognize your speech")
            print(f"   5. 🧠 Gemini AI will understand and respond intelligently")
            print(f"   6. 💬 Natural conversation will continue")
            
            print(f"\n💡 SPEAK NATURALLY:")
            print(f"   • 'Petri dishes 45 rupees per piece hai sir'")
            print(f"   • 'Laboratory gloves 60 rupees main mil jayenge'")
            print(f"   • 'Bulk order hai to discount de sakte hain'")
            print(f"   • Mix Hindi and English naturally!")
            
            return call_data['sid']
            
        else:
            print(f"❌ CALL FAILED!")
            print(f"📊 Status Code: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    print("🎤 DIRECT SPEECH RECOGNITION TEST")
    print("🧠 Real-time AI conversation with Gemini")
    print("🌐 Using your ngrok tunnel")
    print("=" * 60)
    
    print(f"\n📋 SYSTEM CHECK:")
    print(f"   🌐 Ngrok URL: ✅ https://59b6-2401-4900-1c66-9039-5c24-977c-347-d277.ngrok-free.app")
    print(f"   📞 Phone: ✅ +918800000488")
    print(f"   🔧 Twilio: ✅ Configured")
    print(f"   🧠 Gemini AI: ✅ Ready")
    
    confirm = input(f"\n🚀 Start real speech recognition call? (y/N): ").strip().lower()
    
    if confirm == 'y':
        result = make_speech_recognition_call()
        
        if result:
            print(f"\n🎉 SUCCESS! REAL SPEECH RECOGNITION ACTIVE!")
            print(f"📞 Call SID: {result}")
            print(f"🎤 Answer the call and speak naturally")
            print(f"🧠 AI will understand and respond intelligently")
            print(f"📊 Check your ngrok terminal for webhook activity")
        else:
            print(f"\n❌ Call failed")
    else:
        print(f"📞 Call cancelled")

if __name__ == "__main__":
    main() 