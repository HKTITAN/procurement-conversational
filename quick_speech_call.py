#!/usr/bin/env python3
"""
Quick Speech Recognition Call
Makes a call with your ngrok URL for speech recognition
"""

import requests
import base64
from datetime import datetime

def make_quick_speech_call():
    """Make a quick call with speech recognition"""
    
    print("🎤 QUICK SPEECH RECOGNITION CALL")
    print("=" * 50)
    
    # Your details
    ngrok_url = "https://59b6-2401-4900-1c66-9039-5c24-977c-347-d277.ngrok-free.app"
    phone = "+918800000488"
    account_sid = "AC820daae89092e30fee3487e80162d2e2"
    auth_token = "690636dcdd752868f4e77648dc0d49eb"
    from_number = "+14323484517"
    
    # Create simple TwiML for speech recognition
    twiml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">
        Namaste! Main Bio Mac Lifesciences se bol raha hun. 
        Hum laboratory supplies ki company hain.
        Humein petri dishes, gloves aur slides chahiye.
        Aapka rate kya hai?
    </Say>
    
    <Pause length="2"/>
    
    <Gather input="speech" 
            language="hi-IN" 
            speechTimeout="5" 
            timeout="10"
            action="{ngrok_url}/webhook/speech"
            method="POST">
        <Say voice="Polly.Aditi" language="hi-IN">
            Please bataiye aapka pricing. Main sun raha hun.
        </Say>
    </Gather>
    
    <Say voice="Polly.Aditi" language="hi-IN">
        Dhanyawad! Main aapko call back karunga.
    </Say>
    <Hangup/>
</Response>"""
    
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
        'Twiml': twiml_content,
        'Record': 'true',
        'Timeout': '30'
    }
    
    try:
        print(f"📞 Calling {phone} with speech recognition...")
        print(f"🌐 Speech webhook: {ngrok_url}/webhook/speech")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 201:
            call_data = response.json()
            print(f"✅ CALL STARTED!")
            print(f"🆔 Call SID: {call_data['sid']}")
            print(f"📊 Status: {call_data['status']}")
            
            print(f"\n🎤 WHEN YOU SPEAK:")
            print(f"   • Twilio will capture your speech")
            print(f"   • Send it to: {ngrok_url}/webhook/speech")
            print(f"   • Your webhook server will process it")
            print(f"   • If no server running, you'll get application error")
            
            print(f"\n💡 TO FIX APPLICATION ERROR:")
            print(f"   1. Start webhook server: python start_speech_server.py")
            print(f"   2. Make sure ngrok is running: ngrok http 5000")
            print(f"   3. Webhook endpoints should be accessible")
            
            return call_data['sid']
            
        else:
            print(f"❌ CALL FAILED!")
            print(f"📊 Status Code: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    make_quick_speech_call() 