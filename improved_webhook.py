#!/usr/bin/env python3
"""
Improved webhook server for Twilio calls
- Handles rupees currency
- Better voice recognition
- DTMF (numpad) backup input
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
    """Extract price from speech - prioritize rupees"""
    # Enhanced patterns for Indian currency
    patterns = [
        r'(\d+\.?\d*)\s*rupees?',
        r'(\d+\.?\d*)\s*rs',
        r'(\d+\.?\d*)\s*each',
        r'(\d+\.?\d*)\s*per\s*piece',
        r'(\d+\.?\d*)\s*per\s*unit',
        r'(\d+\.?\d*)\s*only',
        r'(\d+\.?\d*)\s*(?:hundred|thousand)',
        r'\$?(\d+\.?\d*)'  # fallback for dollars
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return float(match.group(1))
    return None

@app.route('/webhook/voice', methods=['POST'])
def voice_handler():
    """Handle voice calls with improved recognition"""
    print("📞 VOICE WEBHOOK HIT!")
    
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" rate="slow">
        Hello! This is an AI assistant calling from Bio Mac Lifesciences. 
        We need quotes for laboratory supplies in rupees. Can you help us with pricing?
    </Say>
    <Gather input="speech dtmf" action="/webhook/gather" timeout="15" speechTimeout="auto" enhanced="true" speechModel="experimental_conversations">
        <Say voice="alice" rate="slow">Please say yes if you can provide quotes, or press 1 for yes, 0 for no.</Say>
    </Gather>
    <Say voice="alice">Thank you, we'll call back later.</Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/gather', methods=['POST'])
def gather_handler():
    """Handle speech and DTMF responses"""
    speech = request.form.get('SpeechResult', '')
    digits = request.form.get('Digits', '')
    call_sid = request.form.get('CallSid', '')
    
    input_type = "DTMF" if digits else "Voice"
    user_input = digits if digits else speech
    
    print(f"🎤 INPUT ({input_type}): {user_input}")
    
    # Continue conversation
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" rate="slow">
        Great! What is your price for Petri dishes, 100mm sterile, quantity 30 units? 
        Please tell me the price per piece in rupees.
    </Say>
    <Gather input="speech dtmf" action="/webhook/gather2" timeout="20" speechTimeout="auto" enhanced="true" speechModel="experimental_conversations">
        <Say voice="alice" rate="slow">Say the price in rupees, or use keypad: press star, then the price, then hash. For example, star-40-hash for 40 rupees.</Say>
    </Gather>
    <Say voice="alice">Let me try a different item.</Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/gather2', methods=['POST'])
def gather2_handler():
    """Handle price quotes with DTMF backup"""
    speech = request.form.get('SpeechResult', '')
    digits = request.form.get('Digits', '')
    call_sid = request.form.get('CallSid', '')
    
    input_type = "DTMF" if digits else "Voice"
    user_input = digits if digits else speech
    
    print(f"🎤 PRICE INPUT ({input_type}): {user_input}")
    
    # Extract price
    price = None
    if digits:
        # Handle DTMF: *40# format or just digits
        clean_digits = digits.replace('*', '').replace('#', '')
        try:
            price = float(clean_digits)
        except:
            pass
    else:
        price = extract_price(speech)
    
    if price:
        log_quote("Petri Dishes 100mm", price, "INR", call_sid, user_input, input_type)
    
    # Ask for second item
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" rate="slow">
        Thank you! Now, what is your price for Laboratory Gloves, Nitrile, powder-free, quantity 15 pieces?
        Please tell me the price per piece in rupees.
    </Say>
    <Gather input="speech dtmf" action="/webhook/gather3" timeout="20" speechTimeout="auto" enhanced="true">
        <Say voice="alice" rate="slow">Say the price in rupees, or use keypad: star-price-hash.</Say>
    </Gather>
    <Say voice="alice">Moving to final item.</Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/gather3', methods=['POST'])
def gather3_handler():
    """Handle final item quote"""
    speech = request.form.get('SpeechResult', '')
    digits = request.form.get('Digits', '')
    call_sid = request.form.get('CallSid', '')
    
    input_type = "DTMF" if digits else "Voice"
    user_input = digits if digits else speech
    
    print(f"🎤 FINAL PRICE ({input_type}): {user_input}")
    
    # Extract price
    price = None
    if digits:
        clean_digits = digits.replace('*', '').replace('#', '')
        try:
            price = float(clean_digits)
        except:
            pass
    else:
        price = extract_price(speech)
    
    if price:
        log_quote("Laboratory Gloves Nitrile", price, "INR", call_sid, user_input, input_type)
    
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" rate="slow">
        Perfect! Thank you for providing the quotes in rupees. 
        We have recorded your prices and will review them. 
        We'll get back to you with our purchase order soon. 
        Thank you for your time, and have a great day!
    </Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/status', methods=['POST'])
def status_handler():
    """Handle call status"""
    status = request.form.get('CallStatus', '')
    call_sid = request.form.get('CallSid', '')
    print(f"📊 CALL STATUS: {status} ({call_sid})")
    return 'OK'

@app.route('/health')
def health():
    """Health check"""
    return {"status": "healthy", "currency": "INR"}

@app.route('/quotes')
def show_quotes():
    """Show collected quotes in rupees"""
    try:
        quotes_html = "<h2>🇮🇳 Quotes Collected (in Rupees)</h2>"
        with open('quotes_live.csv', 'r') as f:
            content = f.read()
        quotes_html += f"<pre>{content}</pre>"
        return quotes_html
    except:
        return "<h2>No quotes collected yet</h2>"

if __name__ == '__main__':
    print("🚀 IMPROVED WEBHOOK SERVER STARTING")
    print("💰 Currency: Indian Rupees (INR)")
    print("🎤 Enhanced speech recognition + DTMF backup")
    app.run(host='0.0.0.0', port=5000, debug=False) 