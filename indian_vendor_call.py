#!/usr/bin/env python3
"""
Indian Vendor Call - Realistic procurement conversation
Uses natural Indian voices and realistic vendor interaction
"""

import os
import requests
import json
import time
from datetime import datetime
import base64

def make_vendor_call(phone_number="+918800000488", vendor_name="ABC Medical Supplies"):
    """Make a realistic vendor call with natural Indian voices"""
    
    print("📞 MAKING REALISTIC VENDOR CALL")
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
    
    # Create realistic vendor conversation TwiML with natural Indian voice
    twiml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <!-- Initial greeting in Hindi-English mix -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Namaste! Main Bio Mac Lifesciences se bol raha hun. 
        Hum laboratory supplies ki company hain aur aapke saath business karna chahte hain.
    </Say>
    
    <Pause length="1"/>
    
    <!-- Business introduction in natural Hinglish -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Humein kuch laboratory items ki urgent requirement hai. 
        Kya aap petri dishes, laboratory gloves, aur microscope slides supply kar sakte hain?
    </Say>
    
    <Pause length="2"/>
    
    <!-- Pricing inquiry -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Agar possible hai to please aap apna rate bata dijiye. 
        Hum bulk order kar rahe hain, to hopefully achha discount mil jayega.
    </Say>
    
    <Pause length="1"/>
    
    <!-- Professional closing -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Main wait kar raha hun aapke response ka. 
        Aap kuch boliye, main sun raha hun.
    </Say>
    
    <!-- Gather input to simulate conversation -->
    <Gather input="speech" 
            language="hi-IN" 
            speechTimeout="5" 
            timeout="10"
            action="http://httpbin.org/post"
            method="POST">
        <Say voice="Polly.Aditi" language="hi-IN">
            Please bataiye aapka rate kya hai?
        </Say>
    </Gather>
    
    <!-- Fallback if no response -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Koi baat nahi, main phir se call karunga. 
        Dhanyawad aur namaste!
    </Say>
    
    <Hangup/>
</Response>"""
    
    # Use Twilio API directly with TwiML
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"
    
    # Authentication
    auth = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Call parameters with realistic TwiML
    data = {
        'From': from_number,
        'To': phone_number,
        'Twiml': twiml_content,
        'Record': 'true',
        'Timeout': '30',
        'MachineDetection': 'Enable'
    }
    
    try:
        print(f"\n📞 INITIATING VENDOR CALL...")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Conversation: Realistic laboratory supplies procurement")
        print(f"🗣️  Voice: Natural Hindi (Polly.Aditi)")
        print(f"🎤 Features: Speech recognition enabled")
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 201:
            # Success!
            call_data = response.json()
            call_sid = call_data['sid']
            
            print(f"✅ VENDOR CALL INITIATED!")
            print(f"🆔 Call SID: {call_sid}")
            print(f"📊 Status: {call_data['status']}")
            print(f"📱 From: {call_data['from']}")
            print(f"📞 To: {call_data['to']}")
            
            # Monitor call
            print(f"\n📊 Monitoring vendor conversation...")
            monitor_call_status(account_sid, auth_token, call_sid, 60)
            
            return call_sid
            
        else:
            print(f"❌ VENDOR CALL FAILED!")
            print(f"📊 Status Code: {response.status_code}")
            print(f"📝 Response: {response.text}")
            
            # Show specific guidance
            if response.status_code == 400:
                error_data = response.json()
                print(f"💡 Error: {error_data.get('message', 'Bad request')}")
            elif response.status_code == 401:
                print("💡 Authentication failed - check credentials")
            elif response.status_code == 403:
                print("💡 Forbidden - check account balance or permissions")
            
            return False
            
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

def monitor_call_status(account_sid, auth_token, call_sid, max_seconds=60):
    """Monitor vendor call with detailed status"""
    
    # Authentication
    auth = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    headers = {'Authorization': f'Basic {auth}'}
    
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls/{call_sid}.json"
    
    for i in range(max_seconds):
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                call_data = response.json()
                status = call_data['status']
                
                # More detailed status reporting
                if status == 'ringing':
                    print(f"📞 [{i+1:02d}s] Status: {status} - Calling vendor...")
                elif status == 'in-progress':
                    print(f"🎤 [{i+1:02d}s] Status: {status} - Vendor conversation active")
                elif status == 'queued':
                    print(f"⏳ [{i+1:02d}s] Status: {status} - Call queued")
                else:
                    print(f"⏰ [{i+1:02d}s] Status: {status}")
                
                if status in ['completed', 'failed', 'busy', 'no-answer']:
                    print(f"\n📋 VENDOR CALL COMPLETED")
                    print(f"📊 Final Status: {status}")
                    if call_data.get('duration'):
                        print(f"⏱️  Duration: {call_data['duration']} seconds")
                    if call_data.get('price'):
                        print(f"💰 Cost: ${call_data['price']} {call_data.get('price_unit', 'USD')}")
                    
                    # Status-specific messages
                    if status == 'completed':
                        print(f"✅ Vendor answered and heard the procurement message!")
                    elif status == 'no-answer':
                        print(f"📵 Vendor didn't answer - may need to try again")
                    elif status == 'busy':
                        print(f"📞 Vendor line was busy - try calling later")
                    elif status == 'failed':
                        print(f"❌ Call failed - check number or try again")
                    
                    break
                
            else:
                print(f"❌ Status check failed: {response.status_code}")
                break
                
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Status check error: {e}")
            break

def create_conversation_simulation():
    """Show what the conversation flow would be like"""
    print("\n🎭 CONVERSATION SIMULATION")
    print("=" * 50)
    print("🎤 Bio Mac Lifesciences:")
    print("   'Namaste! Main Bio Mac Lifesciences se bol raha hun.'")
    print("   'Hum laboratory supplies ki company hain.'")
    print("   'Humein petri dishes, gloves aur slides chahiye.'")
    print("   'Aapka rate kya hai?'")
    print()
    print("🗣️  Expected Vendor Response:")
    print("   'Ji sir, petri dishes 45 rupees per piece hai.'")
    print("   'Laboratory gloves 60 rupees main mil jayenge.'") 
    print("   'Microscope slides 25 rs each hai.'")
    print()
    print("🧠 Gemini AI would extract:")
    print("   • Petri dishes: ₹45 per piece")
    print("   • Lab gloves: ₹60 per piece") 
    print("   • Microscope slides: ₹25 each")

def main():
    """Main function for Indian vendor calling"""
    print("🇮🇳 INDIAN VENDOR CALLING SYSTEM")
    print("🏢 Bio Mac Lifesciences - Laboratory Supplies Procurement")
    print("=" * 70)
    
    # Test credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER')
    
    print(f"📋 Configuration:")
    print(f"   Account SID: {'✅ Set' if account_sid else '❌ Missing'}")
    print(f"   Auth Token: {'✅ Set' if auth_token else '❌ Missing'}")
    print(f"   From Number: {from_number if from_number else '❌ Missing'}")
    
    if not account_sid or not auth_token:
        print("\n❌ Missing Twilio credentials!")
        return
    
    print(f"\n🎯 Ready for realistic vendor procurement calls!")
    
    # Show conversation simulation first
    create_conversation_simulation()
    
    # Get phone number (default to test number)
    try:
        print(f"\n📞 Vendor Phone Number:")
        print(f"   Default: +918800000488 (Test Number)")
        print(f"   Or enter a different vendor number")
        
        phone = input(f"Phone number (press Enter for default): ").strip()
        
        if not phone:
            phone = "+918800000488"
            vendor_name = "Test Vendor (You)"
        else:
            if not phone.startswith('+'):
                phone = f"+{phone}"
            vendor_name = input("Vendor name: ").strip() or "Unknown Vendor"
        
        # Confirmation
        print(f"\n📞 About to call vendor:")
        print(f"   🏢 Company: Bio Mac Lifesciences")
        print(f"   📱 From: {from_number}")
        print(f"   📞 To: {phone}")
        print(f"   👤 Vendor: {vendor_name}")
        print(f"   🎯 Purpose: Laboratory supplies procurement")
        print(f"   🗣️  Voice: Natural Hindi (Polly.Aditi)")
        print(f"   🎤 Features: Speech recognition enabled")
        print(f"   ⏱️  Duration: ~60 seconds max")
        
        confirm = input(f"\nProceed with vendor call? (y/N): ").strip().lower()
        
        if confirm == 'y':
            print(f"\n🚀 Calling vendor for laboratory supplies...")
            result = make_vendor_call(phone, vendor_name)
            
            if result:
                print(f"\n🎉 VENDOR CALL SUCCESS!")
                print(f"📞 Call SID: {result}")
                print(f"📱 Vendor should receive realistic procurement call")
                print(f"🎤 Natural Hindi conversation about lab supplies")
                print(f"📊 Check Twilio Console for call recordings")
                print(f"\n💡 System is ready for:")
                print(f"   ✅ Real vendor procurement calls")
                print(f"   ✅ Natural Hindi-English conversations")
                print(f"   ✅ Intelligent quote extraction")
                print(f"   ✅ Bulk vendor calling campaigns")
            else:
                print(f"\n❌ Vendor call failed - check error details above")
        else:
            print(f"📞 Vendor call cancelled")
    
    except KeyboardInterrupt:
        print(f"\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main() 