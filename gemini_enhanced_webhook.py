#!/usr/bin/env python3
"""
Gemini-Enhanced Bilingual Webhook - Intelligent Hindi-English Conversations
- Advanced conversation understanding with Google Gemini AI
- Context-aware responses and natural conversation flow
- Smart quote processing and vendor interaction management
- Real-time Hindi-English-Hinglish conversation capabilities
"""

import os
import json
import asyncio
import websockets
import base64
from flask import Flask, request
import csv
import re
from datetime import datetime
import google.generativeai as genai
import threading
import queue
import time

app = Flask(__name__)

# Initialize Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class GeminiConversationManager:
    """Manages intelligent conversations with Gemini AI"""
    
    def __init__(self):
        # Initialize with working model
        model_options = [
            'models/gemini-1.5-flash-8b',      # Most quota-efficient
            'models/gemini-2.0-flash-lite',    # Fast alternative
            'models/gemini-1.5-flash',         # Standard option
            'models/gemini-2.0-flash-exp'      # Experimental (may fail)
        ]
        
        self.model = None
        system_instruction = """
        You are an intelligent assistant for Bio Mac Lifesciences, a company procuring laboratory supplies. 
        You are conducting a professional yet friendly conversation with Indian vendors to get quotes.
        
        Key traits:
        - You speak naturally in Hindi-English mix (Hinglish) as common in Indian business
        - You understand context, emotions, and implicit meanings
        - You can handle interruptions, clarifications, and side conversations naturally
        - You're polite but persistent in getting accurate quotes
        - You understand Indian business culture and communication patterns
        
        Your goals:
        1. Get accurate prices for laboratory items
        2. Build rapport with vendors
        3. Handle any confusion or questions naturally
        4. Extract structured quote information from conversations
        
        Remember: You're having a REAL conversation, not just reading a script.
        """
        
        for model_name in model_options:
            try:
                self.model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction
                )
                # Quick test
                self.model.generate_content("Hi")
                print(f"✅ Gemini conversation model: {model_name}")
                break
            except Exception as e:
                print(f"⚠️  Model {model_name} failed: {str(e)[:100]}...")
                continue
        
        if not self.model:
            print("❌ No Gemini models available! Using fallback.")
            # Fallback without system instruction
            self.model = genai.GenerativeModel('models/gemini-1.5-flash-8b')
        
        self.conversation_history = []
        self.current_context = {
            'items_discussed': [],
            'quotes_received': [],
            'vendor_mood': 'neutral',
            'conversation_stage': 'introduction'
        }
    
    def analyze_speech_intent(self, speech_text, call_context):
        """Analyze what the user really means"""
        try:
            prompt = f"""
            Analyze this speech from a vendor in a procurement call:
            Speech: "{speech_text}"
            Context: {json.dumps(call_context)}
            
            Determine:
            1. Intent (quote_given, question, confusion, agreement, disagreement, etc.)
            2. Extracted price (if any)
            3. Item being discussed
            4. Emotional tone
            5. Suggested response approach
            
            Return JSON format.
            """
            
            response = self.model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            print(f"❌ Gemini analysis error: {e}")
            return {"intent": "unclear", "suggested_response": "neutral"}
    
    def generate_natural_response(self, analysis, conversation_context):
        """Generate contextually appropriate response"""
        try:
            prompt = f"""
            Generate a natural, conversational response for this situation:
            
            Analysis: {json.dumps(analysis)}
            Context: {json.dumps(conversation_context)}
            Previous conversation: {json.dumps(self.conversation_history[-3:])}
            
            Generate response that:
            1. Feels natural and human-like
            2. Uses appropriate Hindi-English mix
            3. Advances the conversation toward getting quotes
            4. Handles any confusion or questions
            5. Maintains professional but friendly tone
            
            Return JSON with:
            - "hindi_text": Natural Hindi response
            - "english_text": Natural English response  
            - "action": Next step to take
            - "confidence": How confident you are in this response
            """
            
            response = self.model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            print(f"❌ Response generation error: {e}")
            return {
                "hindi_text": "Samjha sir, aage chalte hain.",
                "english_text": "Understood sir, let's continue.",
                "action": "continue",
                "confidence": 0.5
            }
    
    def extract_price_with_context(self, speech, item_context):
        """Use Gemini to extract prices with better context understanding"""
        try:
            prompt = f"""
            Extract price information from this speech:
            Speech: "{speech}"
            Item being discussed: "{item_context}"
            
            Consider:
            - Hindi/English number words
            - Implicit pricing (like "same as before", "usual rate")
            - Contextual clues
            - Indian business conversation patterns
            
            Return JSON:
            {{"price": numerical_value_or_null, "currency": "INR", "confidence": 0.0-1.0, "explanation": "why this price"}}
            """
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            return result.get('price'), result.get('confidence', 0.5)
        except Exception as e:
            print(f"❌ Price extraction error: {e}")
            return None, 0.0

def log_quote_enhanced(item, price, currency, call_sid, speech, input_type, language_detected, confidence, context):
    """Enhanced quote logging with Gemini insights"""
    try:
        with open('quotes_live_gemini.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow([
                    'timestamp', 'vendor', 'item', 'price', 'currency', 'call_sid', 
                    'speech', 'input_type', 'language', 'confidence', 'context', 'ai_insights'
                ])
            
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
                confidence,
                json.dumps(context),
                'gemini_enhanced'
            ])
        print(f"✅ ENHANCED QUOTE LOGGED: {item} = ₹{price} (confidence: {confidence})")
    except Exception as e:
        print(f"❌ Enhanced logging error: {e}")

# Initialize conversation manager
conversation_manager = GeminiConversationManager()

@app.route('/webhook/voice', methods=['POST'])
def voice_handler_gemini():
    """Gemini-enhanced voice conversation starter"""
    print("📞 GEMINI-ENHANCED BILINGUAL WEBHOOK HIT!")
    
    # Enhanced greeting with more natural flow
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" rate="slow" language="hi-IN">
        Namaste ji! Main Bio Mac Lifesciences se bol raha hun. 
        Hum laboratory equipment kharidna chahte hain.
        Kya aap humare saath business kar sakte hain? Rates de sakte hain?
    </Say>
    <Pause length="1"/>
    <Gather input="speech" action="/webhook/gather_gemini" timeout="20" speechTimeout="auto" enhanced="true" speechModel="experimental_conversations" language="hi-IN,en-IN,hi,en">
        <Say voice="Polly.Aditi" rate="slow" language="hi-IN">
            Agar aap quotes de sakte hain toh haan ya yes boliye.
            Ya koi problem hai toh bata dijiye.
        </Say>
    </Gather>
    <Say voice="Polly.Aditi" language="hi-IN">Koi baat nahi sir, baad mein call karenge.</Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/gather_gemini', methods=['POST'])
def gather_handler_gemini():
    """Gemini-enhanced response handling"""
    speech = request.form.get('SpeechResult', '').strip()
    call_sid = request.form.get('CallSid', '')
    
    print(f"🎤 GEMINI ANALYZING: '{speech}'")
    
    # Analyze with Gemini
    context = {
        'conversation_stage': 'initial_response',
        'current_item': None,
        'call_sid': call_sid
    }
    
    analysis = conversation_manager.analyze_speech_intent(speech, context)
    print(f"🧠 GEMINI ANALYSIS: {analysis}")
    
    # Generate intelligent response
    response_data = conversation_manager.generate_natural_response(analysis, context)
    print(f"💬 GEMINI RESPONSE: {response_data}")
    
    # Update conversation context
    conversation_manager.current_context['conversation_stage'] = 'item_discussion'
    conversation_manager.conversation_history.append({
        'user_speech': speech,
        'analysis': analysis,
        'response': response_data,
        'timestamp': datetime.now().isoformat()
    })
    
    # Create dynamic TwiML based on Gemini's understanding
    if analysis.get('intent') == 'agreement' or 'positive' in analysis.get('intent', ''):
        next_action = "/webhook/item1_gemini"
        item_intro = response_data.get('hindi_text', 'Bahut accha sir! Chaliye business karte hain.')
    else:
        next_action = "/webhook/item1_gemini"  # Still proceed but adjust approach
        item_intro = "Theek hai sir, koi dikkat nahi. Main items ke bare mein puchta hun."
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" rate="slow" language="hi-IN">
        {item_intro}
    </Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" rate="slow" language="en-IN">
        Let me ask about our first item - Petri dishes, 100 millimeter size.
        Hume 30 pieces chahiye. What's your rate per piece?
    </Say>
    <Gather input="speech" action="{next_action}" timeout="25" speechTimeout="auto" enhanced="true" speechModel="experimental_conversations" language="hi-IN,en-IN,hi,en">
        <Say voice="Polly.Aditi" rate="slow" language="hi-IN">
            Petri dishes ka rate batayiye sir. Per piece kitne rupees?
        </Say>
    </Gather>
    <Say voice="Polly.Aditi" language="hi-IN">Samay dene ke liye dhanyawad sir.</Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/item1_gemini', methods=['POST'])
def item1_handler_gemini():
    """Gemini-enhanced first item handling"""
    speech = request.form.get('SpeechResult', '').strip()
    call_sid = request.form.get('CallSid', '')
    
    print(f"🎤 PETRI DISHES QUOTE (GEMINI): '{speech}'")
    
    # Gemini analysis for price extraction
    context = {
        'conversation_stage': 'price_discussion',
        'current_item': 'Petri Dishes 100mm',
        'expected_quantity': 30
    }
    
    analysis = conversation_manager.analyze_speech_intent(speech, context)
    price, confidence = conversation_manager.extract_price_with_context(speech, "Petri dishes 100mm")
    
    print(f"🧠 PRICE ANALYSIS: {price} (confidence: {confidence})")
    
    # Generate contextual response
    if price and confidence > 0.6:
        log_quote_enhanced("Petri Dishes 100mm", price, "INR", call_sid, speech, "Voice", "Gemini-Enhanced", confidence, context)
        response_data = conversation_manager.generate_natural_response({
            **analysis, 
            'price_received': price,
            'success': True
        }, context)
        confirmation = response_data.get('hindi_text', f'Samjha sir, Petri dishes {price} rupees per piece.')
    else:
        # Intelligent clarification
        response_data = conversation_manager.generate_natural_response({
            **analysis,
            'price_unclear': True,
            'needs_clarification': True
        }, context)
        confirmation = response_data.get('hindi_text', 'Rate clear nahi suna sir, phir se bata dijiye.')
    
    # Continue to next item with context
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" rate="slow" language="hi-IN">
        {confirmation}
    </Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" rate="slow" language="en-IN">
        Next item sir - Laboratory gloves, nitrile powder-free.
        We need 15 pieces. Kya rate hai gloves ka?
    </Say>
    <Gather input="speech" action="/webhook/item2_gemini" timeout="25" speechTimeout="auto" enhanced="true" speechModel="experimental_conversations" language="hi-IN,en-IN,hi,en">
        <Say voice="Polly.Aditi" rate="slow" language="hi-IN">
            Laboratory gloves ka rate per piece batayiye sir.
        </Say>
    </Gather>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/webhook/item2_gemini', methods=['POST'])
def item2_handler_gemini():
    """Gemini-enhanced second item handling with conversation closure"""
    speech = request.form.get('SpeechResult', '').strip()
    call_sid = request.form.get('CallSid', '')
    
    print(f"🎤 GLOVES QUOTE (GEMINI): '{speech}'")
    
    # Final analysis
    context = {
        'conversation_stage': 'final_item',
        'current_item': 'Laboratory Gloves Nitrile',
        'conversation_ending': True
    }
    
    analysis = conversation_manager.analyze_speech_intent(speech, context)
    price, confidence = conversation_manager.extract_price_with_context(speech, "Laboratory gloves nitrile")
    
    if price and confidence > 0.6:
        log_quote_enhanced("Laboratory Gloves Nitrile", price, "INR", call_sid, speech, "Voice", "Gemini-Enhanced", confidence, context)
        confirmation = f"Perfect sir! Gloves {price} rupees per piece. Bahut accha rate hai."
    else:
        confirmation = "Gloves ka rate samjha sir, dhanyawad."
    
    # Generate intelligent closing
    closing_response = conversation_manager.generate_natural_response({
        'intent': 'conversation_closing',
        'quotes_collected': True,
        'business_successful': True
    }, context)
    
    closing_text = closing_response.get('hindi_text', 
        'Bahut dhanyawad sir! Aapke rates note kar liye hain. Purchase order jaldi bhejenge.')
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" rate="slow" language="hi-IN">
        {confirmation}
    </Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" rate="slow" language="en-IN">
        Thank you very much sir for providing the quotes.
        Our procurement team will review and send purchase order soon.
    </Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" rate="slow" language="hi-IN">
        {closing_text}
        Business karne ke liye bahut dhanyawad sir.
        Namaste ji!
    </Say>
</Response>'''
    
    return twiml, 200, {'Content-Type': 'text/xml'}

@app.route('/health')
def health_gemini():
    """Enhanced health check with Gemini status"""
    gemini_status = "connected" if GEMINI_API_KEY else "not_configured"
    return {
        "status": "healthy", 
        "ai_engine": "Google Gemini 2.0 Flash",
        "gemini_status": gemini_status,
        "features": ["intelligent_conversation", "context_awareness", "bilingual_understanding"],
        "languages": ["Hindi", "English", "Hinglish"], 
        "voice_recognition": "twilio+gemini-enhanced"
    }

@app.route('/quotes')
def show_quotes_gemini():
    """Display Gemini-enhanced quotes"""
    try:
        quotes_html = "<h2>🤖 Gemini-Enhanced Bilingual Quotes</h2>"
        quotes_html += "<h3>Intelligent conversation analysis and quote extraction</h3>"
        with open('quotes_live_gemini.csv', 'r') as f:
            content = f.read()
        quotes_html += f"<pre>{content}</pre>"
        
        # Show conversation insights
        quotes_html += "<h3>🧠 Conversation Insights</h3>"
        quotes_html += f"<pre>{json.dumps(conversation_manager.conversation_history, indent=2)}</pre>"
        
        return quotes_html
    except:
        return "<h2>🤖 कोई Gemini-enhanced quotes अभी तक collect नहीं हुए</h2>"

@app.route('/webhook/status', methods=['POST'])
def status_handler_gemini():
    """Enhanced status handler"""
    status = request.form.get('CallStatus', '')
    call_sid = request.form.get('CallSid', '')
    duration = request.form.get('CallDuration', '0')
    print(f"📊 GEMINI CALL STATUS: {status} (SID: {call_sid}, Duration: {duration}s)")
    
    # Log conversation completion
    conversation_manager.current_context['call_completed'] = True
    conversation_manager.current_context['call_duration'] = duration
    
    return 'OK'

if __name__ == '__main__':
    print("🚀 GEMINI-ENHANCED BILINGUAL WEBHOOK SERVER")
    print("🤖 AI Engine: Google Gemini 2.0 Flash")  
    print("🧠 Features: Intelligent conversation, context awareness")
    print("🇮🇳 Languages: Hindi + English + Hinglish Mix")
    print("💰 Currency: Indian Rupees (INR)")
    print("🎤 Voice: Twilio + Gemini Enhanced Analysis")
    
    if not GEMINI_API_KEY:
        print("⚠️  WARNING: GEMINI_API_KEY not found. Set it as environment variable.")
        print("   Get your key from: https://aistudio.google.com/")
    
    app.run(host='0.0.0.0', port=5000, debug=False) 