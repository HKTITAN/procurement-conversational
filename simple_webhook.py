#!/usr/bin/env python3
"""
Simple working webhook server for Twilio calls
"""

from flask import Flask, request
import csv
import re
from datetime import datetime

app = Flask(__name__)

# Quote collection
quotes_collected = []

def log_quote(item, price, call_sid, speech):
    """Log quote to CSV"""
    try:
        with open('quotes_live.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            # Write header if file is empty
            if f.tell() == 0:
                writer.writerow(['timestamp', 'vendor', 'item', 'price', 'call_sid', 'speech'])
            
            writer.writerow([
                datetime.now().isoformat(),
                'Harshit Khemani',
                item,
                price,
                call_sid,
                speech
            ])
        print(f"✅ QUOTE LOGGED: {item} = ${price}")
    except Exception as e:
        print(f"❌ Error logging: {e}")

def extract_price(text):
    """Extract price from speech"""
    patterns = [r'\$?(\d+\.?\d*)', r'(\d+\.?\d*)\s*dollars?', r'(\d+\.?\d*)\s*rupees?']
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return float(match.group(1))
    return None

@app.route('/webhook/voice', methods=['POST'])
def voice_handler():
    """Handle voice calls"""
    print("📞 VOICE WEBHOOK HIT!")
    
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">
        Hello! This is an AI assistant calling from Bio Mac Lifesciences. 
        We need quotes for laboratory supplies. Can you help us with pricing?
    </Say>
    <Gather input="speech" action="/webhook/gather" timeout="10">
        <Say voice="alice">Please say yes if you can provide quotes.</Say>
    </Gather>
    <Say voice="alice">Thank you, we'll call back later.</Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/gather', methods=['POST'])
def gather_handler():
    """Handle speech responses"""
    speech = request.form.get('SpeechResult', '')
    call_sid = request.form.get('CallSid', '')
    
    print(f"🎤 SPEECH: {speech}")
    
    # Extract price if any
    price = extract_price(speech)
    if price:
        log_quote("Lab Supply", price, call_sid, speech)
    
    # Continue conversation
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">
        Great! What's your price for Petri dishes, 100mm sterile, quantity 30 units?
    </Say>
    <Gather input="speech" action="/webhook/gather2" timeout="15">
        <Say voice="alice">Please provide the price per unit.</Say>
    </Gather>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/gather2', methods=['POST'])
def gather2_handler():
    """Handle second item quotes"""
    speech = request.form.get('SpeechResult', '')
    call_sid = request.form.get('CallSid', '')
    
    print(f"🎤 SPEECH 2: {speech}")
    
    price = extract_price(speech)
    if price:
        log_quote("Petri Dishes 100mm", price, call_sid, speech)
    
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">
        Perfect! Thank you for the quotes. We'll review and get back to you soon. 
        Have a great day!
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
    return {"status": "healthy", "quotes": len(quotes_collected)}

@app.route('/quotes')
def show_quotes():
    """Show collected quotes"""
    try:
        with open('quotes_live.csv', 'r') as f:
            content = f.read()
        return f"<pre>{content}</pre>"
    except:
        return "No quotes yet"

if __name__ == '__main__':
    print("🚀 SIMPLE WEBHOOK SERVER STARTING")
    print("📞 Ready for Twilio calls")
    app.run(host='0.0.0.0', port=5000, debug=False) 