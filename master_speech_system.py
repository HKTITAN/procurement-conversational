#!/usr/bin/env python3
"""
Master Speech Recognition System
Handles everything: ngrok, speech server, live feedback, and calls
"""

import os
import sys
import time
import threading
import subprocess
import requests
import base64
import json
from datetime import datetime
from flask import Flask, request, Response
import google.generativeai as genai

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

# Global state
conversation_log = []
current_call_sid = None
ngrok_url = None
server_running = False

# Twilio credentials
TWILIO_ACCOUNT_SID = "AC820daae89092e30fee3487e80162d2e2"
TWILIO_AUTH_TOKEN = "690636dcdd752868f4e77648dc0d49eb"
TWILIO_FROM_NUMBER = "+14323484517"
DEFAULT_PHONE = "+918800000488"

def print_live_feedback(message, category="INFO"):
    """Print live feedback with timestamps and colors"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    colors = {
        "INFO": "37",      # White
        "SUCCESS": "32",   # Green
        "ERROR": "31",     # Red
        "SPEECH": "36",    # Cyan
        "AI": "33",        # Yellow
        "CALL": "35"       # Magenta
    }
    
    color_code = colors.get(category, "37")
    print(f"\033[{color_code}m[{timestamp}] {category}: {message}\033[0m")

def extract_requirements_from_speech(speech_text):
    """Extract specific requirements and pricing from speech using Gemini"""
    if not model or not speech_text:
        return None
    
    try:
        extraction_prompt = f"""
        Analyze this vendor response for laboratory supplies procurement:
        "{speech_text}"
        
        Extract and return ONLY a JSON object with these fields:
        {{
            "items_mentioned": ["item1", "item2"],
            "prices": [{{"item": "item_name", "price": 45, "unit": "per piece", "currency": "INR"}}],
            "discounts": "any discount information",
            "delivery_time": "delivery information",
            "minimum_order": "minimum order info",
            "contact_info": "any contact details",
            "other_notes": "other important info"
        }}
        
        If no information is found for a field, use null or empty array.
        Return ONLY valid JSON, no other text.
        """
        
        response = model.generate_content(extraction_prompt)
        extracted_data = response.text.strip()
        
        # Try to parse as JSON
        try:
            return json.loads(extracted_data)
        except:
            # If JSON parsing fails, return raw text
            return {"raw_response": extracted_data, "speech_text": speech_text}
            
    except Exception as e:
        print_live_feedback(f"Extraction error: {e}", "ERROR")
        return {"error": str(e), "speech_text": speech_text}

def generate_intelligent_response(vendor_speech):
    """Generate intelligent response with live feedback"""
    if not model:
        return "Samjha sir, dhanyawad!"
    
    try:
        print_live_feedback(f"Processing speech: '{vendor_speech}'", "SPEECH")
        
        # Extract requirements first
        extracted_data = extract_requirements_from_speech(vendor_speech)
        if extracted_data:
            print_live_feedback(f"Extracted data: {json.dumps(extracted_data, indent=2)}", "SUCCESS")
        
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
        
        # Log the conversation with extracted data
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "vendor_said": vendor_speech,
            "ai_response": ai_response,
            "extracted_data": extracted_data,
            "call_sid": current_call_sid
        }
        conversation_log.append(conversation_entry)
        
        print_live_feedback(f"AI Response: '{ai_response}'", "AI")
        
        # Save to file for persistence
        with open("live_conversation_log.json", "w") as f:
            json.dump(conversation_log, f, indent=2)
        
        return ai_response
        
    except Exception as e:
        print_live_feedback(f"AI error: {e}", "ERROR")
        return "Haan sir, samjha. Aur kuch bataiye?"

@app.route('/webhook/speech', methods=['POST'])
def handle_speech():
    """Handle speech recognition with live feedback"""
    global current_call_sid
    
    # Get speech recognition results
    speech_result = request.form.get('SpeechResult', '')
    confidence = request.form.get('Confidence', '0')
    call_sid = request.form.get('CallSid', '')
    
    print_live_feedback("=" * 60, "INFO")
    print_live_feedback(f"SPEECH RECOGNIZED!", "SPEECH")
    print_live_feedback(f"Text: '{speech_result}'", "SPEECH")
    print_live_feedback(f"Confidence: {confidence}", "SPEECH")
    print_live_feedback(f"Call SID: {call_sid}", "SPEECH")
    print_live_feedback("=" * 60, "INFO")
    
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
        print_live_feedback("No speech detected", "ERROR")
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
    """Initial voice webhook with live feedback"""
    global current_call_sid
    current_call_sid = request.form.get('CallSid', '')
    
    print_live_feedback(f"NEW CALL STARTED - SID: {current_call_sid}", "CALL")
    
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
    """Handle call status with live feedback"""
    call_status = request.form.get('CallStatus', '')
    call_sid = request.form.get('CallSid', '')
    
    print_live_feedback(f"Call {call_sid}: {call_status}", "CALL")
    return "OK"

@app.route('/health')
def health():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "gemini": "configured" if model else "not configured",
        "endpoints": ["voice", "speech", "status"],
        "ngrok_url": ngrok_url,
        "conversation_count": len(conversation_log),
        "timestamp": datetime.now().isoformat()
    }

@app.route('/conversation')
def show_conversation():
    """Show live conversation log"""
    return {"conversation_log": conversation_log}

@app.route('/')
def home():
    """Live dashboard"""
    return f"""
    <h1>🎤 Live Speech Recognition Dashboard</h1>
    <p><strong>Status:</strong> ✅ Running</p>
    <p><strong>Gemini AI:</strong> {'✅ Ready' if model else '❌ Not configured'}</p>
    <p><strong>Ngrok URL:</strong> {ngrok_url or 'Not set'}</p>
    <p><strong>Conversations:</strong> {len(conversation_log)}</p>
    <h2>🎯 Live Endpoints:</h2>
    <ul>
        <li><a href="/health">Health Check</a></li>
        <li><a href="/conversation">Live Conversation Log</a></li>
        <li>POST /webhook/voice - Call handler</li>
        <li>POST /webhook/speech - Speech processor</li>
    </ul>
    <h2>📊 Last Update:</h2>
    <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    """

def start_ngrok():
    """Start ngrok tunnel"""
    global ngrok_url
    
    print_live_feedback("Starting ngrok tunnel...", "INFO")
    
    try:
        # Start ngrok process
        ngrok_process = subprocess.Popen(
            ['ngrok', 'http', '5000', '--log=stdout'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for ngrok to start and get URL
        time.sleep(5)
        
        # Get ngrok URL from API
        try:
            response = requests.get('http://localhost:4040/api/tunnels')
            if response.status_code == 200:
                tunnels = response.json()['tunnels']
                if tunnels:
                    ngrok_url = tunnels[0]['public_url']
                    print_live_feedback(f"Ngrok tunnel active: {ngrok_url}", "SUCCESS")
                    return ngrok_process, ngrok_url
        except:
            pass
        
        print_live_feedback("Could not get ngrok URL automatically", "ERROR")
        print_live_feedback("Please check ngrok manually and provide URL", "INFO")
        return ngrok_process, None
        
    except Exception as e:
        print_live_feedback(f"Failed to start ngrok: {e}", "ERROR")
        return None, None

def make_speech_call(phone_number, ngrok_url):
    """Make a call with speech recognition"""
    print_live_feedback(f"Making call to {phone_number}", "CALL")
    
    # Webhook URLs using ngrok
    voice_webhook = f"{ngrok_url}/webhook/voice"
    
    # Make the call
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Calls.json"
    auth = base64.b64encode(f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'From': TWILIO_FROM_NUMBER,
        'To': phone_number,
        'Url': voice_webhook,
        'Method': 'POST',
        'StatusCallback': f"{ngrok_url}/webhook/status",
        'StatusCallbackEvent': ['initiated', 'ringing', 'answered', 'completed'],
        'StatusCallbackMethod': 'POST',
        'Record': 'true',
        'Timeout': '30'
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 201:
            call_data = response.json()
            print_live_feedback(f"Call started! SID: {call_data['sid']}", "SUCCESS")
            return call_data['sid']
        else:
            print_live_feedback(f"Call failed: {response.text}", "ERROR")
            return False
            
    except Exception as e:
        print_live_feedback(f"Call error: {e}", "ERROR")
        return False

def start_webhook_server():
    """Start the Flask webhook server"""
    global server_running
    server_running = True
    print_live_feedback("Starting webhook server on port 5000...", "INFO")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def main():
    """Main function to orchestrate everything"""
    print("🚀 MASTER SPEECH RECOGNITION SYSTEM")
    print("🧠 Complete Solution: Ngrok + Server + Live Feedback + Calls")
    print("=" * 70)
    
    # Step 1: Start ngrok
    print_live_feedback("Step 1: Starting ngrok tunnel", "INFO")
    ngrok_process, ngrok_url_result = start_ngrok()
    
    if not ngrok_url_result:
        manual_url = input("Enter your ngrok URL manually (e.g., https://abc123.ngrok.io): ").strip()
        if manual_url:
            global ngrok_url
            ngrok_url = manual_url
            print_live_feedback(f"Using manual ngrok URL: {ngrok_url}", "INFO")
        else:
            print_live_feedback("No ngrok URL provided. Exiting.", "ERROR")
            return
    else:
        ngrok_url = ngrok_url_result
    
    # Step 2: Start webhook server in background
    print_live_feedback("Step 2: Starting webhook server", "INFO")
    server_thread = threading.Thread(target=start_webhook_server, daemon=True)
    server_thread.start()
    time.sleep(3)  # Wait for server to start
    
    print_live_feedback("System ready!", "SUCCESS")
    print_live_feedback(f"Dashboard: {ngrok_url}", "INFO")
    print_live_feedback("Live feedback will appear here during calls", "INFO")
    
    # Step 3: Interactive loop
    while True:
        print("\n" + "="*50)
        print("🎤 LIVE SPEECH RECOGNITION SYSTEM")
        print("="*50)
        print("1. 📞 Make call with live feedback")
        print("2. 📊 Show conversation log")
        print("3. 🌐 Show system status")
        print("4. ❌ Exit")
        
        choice = input("\nChoose option (1-4): ").strip()
        
        if choice == "1":
            phone = input(f"Phone number ({DEFAULT_PHONE}): ").strip()
            if not phone:
                phone = DEFAULT_PHONE
            
            print_live_feedback("="*60, "INFO")
            print_live_feedback("MAKING CALL WITH LIVE SPEECH RECOGNITION", "CALL")
            print_live_feedback("="*60, "INFO")
            
            call_sid = make_speech_call(phone, ngrok_url)
            if call_sid:
                print_live_feedback("Call initiated! Watch for live feedback below:", "SUCCESS")
                print_live_feedback("Speak when prompted - you'll see real-time processing", "INFO")
            
        elif choice == "2":
            print("\n📊 CONVERSATION LOG:")
            if conversation_log:
                for i, entry in enumerate(conversation_log, 1):
                    print(f"\n--- Conversation {i} ---")
                    print(f"Time: {entry['timestamp']}")
                    print(f"Vendor: {entry['vendor_said']}")
                    print(f"AI: {entry['ai_response']}")
                    if entry.get('extracted_data'):
                        print(f"Extracted: {json.dumps(entry['extracted_data'], indent=2)}")
            else:
                print("No conversations yet.")
        
        elif choice == "3":
            print(f"\n🌐 SYSTEM STATUS:")
            print(f"   Ngrok URL: {ngrok_url}")
            print(f"   Server: {'✅ Running' if server_running else '❌ Stopped'}")
            print(f"   Gemini AI: {'✅ Ready' if model else '❌ Not configured'}")
            print(f"   Conversations: {len(conversation_log)}")
        
        elif choice == "4":
            print_live_feedback("Shutting down system...", "INFO")
            if ngrok_process:
                ngrok_process.terminate()
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 