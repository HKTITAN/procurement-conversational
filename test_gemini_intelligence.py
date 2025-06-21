#!/usr/bin/env python3
"""
Quick test of Gemini intelligence
"""
import requests
import json

def test_gemini_intelligence():
    """Test Gemini's understanding of Hindi-English conversations"""
    
    test_cases = [
        "Petri dishes ka rate 45 rupees per piece hai sir",
        "Laboratory gloves 60 rupees main mil jayenge",
        "Microscope slides 25 rs each hai bhaiya",
        "Sab items milenge but price thoda high hai",
        "Delivery 2 days main ho jayegi, payment advance chahiye"
    ]
    
    print("🧠 TESTING GEMINI INTELLIGENCE")
    print("=" * 60)
    
    for i, vendor_input in enumerate(test_cases, 1):
        print(f"\n🎤 Test {i}: Vendor says: '{vendor_input}'")
        print("-" * 40)
        
        try:
            response = requests.post(
                'http://localhost:5000/simulate_conversation',
                json={'vendor_input': vendor_input},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Gemini Response:")
                try:
                    # Try to parse the AI analysis as JSON
                    ai_analysis = json.loads(data['ai_analysis'])
                    if 'extracted_quote' in ai_analysis:
                        quote = ai_analysis['extracted_quote']
                        print(f"   💰 Extracted Quote: {quote}")
                    if 'ai_response' in ai_analysis:
                        print(f"   🤖 AI Response: {ai_analysis['ai_response']}")
                except:
                    # If not JSON, just show the raw response
                    print(f"   🤖 Raw Response: {data['ai_analysis']}")
            else:
                print(f"❌ Error: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Server not running. Please start gemini_simple_test.py first!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 This shows how much smarter Gemini is than basic regex!")

if __name__ == "__main__":
    test_gemini_intelligence() 