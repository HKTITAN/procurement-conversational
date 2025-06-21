#!/usr/bin/env python3
"""
Better voice webhook server with improved speech recognition
- Enhanced voice recognition settings  
- No DTMF instructions confusing users
- Clear speech processing
- Rupees currency support
"""

from flask import Flask, request
import csv
import re
from datetime import datetime

app = Flask(__name__)

def log_quote(item, price, currency, call_sid, speech, input_type):
    """Log quote to CSV with currency support"""
    try:
        with open('quotes_live.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            # Write header if file is empty
            if f.tell() == 0:
                writer.writerow(['timestamp', 'vendor', 'item', 'price', 'currency', 'call_sid', 'speech', 'input_type'])
            
            writer.writerow([
                datetime.now().isoformat(),
                'Harshit Khemani',
                item,
                price,
                currency,
                call_sid,
                speech,
                input_type
            ])
        print(f"✅ QUOTE LOGGED: {item} = ₹{price} ({input_type})")
    except Exception as e:
        print(f"❌ Error logging: {e}")

def extract_price(text):
    """Extract price from speech - enhanced patterns"""
    if not text:
        return None
        
    text = text.lower().strip()
    print(f"🔍 Extracting price from: '{text}'")
    
    # Enhanced patterns for price extraction - most specific first
    patterns = [
        r'(\d+\.?\d*)\s*rupees?',
        r'(\d+\.?\d*)\s*rs\.?',
        r'price\s*is\s*(\d+\.?\d*)',
        r'costs?\s*(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*each',
        r'(\d+\.?\d*)\s*per\s*piece',
        r'(\d+\.?\d*)\s*per\s*unit',
        r'(\d+\.?\d*)\s*only',
        r'(\d+\.?\d*)\s*dollars?',
        r'(\d+\.?\d*)\s*(?:hundred|thousand)',
        r'(\d+\.?\d*)'  # Just numbers as fallback
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            price = float(match.group(1))
            print(f"💰 Found price: ₹{price}")
            return price
    
    print(f"❌ No price found in: '{text}'")
    return None

@app.route('/webhook/voice', methods=['POST'])
def voice_handler():
    """Handle voice calls with best recognition settings"""
    print("📞 VOICE WEBHOOK HIT!")
    
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" rate="medium" language="en-IN">
        Hello! This is an AI assistant calling from Bio Mac Lifesciences. 
        We need quotes for laboratory supplies in Indian rupees. 
        Can you help us with pricing today?
    </Say>
    <Gather input="speech" action="/webhook/gather" timeout="10" speechTimeout="3" enhanced="true" speechModel="phone_call" language="en-IN">
        <Say voice="alice" rate="medium" language="en-IN">
            Please say yes if you can provide quotes, or no if you cannot help today.
        </Say>
    </Gather>
    <Say voice="alice" language="en-IN">Thank you, we will call back later.</Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/gather', methods=['POST'])
def gather_handler():
    """Handle initial response"""
    speech = request.form.get('SpeechResult', '').strip()
    call_sid = request.form.get('CallSid', '')
    
    print(f"🎤 RESPONSE: '{speech}'")
    
    # Check if positive response
    positive_words = ['yes', 'yeah', 'sure', 'okay', 'ok', 'definitely', 'absolutely']
    is_positive = any(word in speech.lower() for word in positive_words) if speech else False
    
    if is_positive:
        print("✅ Positive response - continuing with quotes")
    else:
        print("⚠️ Unclear response - continuing anyway")
    
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" rate="medium" language="en-IN">
        Great! What is your price for Petri dishes, 100 millimeter sterile, quantity 30 pieces? 
        Please tell me the price per piece in rupees.
    </Say>
    <Gather input="speech" action="/webhook/gather2" timeout="15" speechTimeout="5" enhanced="true" speechModel="phone_call" language="en-IN">
        <Say voice="alice" rate="medium" language="en-IN">
            Please clearly say the price per piece in rupees.
        </Say>
    </Gather>
    <Say voice="alice" language="en-IN">Let me try the next item.</Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/gather2', methods=['POST'])
def gather2_handler():
    """Handle first item price"""
    speech = request.form.get('SpeechResult', '').strip()
    call_sid = request.form.get('CallSid', '')
    
    print(f"🎤 PRICE 1: '{speech}'")
    
    # Extract price
    price = extract_price(speech)
    if price:
        log_quote("Petri Dishes 100mm", price, "INR", call_sid, speech, "Voice")
        price_confirm = f"So that's {price} rupees per piece for Petri dishes. Thank you!"
    else:
        price_confirm = "I couldn't catch the exact price, but let's continue."
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" rate="medium" language="en-IN">
        {price_confirm} Now, what is your price for Laboratory Gloves, Nitrile powder-free, quantity 15 pieces?
        Please tell me the price per piece in rupees.
    </Say>
    <Gather input="speech" action="/webhook/gather3" timeout="15" speechTimeout="5" enhanced="true" speechModel="phone_call" language="en-IN">
        <Say voice="alice" rate="medium" language="en-IN">
            Please say the price per piece for the laboratory gloves in rupees.
        </Say>
    </Gather>
    <Say voice="alice" language="en-IN">Moving to the final item.</Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/gather3', methods=['POST'])
def gather3_handler():
    """Handle second item price"""
    speech = request.form.get('SpeechResult', '').strip()
    call_sid = request.form.get('CallSid', '')
    
    print(f"🎤 PRICE 2: '{speech}'")
    
    # Extract price
    price = extract_price(speech)
    if price:
        log_quote("Laboratory Gloves Nitrile", price, "INR", call_sid, speech, "Voice")
        price_confirm = f"Excellent! {price} rupees per piece for laboratory gloves."
    else:
        price_confirm = "Thank you for the pricing information."
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" rate="medium" language="en-IN">
        {price_confirm} Perfect! Thank you for providing the quotes in Indian rupees. 
        We have recorded your prices and will review them with our procurement team. 
        We will get back to you with our purchase order very soon. 
        Thank you for your time and have a wonderful day!
    </Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/status', methods=['POST'])
def status_handler():
    """Handle call status updates"""
    status = request.form.get('CallStatus', '')
    call_sid = request.form.get('CallSid', '')
    print(f"📊 CALL STATUS: {status} ({call_sid})")
    return 'OK'

@app.route('/health')
def health():
    """Health check"""
    return {"status": "healthy", "currency": "INR", "voice_recognition": "enhanced"}

@app.route('/quotes')
def show_quotes():
    """Show collected quotes"""
    try:
        quotes_html = "<h2>🇮🇳 Quotes Collected (Indian Rupees)</h2>"
        with open('quotes_live.csv', 'r') as f:
            content = f.read()
        quotes_html += f"<pre>{content}</pre>"
        return quotes_html
    except:
        return "<h2>No quotes collected yet</h2>"

if __name__ == '__main__':
    print("🚀 BETTER VOICE WEBHOOK SERVER STARTING")
    print("🇮🇳 Currency: Indian Rupees (INR)")  
    print("🎤 Enhanced speech recognition (no DTMF)")
    print("🗣️ Language: English-India")
    print("📞 Speech Model: phone_call")
    app.run(host='0.0.0.0', port=5000, debug=False) 