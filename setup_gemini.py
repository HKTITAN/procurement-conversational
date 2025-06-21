#!/usr/bin/env python3
"""
Setup Script for Gemini-Enhanced Bilingual Webhook
This script helps you configure and run the enhanced system
"""

import os
import sys
import subprocess
import requests

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    print("✅ Python version compatible:", sys.version.split()[0])
    return True

def install_dependencies():
    """Install required packages"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_gemini_api_key():
    """Check if Gemini API key is configured"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == "your_gemini_api_key_here":
        print("⚠️  Gemini API key not configured!")
        print("📝 To get your API key:")
        print("   1. Go to https://aistudio.google.com/")
        print("   2. Sign in with your Google account")
        print("   3. Click 'Get API Key'")
        print("   4. Create a new API key")
        print("   5. Set it as environment variable: export GEMINI_API_KEY='your_key_here'")
        print("   6. Or add it to gemini_config.py")
        return False
    
    print("✅ Gemini API key found")
    return True

def test_gemini_connection():
    """Test connection to Gemini API"""
    try:
        import google.generativeai as genai
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        
        # Try quota-friendly models in order
        model_options = [
            'models/gemini-1.5-flash-8b',      # Most efficient
            'models/gemini-2.0-flash-lite',    # Fast alternative
            'models/gemini-1.5-flash',         # Standard option
            'models/gemini-2.0-flash-exp'      # Experimental (may fail)
        ]
        
        model = None
        for model_name in model_options:
            try:
                model = genai.GenerativeModel(model_name)
                # Quick test
                model.generate_content("Hi")
                print(f"✅ Using model: {model_name}")
                break
            except Exception as e:
                print(f"⚠️  Model {model_name} failed: {str(e)[:100]}...")
                continue
        
        if not model:
            raise Exception("No working Gemini models available!")
        
        response = model.generate_content("Say 'Hello' in Hindi")
        
        print("✅ Gemini API connection successful")
        print(f"🤖 Test response: {response.text}")
        return True
    except Exception as e:
        print(f"❌ Gemini API connection failed: {e}")
        return False

def check_twilio_setup():
    """Check Twilio configuration (optional)"""
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    if not account_sid or not auth_token:
        print("ℹ️  Twilio credentials not configured (optional for testing)")
        print("   For voice calls, you'll need Twilio credentials")
        return False
    
    print("✅ Twilio credentials found")
    return True

def create_sample_config():
    """Create sample configuration if needed"""
    if not os.path.exists('gemini_config.py'):
        print("📝 Creating sample configuration file...")
        subprocess.run(['cp', 'gemini_config_example.py', 'gemini_config.py'])
        print("✅ Created gemini_config.py - please edit with your API key")

def run_tests():
    """Run basic functionality tests"""
    print("🧪 Running basic tests...")
    
    try:
        # Test CSV file creation
        with open('test_quotes.csv', 'w') as f:
            f.write('test,data\n')
        os.remove('test_quotes.csv')
        print("✅ File operations working")
        
        # Test JSON operations
        import json
        test_data = {"test": "data"}
        json.dumps(test_data)
        print("✅ JSON operations working")
        
        return True
    except Exception as e:
        print(f"❌ Basic tests failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Gemini-Enhanced Bilingual Webhook")
    print("=" * 50)
    
    # Check system requirements
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Check configuration
    check_gemini_api_key()
    check_twilio_setup()
    
    # Create sample config if needed
    create_sample_config()
    
    # Run tests
    if not run_tests():
        return False
    
    # Test Gemini if API key is available
    if os.getenv('GEMINI_API_KEY') and os.getenv('GEMINI_API_KEY') != "your_gemini_api_key_here":
        test_gemini_connection()
    
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. Configure your Gemini API key in gemini_config.py")
    print("2. Run: python gemini_enhanced_webhook.py")
    print("3. Test at: http://localhost:5000/health")
    print("4. For voice calls, configure Twilio webhook to your server")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 