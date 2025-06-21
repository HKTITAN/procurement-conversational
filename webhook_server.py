#!/usr/bin/env python3
"""
Webhook server for Likwid.AI Procurement Automation
Handles real-time voice conversation and quote collection
"""

from flask import Flask, request, Response
import csv
import json
import os
from datetime import datetime

app = Flask(__name__)

# Configuration
CLIENT_NAME = "Bio Mac Lifesciences"
VENDOR_NAME = "Harshit Khemani"
QUOTES_FILE = "quotes.csv"

# Conversation state
conversation_state = {
    'current_item_index': 0,
    'items_to_quote': [
        {'name': 'Petri Dishes 100mm', 'quantity': 30, 'specs': 'Sterile polystyrene with lid'},
        {'name': 'Micropipette Tips 1000μL', 'quantity': 73, 'specs': 'Sterile filtered tips'},
        {'name': 'Laboratory Gloves Nitrile', 'quantity': 15, 'specs': 'Powder-free size M'},
        {'name': 'pH Buffer Solution 7.0', 'quantity': 22, 'specs': '500ml bottle certified reference'},
        {'name': 'Eppendorf Tubes 1.5ml', 'quantity': 37, 'specs': 'Sterile DNase/RNase free'},
        {'name': 'Cell Culture Media', 'quantity': 20, 'specs': 'DMEM with 10% FBS sterile'},
        {'name': 'Microscope Slides', 'quantity': 25, 'specs': 'Plain glass 75x25mm'}
    ],
    'quotes_collected': [],
    'conversation_started': False
}

def log_quote(item_name, price, quantity, call_sid, raw_text):
    """Log quote to CSV file"""
    try:
        file_exists = os.path.isfile(QUOTES_FILE)
        
        with open(QUOTES_FILE, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'vendor_name', 'item_name', 'price', 'quantity', 'call_sid', 'raw_text']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                'timestamp': datetime.now().isoformat(),
                'vendor_name': VENDOR_NAME,
                'item_name': item_name,
                'price': price,
                'quantity': quantity,
                'call_sid': call_sid,
                'raw_text': raw_text
            })
        
        print(f"📝 Quote logged: {item_name} - ${price} per unit")
        
    except Exception as e:
        print(f"❌ Error logging quote: {e}")

def extract_price_from_speech(speech_text):
    """Extract price information from speech"""
    import re
    
    # Look for various price patterns
    patterns = [
        r'(\d+\.?\d*)\s*dollars?\s*(?:per|each)',
        r'(\d+\.?\d*)\s*(?:per|each)',
        r'\$(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*rupees?',
        r'price\s+is\s+(\d+\.?\d*)',
        r'costs?\s+(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*only'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, speech_text.lower())
        if matches:
            try:
                return float(matches[0])
            except:
                continue
    
    return None

@app.route('/webhook/voice', methods=['POST'])
def handle_voice():
    """Handle initial voice webhook - start conversation"""
    print(f"📞 Voice webhook called - Starting conversation")
    
    # Initial greeting
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">
        Hi, this is an AI assistant calling on behalf of {CLIENT_NAME}. 
        I'm reaching out to get quotes for some laboratory supplies we need to order. 
        Is this a good time to discuss pricing for a few items?
    </Say>
    <Gather input="speech" timeout="10" speechTimeout="5" action="/webhook/gather" method="POST">
        <Say voice="alice">Please say yes if you're available to provide quotes, or let me know when would be a better time.</Say>
    </Gather>
    <Say voice="alice">I didn't hear a response. I'll call back later. Thank you!</Say>
</Response>"""
    
    conversation_state['conversation_started'] = True
    return Response(twiml, mimetype='text/xml')

@app.route('/webhook/gather', methods=['POST'])
def handle_gather():
    """Handle speech input during conversation"""
    speech_result = request.form.get('SpeechResult', '')
    call_sid = request.form.get('CallSid', '')
    
    print(f"🎤 Speech received: {speech_result}")
    
    current_index = conversation_state['current_item_index']
    items = conversation_state['items_to_quote']
    
    # Extract price if mentioned
    price = extract_price_from_speech(speech_result)
    if price and current_index > 0:  # Don't log price from initial greeting
        prev_item = items[current_index - 1]
        log_quote(prev_item['name'], price, prev_item['quantity'], call_sid, speech_result)
        conversation_state['quotes_collected'].append({
            'item': prev_item['name'],
            'price': price,
            'quantity': prev_item['quantity']
        })
    
    # Continue conversation or wrap up
    if current_index < len(items):
        # Ask about next item
        item = items[current_index]
        conversation_state['current_item_index'] += 1
        
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">
        Great! Next, we need {item['name']}. The specifications are {item['specs']}. 
        We need {item['quantity']} units. What's your price per unit for this item?
    </Say>
    <Gather input="speech" timeout="15" speechTimeout="7" action="/webhook/gather" method="POST">
        <Say voice="alice">Please provide the price per unit.</Say>
    </Gather>
    <Say voice="alice">Let me move to the next item.</Say>
</Response>"""
        
    else:
        # End conversation
        quotes_count = len(conversation_state['quotes_collected'])
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">
        Perfect! Thank you for providing quotes on {quotes_count} items. 
        I've recorded all the pricing information. 
        We'll review the quotes and get back to you with our purchase order soon. 
        Thank you for your time, and have a great day!
    </Say>
</Response>"""
        
        print(f"✅ Conversation completed! Collected {quotes_count} quotes")
    
    return Response(twiml, mimetype='text/xml')

@app.route('/webhook/status', methods=['POST'])
def handle_status():
    """Handle call status updates"""
    call_status = request.form.get('CallStatus', '')
    call_sid = request.form.get('CallSid', '')
    
    print(f"📊 Call status update: {call_status} (SID: {call_sid})")
    
    return Response('OK', mimetype='text/plain')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'conversation_active': conversation_state['conversation_started'],
        'items_remaining': len(conversation_state['items_to_quote']) - conversation_state['current_item_index'],
        'quotes_collected': len(conversation_state['quotes_collected'])
    }

@app.route('/status', methods=['GET'])
def get_status():
    """Get current conversation status"""
    return {
        'conversation_state': conversation_state,
        'quotes_file_exists': os.path.exists(QUOTES_FILE)
    }

if __name__ == '__main__':
    print("🚀 Starting Likwid.AI Webhook Server...")
    print(f"📞 Ready to handle voice conversation with {VENDOR_NAME}")
    print(f"📝 Quotes will be logged to: {QUOTES_FILE}")
    print("🌐 Server starting on http://localhost:5000")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True) 