#!/usr/bin/env python3
"""
Startup script for Likwid.AI Procurement Automation System
Helps configure ngrok and make real calls to vendors
"""

import os
import sys
import subprocess
import time
import requests
from config import config

def print_banner():
    print("\n" + "="*80)
    print("🚀 LIKWID.AI PROCUREMENT AUTOMATION - LIVE CALL SYSTEM")
    print("="*80)
    print("This script will help you make a REAL call to the vendor using Twilio ConversationRelay")
    print()

def check_ngrok():
    """Check if ngrok is available and provide setup instructions"""
    print("🔍 Step 1: Checking ngrok availability...")
    
    try:
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ ngrok is available!")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass
    
    print("❌ ngrok not found in PATH")
    print("\n📋 MANUAL NGROK SETUP INSTRUCTIONS:")
    print("1. Download ngrok from: https://ngrok.com/download")
    print("2. Extract the ngrok.exe file")
    print("3. Open a new Command Prompt/PowerShell window")
    print("4. Navigate to where you extracted ngrok.exe")
    print("5. Run: ngrok.exe http 5000")
    print("6. Copy the HTTPS URL (e.g., https://abc123.ngrok.io)")
    print("7. Come back here and enter that URL when prompted")
    print()
    
    return False

def get_ngrok_url():
    """Get ngrok URL from user or auto-detect"""
    print("🌐 Step 2: Setting up webhook URL...")
    
    # Try to auto-detect ngrok
    try:
        response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
        if response.status_code == 200:
            tunnels = response.json().get('tunnels', [])
            for tunnel in tunnels:
                if tunnel.get('config', {}).get('addr') == 'localhost:5000':
                    url = tunnel['public_url']
                    if url.startswith('https://'):
                        print(f"✅ Auto-detected ngrok URL: {url}")
                        return url
    except:
        pass
    
    # Manual input
    print("⚠️  Could not auto-detect ngrok URL")
    print("Please start ngrok manually:")
    print("1. Open new terminal/command prompt")
    print("2. Run: ngrok http 5000")
    print("3. Copy the HTTPS URL from ngrok output")
    print()
    
    while True:
        url = input("Enter your ngrok HTTPS URL (e.g., https://abc123.ngrok.io): ").strip()
        if url.startswith('https://') and len(url) > 10:
            # Test the URL
            try:
                test_url = f"{url}/health"
                print(f"🔍 Testing webhook URL: {test_url}")
                # We'll test this after starting the server
                return url
            except:
                pass
        
        print("❌ Invalid URL. Please enter a valid HTTPS ngrok URL")

def update_webhook_urls(base_url):
    """Update the main.py file with the actual webhook URLs"""
    print("📝 Step 3: Updating webhook URLs in system...")
    
    try:
        # Read current main.py
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace placeholder URLs
        old_url1 = '"https://your-ngrok-url.ngrok.io/webhook/quote"'
        new_url1 = f'"{base_url}/webhook/quote"'
        
        old_url2 = "'https://your-ngrok-url.ngrok.io/webhook/voice'"
        new_url2 = f"'{base_url}/webhook/voice'"
        
        content = content.replace(old_url1, new_url1)
        content = content.replace(old_url2, new_url2)
        
        # Write back
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Updated webhook URLs to: {base_url}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating URLs: {e}")
        return False

def start_webhook_server():
    """Start the webhook server in background"""
    print("🖥️  Step 4: Starting webhook server...")
    
    try:
        # Import and start the system
        from main import ProcurementAutomationSystem
        
        system = ProcurementAutomationSystem()
        system.start_webhook_server()
        
        print("✅ Webhook server started on localhost:5000")
        return system
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None

def test_webhook_connection(base_url):
    """Test if webhook is accessible"""
    print("🔗 Step 5: Testing webhook connection...")
    
    try:
        health_url = f"{base_url}/health"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Webhook server is accessible from internet!")
            return True
        else:
            print(f"❌ Webhook test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Webhook connection error: {e}")
        print("⚠️  Please ensure:")
        print("   - ngrok is running: ngrok http 5000")
        print("   - Webhook server is running")
        print("   - URLs are correctly configured")
        return False

def initiate_real_call(system):
    """Initiate the real call to vendor"""
    print("📞 Step 6: Initiating REAL call to vendor...")
    print()
    print("🎯 CALL DETAILS:")
    print(f"   Client: {config.CLIENT_NAME}")
    print(f"   Vendor: {config.TEST_VENDOR['name']}")
    print(f"   Phone: {config.TEST_VENDOR['phone']}")
    print(f"   From: {config.TWILIO_PHONE_NUMBER}")
    print()
    
    confirm = input("⚠️  This will make a REAL phone call. Continue? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Call cancelled by user")
        return False
    
    try:
        # Run the procurement workflow which will make the real call
        print("🚀 Starting procurement workflow...")
        system.run_procurement_workflow()
        
        print("✅ Procurement workflow completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during call: {e}")
        return False

def main():
    """Main function"""
    print_banner()
    
    # Step 1: Check ngrok
    ngrok_available = check_ngrok()
    
    # Step 2: Get webhook URL
    base_url = get_ngrok_url()
    
    # Step 3: Update URLs in main.py
    if not update_webhook_urls(base_url):
        print("❌ Failed to update webhook URLs")
        return False
    
    # Step 4: Start webhook server
    system = start_webhook_server()
    if not system:
        print("❌ Failed to start webhook server")
        return False
    
    # Give server time to start
    time.sleep(3)
    
    # Step 5: Test webhook connection
    if not test_webhook_connection(base_url):
        print("❌ Webhook connection test failed")
        print("⚠️  You can still try the call, but webhooks may not work properly")
        
        retry = input("Continue anyway? (yes/no): ").strip().lower()
        if retry != 'yes':
            return False
    
    # Step 6: Make the real call
    success = initiate_real_call(system)
    
    if success:
        print("\n" + "="*80)
        print("🎉 CALL COMPLETED SUCCESSFULLY!")
        print("📁 Check the generated CSV files for results:")
        print("   • requirements.csv - Items that needed procurement")
        print("   • quotes.csv - Quotes collected during the call") 
        print("   • final_orders.csv - Optimized purchase orders")
        print("="*80)
    else:
        print("\n❌ Call process failed or was cancelled")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 