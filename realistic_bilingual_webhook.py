#!/usr/bin/env python3
"""
Realistic Bilingual Webhook - Natural Hindi-English Mix
- Advanced speech recognition with multiple language models
- Natural conversational flow with Hindi-English code-switching
- Realistic Indian business conversation style
- Enhanced voice quality and clarity
"""

from flask import Flask, request
import csv
import re
from datetime import datetime

app = Flask(__name__)

def log_quote(item, price, currency, call_sid, speech, input_type, language_detected):
    """Log quote to CSV with enhanced language tracking"""
    try:
        with open('quotes_live.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            # Write header if file is empty
            if f.tell() == 0:
                writer.writerow(['timestamp', 'vendor', 'item', 'price', 'currency', 'call_sid', 'speech', 'input_type', 'language', 'confidence'])
            
            writer.writerow([
                datetime.now().isoformat(),
                'Harshit Khemani',
                item,
                price,
                currency,
                call_sid,
                speech,
                input_type,
                language_detected,
                'high'
            ])
        print(f"✅ QUOTE LOGGED: {item} = ₹{price} ({language_detected}, {input_type})")
    except Exception as e:
        print(f"❌ Error logging: {e}")

def detect_language_enhanced(text):
    """Enhanced language detection for Hindi-English mix"""
    if not text:
        return "Unknown"
    
    hindi_words = ['रुपये', 'रुपया', 'पैसे', 'हजार', 'सौ', 'है', 'का', 'के', 'मे', 'से', 'ठीक', 'अच्छा', 'बताओ', 'कितना']
    english_words = ['rupees', 'rs', 'price', 'cost', 'each', 'per', 'piece', 'unit', 'yes', 'no', 'okay', 'repeat']
    
    text_lower = text.lower()
    hindi_count = sum(1 for word in hindi_words if word in text_lower)
    english_count = sum(1 for word in english_words if word in text_lower)
    
    if hindi_count > english_count:
        return "Hindi-Primary"
    elif english_count > hindi_count:
        return "English-Primary"
    elif hindi_count > 0 and english_count > 0:
        return "Hinglish-Mix"
    else:
        return "Unclear"

def extract_price_advanced(text):
    """Advanced price extraction with natural language processing"""
    if not text:
        return None
        
    text = text.lower().strip()
    print(f"🔍 Advanced price extraction from: '{text}'")
    
    # Handle common Indian number expressions
    number_words = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
        'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
        'twenty': '20', 'thirty': '30', 'forty': '40', 'fifty': '50',
        'sixty': '60', 'seventy': '70', 'eighty': '80', 'ninety': '90',
        'hundred': '100', 'thousand': '1000',
        # Hindi numbers
        'एक': '1', 'दो': '2', 'तीन': '3', 'चार': '4', 'पांच': '5', 'पाँच': '5',
        'छह': '6', 'सात': '7', 'आठ': '8', 'नौ': '9', 'दस': '10',
        'बीस': '20', 'तीस': '30', 'चालीस': '40', 'पचास': '50',
        'साठ': '60', 'सत्तर': '70', 'अस्सी': '80', 'नब्बे': '90',
        'सौ': '100', 'हजार': '1000'
    }
    
    # Replace word numbers with digits
    for word, digit in number_words.items():
        text = text.replace(word, digit)
    
    # Advanced bilingual patterns with context
    patterns = [
        # Hindi price patterns
        r'(\d+\.?\d*)\s*रुपये?\s*(?:में|का|है|होगा|मिलेगा)?',
        r'(\d+\.?\d*)\s*रुपया?\s*(?:में|का|है|होगा|मिलेगा)?',
        r'(\d+\.?\d*)\s*पैसे?\s*(?:में|का|है|होगा|मिलेगा)?',
        r'(\d+\.?\d*)\s*rs\.?\s*(?:में|का|है|होगा|मिलेगा)?',
        
        # English price patterns
        r'(\d+\.?\d*)\s*rupees?\s*(?:each|per|only|total)?',
        r'(\d+\.?\d*)\s*rs\.?\s*(?:each|per|only|total)?',
        r'(?:price|cost|rate)\s*(?:is|will be)?\s*(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*(?:each|per\s*piece|per\s*unit)',
        
        # Mixed Hinglish patterns
        r'(\d+\.?\d*)\s*(?:ka|ke|ki)\s*(?:hai|hoga|milega)',
        r'(\d+\.?\d*)\s*(?:hai|hoga|milega)\s*(?:rupees?|rs)',
        r'(\d+\.?\d*)\s*(?:main|mein)\s*(?:rupees?|rs)',
        r'(\d+\.?\d*)\s*(?:rupees?|rs)\s*(?:ka|ke|ki|hai)',
        
        # Conversational patterns
        r'(?:sirf|only|bas)\s*(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*(?:tak|only|sirf)',
        r'around\s*(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*(?:around|lagbhag)',
        
        # Pure numbers (fallback)
        r'(\d+\.?\d*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                price = float(match.group(1))
                print(f"💰 Found price: ₹{price}")
                return price
            except:
                continue
    
    print(f"❌ No price found in: '{text}'")
    return None

@app.route('/webhook/voice', methods=['POST'])
def voice_handler():
    """Natural bilingual voice conversation starter"""
    print("📞 REALISTIC BILINGUAL WEBHOOK HIT!")
    
    # More natural, slower, clearer voice with multiple language models
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" rate="slow" language="hi-IN">
        Namaste ji! Main Bio Mac Lifesciences company se bol raha hun. 
        Hum laboratory supplies kharidna chahte hain aur aapse rates puchna chahte hain.
        Kya aap humare saath business kar sakte hain?
    </Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" rate="slow" language="en-IN">
        Hello sir, this is regarding laboratory equipment pricing. 
        Can you help us with some quotes today?
    </Say>
    <Gather input="speech" action="/webhook/gather" timeout="15" speechTimeout="auto" enhanced="true" speechModel="experimental_conversations" language="hi-IN,en-IN,hi,en">
        <Say voice="Polly.Aditi" rate="slow" language="hi-IN">
            Haan ya yes boliye agar aap quotes de sakte hain. 
            Ya phir nahin boliye agar busy hain.
        </Say>
    </Gather>
    <Say voice="Polly.Aditi" language="hi-IN">Theek hai sir, phir kabhi call karenge. Dhanyawad!</Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/gather', methods=['POST'])
def gather_handler():
    """Handle natural bilingual responses"""
    speech = request.form.get('SpeechResult', '').strip()
    call_sid = request.form.get('CallSid', '')
    
    print(f"🎤 RESPONSE: '{speech}'")
    
    # Enhanced positive response detection
    positive_indicators = [
        'yes', 'yeah', 'yep', 'sure', 'okay', 'ok', 'definitely', 'absolutely', 'of course',
        'haan', 'han', 'ha', 'bilkul', 'jarur', 'zaroor', 'theek hai', 'accha', 'sahi hai',
        'kar sakte', 'kar sakta', 'de sakta', 'de sakte', 'mil jayega', 'ho jayega'
    ]
    
    is_positive = any(indicator in speech.lower() for indicator in positive_indicators) if speech else True
    
    language = detect_language_enhanced(speech)
    print(f"🗣️ Language mix: {language}")
    
    if is_positive:
        print("✅ Positive response - continuing with natural conversation")
    else:
        print("⚠️ Proceeding with business conversation")
    
    # Natural, conversational approach
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" rate="slow" language="hi-IN">
        Bahut accha! Thank you sir. 
        Main aapse kuch laboratory items ke rates puchna chahta hun.
    </Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" rate="slow" language="en-IN">
        First item is Petri dishes - 100 millimeter, sterile ones. 
        Hume 30 pieces chahiye. Ek piece ka kya rate hai?
    </Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" rate="slow" language="hi-IN">
        Petri dishes ka per piece rate batayiye rupees mein.
    </Say>
    <Gather input="speech" action="/webhook/gather2" timeout="20" speechTimeout="auto" enhanced="true" speechModel="experimental_conversations" language="hi-IN,en-IN,hi,en">
        <Say voice="Polly.Aditi" rate="slow" language="hi-IN">
            Rate bata dijiye sir. Kitne rupees per piece?
        </Say>
    </Gather>
    <Say voice="Polly.Aditi" language="hi-IN">Koi baat nahi, aage chalte hain.</Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/gather2', methods=['POST'])
def gather2_handler():
    """Handle first price with natural conversation"""
    speech = request.form.get('SpeechResult', '').strip()
    call_sid = request.form.get('CallSid', '')
    
    print(f"🎤 PETRI DISH PRICE: '{speech}'")
    
    language = detect_language_enhanced(speech)
    print(f"🗣️ Language mix: {language}")
    
    # Extract price with advanced processing
    price = extract_price_advanced(speech)
    
    if price:
        log_quote("Petri Dishes 100mm", price, "INR", call_sid, speech, "Voice", language)
        if "hindi" in language.lower():
            price_confirm = f"Samjha sir, Petri dishes {price} rupees per piece. Theek hai."
        else:
            price_confirm = f"Got it sir, Petri dishes {price} rupees per piece. Thank you."
    else:
        if "repeat" in speech.lower():
            price_confirm = "Sorry sir, main phir se puchta hun."
        else:
            price_confirm = "Rate samajh nahi aaya completely, but chaliye next item pe jaate hain."
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" rate="slow" language="hi-IN">
        {price_confirm}
    </Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" rate="slow" language="en-IN">
        Next item - Laboratory gloves, nitrile material, powder-free.
        Hume 15 pieces chahiye. Gloves ka per piece rate kya hai?
    </Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" rate="slow" language="hi-IN">
        Laboratory gloves ka rate per piece rupees mein bata dijiye.
    </Say>
    <Gather input="speech" action="/webhook/gather3" timeout="20" speechTimeout="auto" enhanced="true" speechModel="experimental_conversations" language="hi-IN,en-IN,hi,en">
        <Say voice="Polly.Aditi" rate="slow" language="hi-IN">
            Gloves ka rate sir? Kitne rupees per piece?
        </Say>
    </Gather>
    <Say voice="Polly.Aditi" language="hi-IN">Samay dene ke liye dhanyawad sir.</Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/gather3', methods=['POST'])
def gather3_handler():
    """Handle final price with natural conclusion"""
    speech = request.form.get('SpeechResult', '').strip()
    call_sid = request.form.get('CallSid', '')
    
    print(f"🎤 GLOVES PRICE: '{speech}'")
    
    language = detect_language_enhanced(speech)
    print(f"🗣️ Language mix: {language}")
    
    # Extract price with advanced processing
    price = extract_price_advanced(speech)
    
    if price:
        log_quote("Laboratory Gloves Nitrile", price, "INR", call_sid, speech, "Voice", language)
        if "hindi" in language.lower():
            price_confirm = f"Perfect sir! Gloves {price} rupees per piece. Bahut accha rate hai."
        else:
            price_confirm = f"Excellent sir! Gloves {price} rupees per piece. Very good pricing."
    else:
        price_confirm = "Rate ke liye dhanyawad sir."
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" rate="slow" language="hi-IN">
        {price_confirm}
    </Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" rate="slow" language="en-IN">
        Thank you very much sir for providing the quotes.
        Aapke rates humne note kar liye hain.
        Our procurement team will review everything and we will send you purchase order very soon.
    </Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" rate="slow" language="hi-IN">
        Business karne ke liye dhanyawad sir. 
        Humara purchase order jaldi aayega.
        Aap se baat karke bahut accha laga.
        Have a great day sir! Namaste!
    </Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/status', methods=['POST'])
def status_handler():
    """Handle call status with detailed logging"""
    status = request.form.get('CallStatus', '')
    call_sid = request.form.get('CallSid', '')
    duration = request.form.get('CallDuration', '0')
    print(f"📊 CALL STATUS: {status} (SID: {call_sid}, Duration: {duration}s)")
    return 'OK'

@app.route('/health')
def health():
    """Enhanced health check"""
    return {
        "status": "healthy", 
        "currency": "INR", 
        "languages": ["Hindi", "English", "Hinglish"], 
        "voice_recognition": "advanced-bilingual",
        "voice_engine": "Polly.Aditi",
        "speech_model": "experimental_conversations"
    }

@app.route('/quotes')
def show_quotes():
    """Display quotes with enhanced formatting"""
    try:
        quotes_html = "<h2>🇮🇳 Advanced Bilingual Quotes (Hindi + English + Hinglish)</h2>"
        quotes_html += "<h3>Natural conversation with Indian vendor</h3>"
        with open('quotes_live.csv', 'r') as f:
            content = f.read()
        quotes_html += f"<pre>{content}</pre>"
        return quotes_html
    except:
        return "<h2>कोई quotes अभी तक collect नहीं हुए / No quotes collected yet</h2>"

if __name__ == '__main__':
    print("🚀 REALISTIC BILINGUAL WEBHOOK SERVER")
    print("🇮🇳 Languages: Hindi + English + Hinglish Mix")  
    print("💰 Currency: Indian Rupees (INR)")
    print("🎤 Voice: Polly.Aditi (Natural Indian voice)")
    print("🗣️ Speech: Advanced experimental conversations model")
    print("💬 Style: Natural Indian business conversation")
    app.run(host='0.0.0.0', port=5000, debug=False) 