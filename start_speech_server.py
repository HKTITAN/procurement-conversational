#!/usr/bin/env python3
"""
Start Speech Recognition Server
Starts the webhook server with proper speech recognition endpoints
"""

import os
import sys
from flask import Flask, request, Response
import google.generativeai as genai
from datetime import datetime

# Set environment variables
os.environ['GEMINI_API_KEY'] = 'AIzaSyBCXNuaO9VlL5z1phh4mWGEVnnmRFk9TNg'

# Initialize Flask app
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

def generate_intelligent_response(vendor_speech):
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
        
        print(f"🎤 VENDOR: '{vendor_speech}'")
        print(f"🧠 AI RESPONSE: '{ai_response}'")
        
        return ai_response
        
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return "Haan sir, samjha. Aur kuch bataiye?"

@app.route('/webhook/speech', methods=['POST'])
def handle_speech():
    """Handle speech recognition results from Twilio"""
    
    # Get speech recognition results
    speech_result = request.form.get('SpeechResult', '')
    confidence = request.form.get('Confidence', '0')
    call_sid = request.form.get('CallSid', '')
    
    print(f"\n🎤 SPEECH RECOGNITION:")
    print(f"   Speech: '{speech_result}'")
    print(f"   Confidence: {confidence}")
    print(f"   Call SID: {call_sid}")
    
    if speech_result:
        # Generate intelligent response using Gemini
        ai_response = generate_intelligent_response(speech_result)
        
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
    call_sid = request.form.get('CallSid', '')
    
    print(f"\n📞 NEW SPEECH RECOGNITION CALL")
    print(f"   Call SID: {call_sid}")
    
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
    return {
        "status": "healthy", 
        "gemini": "configured" if model else "not configured",
        "endpoints": ["voice", "speech", "status"],
        "timestamp": datetime.now().isoformat()
    }

@app.route('/conversation')
def show_conversation():
    """Show conversation log"""
    return {"conversation_log": conversation_log}

@app.route('/')
def home():
    """Home page"""
    return """
    <h1>🎤 Speech Recognition Webhook Server</h1>
    <p><strong>Status:</strong> ✅ Running</p>
    <p><strong>Gemini AI:</strong> {'✅ Ready' if model else '❌ Not configured'}</p>
    <h2>🎯 Endpoints:</h2>
    <ul>
        <li><a href="/health">Health Check</a></li>
        <li><a href="/conversation">Conversation Log</a></li>
        <li>POST /webhook/voice - Initial call handler</li>
        <li>POST /webhook/speech - Speech recognition handler</li>
        <li>POST /webhook/status - Call status updates</li>
    </ul>
    """

if __name__ == "__main__":
    print("🎤 STARTING SPEECH RECOGNITION WEBHOOK SERVER")
    print("🧠 Gemini AI Speech Processing")
    print("=" * 60)
    print(f"✅ Server will run on: http://0.0.0.0:5000")
    print(f"🌐 Ngrok tunnel: Available via ngrok")
    print(f"🎯 Endpoints: /webhook/voice, /webhook/speech, /webhook/status")
    print(f"🧠 Gemini AI: {'Ready' if model else 'Not configured'}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False) 