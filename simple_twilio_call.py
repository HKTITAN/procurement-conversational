#!/usr/bin/env python3
"""
Simple Twilio Call - Direct API approach
Makes calls using HTTP requests instead of Twilio SDK
"""

import os
import requests
import json
import time
from datetime import datetime
from urllib.parse import urlencode
import base64

def make_twilio_call_direct(phone_number, vendor_name="Test Vendor"):
    """Make a call using direct Twilio API calls"""
    
    print("📞 MAKING REAL CALL VIA TWILIO API")
    print("=" * 60)
    
    # Get credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER', '+14323484517')
    
    if not account_sid or not auth_token:
        print("❌ Missing Twilio credentials!")
        return False
    
    print(f"✅ Account SID: {account_sid[:10]}...")
    print(f"✅ Auth Token: {auth_token[:6]}...")
    print(f"✅ From Number: {from_number}")
    print(f"📞 To Number: {phone_number}")
    print(f"👤 Vendor: {vendor_name}")
    
    # Webhook URL - your server
    webhook_url = "http://localhost:5000/webhook/voice"
    
    # Prepare API call
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
        'Url': webhook_url,
        'Method': 'POST',
        'StatusCallback': 'http://localhost:5000/webhook/status',
        'StatusCallbackEvent': 'initiated,ringing,answered,completed',
        'StatusCallbackMethod': 'POST',
        'Record': 'true',
        'Timeout': '30',
        'MachineDetection': 'Enable'
    }
    
    print(f"\n🌐 Webhook URL: {webhook_url}")
    print(f"📊 Status callback: http://localhost:5000/webhook/status")
    
    try:
        print(f"\n📞 INITIATING CALL...")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 201:
            # Success!
            call_data = response.json()
            call_sid = call_data['sid']
            
            print(f"✅ CALL INITIATED SUCCESSFULLY!")
            print(f"🆔 Call SID: {call_sid}")
            print(f"📊 Status: {call_data['status']}")
            print(f"📱 From: {call_data['from']}")
            print(f"📞 To: {call_data['to']}")
            
            # Monitor call status
            monitor_call_status(account_sid, auth_token, call_sid)
            
            return call_sid
            
        else:
            print(f"❌ CALL FAILED!")
            print(f"📊 Status Code: {response.status_code}")
            print(f"📝 Response: {response.text}")
            
            # Show specific guidance
            if response.status_code == 401:
                print("💡 Authentication failed - check Account SID and Auth Token")
            elif response.status_code == 400:
                print("💡 Bad request - check phone number format")
            elif response.status_code == 403:
                print("💡 Forbidden - check account permissions or balance")
            
            return False
            
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

def monitor_call_status(account_sid, auth_token, call_sid):
    """Monitor call status using direct API"""
    
    print(f"\n📊 MONITORING CALL STATUS...")
    
    # Authentication
    auth = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    headers = {'Authorization': f'Basic {auth}'}
    
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls/{call_sid}.json"
    
    for i in range(60):  # Monitor for 1 minute
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                call_data = response.json()
                status = call_data['status']
                
                print(f"⏰ [{i+1:02d}s] Status: {status}")
                
                if status in ['completed', 'failed', 'busy', 'no-answer']:
                    print(f"\n📋 CALL COMPLETED")
                    print(f"📊 Final Status: {status}")
                    if call_data.get('duration'):
                        print(f"⏱️  Duration: {call_data['duration']} seconds")
                    if call_data.get('price'):
                        print(f"💰 Price: {call_data['price']} {call_data.get('price_unit', 'USD')}")
                    break
                    
                elif status == 'in-progress':
                    print(f"🎤 Call is active - conversation in progress...")
                
            else:
                print(f"❌ Status check failed: {response.status_code}")
                break
                
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Status check error: {e}")
            break

def test_webhook_server():
    """Test if webhook server is running"""
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Webhook server is running")
            return True
        else:
            print(f"⚠️  Webhook server returned status {response.status_code}")
            return False
    except:
        print("❌ Webhook server is not running")
        print("💡 Start with: python gemini_enhanced_webhook.py")
        return False

def main():
    """Main function"""
    print("🤖 SIMPLE TWILIO CALLING SYSTEM")
    print("=" * 70)
    
    # Check webhook server
    print("🌐 Checking webhook server...")
    if not test_webhook_server():
        print("\n❌ Webhook server is required for calls")
        print("💡 Please start the server first:")
        print("   python gemini_enhanced_webhook.py")
        return
    
    # Test credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER')
    
    print(f"\n📋 Configuration:")
    print(f"   Account SID: {'✅ Set' if account_sid else '❌ Missing'}")
    print(f"   Auth Token: {'✅ Set' if auth_token else '❌ Missing'}")
    print(f"   From Number: {from_number if from_number else '❌ Missing'}")
    
    if not account_sid or not auth_token:
        print("\n❌ Missing Twilio credentials!")
        print("💡 Set environment variables:")
        print("   $env:TWILIO_ACCOUNT_SID='your_sid'")
        print("   $env:TWILIO_AUTH_TOKEN='your_token'")
        print("   $env:TWILIO_FROM_NUMBER='+14323484517'")
        return
    
    print(f"\n🎯 Ready to make calls!")
    
    # Get phone number to call
    try:
        print(f"\n📞 Enter phone number to call:")
        print(f"   Example: +1234567890 (your test number)")
        print(f"   Example: +919876543210 (vendor number)")
        
        phone = input("Phone number: ").strip()
        
        if not phone:
            print("❌ No phone number entered")
            return
        
        if not phone.startswith('+'):
            phone = f"+{phone}"
        
        vendor_name = input("Vendor name (optional): ").strip() or "Test Vendor"
        
        # Confirmation
        print(f"\n📞 About to call:")
        print(f"   📱 From: {from_number}")
        print(f"   📞 To: {phone}")
        print(f"   👤 Vendor: {vendor_name}")
        print(f"   🎯 Purpose: Laboratory supplies procurement")
        print(f"   🤖 AI: Gemini-enhanced conversation")
        
        confirm = input(f"\nProceed with call? (y/N): ").strip().lower()
        
        if confirm == 'y':
            print(f"\n🚀 Starting intelligent call...")
            result = make_twilio_call_direct(phone, vendor_name)
            
            if result:
                print(f"\n🎉 SUCCESS!")
                print(f"📞 Call initiated with SID: {result}")
                print(f"💡 Monitor your webhook server logs for conversation")
                print(f"📊 Check Twilio Console for call details")
            else:
                print(f"\n❌ Call failed")
        else:
            print(f"📞 Call cancelled")
    
    except KeyboardInterrupt:
        print(f"\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main() 