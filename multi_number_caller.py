#!/usr/bin/env python3
"""
Multi-Number Caller for Twilio Trial Accounts
Handles verified numbers and provides guidance for trial limitations
"""

import os
import requests
import base64
import json
from datetime import datetime

# Twilio credentials
TWILIO_ACCOUNT_SID = "AC820daae89092e30fee3487e80162d2e2"
TWILIO_AUTH_TOKEN = "690636dcdd752868f4e77648dc0d49eb"
TWILIO_FROM_NUMBER = "+14323484517"

# Pre-configured verified numbers (you can add more after verifying)
VERIFIED_NUMBERS = {
    "Your Phone": "+918800000488",
    "Test Number 1": "",  # Add verified numbers here
    "Test Number 2": "",  # Add verified numbers here
    "Vendor A": "",       # Add verified vendor numbers here
    "Vendor B": "",       # Add verified vendor numbers here
}

def check_account_info():
    """Check Twilio account information and limitations"""
    print("🔍 CHECKING TWILIO ACCOUNT INFO")
    print("=" * 50)
    
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}.json"
    auth = base64.b64encode(f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            account_data = response.json()
            account_type = account_data.get('type', 'Unknown')
            status = account_data.get('status', 'Unknown')
            
            print(f"📋 Account Type: {account_type}")
            print(f"📊 Account Status: {status}")
            
            if account_type.lower() == 'trial':
                print("\n⚠️  TRIAL ACCOUNT LIMITATIONS:")
                print("   • Can only call verified phone numbers")
                print("   • Cannot call unverified/random numbers")
                print("   • Limited credits (~$15-20)")
                print("   • All calls will have trial message prefix")
                print("\n💡 To call new numbers:")
                print("   1. Go to: https://console.twilio.com/")
                print("   2. Navigate: Phone Numbers → Verified Caller IDs")
                print("   3. Add and verify the number you want to call")
            else:
                print("✅ Full account - can call most numbers")
                
        else:
            print(f"❌ Error checking account: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def get_verified_numbers():
    """Get list of verified caller IDs from Twilio"""
    print("\n📞 FETCHING VERIFIED NUMBERS")
    print("=" * 40)
    
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/OutgoingCallerIds.json"
    auth = base64.b64encode(f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            verified_numbers = []
            
            print("✅ Verified numbers you can call:")
            for caller_id in data.get('outgoing_caller_ids', []):
                phone_number = caller_id.get('phone_number', '')
                friendly_name = caller_id.get('friendly_name', 'Unknown')
                verified_numbers.append(phone_number)
                print(f"   📱 {phone_number} ({friendly_name})")
            
            return verified_numbers
        else:
            print(f"❌ Error fetching verified numbers: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def make_intelligent_call(phone_number, vendor_name="Unknown Vendor", call_type="procurement"):
    """Make an intelligent call to a verified number"""
    
    print(f"\n📞 MAKING CALL TO: {vendor_name} ({phone_number})")
    print("=" * 60)
    
    # Different TwiML based on call type
    if call_type == "procurement":
        twiml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">
        Namaste! Main Bio Mac Lifesciences se bol raha hun. 
        Hum laboratory supplies ki company hain.
        Humein kuch items ki urgent requirement hai.
    </Say>
    
    <Pause length="2"/>
    
    <Say voice="Polly.Aditi" language="hi-IN">
        Petri dishes, laboratory gloves, aur microscope slides chahiye.
        Aapka rate kya hai in items ka? 
        Please pricing bataiye.
    </Say>
    
    <Pause length="5"/>
    
    <Say voice="Polly.Aditi" language="hi-IN">
        Samjha sir. Main notes le raha hun.
        Delivery time kya hai? Aur minimum order quantity?
    </Say>
    
    <Pause length="3"/>
    
    <Say voice="Polly.Aditi" language="hi-IN">
        Theek hai. Main aapko email bhejunga detailed requirements ke saath.
        Bio Mac Lifesciences ki taraf se dhanyawad. Namaste!
    </Say>
    <Hangup/>
</Response>"""
    
    elif call_type == "test":
        twiml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">
        Hello! Yeh ek test call hai Bio Mac Lifesciences ki taraf se.
        System testing kar rahe hain. Dhanyawad!
    </Say>
    <Pause length="2"/>
    <Say voice="Polly.Aditi" language="hi-IN">
        Test complete. Namaste!
    </Say>
    <Hangup/>
</Response>"""
    
    elif call_type == "follow_up":
        twiml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">
        Namaste! Main Bio Mac Lifesciences se follow-up kar raha hun.
        Pichle call mein jo quotes discuss kiye the, 
        kya aap final pricing confirm kar sakte hain?
    </Say>
    <Pause length="3"/>
    <Say voice="Polly.Aditi" language="hi-IN">
        Dhanyawad sir. Main call back karunga. Namaste!
    </Say>
    <Hangup/>
</Response>"""
    
    # Make the call
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Calls.json"
    auth = base64.b64encode(f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'From': TWILIO_FROM_NUMBER,
        'To': phone_number,
        'Twiml': twiml_content,
        'Record': 'true',
        'Timeout': '30'
    }
    
    try:
        print(f"📞 Calling {vendor_name}...")
        print(f"🎯 Call Type: {call_type.title()}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 201:
            call_data = response.json()
            print(f"\n✅ CALL INITIATED!")
            print(f"🆔 Call SID: {call_data['sid']}")
            print(f"📊 Status: {call_data['status']}")
            print(f"📱 From: {TWILIO_FROM_NUMBER}")
            print(f"📞 To: {phone_number}")
            
            return call_data['sid']
            
        else:
            print(f"\n❌ CALL FAILED!")
            print(f"📊 Status Code: {response.status_code}")
            print(f"📝 Response: {response.text}")
            
            # Common error handling
            if "is not a valid phone number" in response.text:
                print("💡 Fix: Check phone number format (+country_code)")
            elif "not a verified phone number" in response.text:
                print("💡 Fix: Verify this number in Twilio Console first")
            elif "Trial account" in response.text:
                print("💡 Fix: This number needs to be verified for trial accounts")
            
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def add_number_to_verified_list():
    """Guide user to add a number to verified list"""
    print("\n📋 HOW TO ADD NEW NUMBERS FOR CALLING:")
    print("=" * 50)
    print("1. 🌐 Go to: https://console.twilio.com/")
    print("2. 📱 Navigate: Phone Numbers → Manage → Verified Caller IDs")
    print("3. ➕ Click: 'Add a new number'")
    print("4. 📞 Enter the phone number (with country code)")
    print("5. ✅ Verify via SMS or voice call")
    print("6. 🎯 Once verified, you can call that number")
    print("\n💡 Example numbers to verify:")
    print("   • Your personal phone")
    print("   • Your office phone")
    print("   • Vendor phone numbers")
    print("   • Team member phones")

def main():
    """Main function for multi-number calling"""
    print("📞 MULTI-NUMBER CALLING SYSTEM")
    print("🔒 Twilio Trial Account Compatible")
    print("=" * 60)
    
    # Check account info
    check_account_info()
    
    # Get verified numbers
    verified_numbers = get_verified_numbers()
    
    while True:
        print("\n" + "="*50)
        print("📞 MULTI-NUMBER CALLING OPTIONS")
        print("="*50)
        print("1. 📱 Call from pre-configured list")
        print("2. 📞 Call custom verified number")
        print("3. 🔍 Check verified numbers")
        print("4. ➕ How to add new numbers")
        print("5. 🧪 Test call to your phone")
        print("6. ❌ Exit")
        
        choice = input("\nChoose option (1-6): ").strip()
        
        if choice == "1":
            print("\n📋 PRE-CONFIGURED NUMBERS:")
            valid_numbers = {k: v for k, v in VERIFIED_NUMBERS.items() if v}
            
            if not valid_numbers:
                print("❌ No pre-configured numbers found!")
                print("💡 Add verified numbers to VERIFIED_NUMBERS in the script")
                continue
            
            for i, (name, number) in enumerate(valid_numbers.items(), 1):
                print(f"   {i}. {name}: {number}")
            
            try:
                selection = int(input(f"\nSelect number (1-{len(valid_numbers)}): "))
                if 1 <= selection <= len(valid_numbers):
                    name, number = list(valid_numbers.items())[selection-1]
                    
                    call_type = input("Call type (procurement/test/follow_up) [procurement]: ").strip()
                    if not call_type:
                        call_type = "procurement"
                    
                    make_intelligent_call(number, name, call_type)
                else:
                    print("❌ Invalid selection")
            except ValueError:
                print("❌ Invalid input")
        
        elif choice == "2":
            phone = input("Enter verified phone number (+country_code): ").strip()
            if phone:
                if not phone.startswith('+'):
                    phone = f"+{phone}"
                
                vendor_name = input("Vendor name (optional): ").strip() or "Custom Number"
                call_type = input("Call type (procurement/test/follow_up) [procurement]: ").strip()
                if not call_type:
                    call_type = "procurement"
                
                make_intelligent_call(phone, vendor_name, call_type)
        
        elif choice == "3":
            get_verified_numbers()
        
        elif choice == "4":
            add_number_to_verified_list()
        
        elif choice == "5":
            your_phone = VERIFIED_NUMBERS.get("Your Phone", "+918800000488")
            print(f"📞 Making test call to: {your_phone}")
            make_intelligent_call(your_phone, "Your Phone", "test")
        
        elif choice == "6":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main() 