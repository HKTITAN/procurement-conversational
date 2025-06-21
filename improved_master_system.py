#!/usr/bin/env python3
"""
Improved Master Speech Recognition System
Properly understands speech, records to CSV, progresses through items
"""

import os
import sys
import time
import threading
import subprocess
import requests
import base64
import json
import csv
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

# Procurement tracking
required_items = ["Petri dishes", "Laboratory gloves", "Microscope slides"]
collected_items = {}
current_item_index = 0

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
        "CALL": "35",      # Magenta
        "CSV": "34"        # Blue
    }
    
    color_code = colors.get(category, "37")
    print(f"\033[{color_code}m[{timestamp}] {category}: {message}\033[0m")

def save_to_csv(item_data):
    """Save item data to CSV file"""
    csv_filename = f"procurement_quotes_{datetime.now().strftime('%Y%m%d')}.csv"
    
    # Check if file exists to determine if we need headers
    file_exists = os.path.exists(csv_filename)
    
    with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['timestamp', 'call_sid', 'item_name', 'price', 'unit', 'currency', 
                     'minimum_order', 'delivery_time', 'discount_info', 'vendor_notes']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(item_data)
    
    print_live_feedback(f"Saved to CSV: {item_data['item_name']} - ₹{item_data['price']} {item_data['unit']}", "CSV")

def extract_item_details(speech_text, target_item):
    """Extract specific item details using Gemini AI"""
    if not model or not speech_text:
        return None
    
    try:
        extraction_prompt = f"""
        The vendor is responding about "{target_item}" for laboratory supplies.
        Vendor said: "{speech_text}"
        
        Extract ONLY the information about {target_item} and return a JSON object:
        {{
            "item_found": true/false,
            "item_name": "{target_item}",
            "price": number (extract just the number, no currency),
            "unit": "per piece/per box/per pack/etc",
            "currency": "INR/USD/etc",
            "minimum_order": "minimum quantity if mentioned",
            "delivery_time": "delivery time if mentioned",
            "discount_info": "any discount information",
            "vendor_notes": "any other important notes"
        }}
        
        If no pricing information is found for {target_item}, set item_found to false.
        Extract numbers carefully - if they say "45 rupees per piece", price should be 45.
        Return ONLY valid JSON, no other text.
        """
        
        response = model.generate_content(extraction_prompt)
        extracted_text = response.text.strip()
        
        # Clean up the response to ensure valid JSON
        if extracted_text.startswith('```json'):
            extracted_text = extracted_text.replace('```json', '').replace('```', '')
        
        try:
            return json.loads(extracted_text)
        except json.JSONDecodeError:
            print_live_feedback(f"JSON parsing failed: {extracted_text}", "ERROR")
            return None
            
    except Exception as e:
        print_live_feedback(f"Extraction error: {e}", "ERROR")
        return None

def get_next_item_question():
    """Get the question for the next item"""
    global current_item_index, required_items
    
    if current_item_index < len(required_items):
        item = required_items[current_item_index]
        questions = {
            "Petri dishes": "Petri dishes ka rate kya hai? Kitne rupees per piece?",
            "Laboratory gloves": "Laboratory gloves ka price kya hai? Aur minimum order kitna hai?",
            "Microscope slides": "Microscope slides kitne main milenge? Per piece ya per box?"
        }
        return questions.get(item, f"{item} ka rate kya hai?")
    return None

def generate_intelligent_response(vendor_speech):
    """Generate intelligent response with proper item progression"""
    global current_item_index, required_items, collected_items, current_call_sid
    
    if not model:
        return "Samjha sir, dhanyawad!"
    
    try:
        print_live_feedback(f"Processing speech: '{vendor_speech}'", "SPEECH")
        
        # Check if we're still collecting items
        if current_item_index < len(required_items):
            current_item = required_items[current_item_index]
            print_live_feedback(f"Looking for: {current_item}", "INFO")
            
            # Extract details for current item
            item_details = extract_item_details(vendor_speech, current_item)
            
            if item_details and item_details.get('item_found'):
                print_live_feedback(f"Found details for {current_item}!", "SUCCESS")
                
                # Prepare CSV data
                csv_data = {
                    'timestamp': datetime.now().isoformat(),
                    'call_sid': current_call_sid,
                    'item_name': item_details.get('item_name', current_item),
                    'price': item_details.get('price', 'N/A'),
                    'unit': item_details.get('unit', 'N/A'),
                    'currency': item_details.get('currency', 'INR'),
                    'minimum_order': item_details.get('minimum_order', 'N/A'),
                    'delivery_time': item_details.get('delivery_time', 'N/A'),
                    'discount_info': item_details.get('discount_info', 'N/A'),
                    'vendor_notes': item_details.get('vendor_notes', 'N/A')
                }
                
                # Save to CSV
                save_to_csv(csv_data)
                
                # Store in memory
                collected_items[current_item] = item_details
                
                # Move to next item
                current_item_index += 1
                
                # Generate response
                if current_item_index < len(required_items):
                    next_item = required_items[current_item_index]
                    next_question = get_next_item_question()
                    response = f"Theek hai, {current_item} ka rate samajh gaya - {item_details.get('price')} rupees {item_details.get('unit')}. Ab {next_question}"
                else:
                    # All items collected - conclude call
                    response = "Bahut achha! Main sab items ka rate note kar liya hun. Main aapko email bhejunga detailed requirements ke saath. Dhanyawad!"
                
                print_live_feedback(f"AI Response: '{response}'", "AI")
                return response
            
            else:
                # Didn't understand - ask again more specifically
                specific_question = get_next_item_question()
                response = f"Sorry sir, {current_item} ka rate clear nahi suna. {specific_question} Please clearly bataiye."
                print_live_feedback(f"AI Response: '{response}'", "AI")
                return response
        
        else:
            # All items collected
            return "Sab kuch complete ho gaya. Dhanyawad sir!"
        
    except Exception as e:
        print_live_feedback(f"AI error: {e}", "ERROR")
        return "Haan sir, samjha. Aur kuch bataiye?"

@app.route('/webhook/speech', methods=['POST'])
def handle_speech():
    """Handle speech recognition with improved logic"""
    global current_call_sid, current_item_index, required_items
    
    # Get speech recognition results
    speech_result = request.form.get('SpeechResult', '')
    confidence = request.form.get('Confidence', '0')
    call_sid = request.form.get('CallSid', '')
    
    print_live_feedback("=" * 60, "INFO")
    print_live_feedback(f"SPEECH RECOGNIZED!", "SPEECH")
    print_live_feedback(f"Text: '{speech_result}'", "SPEECH")
    print_live_feedback(f"Confidence: {confidence}", "SPEECH")
    print_live_feedback(f"Progress: {current_item_index}/{len(required_items)} items", "INFO")
    print_live_feedback("=" * 60, "INFO")
    
    if speech_result:
        # Generate intelligent response
        ai_response = generate_intelligent_response(speech_result)
        
        # Check if we're done with all items
        if current_item_index >= len(required_items):
            # All items collected - conclude call
            twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">{ai_response}</Say>
    <Pause length="2"/>
    <Say voice="Polly.Aditi" language="hi-IN">
        Main aapko email bhejunga sab details ke saath. 
        Bio Mac Lifesciences ki taraf se dhanyawad. Namaste!
    </Say>
    <Hangup/>
</Response>"""
        else:
            # Continue with next item
            twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">{ai_response}</Say>
    <Pause length="2"/>
    
    <!-- Continue listening for next item -->
    <Gather input="speech" 
            language="hi-IN" 
            speechTimeout="5" 
            timeout="10"
            action="/webhook/speech"
            method="POST">
        <Say voice="Polly.Aditi" language="hi-IN">
            Main sun raha hun.
        </Say>
    </Gather>
    
    <!-- Fallback -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Koi response nahi mila. Main phir se call karunga. Dhanyawad!
    </Say>
    <Hangup/>
</Response>"""
    else:
        print_live_feedback("No speech detected", "ERROR")
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">
        Koi baat nahi sir, line clear nahi tha. 
        Main phir se call karunga. Dhanyawad!
    </Say>
    <Hangup/>
</Response>"""
    
    return Response(twiml_response, mimetype='text/xml')

@app.route('/webhook/voice', methods=['POST'])
def handle_voice():
    """Initial voice webhook with improved flow"""
    global current_call_sid, current_item_index, collected_items
    
    current_call_sid = request.form.get('CallSid', '')
    
    # Reset for new call
    current_item_index = 0
    collected_items = {}
    
    print_live_feedback(f"NEW CALL STARTED - SID: {current_call_sid}", "CALL")
    print_live_feedback(f"Items to collect: {', '.join(required_items)}", "INFO")
    
    first_question = get_next_item_question()
    
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <!-- Initial greeting -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Namaste! Main Bio Mac Lifesciences se bol raha hun. 
        Hum laboratory supplies ki company hain.
    </Say>
    
    <Pause length="1"/>
    
    <!-- First item question -->
    <Say voice="Polly.Aditi" language="hi-IN">
        {first_question}
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
            Please clearly bataiye rate. Main sun raha hun.
        </Say>
    </Gather>
    
    <!-- Fallback if no response -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Connection problem lag raha hai. Main phir se call karunga. Namaste!
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
    
    if call_status == 'completed':
        print_live_feedback(f"Call completed! Collected {len(collected_items)}/{len(required_items)} items", "SUCCESS")
        if collected_items:
            print_live_feedback("Items collected:", "SUCCESS")
            for item, details in collected_items.items():
                print_live_feedback(f"  • {item}: ₹{details.get('price', 'N/A')} {details.get('unit', '')}", "CSV")
    
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
        "current_progress": f"{current_item_index}/{len(required_items)}",
        "collected_items": len(collected_items),
        "timestamp": datetime.now().isoformat()
    }

@app.route('/conversation')
def show_conversation():
    """Show live conversation log"""
    return {
        "conversation_log": conversation_log,
        "collected_items": collected_items,
        "progress": f"{current_item_index}/{len(required_items)}"
    }

@app.route('/')
def home():
    """Live dashboard"""
    return f"""
    <h1>🎤 Improved Speech Recognition Dashboard</h1>
    <p><strong>Status:</strong> ✅ Running</p>
    <p><strong>Gemini AI:</strong> {'✅ Ready' if model else '❌ Not configured'}</p>
    <p><strong>Ngrok URL:</strong> {ngrok_url or 'Not set'}</p>
    <p><strong>Progress:</strong> {current_item_index}/{len(required_items)} items collected</p>
    <p><strong>Items:</strong> {', '.join(required_items)}</p>
    <h2>🎯 Collected Items:</h2>
    <ul>
    {''.join([f'<li><strong>{item}:</strong> ₹{details.get("price", "N/A")} {details.get("unit", "")}</li>' for item, details in collected_items.items()])}
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
    
    # Reset progress for new call
    global current_item_index, collected_items
    current_item_index = 0
    collected_items = {}
    
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
            print_live_feedback(f"Will ask for: {', '.join(required_items)}", "INFO")
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
    print("🚀 IMPROVED SPEECH RECOGNITION SYSTEM")
    print("🧠 Smart Item Progression + CSV Recording")
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
    print_live_feedback("Will automatically progress through items and save to CSV", "INFO")
    
    # Step 3: Interactive loop
    while True:
        print("\n" + "="*50)
        print("🎤 IMPROVED SPEECH RECOGNITION SYSTEM")
        print("="*50)
        print("1. 📞 Make call with smart progression")
        print("2. 📊 Show collected items")
        print("3. 📄 View CSV file")
        print("4. 🌐 Show system status")
        print("5. ❌ Exit")
        
        choice = input("\nChoose option (1-5): ").strip()
        
        if choice == "1":
            phone = input(f"Phone number ({DEFAULT_PHONE}): ").strip()
            if not phone:
                phone = DEFAULT_PHONE
            
            print_live_feedback("="*60, "INFO")
            print_live_feedback("MAKING SMART PROCUREMENT CALL", "CALL")
            print_live_feedback(f"Items to collect: {', '.join(required_items)}", "INFO")
            print_live_feedback("="*60, "INFO")
            
            call_sid = make_speech_call(phone, ngrok_url)
            if call_sid:
                print_live_feedback("Call initiated! Watch for automatic progression:", "SUCCESS")
                print_live_feedback("System will ask for each item and save to CSV", "INFO")
            
        elif choice == "2":
            print(f"\n📊 COLLECTED ITEMS ({len(collected_items)}/{len(required_items)}):")
            if collected_items:
                for item, details in collected_items.items():
                    print(f"✅ {item}: ₹{details.get('price', 'N/A')} {details.get('unit', '')}")
                    if details.get('minimum_order'):
                        print(f"   Min Order: {details['minimum_order']}")
                    if details.get('delivery_time'):
                        print(f"   Delivery: {details['delivery_time']}")
            else:
                print("No items collected yet.")
        
        elif choice == "3":
            csv_filename = f"procurement_quotes_{datetime.now().strftime('%Y%m%d')}.csv"
            if os.path.exists(csv_filename):
                print(f"\n📄 CSV FILE: {csv_filename}")
                with open(csv_filename, 'r', encoding='utf-8') as f:
                    print(f.read())
            else:
                print("No CSV file found yet.")
        
        elif choice == "4":
            print(f"\n🌐 SYSTEM STATUS:")
            print(f"   Ngrok URL: {ngrok_url}")
            print(f"   Server: {'✅ Running' if server_running else '❌ Stopped'}")
            print(f"   Gemini AI: {'✅ Ready' if model else '❌ Not configured'}")
            print(f"   Progress: {current_item_index}/{len(required_items)} items")
            print(f"   Collected: {len(collected_items)} items")
        
        elif choice == "5":
            print_live_feedback("Shutting down system...", "INFO")
            if ngrok_process:
                ngrok_process.terminate()
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 