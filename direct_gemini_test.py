#!/usr/bin/env python3
"""
Direct Gemini API Test - No Server Required
Shows the power of Gemini for understanding Hindi-English conversations
"""

import os
import json
import google.generativeai as genai

# Set up Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
print(f"🔑 API Key: {'Found ✅' if GEMINI_API_KEY else 'Missing ❌'}")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Try models in order of preference (quota-friendly)
    model_options = [
        'models/gemini-1.5-flash-8b',      # Fastest, lowest quota usage
        'models/gemini-2.0-flash-lite',    # Fast and efficient  
        'models/gemini-1.5-flash',         # Good balance
        'gemini-1.5-flash',                # Alternative name
        'models/gemini-1.5-flash-latest'   # Latest version
    ]
    
    model = None
    working_model = None
    
    for model_name in model_options:
        try:
            print(f"🧪 Trying model: {model_name}")
            test_model = genai.GenerativeModel(model_name)
            # Quick test
            test_response = test_model.generate_content("Hi")
            model = test_model
            working_model = model_name
            print(f"✅ SUCCESS! Using: {model_name}")
            break
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower():
                print(f"⚠️  Quota exceeded for {model_name}")
            elif "404" in error_msg:
                print(f"⚠️  Model {model_name} not found")
            else:
                print(f"⚠️  {model_name} failed: {error_msg[:80]}...")
            continue
    
    if not model:
        print("\n❌ NO WORKING MODELS FOUND!")
        print("🔍 Possible issues:")
        print("   1. 📊 Quota exceeded (free tier limit)")
        print("   2. 🔑 API key issues")
        print("   3. 🌐 Network connectivity")
        print("\n💡 Solutions:")
        print("   • Wait a few minutes and try again")
        print("   • Check quota: https://ai.google.dev/gemini-api/docs/rate-limits")
        print("   • Verify API key: https://aistudio.google.com/apikey")
        exit(1)
else:
    print("❌ Please set GEMINI_API_KEY first!")
    exit(1)

def test_vendor_conversation(vendor_input):
    """Test Gemini's understanding of vendor conversation"""
    
    prompt = f"""
    You are an AI procurement assistant conducting business calls with Indian vendors.
    
    The vendor just said: "{vendor_input}"
    
    Your task:
    1. Extract any pricing information (item name, price per unit, currency)
    2. Identify the language mix (Hindi/English/Hinglish)
    3. Generate a natural response to continue the conversation
    4. Determine what to ask next
    
    Respond ONLY in valid JSON format:
    {{
        "extracted_info": {{
            "item": "item name or null",
            "price": "price number or null", 
            "currency": "INR/USD/etc or null",
            "unit": "per piece/per kg/etc or null"
        }},
        "language_analysis": "Hindi/English/Hinglish/Mixed",
        "vendor_sentiment": "positive/neutral/negative/confused",
        "ai_response": "Your natural Hindi-English response to vendor",
        "next_action": "what to do next in conversation"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {e}"

def main():
    """Run comprehensive tests"""
    
    print("🧠 GEMINI INTELLIGENCE DEMONSTRATION")
    print("🇮🇳 Testing Hindi-English Business Conversations")
    print("=" * 70)
    
    test_cases = [
        "Petri dishes ka rate 45 rupees per piece hai sir",
        "Laboratory gloves 60 rupees main mil jayenge",
        "Microscope slides 25 rs each hai bhaiya", 
        "Sorry sir, price list nahi hai abhi, kal bhej denge",
        "Bulk order hai to discount de sakte hain - 10% kam kar dete hain",
        "Transport charges alag lagenge sir, 50 rupees per order",
        "GST included hai ya separate hai sir?",
        "Quality achha hai, import kiya hai China se"
    ]
    
    for i, vendor_input in enumerate(test_cases, 1):
        print(f"\n🎤 Test {i}: '{vendor_input}'")
        print("-" * 50)
        
        result = test_vendor_conversation(vendor_input)
        
        try:
            # Try to parse as JSON
            data = json.loads(result)
            
            print("✅ GEMINI ANALYSIS:")
            if data.get('extracted_info'):
                info = data['extracted_info']
                if info.get('item') and info.get('price'):
                    print(f"   💰 Quote: {info['item']} = ₹{info['price']} {info.get('unit', '')}")
                else:
                    print("   💰 No clear pricing found")
                    
            print(f"   🗣️  Language: {data.get('language_analysis', 'Unknown')}")
            print(f"   😊 Sentiment: {data.get('vendor_sentiment', 'Unknown')}")
            print(f"   🤖 AI Response: {data.get('ai_response', 'No response')}")
            print(f"   🎯 Next Action: {data.get('next_action', 'Continue')}")
            
        except json.JSONDecodeError:
            print("✅ GEMINI RAW RESPONSE:")
            print(f"   {result}")
        except Exception as e:
            print(f"❌ Error processing: {e}")
    
    print("\n" + "=" * 70)
    print("🎯 KEY ADVANTAGES OVER YOUR CURRENT SYSTEM:")
    print("   ✅ Understands context, not just keywords")
    print("   ✅ Handles Hindi-English mixing naturally") 
    print("   ✅ Extracts pricing even when vendor speaks unclearly")
    print("   ✅ Generates intelligent responses")
    print("   ✅ Adapts to vendor's communication style")
    print("\n🚀 Ready to replace your Twilio system with this intelligence!")

if __name__ == "__main__":
    main() 