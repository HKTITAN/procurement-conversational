#!/usr/bin/env python3
"""
Speech Demo Call - Shows how speech recognition would work
Demonstrates intelligent conversation with simulated speech recognition
"""

import os
import requests
import json
import time
from datetime import datetime
import base64
import google.generativeai as genai

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

def generate_intelligent_response(vendor_speech):
    """Use Gemini to generate intelligent response to vendor speech"""
    if not model:
        return "Samjha sir, dhanyawad!"
    
    try:
        prompt = f"""
        You are Bio Mac Lifesciences calling a vendor for laboratory supplies. 
        The vendor just said: "{vendor_speech}"
        
        Generate a natural Hindi-English response that:
        1. Acknowledges what they said
        2. Asks for specific pricing if they mentioned items
        3. Follows up on business details
        4. Keeps the conversation professional but friendly
        5. Uses natural Indian business language (Hinglish)
        
        Respond in 1-2 sentences maximum, as if speaking on phone.
        """
        
        response = model.generate_content(prompt)
        ai_response = response.text.strip()
        return ai_response
        
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return "Haan sir, samjha. Aur kuch bataiye?"

def make_speech_demo_call(phone_number="+918800000488", vendor_name="ABC Medical Supplies"):
    """Make a call that demonstrates how speech recognition would work"""
    
    print("🎤 MAKING SPEECH RECOGNITION DEMO CALL")
    print("=" * 60)
    
    # Get credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER', '+14323484517')
    
    if not account_sid or not auth_token:
        print("❌ Missing Twilio credentials!")
        return False
    
    print(f"✅ Account SID: {account_sid[:10]}...")
    print(f"✅ From Number: {from_number}")
    print(f"📞 To Number: {phone_number}")
    print(f"🏢 Vendor: {vendor_name}")
    print(f"🧠 AI: {'Gemini Ready' if model else 'Fallback Mode'}")
    
    # Simulate some vendor responses to show intelligent conversation
    sample_responses = [
        "Petri dishes 45 rupees per piece hai sir",
        "Laboratory gloves 60 rupees main mil jayenge", 
        "Microscope slides 25 rs each hai bhaiya",
        "Bulk order hai to discount de sakte hain"
    ]
    
    print(f"\n🎭 SIMULATED CONVERSATION DEMO:")
    print("=" * 50)
    
    for i, vendor_response in enumerate(sample_responses, 1):
        print(f"\n🎤 Simulated Vendor Response {i}:")
        print(f"   '{vendor_response}'")
        
        ai_response = generate_intelligent_response(vendor_response)
        print(f"🧠 AI Generated Response:")
        print(f"   '{ai_response}'")
        
        time.sleep(1)  # Pause for readability
    
    # Create TwiML that explains the demo
    twiml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <!-- Introduction -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Namaste! Main Bio Mac Lifesciences se bol raha hun. 
        Main aapko speech recognition demo kar raha hun.
    </Say>
    
    <Pause length="2"/>
    
    <!-- Explain the demo -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Normal situation mein, main aapka response sunega aur Gemini AI se 
        intelligent jawab generate karega. 
        Lekin abhi technical limitation hai localhost ke wajah se.
    </Say>
    
    <Pause length="2"/>
    
    <!-- Show what would happen -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Agar aap kehte: Petri dishes 45 rupees per piece hai sir,
        to main samjhunga aur puchunga: Kitni quantity mein chahiye? Discount kya hai bulk order mein?
    </Say>
    
    <Pause length="2"/>
    
    <!-- Explain solution -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Real production mein, hum ngrok ya public server use karenge 
        speech recognition ke liye. Tab yeh fully interactive hoga.
    </Say>
    
    <Pause length="1"/>
    
    <!-- Closing -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Demo complete! System ready hai production ke liye. 
        Dhanyawad aur namaste!
    </Say>
    
    <Hangup/>
</Response>"""
    
    # Make the call
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"
    
    # Authentication
    auth = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Call parameters
    data = {
        'From': from_number,
        'To': phone_number,
        'Twiml': twiml_content,
        'Record': 'true',
        'Timeout': '30'
    }
    
    try:
        print(f"\n📞 INITIATING DEMO CALL...")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Purpose: Demonstrate speech recognition capability")
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 201:
            call_data = response.json()
            call_sid = call_data['sid']
            
            print(f"✅ DEMO CALL INITIATED!")
            print(f"🆔 Call SID: {call_sid}")
            print(f"📊 Status: {call_data['status']}")
            
            print(f"\n🎤 CALL WILL EXPLAIN:")
            print(f"   • How speech recognition would work")
            print(f"   • Current technical limitation (localhost)")
            print(f"   • Solution for production (ngrok/public server)")
            print(f"   • AI response examples")
            
            return call_sid
            
        else:
            print(f"❌ DEMO CALL FAILED!")
            print(f"📊 Status Code: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

def explain_speech_recognition_solution():
    """Explain how to enable real speech recognition"""
    print("\n💡 HOW TO ENABLE REAL SPEECH RECOGNITION:")
    print("=" * 60)
    print("🔧 CURRENT ISSUE:")
    print("   • Twilio needs publicly accessible webhook URLs")
    print("   • localhost:5000 is not reachable from Twilio servers")
    print("   • Speech recognition needs real-time webhook responses")
    print()
    print("✅ SOLUTIONS:")
    print("   1. 🌐 NGROK (Easiest):")
    print("      • Install: https://ngrok.com/download")
    print("      • Run: ngrok http 5000")
    print("      • Use the public URL in webhook")
    print()
    print("   2. 🏗️ CLOUD DEPLOYMENT:")
    print("      • Deploy to Heroku, AWS, or Google Cloud")
    print("      • Use public domain for webhooks")
    print()
    print("   3. 📱 TWILIO STUDIO:")
    print("      • Visual flow builder")
    print("      • Built-in speech recognition")
    print("      • No server needed")
    print()
    print("🚀 WHAT WORKS NOW:")
    print("   ✅ Making calls with natural Indian voice")
    print("   ✅ Gemini AI intelligence for response generation")
    print("   ✅ Realistic procurement conversations")
    print("   ✅ Quote extraction from pre-defined responses")
    print()
    print("📈 NEXT STEPS FOR FULL SPEECH RECOGNITION:")
    print("   1. Set up ngrok or cloud deployment")
    print("   2. Update webhook URLs to public addresses")
    print("   3. Test real-time speech recognition")
    print("   4. Deploy for production vendor calling")

def main():
    """Main function"""
    print("🎤 SPEECH RECOGNITION DEMO SYSTEM")
    print("🧠 Shows how Gemini AI would respond to vendor speech")
    print("=" * 70)
    
    # Show simulated conversation first
    if model:
        print("\n🎭 TESTING GEMINI AI RESPONSES:")
        print("=" * 40)
        
        test_speeches = [
            "Petri dishes 45 rupees per piece hai sir",
            "Laboratory gloves 60 rupees main mil jayenge",
            "Sorry sir, price list nahi hai abhi",
            "Bulk order hai to discount de sakte hain"
        ]
        
        for speech in test_speeches:
            print(f"\n🎤 Vendor says: '{speech}'")
            response = generate_intelligent_response(speech)
            print(f"🧠 AI responds: '{response}'")
    
    # Test credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER')
    
    print(f"\n📋 Configuration:")
    print(f"   Account SID: {'✅ Set' if account_sid else '❌ Missing'}")
    print(f"   Auth Token: {'✅ Set' if auth_token else '❌ Missing'}")
    print(f"   From Number: {from_number if from_number else '❌ Missing'}")
    print(f"   Gemini AI: {'✅ Ready' if model else '❌ Not configured'}")
    
    if not account_sid or not auth_token:
        print("\n❌ Missing Twilio credentials!")
        explain_speech_recognition_solution()
        return
    
    try:
        print(f"\n🎯 Ready to demonstrate speech recognition!")
        print(f"📞 This will call and explain the system")
        
        phone = input(f"Phone number (+918800000488): ").strip()
        if not phone:
            phone = "+918800000488"
        
        if not phone.startswith('+'):
            phone = f"+{phone}"
        
        print(f"\n📞 About to make demo call:")
        print(f"   📱 From: {from_number}")
        print(f"   📞 To: {phone}")
        print(f"   🎯 Purpose: Speech recognition explanation")
        print(f"   🗣️ Voice: Natural Hindi (Polly.Aditi)")
        
        confirm = input(f"\nMake demo call? (y/N): ").strip().lower()
        
        if confirm == 'y':
            print(f"\n🚀 Making speech recognition demo call...")
            result = make_speech_demo_call(phone)
            
            if result:
                print(f"\n🎉 DEMO CALL SUCCESS!")
                print(f"📞 Call SID: {result}")
                print(f"🎤 Listen to the explanation of how speech recognition works")
                
                # Show the technical explanation
                explain_speech_recognition_solution()
            else:
                print(f"\n❌ Demo call failed")
        else:
            print(f"📞 Demo cancelled")
            explain_speech_recognition_solution()
    
    except KeyboardInterrupt:
        print(f"\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main() 