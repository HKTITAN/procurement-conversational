#!/usr/bin/env python3
"""
Direct Script to Call Both Harshit Khemani and Sidharth Sharma
Uses the improved master system functionality
"""

import requests
import base64
import time
from datetime import datetime

# Twilio credentials
TWILIO_ACCOUNT_SID = "AC820daae89092e30fee3487e80162d2e2"
TWILIO_AUTH_TOKEN = "690636dcdd752868f4e77648dc0d49eb"
TWILIO_FROM_NUMBER = "+14323484517"

# Contact list
CONTACTS = {
    "Harshit Khemani": "+918800000488",
    "Sidharth Sharma": "+919876788808"
}

# Ngrok URL (you can update this)
NGROK_URL = "https://59b6-2401-4900-1c66-9039-5c24-977c-347-d277.ngrok-free.app"

def print_status(message, category="INFO"):
    """Print status with timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {category}: {message}")

def make_call(contact_name, phone_number):
    """Make a call to a specific contact"""
    print_status(f"Calling {contact_name} at {phone_number}", "CALL")
    
    # Webhook URLs
    voice_webhook = f"{NGROK_URL}/webhook/voice"
    status_webhook = f"{NGROK_URL}/webhook/status"
    
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
        'Url': voice_webhook,
        'Method': 'POST',
        'StatusCallback': status_webhook,
        'StatusCallbackEvent': ['initiated', 'ringing', 'answered', 'completed'],
        'StatusCallbackMethod': 'POST',
        'Record': 'true',
        'Timeout': '30'
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 201:
            call_data = response.json()
            print_status(f"✅ Call initiated to {contact_name}!", "SUCCESS")
            print_status(f"Call SID: {call_data['sid']}", "SUCCESS")
            print_status(f"Status: {call_data['status']}", "INFO")
            return call_data['sid']
        else:
            print_status(f"❌ Call failed to {contact_name}: {response.text}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"❌ Error calling {contact_name}: {e}", "ERROR")
        return False

def main():
    """Main function to call both contacts"""
    print("📞 CALLING HARSHIT KHEMANI & SIDHARTH SHARMA")
    print("🧠 Using Improved Master System with AI Speech Recognition")
    print("=" * 60)
    
    # Verify ngrok URL
    print_status(f"Using ngrok URL: {NGROK_URL}", "INFO")
    print_status("Make sure your webhook server is running on port 5000", "INFO")
    
    # Get delay between calls
    delay_input = input("\nDelay between calls in seconds (default 30): ").strip()
    try:
        delay = int(delay_input) if delay_input else 30
    except ValueError:
        delay = 30
    
    print(f"\n⏰ Will wait {delay} seconds between calls")
    print("🎯 Each call will automatically collect procurement quotes:")
    print("   • Petri dishes")
    print("   • Laboratory gloves") 
    print("   • Microscope slides")
    print("📊 All data will be saved to CSV automatically")
    
    # Confirm before proceeding
    confirm = input("\nProceed with calls? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled by user")
        return
    
    successful_calls = []
    
    # Call each contact
    for i, (contact_name, phone_number) in enumerate(CONTACTS.items()):
        print(f"\n{'='*60}")
        print(f"📞 CALLING {contact_name.upper()} ({i+1}/{len(CONTACTS)})")
        print(f"{'='*60}")
        
        call_sid = make_call(contact_name, phone_number)
        
        if call_sid:
            successful_calls.append({
                'name': contact_name,
                'phone': phone_number,
                'call_sid': call_sid,
                'timestamp': datetime.now().isoformat()
            })
            
            # Wait between calls if not the last contact
            if i < len(CONTACTS) - 1:
                print_status(f"Waiting {delay} seconds before next call...", "INFO")
                for remaining in range(delay, 0, -1):
                    print(f"\rNext call in {remaining} seconds...", end='', flush=True)
                    time.sleep(1)
                print()  # New line after countdown
        
    # Report results
    print(f"\n{'='*60}")
    print("📊 CALL SUMMARY")
    print(f"{'='*60}")
    
    if successful_calls:
        print(f"✅ Successfully initiated {len(successful_calls)} calls:")
        for call_info in successful_calls:
            print(f"   📞 {call_info['name']}: {call_info['phone']}")
            print(f"      Call SID: {call_info['call_sid']}")
            print(f"      Time: {call_info['timestamp']}")
        
        print("\n🎤 LIVE MONITORING:")
        print("   • Watch terminal for real-time speech recognition")
        print("   • AI will automatically ask for each item")
        print("   • Data will be saved to CSV automatically")
        print(f"   • Dashboard: {NGROK_URL}")
        
        print("\n📋 EXPECTED FLOW:")
        print("   1. AI greets in Hindi: 'Namaste! Bio Mac Lifesciences se...'")
        print("   2. Asks for Petri dishes pricing")
        print("   3. Processes response and moves to Laboratory gloves")
        print("   4. Asks for Microscope slides")
        print("   5. Concludes call and saves all data to CSV")
        
        print("\n⏳ Calls are now active. Check your phone!")
        print("📱 Answer the calls to provide quotes for the laboratory supplies")
        
    else:
        print("❌ No calls were successful")
        print("💡 Make sure:")
        print("   • Webhook server is running (python improved_master_system.py)")
        print("   • Ngrok URL is correct and accessible")
        print("   • Phone numbers are verified in Twilio (trial account)")

if __name__ == "__main__":
    main() 