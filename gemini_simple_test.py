#!/usr/bin/env python3
"""
Simple Gemini API Test - Verify Your Setup
Tests basic Gemini functionality before running the full Live API system
"""

import os
import json
from flask import Flask, request, jsonify
import google.generativeai as genai
from datetime import datetime

app = Flask(__name__)

# Initialize Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
print(f"🔑 API Key found: {'Yes' if GEMINI_API_KEY else 'No'}")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Try models in order of preference (free tier friendly)
    model_options = [
        'models/gemini-1.5-flash',
        'models/gemini-1.5-flash-8b', 
        'models/gemini-2.0-flash-lite',
        'models/gemini-1.5-flash-latest',
        'gemini-1.5-flash'
    ]
    
    model = None
    for model_name in model_options:
        try:
            model = genai.GenerativeModel(model_name)
            # Test the model with a simple prompt
            test_response = model.generate_content("Say hello")
            print(f"✅ Using model: {model_name}")
            break
        except Exception as e:
            print(f"⚠️  Model {model_name} failed: {str(e)[:100]}...")
            continue
    
    if not model:
        print("❌ No Gemini models are working! Check your quota.")
        print("💡 Visit: https://ai.google.dev/gemini-api/docs/rate-limits")
else:
    print("❌ GEMINI_API_KEY not found!")
    model = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    api_key_status = "configured" if GEMINI_API_KEY else "missing"
    
    return jsonify({
        "status": "healthy",
        "system": "Gemini API Test Server",
        "gemini_api_key": api_key_status,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/test_gemini', methods=['POST'])
def test_gemini():
    """Test Gemini API with a simple conversation"""
    if not model:
        return jsonify({
            "error": "Gemini API not configured",
            "message": "Please set GEMINI_API_KEY environment variable"
        }), 400
    
    try:
        # Test prompt for Hindi-English conversation
        test_prompt = """
        You are an intelligent procurement assistant for an Indian company. 
        A vendor just said: "Petri dishes ka rate 50 rupees per piece hai sir"
        
        Extract the following information:
        - Item name
        - Price per piece
        - Currency
        - Language used (Hindi/English/Hinglish)
        
        Respond in JSON format and also provide a natural response to continue the conversation.
        """
        
        response = model.generate_content(test_prompt)
        
        return jsonify({
            "status": "success",
            "gemini_response": response.text,
            "test_prompt": test_prompt,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "error": "Gemini API error",
            "message": str(e)
        }), 500

@app.route('/simulate_conversation', methods=['POST'])
def simulate_conversation():
    """Simulate a vendor conversation"""
    if not model:
        return jsonify({"error": "Gemini not configured"}), 400
    
    data = request.get_json()
    vendor_input = data.get('vendor_input', '')
    
    if not vendor_input:
        return jsonify({"error": "vendor_input required"}), 400
    
    try:
        conversation_prompt = f"""
        You are conducting a procurement call with an Indian vendor. The vendor just said:
        "{vendor_input}"
        
        Your task:
        1. Extract any pricing information (item name, price, currency)
        2. Respond naturally to continue collecting quotes for laboratory items
        3. If no price was given, ask for specific items: Petri dishes, Laboratory gloves, Microscope slides
        
        Respond in natural Hindi-English mix suitable for Indian business.
        
        Format your response as JSON:
        {{
            "extracted_quote": {{"item": "...", "price": "...", "currency": "..."}},
            "ai_response": "Your natural response to the vendor",
            "next_action": "what to do next"
        }}
        """
        
        response = model.generate_content(conversation_prompt)
        
        return jsonify({
            "status": "success",
            "vendor_input": vendor_input,
            "ai_analysis": response.text,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "error": "Conversation simulation failed",
            "message": str(e)
        }), 500

@app.route('/', methods=['GET'])
def home():
    """Simple home page"""
    return f"""
    <html>
    <head><title>🤖 Gemini API Test</title></head>
    <body style="font-family: Arial; padding: 40px; background: #f5f5f5;">
        <h1>🤖 Gemini API Test Server</h1>
        <p><strong>Status:</strong> {'✅ Ready' if model else '❌ Not Configured'}</p>
        <p><strong>API Key:</strong> {'✅ Found' if GEMINI_API_KEY else '❌ Missing'}</p>
        
        <h2>🧪 Test Endpoints:</h2>
        <ul>
            <li><a href="/health">Health Check</a></li>
        </ul>
        
        <h2>🎯 Test Gemini Intelligence:</h2>
        <button onclick="testGemini()">Test Gemini API</button>
        <div id="result" style="margin-top: 20px; padding: 20px; background: white; border-radius: 5px;"></div>
        
        <h2>💬 Simulate Vendor Conversation:</h2>
        <input type="text" id="vendorInput" placeholder="Enter vendor response..." style="width: 400px; padding: 10px;">
        <button onclick="simulateConversation()">Simulate</button>
        
        <script>
        async function testGemini() {{
            const result = document.getElementById('result');
            result.innerHTML = 'Testing Gemini API...';
            
            try {{
                const response = await fetch('/test_gemini', {{method: 'POST'}});
                const data = await response.json();
                result.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            }} catch (error) {{
                result.innerHTML = 'Error: ' + error.message;
            }}
        }}
        
        async function simulateConversation() {{
            const vendorInput = document.getElementById('vendorInput').value;
            const result = document.getElementById('result');
            
            if (!vendorInput) {{
                alert('Please enter vendor input');
                return;
            }}
            
            result.innerHTML = 'Simulating conversation...';
            
            try {{
                const response = await fetch('/simulate_conversation', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{'vendor_input': vendorInput}})
                }});
                const data = await response.json();
                result.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            }} catch (error) {{
                result.innerHTML = 'Error: ' + error.message;
            }}
        }}
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("🚀 GEMINI API TEST SERVER")
    print("🔧 Testing basic Gemini functionality")
    print("🌐 Open http://localhost:5000 to test")
    
    if not GEMINI_API_KEY:
        print("⚠️  WARNING: GEMINI_API_KEY not found!")
        print("   Set it with: $env:GEMINI_API_KEY='your_key_here'")
    else:
        print("✅ Gemini API key configured")
        print("📝 Ready to test intelligent conversation!")
    
    app.run(host='0.0.0.0', port=5000, debug=False) 