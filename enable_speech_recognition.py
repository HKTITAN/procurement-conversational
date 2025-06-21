#!/usr/bin/env python3
"""
Enable Speech Recognition - Setup guide for real speech recognition
Helps you set up ngrok for public webhook access
"""

import os
import requests
import subprocess
import json
import time

def check_ngrok_installed():
    """Check if ngrok is installed"""
    try:
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ngrok is installed")
            print(f"   Version: {result.stdout.strip()}")
            return True
        else:
            print("❌ ngrok not found")
            return False
    except FileNotFoundError:
        print("❌ ngrok not installed")
        return False

def install_ngrok_instructions():
    """Show instructions to install ngrok"""
    print("\n💡 HOW TO INSTALL NGROK:")
    print("=" * 40)
    print("1. 🌐 Go to: https://ngrok.com/download")
    print("2. 📥 Download for Windows")
    print("3. 📂 Extract to a folder (e.g., C:\\ngrok\\)")
    print("4. 🛠️ Add to PATH or use full path")
    print("5. 🔑 Sign up for free account (optional)")
    print("6. 🎯 Run: ngrok http 5000")
    print()
    print("🚀 ALTERNATIVE - Quick Download:")
    print("   PowerShell:")
    print("   Invoke-WebRequest -Uri 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip' -OutFile 'ngrok.zip'")
    print("   Expand-Archive -Path 'ngrok.zip' -DestinationPath '.'")

def test_webhook_server():
    """Test if webhook server is running"""
    try:
        response = requests.get("http://localhost:5000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Webhook server is running on localhost:5000")
            return True
        else:
            print("❌ Webhook server responding with error")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Webhook server not running")
        return False
    except Exception as e:
        print(f"❌ Error checking webhook server: {e}")
        return False

def start_webhook_server():
    """Instructions to start webhook server"""
    print("\n📡 START WEBHOOK SERVER:")
    print("=" * 30)
    print("Open a new terminal/PowerShell window and run:")
    print("")
    print("cd \"C:\\Users\\harsh\\My Drive\\1. Projects\\procurement-conversational\"")
    print("$env:GEMINI_API_KEY=\"AIzaSyBCXNuaO9VlL5z1phh4mWGEVnnmRFk9TNg\"")
    print("python interactive_vendor_call.py")
    print("")
    print("This will start the Flask server with Gemini AI integration.")

def create_ngrok_config():
    """Create simple ngrok configuration"""
    config_content = """version: "2"
authtoken: YOUR_AUTH_TOKEN_HERE
tunnels:
  webhook:
    proto: http
    addr: 5000
    subdomain: biomac-webhook  # optional custom subdomain
"""
    
    try:
        with open("ngrok.yml", "w") as f:
            f.write(config_content)
        print("✅ Created ngrok.yml config file")
        print("💡 Edit ngrok.yml to add your auth token (optional)")
    except Exception as e:
        print(f"❌ Error creating config: {e}")

def show_ngrok_usage():
    """Show how to use ngrok for speech recognition"""
    print("\n🌐 USING NGROK FOR SPEECH RECOGNITION:")
    print("=" * 50)
    print("1. 📡 Start webhook server (in one terminal):")
    print("   python interactive_vendor_call.py")
    print("")
    print("2. 🌍 Start ngrok tunnel (in another terminal):")
    print("   ngrok http 5000")
    print("")
    print("3. 📋 Copy the public URL from ngrok:")
    print("   Example: https://abc123.ngrok.io")
    print("")
    print("4. 🔧 Update webhook URLs in calling script:")
    print("   Replace: http://localhost:5000/webhook/voice")
    print("   With:    https://abc123.ngrok.io/webhook/voice")
    print("")
    print("5. 📞 Make call - speech recognition will work!")

def create_ngrok_call_script():
    """Create a call script that works with ngrok"""
    script_content = '''#!/usr/bin/env python3
"""
Ngrok-enabled Call Script
Use this after setting up ngrok tunnel
"""

import os
import requests
import base64
import sys

def make_ngrok_call():
    """Make a call using ngrok webhook URL"""
    
    # Get ngrok URL from user
    print("🌐 NGROK SPEECH RECOGNITION CALL")
    print("=" * 40)
    print("1. Start: python interactive_vendor_call.py")
    print("2. Start: ngrok http 5000")
    print("3. Copy the ngrok URL (e.g., https://abc123.ngrok.io)")
    print()
    
    ngrok_url = input("Enter your ngrok URL: ").strip()
    if not ngrok_url:
        print("❌ Need ngrok URL!")
        return
    
    if not ngrok_url.startswith('http'):
        ngrok_url = f"https://{ngrok_url}"
    
    if ngrok_url.endswith('/'):
        ngrok_url = ngrok_url[:-1]
    
    phone = input("Phone number (+918800000488): ").strip()
    if not phone:
        phone = "+918800000488"
    
    # Twilio credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER', '+14323484517')
    
    if not account_sid or not auth_token:
        print("❌ Missing Twilio credentials!")
        return
    
    # Webhook URLs using ngrok
    voice_webhook = f"{ngrok_url}/webhook/voice"
    speech_webhook = f"{ngrok_url}/webhook/speech"
    status_webhook = f"{ngrok_url}/webhook/status"
    
    print(f"📞 Making call with speech recognition:")
    print(f"   Voice Webhook: {voice_webhook}")
    print(f"   Speech Webhook: {speech_webhook}")
    print(f"   Phone: {phone}")
    
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
            print(f"✅ SPEECH RECOGNITION CALL STARTED!")
            print(f"🆔 Call SID: {call_data['sid']}")
            print(f"🎤 Speak when prompted - AI will understand and respond!")
        else:
            print(f"❌ Call failed: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    make_ngrok_call()
'''
    
    try:
        with open("ngrok_call.py", "w") as f:
            f.write(script_content)
        print("✅ Created ngrok_call.py")
        print("💡 Use this script after setting up ngrok tunnel")
    except Exception as e:
        print(f"❌ Error creating script: {e}")

def main():
    """Main function"""
    print("🎤 SPEECH RECOGNITION SETUP GUIDE")
    print("🧠 Enable Real-time AI Conversation")
    print("=" * 50)
    
    print("\n📊 SYSTEM STATUS:")
    print("=" * 20)
    
    # Check ngrok
    ngrok_installed = check_ngrok_installed()
    
    # Check webhook server
    webhook_running = test_webhook_server()
    
    # Check credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    print(f"🔧 Twilio SID: {'✅ Set' if account_sid else '❌ Missing'}")
    print(f"🔧 Twilio Token: {'✅ Set' if auth_token else '❌ Missing'}")
    print(f"🧠 Gemini API: {'✅ Set' if gemini_key else '❌ Missing'}")
    print(f"📡 Webhook Server: {'✅ Running' if webhook_running else '❌ Not running'}")
    print(f"🌐 Ngrok: {'✅ Installed' if ngrok_installed else '❌ Not installed'}")
    
    if not webhook_running:
        start_webhook_server()
    
    if not ngrok_installed:
        install_ngrok_instructions()
    else:
        show_ngrok_usage()
        create_ngrok_call_script()
        create_ngrok_config()
    
    print(f"\n🎯 NEXT STEPS:")
    print("=" * 15)
    if not webhook_running:
        print("1. ❌ Start webhook server first")
    else:
        print("1. ✅ Webhook server running")
    
    if not ngrok_installed:
        print("2. ❌ Install ngrok")
        print("3. ❌ Start ngrok tunnel")
        print("4. ❌ Use ngrok_call.py for real speech recognition")
    else:
        print("2. ✅ Start ngrok tunnel: ngrok http 5000")
        print("3. ✅ Copy ngrok URL")
        print("4. ✅ Run: python ngrok_call.py")
        print("5. ✅ Speak naturally - AI will understand!")
    
    print(f"\n💡 WHAT YOU'LL GET:")
    print("   🎤 Real speech recognition (Hindi + English)")
    print("   🧠 Gemini AI understands what you say")
    print("   🗣️ Intelligent responses in natural conversation")
    print("   📊 Automatic quote extraction and logging")

if __name__ == "__main__":
    main() 