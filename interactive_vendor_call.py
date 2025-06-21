#!/usr/bin/env python3
"""
Interactive Vendor Call - Real conversation with Gemini AI
Handles speech recognition and responds intelligently to vendor responses
"""

import os
import requests
import json
import time
from datetime import datetime
import base64
import threading
from flask import Flask, request, Response
import google.generativeai as genai

# Initialize Flask app for webhook handling
app = Flask(__name__)

# Configure Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash-8b')
        print("✅ Gemini AI initialized")
    except:
        model = None
        print("⚠️ Gemini AI not available")
else:
    model = None
    print("⚠️ GEMINI_API_KEY not set")

# Global conversation state
conversation_log = []
current_call_sid = None

def generate_intelligent_response(vendor_speech, context="procurement"):
    """Use Gemini to generate intelligent response to vendor speech"""
    if not model:
        return "Samjha sir, dhanyawad!"
    
    try:
        prompt = f"""
        You are Bio Mac Lifesciences calling a vendor for laboratory supplies. 
        The vendor just said: "{vendor_speech}"
        
        Generate a natural Hindi-English response that:
        1. Acknowledges what they said
        2. Asks for specific pricing if they mentioned items
        3. Follows up on business details
        4. Keeps the conversation professional but friendly
        5. Uses natural Indian business language (Hinglish)
        
        Respond in 1-2 sentences maximum, as if speaking on phone.
        """
        
        response = model.generate_content(prompt)
        ai_response = response.text.strip()
        
        # Log the conversation
        conversation_log.append({
            "vendor_said": vendor_speech,
            "ai_response": ai_response,
            "timestamp": datetime.now().isoformat()
        })
        
        return ai_response
        
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return "Haan sir, samjha. Aur kuch bataiye?"

@app.route('/webhook/speech', methods=['POST'])
def handle_speech():
    """Handle speech recognition results from Twilio"""
    global current_call_sid
    
    # Get speech recognition results
    speech_result = request.form.get('SpeechResult', '')
    confidence = request.form.get('Confidence', '0')
    call_sid = request.form.get('CallSid', '')
    
    print(f"\n🎤 VENDOR SPOKE:")
    print(f"   Speech: '{speech_result}'")
    print(f"   Confidence: {confidence}")
    print(f"   Call SID: {call_sid}")
    
    if speech_result:
        # Generate intelligent response using Gemini
        ai_response = generate_intelligent_response(speech_result)
        print(f"🧠 AI Response: '{ai_response}'")
        
        # Create TwiML response
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">{ai_response}</Say>
    <Pause length="1"/>
    
    <!-- Ask for more information -->
    <Gather input="speech" 
            language="hi-IN" 
            speechTimeout="5" 
            timeout="8"
            action="/webhook/speech"
            method="POST">
        <Say voice="Polly.Aditi" language="hi-IN">
            Aur kuch bataiye? Koi aur items hai?
        </Say>
    </Gather>
    
    <!-- Final closing -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Theek hai sir, main notes le liya hun. Main aapko email bhejunga details ke saath. 
        Dhanyawad aur namaste!
    </Say>
    <Hangup/>
</Response>"""
    else:
        # No speech detected
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">
        Koi baat nahi sir, ho sakta hai line clear nahi tha. 
        Main phir se call karunga. Dhanyawad!
    </Say>
    <Hangup/>
</Response>"""
    
    return Response(twiml_response, mimetype='text/xml')

@app.route('/webhook/voice', methods=['POST'])
def handle_voice():
    """Initial voice webhook - start the conversation"""
    global current_call_sid
    current_call_sid = request.form.get('CallSid', '')
    
    print(f"\n📞 NEW VENDOR CALL INITIATED")
    print(f"   Call SID: {current_call_sid}")
    
    twiml_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <!-- Initial greeting -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Namaste! Main Bio Mac Lifesciences se bol raha hun. 
        Hum laboratory supplies ki company hain.
    </Say>
    
    <Pause length="1"/>
    
    <!-- Business introduction -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Humein kuch laboratory items ki urgent requirement hai. 
        Petri dishes, laboratory gloves, aur microscope slides chahiye.
        Aapka rate kya hai in items ka?
    </Say>
    
    <Pause length="1"/>
    
    <!-- First speech recognition -->
    <Gather input="speech" 
            language="hi-IN" 
            speechTimeout="5" 
            timeout="10"
            action="/webhook/speech"
            method="POST">
        <Say voice="Polly.Aditi" language="hi-IN">
            Please bataiye aapka pricing. Main sun raha hun.
        </Say>
    </Gather>
    
    <!-- Fallback if no response -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Lagta hai connection problem hai. Main phir se call karunga. Namaste!
    </Say>
    <Hangup/>
</Response>"""
    
    return Response(twiml_response, mimetype='text/xml')

@app.route('/webhook/status', methods=['POST'])
def handle_status():
    """Handle call status updates"""
    call_status = request.form.get('CallStatus', '')
    call_sid = request.form.get('CallSid', '')
    
    print(f"📊 Call {call_sid}: {call_status}")
    return "OK"

@app.route('/health')
def health():
    """Health check endpoint"""
    return {"status": "healthy", "gemini": "configured" if model else "not configured"}

@app.route('/conversation')
def show_conversation():
    """Show conversation log"""
    return {"conversation_log": conversation_log}

def start_webhook_server():
    """Start the webhook server in background"""
    app.run(host='0.0.0.0', port=5000, debug=False)

def make_interactive_call(phone_number="+918800000488", vendor_name="ABC Medical Supplies"):
    """Make an interactive call with real speech recognition"""
    
    print("📞 MAKING INTERACTIVE VENDOR CALL")
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
    print(f"🏢 Vendor: {vendor_name}")
    print(f"🧠 AI: {'Gemini Ready' if model else 'Fallback Mode'}")
    
    # Use webhook server for real interaction
    webhook_url = "http://localhost:5000/webhook/voice"
    
    # Twilio API call
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"
    
    # Authentication
    auth = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Call parameters
    data = {
        'From': from_number,
        'To': phone_number,
        'Url': webhook_url,
        'Method': 'POST',
        'StatusCallback': 'http://localhost:5000/webhook/status',
        'StatusCallbackEvent': ['initiated', 'ringing', 'answered', 'completed'],
        'StatusCallbackMethod': 'POST',
        'Record': 'true',
        'Timeout': '30',
        'MachineDetection': 'Enable'
    }
    
    try:
        print(f"\n📞 INITIATING INTERACTIVE CALL...")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Webhook: {webhook_url}")
        print(f"🎤 Features: Real-time speech recognition + Gemini AI")
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 201:
            call_data = response.json()
            call_sid = call_data['sid']
            
            print(f"✅ INTERACTIVE CALL INITIATED!")
            print(f"🆔 Call SID: {call_sid}")
            print(f"📊 Status: {call_data['status']}")
            
            print(f"\n🎭 CONVERSATION WILL BE:")
            print(f"   1. AI introduces Bio Mac Lifesciences")
            print(f"   2. Asks for laboratory supplies pricing")
            print(f"   3. Listens to your response with speech recognition")
            print(f"   4. Gemini AI generates intelligent follow-up")
            print(f"   5. Continues natural conversation")
            
            return call_sid
            
        else:
            print(f"❌ CALL FAILED!")
            print(f"📊 Status Code: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

def main():
    """Main function"""
    print("🤖 INTERACTIVE VENDOR CALLING SYSTEM")
    print("🧠 Powered by Gemini AI + Twilio Speech Recognition")
    print("=" * 70)
    
    # Check if webhook server is running
    try:
        response = requests.get("http://localhost:5000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Webhook server is running")
        else:
            print("❌ Webhook server not responding")
            return
    except:
        print("❌ Webhook server not running!")
        print("💡 Starting webhook server...")
        
        # Start webhook server in background
        server_thread = threading.Thread(target=start_webhook_server, daemon=True)
        server_thread.start()
        time.sleep(3)  # Wait for server to start
        
        print("✅ Webhook server started")
    
    # Test credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER')
    
    print(f"\n📋 Configuration:")
    print(f"   Account SID: {'✅ Set' if account_sid else '❌ Missing'}")
    print(f"   Auth Token: {'✅ Set' if auth_token else '❌ Missing'}")
    print(f"   From Number: {from_number if from_number else '❌ Missing'}")
    print(f"   Gemini AI: {'✅ Ready' if model else '❌ Not configured'}")
    
    if not account_sid or not auth_token:
        print("\n❌ Missing Twilio credentials!")
        return
    
    try:
        print(f"\n🎯 Ready for interactive vendor calls!")
        print(f"📞 Default number: +918800000488")
        
        phone = input(f"Phone number (Enter for default): ").strip()
        if not phone:
            phone = "+918800000488"
            vendor_name = "Test Vendor (You)"
        else:
            if not phone.startswith('+'):
                phone = f"+{phone}"
            vendor_name = input("Vendor name: ").strip() or "Unknown Vendor"
        
        print(f"\n📞 About to start interactive call:")
        print(f"   📱 From: {from_number}")
        print(f"   📞 To: {phone}")
        print(f"   👤 Vendor: {vendor_name}")
        print(f"   🎤 Speech Recognition: Enabled")
        print(f"   🧠 AI Responses: {'Gemini AI' if model else 'Basic'}")
        
        confirm = input(f"\nStart interactive conversation? (y/N): ").strip().lower()
        
        if confirm == 'y':
            print(f"\n🚀 Starting interactive vendor call...")
            result = make_interactive_call(phone, vendor_name)
            
            if result:
                print(f"\n🎉 INTERACTIVE CALL STARTED!")
                print(f"📞 Call SID: {result}")
                print(f"🎤 Speak naturally when prompted")
                print(f"🧠 AI will understand and respond intelligently")
                print(f"📊 Check http://localhost:5000/conversation for log")
            else:
                print(f"\n❌ Call failed")
        else:
            print(f"📞 Call cancelled")
    
    except KeyboardInterrupt:
        print(f"\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main() 