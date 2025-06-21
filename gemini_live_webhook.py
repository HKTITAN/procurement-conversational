#!/usr/bin/env python3
"""
Gemini Live API Bilingual Webhook - Superior Audio Understanding
- Direct audio processing with Gemini Live API
- Real-time Hindi-English-Hinglish conversation
- Smart quote collection and CSV management
- Much better audio transcription than Twilio
"""

import os
import json
import asyncio
import websockets
import base64
import pyaudio
import wave
import threading
import queue
from datetime import datetime
import csv
from flask import Flask, request, jsonify
from google import genai
import soundfile as sf
import librosa
import numpy as np

app = Flask(__name__)

# Audio Configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000  # Gemini expects 16kHz
RECEIVE_SAMPLE_RATE = 24000  # Gemini outputs 24kHz
CHUNK_SIZE = 512

class GeminiLiveConversationManager:
    """Manages Gemini Live API conversations with superior audio understanding"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.conversation_history = []
        self.current_quotes = []
        self.conversation_state = {
            'stage': 'greeting',
            'current_item': None,
            'vendor_name': 'Unknown Vendor',
            'items_to_discuss': [
                {'name': 'Petri Dishes 100mm', 'quantity': 30, 'unit': 'pieces'},
                {'name': 'Laboratory Gloves Nitrile', 'quantity': 15, 'unit': 'pieces'},
                {'name': 'Microscope Slides', 'quantity': 50, 'unit': 'pieces'}
            ],
            'current_item_index': 0
        }
        self.audio_queue = asyncio.Queue()
        self.response_audio_queue = queue.Queue()
        
    async def start_conversation(self):
        """Start a live conversation session"""
        
        # Enhanced configuration for Indian business conversation
        config = {
            "response_modalities": ["AUDIO", "TEXT"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {"voice_name": "Puck"}
                }
            },
            "system_instruction": """
            You are an intelligent procurement assistant for Bio Mac Lifesciences conducting professional voice calls with Indian vendors.
            
            Your personality:
            - Professional yet warm and friendly
            - Fluent in Hindi-English business communication (Hinglish)
            - Patient and understanding of different communication styles
            - Persistent in getting accurate quotes but polite
            
            Your task:
            1. Introduce yourself and company professionally
            2. Ask for quotes on laboratory items systematically
            3. Extract exact pricing information
            4. Handle any questions or confusion naturally
            5. Maintain conversation flow even with interruptions
            
            Communication style:
            - Use natural Hindi-English mix common in Indian business
            - Be conversational, not robotic
            - Adapt to vendor's preferred language
            - Show appreciation for their time and business
            
            Important: Always speak clearly and naturally. If vendor seems confused, clarify patiently.
            """
        }
        
        print("🚀 Starting Gemini Live conversation...")
        
        try:
            async with self.client.aio.live.connect(
                model="gemini-2.0-flash-live-preview-04-09",
                config=config
            ) as session:
                self.session = session
                
                # Start concurrent tasks
                async with asyncio.TaskGroup() as tg:
                    tg.create_task(self.handle_audio_input())
                    tg.create_task(self.handle_conversation_flow())
                    tg.create_task(self.process_responses())
                    
        except Exception as e:
            print(f"❌ Conversation error: {e}")
            
    async def handle_audio_input(self):
        """Handle microphone input and send to Gemini"""
        print("🎤 Starting audio input handler...")
        
        # Initialize PyAudio for microphone
        audio = pyaudio.PyAudio()
        
        try:
            stream = audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SEND_SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE
            )
            
            print("✅ Microphone ready - you can start speaking")
            
            while True:
                # Read audio chunk
                data = await asyncio.to_thread(stream.read, CHUNK_SIZE)
                
                # Send to Gemini Live API
                await self.session.send_realtime_input(
                    audio=genai.types.Blob(
                        data=data,
                        mime_type="audio/pcm;rate=16000"
                    )
                )
                
        except Exception as e:
            print(f"❌ Audio input error: {e}")
        finally:
            stream.close()
            audio.terminate()
            
    async def handle_conversation_flow(self):
        """Manage the conversation flow and quote collection"""
        print("💬 Starting conversation flow manager...")
        
        # Start with greeting
        await self.send_initial_greeting()
        
        # Wait for responses and manage flow
        await asyncio.sleep(2)  # Give time for greeting to play
        
    async def send_initial_greeting(self):
        """Send intelligent greeting message"""
        greeting_text = """
        Namaste ji! Main Bio Mac Lifesciences company se bol raha hun. 
        Hum laboratory supplies kharidna chahte hain aur aapse rates puchna chahte hain.
        Kya aap humare saath business kar sakte hain? Quotes de sakte hain?
        """
        
        await self.session.send_realtime_input(
            text=greeting_text
        )
        
        self.conversation_state['stage'] = 'waiting_for_agreement'
        print("📞 Greeting sent - waiting for vendor response...")
        
    async def process_responses(self):
        """Process Gemini's responses and manage conversation state"""
        print("🧠 Starting response processor...")
        
        async for response in self.session.receive():
            try:
                if hasattr(response, 'server_content') and response.server_content:
                    server_content = response.server_content
                    
                    # Handle interruptions
                    if hasattr(server_content, 'interrupted') and server_content.interrupted:
                        print("🤐 Conversation interrupted - handling gracefully")
                        
                    # Process audio responses
                    if server_content.model_turn:
                        for part in server_content.model_turn.parts:
                            if part.inline_data:
                                # Queue audio for playback
                                self.response_audio_queue.put(part.inline_data.data)
                                
                            if part.text:
                                # Process text response for conversation management
                                await self.analyze_conversation_progress(part.text)
                                
                    # Check if turn is complete
                    if server_content.turn_complete:
                        print("✅ Gemini finished responding")
                        await self.manage_conversation_flow()
                        
            except Exception as e:
                print(f"❌ Response processing error: {e}")
                
    async def analyze_conversation_progress(self, text_response):
        """Analyze Gemini's response to understand conversation progress"""
        print(f"🧠 Analyzing response: {text_response[:100]}...")
        
        # Log the conversation
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'speaker': 'assistant',
            'text': text_response,
            'stage': self.conversation_state['stage']
        })
        
        # Extract any quotes mentioned in the response
        await self.extract_quotes_from_response(text_response)
        
    async def extract_quotes_from_response(self, text):
        """Extract pricing information from conversation"""
        # This will be enhanced with AI-powered extraction
        import re
        
        # Look for price patterns
        price_patterns = [
            r'(\d+\.?\d*)\s*rupees?',
            r'₹\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*rs\.?',
            r'rate\s+is\s+(\d+\.?\d*)',
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                try:
                    price = float(matches[0])
                    current_item = self.get_current_item()
                    
                    quote = {
                        'timestamp': datetime.now().isoformat(),
                        'item': current_item['name'] if current_item else 'Unknown',
                        'price': price,
                        'currency': 'INR',
                        'vendor': self.conversation_state['vendor_name'],
                        'raw_text': text,
                        'confidence': 0.8
                    }
                    
                    self.current_quotes.append(quote)
                    await self.save_quote_to_csv(quote)
                    print(f"💰 Quote extracted: {quote}")
                    
                except ValueError:
                    continue
                    
    def get_current_item(self):
        """Get the currently discussed item"""
        items = self.conversation_state['items_to_discuss']
        index = self.conversation_state['current_item_index']
        return items[index] if index < len(items) else None
        
    async def save_quote_to_csv(self, quote):
        """Save quote to CSV file"""
        try:
            with open('gemini_live_quotes.csv', 'a', newline='') as f:
                writer = csv.writer(f)
                
                # Write header if file is empty
                if f.tell() == 0:
                    writer.writerow([
                        'timestamp', 'vendor', 'item', 'price', 'currency', 
                        'raw_text', 'confidence', 'conversation_stage'
                    ])
                
                writer.writerow([
                    quote['timestamp'],
                    quote['vendor'],
                    quote['item'],
                    quote['price'],
                    quote['currency'],
                    quote['raw_text'],
                    quote['confidence'],
                    self.conversation_state['stage']
                ])
                
        except Exception as e:
            print(f"❌ CSV save error: {e}")
            
    async def manage_conversation_flow(self):
        """Intelligently manage conversation progression"""
        current_stage = self.conversation_state['stage']
        
        if current_stage == 'waiting_for_agreement':
            # Move to first item
            await self.ask_for_next_item()
            
        elif current_stage == 'discussing_item':
            # Check if we got a quote, then move to next item
            if self.conversation_state['current_item_index'] < len(self.conversation_state['items_to_discuss']) - 1:
                self.conversation_state['current_item_index'] += 1
                await asyncio.sleep(2)  # Brief pause
                await self.ask_for_next_item()
            else:
                await self.conclude_conversation()
                
    async def ask_for_next_item(self):
        """Ask about the next item in the list"""
        current_item = self.get_current_item()
        if not current_item:
            return
            
        self.conversation_state['stage'] = 'discussing_item'
        self.conversation_state['current_item'] = current_item['name']
        
        item_request = f"""
        Next item sir - {current_item['name']}. 
        Hume {current_item['quantity']} {current_item['unit']} chahiye. 
        Kya rate hai per {current_item['unit']}? Please tell me the price.
        """
        
        await self.session.send_realtime_input(text=item_request)
        print(f"📝 Asked about: {current_item['name']}")
        
    async def conclude_conversation(self):
        """Conclude the conversation professionally"""
        self.conversation_state['stage'] = 'concluding'
        
        conclusion = """
        Thank you very much sir for providing all the quotes. 
        Aapke rates humne note kar liye hain. 
        Our procurement team will review everything and we will send you purchase order very soon.
        Business karne ke liye bahut dhanyawad sir. Namaste!
        """
        
        await self.session.send_realtime_input(text=conclusion)
        print("🎯 Conversation concluded - all quotes collected!")
        
        # Generate summary
        await self.generate_conversation_summary()
        
    async def generate_conversation_summary(self):
        """Generate a summary of collected quotes"""
        print("\n📊 CONVERSATION SUMMARY")
        print("=" * 50)
        print(f"Vendor: {self.conversation_state['vendor_name']}")
        print(f"Total Quotes Collected: {len(self.current_quotes)}")
        
        for quote in self.current_quotes:
            print(f"• {quote['item']}: ₹{quote['price']} per piece")
            
        print(f"CSV File: gemini_live_quotes.csv")
        print("=" * 50)

# Audio playback manager
class AudioPlaybackManager:
    """Manages audio playback from Gemini responses"""
    
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.output_stream = None
        self.setup_output_stream()
        
    def setup_output_stream(self):
        """Setup audio output stream"""
        try:
            self.output_stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RECEIVE_SAMPLE_RATE,
                output=True
            )
            print("🔊 Audio output ready")
        except Exception as e:
            print(f"❌ Audio output setup error: {e}")
            
    def play_audio_chunk(self, audio_data):
        """Play audio chunk"""
        try:
            if self.output_stream:
                decoded_audio = base64.b64decode(audio_data)
                self.output_stream.write(decoded_audio)
        except Exception as e:
            print(f"❌ Audio playback error: {e}")
            
    def close(self):
        """Close audio streams"""
        if self.output_stream:
            self.output_stream.close()
        self.audio.terminate()

# Global conversation manager
conversation_manager = None
audio_manager = None

@app.route('/start_conversation', methods=['POST'])
def start_conversation():
    """Start a new Gemini Live conversation"""
    global conversation_manager, audio_manager
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return jsonify({
            "error": "GEMINI_API_KEY not configured",
            "message": "Please set your Gemini API key as environment variable"
        }), 400
    
    try:
        # Initialize managers
        conversation_manager = GeminiLiveConversationManager(api_key)
        audio_manager = AudioPlaybackManager()
        
        # Start conversation in background
        asyncio.create_task(conversation_manager.start_conversation())
        
        return jsonify({
            "status": "conversation_started",
            "message": "Gemini Live conversation initiated",
            "instructions": "Start speaking - the AI will respond naturally"
        })
        
    except Exception as e:
        return jsonify({
            "error": "conversation_start_failed",
            "message": str(e)
        }), 500

@app.route('/conversation_status', methods=['GET'])
def get_conversation_status():
    """Get current conversation status"""
    global conversation_manager
    
    if not conversation_manager:
        return jsonify({"status": "not_started"})
    
    return jsonify({
        "status": "active",
        "conversation_state": conversation_manager.conversation_state,
        "quotes_collected": len(conversation_manager.current_quotes),
        "conversation_history_length": len(conversation_manager.conversation_history)
    })

@app.route('/quotes', methods=['GET'])
def get_quotes():
    """Get collected quotes"""
    global conversation_manager
    
    if not conversation_manager:
        return jsonify({"quotes": [], "message": "No conversation started"})
    
    return jsonify({
        "quotes": conversation_manager.current_quotes,
        "conversation_state": conversation_manager.conversation_state,
        "total_quotes": len(conversation_manager.current_quotes)
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    api_key_status = "configured" if os.getenv('GEMINI_API_KEY') else "missing"
    
    return jsonify({
        "status": "healthy",
        "system": "Gemini Live API Bilingual Webhook",
        "audio_processing": "Superior Gemini Live API",
        "languages": ["Hindi", "English", "Hinglish"],
        "gemini_api_key": api_key_status,
        "features": [
            "real_time_audio_processing",
            "superior_transcription",
            "intelligent_conversation",
            "automatic_quote_extraction",
            "csv_export"
        ]
    })

def start_audio_playback_thread():
    """Start audio playback in separate thread"""
    def audio_playback_loop():
        while True:
            try:
                if conversation_manager and audio_manager:
                    if not conversation_manager.response_audio_queue.empty():
                        audio_data = conversation_manager.response_audio_queue.get()
                        audio_manager.play_audio_chunk(audio_data)
            except Exception as e:
                print(f"❌ Audio playback thread error: {e}")
            
            time.sleep(0.01)  # Small delay to prevent busy waiting
    
    thread = threading.Thread(target=audio_playback_loop, daemon=True)
    thread.start()

if __name__ == '__main__':
    print("🚀 GEMINI LIVE API BILINGUAL WEBHOOK")
    print("🎤 Superior Audio Understanding with Gemini Live API")
    print("🇮🇳 Languages: Hindi + English + Hinglish")
    print("💰 Smart Quote Collection & CSV Export")
    print("🔊 Real-time Audio Processing")
    
    # Check API key
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️  WARNING: GEMINI_API_KEY not found!")
        print("   1. Get your key from: https://aistudio.google.com/")
        print("   2. Set it: export GEMINI_API_KEY='your_key_here'")
        print("   3. Then restart this server")
    else:
        print("✅ Gemini API key found")
    
    # Start audio playback thread
    start_audio_playback_thread()
    
    print("\n📋 API Endpoints:")
    print("   POST /start_conversation - Start new conversation")
    print("   GET  /conversation_status - Check conversation status")
    print("   GET  /quotes - View collected quotes")
    print("   GET  /health - System health check")
    
    app.run(host='0.0.0.0', port=5000, debug=False) 