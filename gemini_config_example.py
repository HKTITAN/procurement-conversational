#!/usr/bin/env python3
"""
Gemini Configuration Example
Copy this file to `gemini_config.py` and add your actual API keys
"""

import os

# Gemini AI Configuration
# Get your API key from: https://aistudio.google.com/
GEMINI_API_KEY = "AIzaSyBCXNuaO9VlL5z1phh4mWGEVnnmRFk9TNg"

# Alternative: Use environment variable (recommended for production)
# GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Optional: For Vertex AI (instead of Gemini API)
# GOOGLE_APPLICATION_CREDENTIALS = "path/to/service-account-key.json"
# GOOGLE_CLOUD_PROJECT = "your-project-id"
# GOOGLE_CLOUD_LOCATION = "us-central1"

# Twilio Configuration (if needed)
# TWILIO_ACCOUNT_SID = "your_twilio_account_sid"
# TWILIO_AUTH_TOKEN = "your_twilio_auth_token"

# Application Settings
FLASK_ENV = "development"
PORT = 5000

def setup_environment():
    """Set up environment variables"""
    os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY
    
    # Optional Vertex AI setup
    # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_APPLICATION_CREDENTIALS
    # os.environ['GOOGLE_CLOUD_PROJECT'] = GOOGLE_CLOUD_PROJECT
    # os.environ['GOOGLE_CLOUD_LOCATION'] = GOOGLE_CLOUD_LOCATION
    
    print("🔑 Environment variables configured")

if __name__ == "__main__":
    setup_environment()
    print("✅ Configuration ready!") 