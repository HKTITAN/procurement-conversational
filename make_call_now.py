#!/usr/bin/env python3
"""
Make Call Now - Immediate call with embedded TwiML
No webhook server required
"""

import requests
import base64
from datetime import datetime

def make_call_now():
    """Make an immediate call with embedded TwiML"""
    
    print("📞 MAKING CALL TO YOU NOW!")
    print("=" * 40)
    
    # Your details
    phone = "+918800000488"
    account_sid = "AC820daae89092e30fee3487e80162d2e2"
    auth_token = "690636dcdd752868f4e77648dc0d49eb"
    from_number = "+14323484517"
    
    # Create TwiML with intelligent conversation
    twiml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <!-- Initial greeting -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Namaste! Main Bio Mac Lifesciences se bol raha hun. 
        Hum laboratory supplies ki company hain.
    </Say>
    
    <Pause length="2"/>
    
    <!-- Business introduction -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Humein kuch laboratory items ki urgent requirement hai. 
        Petri dishes, laboratory gloves, aur microscope slides chahiye.
        Aapka rate kya hai in items ka?
    </Say>
    
    <Pause length="3"/>
    
    <!-- Ask for response -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Please bataiye aapka pricing. Petri dishes ke liye kya rate hai?
        Laboratory gloves ka kya price hai? Aur microscope slides kitne main milenge?
    </Say>
    
    <Pause length="5"/>
    
    <!-- Acknowledge -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Samjha sir. Main notes le raha hun. 
        Agar bulk order hai to discount mil sakta hai kya?
    </Say>
    
    <Pause length="3"/>
    
    <!-- Business details -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Aur delivery ka kya time lagega? GST included hai ya separate?
        Payment terms kya hain aapke?
    </Say>
    
    <Pause length="3"/>
    
    <!-- Closing -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Theek hai sir. Main aapko email bhejunga detailed requirements ke saath.
        Company ka naam Bio Mac Lifesciences hai. 
        Dhanyawad aur namaste!
    </Say>
    
    <Hangup/>
</Response>"""
    
    # Make the call
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"
    auth = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'From': from_number,
        'To': phone,
        'Twiml': twiml_content,
        'Record': 'true',
        'Timeout': '30'
    }
    
    try:
        print(f"📞 Calling {phone} RIGHT NOW...")
        print(f"🏢 From: Bio Mac Lifesciences ({from_number})")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Purpose: Laboratory supplies procurement")
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 201:
            call_data = response.json()
            print(f"\n✅ CALL INITIATED SUCCESSFULLY!")
            print(f"🆔 Call SID: {call_data['sid']}")
            print(f"📊 Status: {call_data['status']}")
            
            print(f"\n🎭 CONVERSATION WILL BE:")
            print(f"   1. 🎤 AI introduces Bio Mac Lifesciences")
            print(f"   2. 🗣️ Asks for laboratory supplies pricing")
            print(f"   3. 💬 Requests specific rates for:")
            print(f"      • Petri dishes")
            print(f"      • Laboratory gloves") 
            print(f"      • Microscope slides")
            print(f"   4. 💼 Discusses bulk discounts")
            print(f"   5. 📋 Asks about delivery & payment terms")
            print(f"   6. 🤝 Professional closing")
            
            print(f"\n📱 YOUR PHONE SHOULD RING NOW!")
            print(f"🎧 Answer and listen to the intelligent conversation")
            print(f"⏱️ Duration: ~60-90 seconds")
            
            return call_data['sid']
            
        else:
            print(f"❌ CALL FAILED!")
            print(f"📊 Status Code: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    result = make_call_now()
    if result:
        print(f"\n🎉 SUCCESS! Call SID: {result}")
        print(f"📞 Check your phone - it should be ringing!")
    else:
        print(f"\n❌ Call failed") 