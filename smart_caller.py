#!/usr/bin/env python3
"""
Smart Caller - Intelligent Procurement Call System
Supports multiple calling methods:
1. Real Twilio calls (if credentials available)
2. Simulated calls (for testing)
3. Gemini Live API calls (advanced voice)
"""

import os
import json
import time
import csv
from datetime import datetime
import google.generativeai as genai

# Try to import Twilio (optional)
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("ℹ️  Twilio not installed. Install with: pip install twilio")

class SmartCaller:
    def __init__(self):
        """Initialize the smart caller with available services"""
        
        # Setup Gemini
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            
            # Initialize Gemini with working model
            model_options = [
                'models/gemini-1.5-flash-8b',
                'models/gemini-2.0-flash-lite',
                'models/gemini-1.5-flash'
            ]
            
            self.gemini_model = None
            for model_name in model_options:
                try:
                    self.gemini_model = genai.GenerativeModel(model_name)
                    self.gemini_model.generate_content("Hi")
                    print(f"✅ Gemini AI ready: {model_name}")
                    break
                except:
                    continue
        
        # Setup Twilio (if available)
        self.twilio_client = None
        self.twilio_from_number = None
        
        if TWILIO_AVAILABLE:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            self.twilio_from_number = os.getenv('TWILIO_FROM_NUMBER', '+1234567890')
            
            if account_sid and auth_token:
                try:
                    self.twilio_client = Client(account_sid, auth_token)
                    print("✅ Twilio ready for real calls")
                except Exception as e:
                    print(f"⚠️  Twilio setup failed: {e}")
        
        # Setup webhooks
        self.webhook_base_url = os.getenv('WEBHOOK_URL', 'http://localhost:5000')
        
        print(f"\n📞 SMART CALLER INITIALIZED")
        print(f"🤖 Gemini AI: {'Ready' if self.gemini_model else 'Not available'}")
        print(f"📱 Twilio: {'Ready' if self.twilio_client else 'Not available'}")
        print(f"🌐 Webhook: {self.webhook_base_url}")
    
    def simulate_intelligent_call(self, phone_number, vendor_name="Test Vendor"):
        """Simulate a smart call using Gemini AI"""
        print(f"\n🎭 SIMULATING INTELLIGENT CALL")
        print(f"📞 Calling: {phone_number} ({vendor_name})")
        print("=" * 50)
        
        if not self.gemini_model:
            print("❌ Gemini AI not available for simulation")
            return False
        
        # Simulate vendor responses
        vendor_responses = [
            "Hello, kaun bol raha hai?",
            "Petri dishes ka rate 45 rupees per piece hai sir",
            "Laboratory gloves 60 rupees main mil jayenge",
            "Bulk order hai toh discount de sakte hain"
        ]
        
        conversation_log = []
        
        for i, vendor_speech in enumerate(vendor_responses):
            print(f"\n🎤 Vendor says: '{vendor_speech}'")
            
            # Use Gemini to understand and respond
            try:
                prompt = f"""
                You are Bio Mac Lifesciences calling vendors for laboratory supplies quotes.
                
                Vendor just said: "{vendor_speech}"
                Call stage: {i+1}/4
                
                Analyze the speech and provide:
                1. What did they mean?
                2. Any price mentioned?
                3. Your intelligent response
                4. Next action
                
                Return JSON format.
                """
                
                response = self.gemini_model.generate_content(prompt)
                analysis = response.text
                
                print(f"🧠 AI Analysis: {analysis[:200]}...")
                
                # Log the interaction
                conversation_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'vendor_speech': vendor_speech,
                    'ai_analysis': analysis,
                    'call_stage': i+1
                })
                
                time.sleep(1)  # Realistic pause
                
            except Exception as e:
                print(f"❌ AI analysis failed: {e}")
        
        # Save conversation log
        self.save_conversation_log(phone_number, vendor_name, conversation_log)
        
        print(f"\n✅ SIMULATED CALL COMPLETED")
        print(f"📋 Conversation logged successfully")
        return True
    
    def make_real_twilio_call(self, phone_number, vendor_name="Unknown Vendor"):
        """Make a real call using Twilio"""
        
        if not self.twilio_client:
            print("❌ Twilio not configured for real calls")
            print("💡 To make real calls:")
            print("   1. Get Twilio account: https://www.twilio.com/")
            print("   2. Set environment variables:")
            print("      $env:TWILIO_ACCOUNT_SID='your_sid'")
            print("      $env:TWILIO_AUTH_TOKEN='your_token'")
            print("      $env:TWILIO_FROM_NUMBER='+1234567890'")
            return False
        
        print(f"\n📞 MAKING REAL CALL")
        print(f"📱 To: {phone_number} ({vendor_name})")
        print(f"🔗 Webhook: {self.webhook_base_url}/webhook/voice")
        
        try:
            call = self.twilio_client.calls.create(
                url=f"{self.webhook_base_url}/webhook/voice",
                to=phone_number,
                from_=self.twilio_from_number,
                status_callback=f"{self.webhook_base_url}/webhook/status",
                status_callback_event=['initiated', 'answered', 'completed'],
                record=True  # Record for analysis
            )
            
            print(f"✅ Call initiated successfully!")
            print(f"🆔 Call SID: {call.sid}")
            print(f"📊 Status: {call.status}")
            
            return call.sid
            
        except Exception as e:
            print(f"❌ Call failed: {e}")
            return False
    
    def make_gemini_live_call(self, phone_number, vendor_name="Unknown Vendor"):
        """Make an advanced call using Gemini Live API"""
        print(f"\n🤖 GEMINI LIVE CALL (Advanced)")
        print(f"📞 To: {phone_number} ({vendor_name})")
        print("🚧 This requires Gemini Live API setup")
        print("💡 For now, using intelligent simulation")
        
        return self.simulate_intelligent_call(phone_number, vendor_name)
    
    def save_conversation_log(self, phone_number, vendor_name, conversation_log):
        """Save conversation details to CSV"""
        try:
            filename = f'call_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'phone_number', 'vendor_name', 
                    'stage', 'vendor_speech', 'ai_analysis'
                ])
                
                for entry in conversation_log:
                    writer.writerow([
                        entry['timestamp'],
                        phone_number,
                        vendor_name,
                        entry['call_stage'],
                        entry['vendor_speech'],
                        entry['ai_analysis']
                    ])
            
            print(f"📝 Call log saved: {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save log: {e}")
    
    def call_vendor_list(self, vendor_list, call_type="simulate"):
        """Call multiple vendors from a list"""
        print(f"\n📋 CALLING VENDOR LIST ({call_type.upper()})")
        print("=" * 60)
        
        results = []
        
        for i, vendor in enumerate(vendor_list):
            phone = vendor.get('phone', '+1234567890')
            name = vendor.get('name', f'Vendor {i+1}')
            
            print(f"\n📞 [{i+1}/{len(vendor_list)}] Calling {name}")
            
            if call_type == "real" and self.twilio_client:
                result = self.make_real_twilio_call(phone, name)
            elif call_type == "gemini_live":
                result = self.make_gemini_live_call(phone, name)
            else:
                result = self.simulate_intelligent_call(phone, name)
            
            results.append({
                'vendor': name,
                'phone': phone,
                'success': result,
                'timestamp': datetime.now().isoformat()
            })
            
            time.sleep(2)  # Pause between calls
        
        print(f"\n📊 CALLING CAMPAIGN COMPLETE")
        print(f"✅ Successful calls: {sum(1 for r in results if r['success'])}")
        print(f"❌ Failed calls: {sum(1 for r in results if not r['success'])}")
        
        return results

def main():
    """Main function - interactive caller"""
    
    caller = SmartCaller()
    
    print(f"\n🎯 SMART PROCUREMENT CALLER")
    print("=" * 60)
    print("Choose calling method:")
    print("1. 🎭 Simulate intelligent call (uses Gemini AI)")
    print("2. 📞 Make real call (requires Twilio)")
    print("3. 🤖 Gemini Live call (advanced)")
    print("4. 📋 Call vendor list")
    print("5. 🧪 Test current setup")
    
    try:
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            phone = input("Enter phone number (or press Enter for test): ").strip() or "+1234567890"
            vendor = input("Enter vendor name (or press Enter for test): ").strip() or "Test Vendor"
            caller.simulate_intelligent_call(phone, vendor)
            
        elif choice == "2":
            phone = input("Enter phone number: ").strip()
            vendor = input("Enter vendor name: ").strip()
            if phone:
                caller.make_real_twilio_call(phone, vendor)
            else:
                print("❌ Phone number required for real calls")
                
        elif choice == "3":
            phone = input("Enter phone number: ").strip() or "+1234567890"
            vendor = input("Enter vendor name: ").strip() or "Test Vendor"
            caller.make_gemini_live_call(phone, vendor)
            
        elif choice == "4":
            # Sample vendor list
            vendors = [
                {"name": "ABC Medical Supplies", "phone": "+91-9876543210"},
                {"name": "XYZ Lab Equipment", "phone": "+91-9876543211"},
                {"name": "PQR Scientific", "phone": "+91-9876543212"}
            ]
            
            call_type = input("Call type (simulate/real/gemini_live): ").strip() or "simulate"
            caller.call_vendor_list(vendors, call_type)
            
        elif choice == "5":
            print(f"\n🧪 TESTING SETUP")
            print(f"🤖 Gemini: {'✅ Ready' if caller.gemini_model else '❌ Not ready'}")
            print(f"📱 Twilio: {'✅ Ready' if caller.twilio_client else '❌ Not ready'}")
            
            if caller.gemini_model:
                print(f"\n🧠 Testing Gemini intelligence...")
                test_response = caller.gemini_model.generate_content(
                    "Vendor said: 'Petri dishes 45 rupees per piece hai'. Extract price and respond naturally."
                )
                print(f"✅ Gemini response: {test_response.text[:100]}...")
        
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print(f"\n👋 Exiting caller...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 