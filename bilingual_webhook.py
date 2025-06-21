#!/usr/bin/env python3
"""
Bilingual webhook server supporting Hindi + English
- Hindi and English voice recognition
- Bilingual price extraction (रुपये, rupees, etc.)
- Indian number patterns
- Mixed language support
"""

from flask import Flask, request
import csv
import re
from datetime import datetime

app = Flask(__name__)

def log_quote(item, price, currency, call_sid, speech, input_type, language_detected):
    """Log quote to CSV with language info"""
    try:
        with open('quotes_live.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            # Write header if file is empty
            if f.tell() == 0:
                writer.writerow(['timestamp', 'vendor', 'item', 'price', 'currency', 'call_sid', 'speech', 'input_type', 'language'])
            
            writer.writerow([
                datetime.now().isoformat(),
                'Harshit Khemani',
                item,
                price,
                currency,
                call_sid,
                speech,
                input_type,
                language_detected
            ])
        print(f"✅ QUOTE LOGGED: {item} = ₹{price} ({language_detected}, {input_type})")
    except Exception as e:
        print(f"❌ Error logging: {e}")

def detect_language(text):
    """Detect if text contains Hindi"""
    hindi_indicators = ['रुपये', 'रुपया', 'पैसे', 'हजार', 'सौ', 'दस', 'बीस', 'तीस', 'चालीस', 'पचास']
    if any(indicator in text for indicator in hindi_indicators):
        return "Hindi"
    return "English"

def extract_price_bilingual(text):
    """Extract price from Hindi/English speech"""
    if not text:
        return None
        
    text = text.lower().strip()
    print(f"🔍 Extracting price from: '{text}'")
    
    # Hindi number words to digits
    hindi_numbers = {
        'एक': '1', 'दो': '2', 'तीन': '3', 'चार': '4', 'पांच': '5',
        'छह': '6', 'सात': '7', 'आठ': '8', 'नौ': '9', 'दस': '10',
        'बीस': '20', 'तीस': '30', 'चालीस': '40', 'पचास': '50',
        'साठ': '60', 'सत्तर': '70', 'अस्सी': '80', 'नब्बे': '90',
        'सौ': '100', 'हजार': '1000'
    }
    
    # Replace Hindi numbers with digits
    for hindi, digit in hindi_numbers.items():
        text = text.replace(hindi, digit)
    
    # Enhanced bilingual patterns
    patterns = [
        # Hindi patterns
        r'(\d+\.?\d*)\s*रुपये',
        r'(\d+\.?\d*)\s*रुपया',
        r'(\d+\.?\d*)\s*पैसे',
        r'(\d+\.?\d*)\s*रुपए',
        r'(\d+\.?\d*)\s*rs',
        
        # English patterns  
        r'(\d+\.?\d*)\s*rupees?',
        r'(\d+\.?\d*)\s*rs\.?',
        r'price\s*is\s*(\d+\.?\d*)',
        r'cost\s*is\s*(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*each',
        r'(\d+\.?\d*)\s*per\s*piece',
        r'(\d+\.?\d*)\s*per\s*unit',
        r'(\d+\.?\d*)\s*only',
        r'(\d+\.?\d*)\s*dollars?',
        
        # Mixed patterns
        r'(\d+\.?\d*)\s*ka\s*hai',  # "40 ka hai"
        r'(\d+\.?\d*)\s*hai',       # "40 hai"
        r'(\d+\.?\d*)\s*milega',    # "40 milega"
        
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
    """Handle voice calls with bilingual support"""
    print("📞 BILINGUAL VOICE WEBHOOK HIT!")
    
    # Use both Hindi and English recognition
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" rate="medium" language="en-IN">
        Namaste! This is an AI assistant calling from Bio Mac Lifesciences. 
        We need quotes for laboratory supplies in rupees. 
        Aap humare saath pricing mein madad kar sakte hain?
        Can you help us with pricing today?
    </Say>
    <Gather input="speech" action="/webhook/gather" timeout="12" speechTimeout="4" enhanced="true" speechModel="phone_call" language="hi-IN,en-IN">
        <Say voice="alice" rate="medium" language="en-IN">
            Please say yes or haan if you can provide quotes, or no or nahin if you cannot help today.
            Haan ya yes kahiye agar aap quote de sakte hain.
        </Say>
    </Gather>
    <Say voice="alice" language="en-IN">Dhanyawad, we will call back later. Thank you.</Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/gather', methods=['POST'])
def gather_handler():
    """Handle bilingual initial response"""
    speech = request.form.get('SpeechResult', '').strip()
    call_sid = request.form.get('CallSid', '')
    
    print(f"🎤 RESPONSE: '{speech}'")
    
    # Check for positive response in both languages
    positive_words = ['yes', 'yeah', 'sure', 'okay', 'ok', 'definitely', 'absolutely', 
                     'haan', 'han', 'bilkul', 'jarur', 'zaroor', 'theek hai']
    is_positive = any(word in speech.lower() for word in positive_words) if speech else False
    
    language = detect_language(speech)
    print(f"🗣️ Language detected: {language}")
    
    if is_positive:
        print("✅ Positive response - continuing with quotes")
    else:
        print("⚠️ Unclear response - continuing anyway")
    
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" rate="medium" language="en-IN">
        Great! Bahut accha! What is your price for Petri dishes, 100 millimeter sterile, quantity 30 pieces? 
        Petri dishes ka kya rate hai? Please tell me the price per piece in rupees.
        Ek piece ka kitne rupees?
    </Say>
    <Gather input="speech" action="/webhook/gather2" timeout="18" speechTimeout="6" enhanced="true" speechModel="phone_call" language="hi-IN,en-IN">
        <Say voice="alice" rate="medium" language="en-IN">
            Please clearly say the price per piece in rupees. 
            Ek piece ka rate rupees mein batayiye.
        </Say>
    </Gather>
    <Say voice="alice" language="en-IN">Let me try the next item. Dusra item try karte hain.</Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/gather2', methods=['POST'])
def gather2_handler():
    """Handle first item price in Hindi/English"""
    speech = request.form.get('SpeechResult', '').strip()
    call_sid = request.form.get('CallSid', '')
    
    print(f"🎤 PRICE 1: '{speech}'")
    
    language = detect_language(speech)
    print(f"🗣️ Language: {language}")
    
    # Extract price using bilingual patterns
    price = extract_price_bilingual(speech)
    if price:
        log_quote("Petri Dishes 100mm", price, "INR", call_sid, speech, "Voice", language)
        if language == "Hindi":
            price_confirm = f"Accha, to Petri dishes ka rate {price} rupees per piece hai. Dhanyawad!"
        else:
            price_confirm = f"So that's {price} rupees per piece for Petri dishes. Thank you!"
    else:
        price_confirm = "I couldn't catch the exact price, but let's continue. Rate samajh nahi aaya, aage chalte hain."
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" rate="medium" language="en-IN">
        {price_confirm} Now, what is your price for Laboratory Gloves, Nitrile powder-free, quantity 15 pieces?
        Ab Laboratory Gloves ka kya rate hai? Nitrile gloves, powder-free, 15 pieces.
        Please tell me the price per piece in rupees. Ek piece ka rate rupees mein.
    </Say>
    <Gather input="speech" action="/webhook/gather3" timeout="18" speechTimeout="6" enhanced="true" speechModel="phone_call" language="hi-IN,en-IN">
        <Say voice="alice" rate="medium" language="en-IN">
            Please say the price per piece for laboratory gloves in rupees.
            Laboratory gloves ka rate per piece rupees mein batayiye.
        </Say>
    </Gather>
    <Say voice="alice" language="en-IN">Moving to final item. Akhiri item pe jaate hain.</Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/gather3', methods=['POST'])
def gather3_handler():
    """Handle second item price in Hindi/English"""
    speech = request.form.get('SpeechResult', '').strip()
    call_sid = request.form.get('CallSid', '')
    
    print(f"🎤 PRICE 2: '{speech}'")
    
    language = detect_language(speech)
    print(f"🗣️ Language: {language}")
    
    # Extract price using bilingual patterns
    price = extract_price_bilingual(speech)
    if price:
        log_quote("Laboratory Gloves Nitrile", price, "INR", call_sid, speech, "Voice", language)
        if language == "Hindi":
            price_confirm = f"Bahut badhiya! Laboratory gloves ka rate {price} rupees per piece."
        else:
            price_confirm = f"Excellent! {price} rupees per piece for laboratory gloves."
    else:
        price_confirm = "Thank you for the pricing information. Rate ke liye dhanyawad."
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" rate="medium" language="en-IN">
        {price_confirm} Perfect! Bahut accha! Thank you for providing quotes in Indian rupees. 
        Aapne jo quotes diye hain, unhe humne record kar liya hai.
        We have recorded your prices and will review them with our procurement team. 
        We will get back to you with purchase order very soon. 
        Bahut jaldi purchase order bhejenge. Thank you for your time and have a wonderful day!
        Aapka samay dene ke liye dhanyawad!
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
    return {"status": "healthy", "currency": "INR", "languages": ["Hindi", "English"], "voice_recognition": "bilingual"}

@app.route('/quotes')
def show_quotes():
    """Show collected quotes with language info"""
    try:
        quotes_html = "<h2>🇮🇳 Bilingual Quotes Collected (Hindi + English)</h2>"
        with open('quotes_live.csv', 'r') as f:
            content = f.read()
        quotes_html += f"<pre>{content}</pre>"
        return quotes_html
    except:
        return "<h2>No quotes collected yet / अभी तक कोई quotes नहीं मिले</h2>"

if __name__ == '__main__':
    print("🚀 BILINGUAL WEBHOOK SERVER STARTING")
    print("🇮🇳 Languages: Hindi + English")  
    print("💰 Currency: Indian Rupees (INR)")
    print("🎤 Speech: Enhanced bilingual recognition")
    print("🗣️ Models: hi-IN, en-IN")
    app.run(host='0.0.0.0', port=5000, debug=False) 