#!/usr/bin/env python3
"""
Multi-Company Procurement Platform with ElevenLabs Conversational AI
Handles inventory management, vendor negotiations, price comparison, and analytics
"""

import os
import sys
import time
import threading
import subprocess
import requests
import base64
import json
import csv
from datetime import datetime, timedelta
from flask import Flask, request, Response, render_template_string, jsonify, redirect, url_for
import google.generativeai as genai
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import uuid

# Set environment variables
os.environ['GEMINI_API_KEY'] = 'AIzaSyBCXNuaO9VlL5z1phh4mWGEVnnmRFk9TNg'

# ElevenLabs Configuration
ELEVENLABS_API_KEY = "sk_ff1d9ea5ad1f795bbfa549805742feab99ca7284a6e66f63"
ELEVENLABS_AGENT_ID = "agent_01jygd7xerew3rzqzf3wxfy936"
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1/convai"
ELEVENLABS_PHONE_NUMBER_ID = None  # To be set via setup function

# Initialize Flask app
app = Flask(__name__)

# Configure Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        print("Gemini AI initialized with Flash 2.0")
    except:
        try:
            model = genai.GenerativeModel('models/gemini-1.5-flash-8b')
            print("Gemini AI initialized with Flash 1.5")
        except:
            model = None
            print("Warning: Gemini AI not available")
else:
    model = None
    print("Warning: GEMINI_API_KEY not set")

# ElevenLabs Agent Configuration
def create_elevenlabs_agent():
    """Create or configure ElevenLabs Conversational AI agent for procurement"""
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Agent configuration for procurement conversations
    agent_config = {
        "name": "Procurement Assistant",
        "description": "AI agent for procurement conversations with vendors",
        "prompt": """You are a professional procurement assistant for Bio Mac Lifesciences, a biotechnology company. Your role is to:

1. Introduce the company professionally
2. Inquire about laboratory supplies and equipment
3. Gather pricing information and availability
4. Ask about delivery terms and minimum orders
5. Collect vendor contact information
6. Be polite but efficient in conversations
7. Use a mix of Hindi and English appropriate for Indian business context

Keep conversations focused and extract maximum business value. End conversations when sufficient information is gathered.""",
        
        "voice": {
            "voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam - professional male voice
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        },
        
        "language": "en",
        
        "response_configuration": {
            "output_format": "pcm_16000",
            "apply_text_normalization": True
        },
        
        "llm": {
            "model": "gemini-2.0-flash",
            "temperature": 0.3,
            "max_tokens": 150
        },
        
        "conversation_configuration": {
            "max_duration_seconds": 180,
            "silence_timeout_ms": 3000,
            "interruption_sensitivity": 0.7
        }
    }
    
    try:
        response = requests.post(
            f"{ELEVENLABS_BASE_URL}/agents",
            headers=headers,
            json=agent_config
        )
        
        if response.status_code == 201:
            agent_data = response.json()
            agent_id = agent_data.get("agent_id")
            print_live_feedback(f"ElevenLabs agent created: {agent_id}", "SUCCESS")
            return agent_id
        else:
            print_live_feedback(f"Failed to create agent: {response.text}", "ERROR")
            return None
            
    except Exception as e:
        print_live_feedback(f"Agent creation error: {e}", "ERROR")
        return None

def start_elevenlabs_conversation(phone_number, agent_id=None):
    """Start a native ElevenLabs Conversational AI outbound call using Batch Calling API"""
    if not agent_id:
        agent_id = ELEVENLABS_AGENT_ID
    
    print_live_feedback(f"Starting ElevenLabs native outbound call to {phone_number}", "INFO")
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Get company context for dynamic conversation
    company_context = get_company_context_for_call()
    
    # Create dynamic prompt and first message
    dynamic_prompt = f"""You are a professional procurement agent calling from {company_context['company_name']}, a leading {company_context['industry']} company in India. 

Your goal is to inquire about laboratory supplies and equipment. You need to:
1. Introduce yourself as {company_context['contact_person']} from {company_context['company_name']}
2. Explain you urgently need: {', '.join(company_context['urgent_items'])}
3. Ask for pricing, availability, and delivery terms
4. Be professional but efficient
5. Use a mix of Hindi and English as appropriate for Indian business

Keep responses concise and business-focused. End the call when you have sufficient pricing and availability information."""

    dynamic_first_message = f"Namaste! This is {company_context['contact_person']} calling from {company_context['company_name']}, a {company_context['industry']} company. We urgently need laboratory supplies including {', '.join(company_context['urgent_items'][:2])}. Could you help us with pricing and availability?"
    
    # Check if phone number ID is configured
    if not ELEVENLABS_PHONE_NUMBER_ID:
        print_live_feedback("❌ Phone number ID not configured!", "ERROR")
        print_live_feedback("📋 SETUP REQUIRED:", "ERROR")
        print_live_feedback("1. Run 'ElevenLabs Agent Management' → 'Setup Phone Number'", "INFO")
        print_live_feedback("2. Or manually set ELEVENLABS_PHONE_NUMBER_ID in the code", "INFO")
        print_live_feedback("3. Import a phone number in ElevenLabs Dashboard first", "INFO")
        return None

    # Get current Unix timestamp for immediate execution
    current_unix_time = int(time.time())
    
    # Batch call configuration for single call
    batch_config = {
        "call_name": f"Procurement Call - {company_context['company_name']} - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "agent_id": agent_id,
        "agent_phone_number_id": ELEVENLABS_PHONE_NUMBER_ID,
        "scheduled_time_unix": current_unix_time,  # Current time for immediate execution
        "recipients": [
            {
                "phone_number": phone_number,
                # Add overrides only if your agent supports them
                "system_prompt": dynamic_prompt,
                "first_message": dynamic_first_message
            }
        ]
    }
    
    print_live_feedback(f"📋 Call Config:", "INFO")
    print_live_feedback(f"   Agent ID: {agent_id}", "INFO")
    print_live_feedback(f"   Phone ID: {ELEVENLABS_PHONE_NUMBER_ID}", "INFO")
    print_live_feedback(f"   Target: {phone_number}", "INFO")
    print_live_feedback(f"   First Message: {dynamic_first_message[:50]}...", "INFO")
    
    # Store conversation context
    conversation_id = f"el_{int(time.time())}_{phone_number[-4:]}"
    conversation_context[conversation_id] = {
        'phone_number': phone_number,
        'company_context': company_context,
        'start_time': datetime.now().isoformat(),
        'status': 'scheduled',
        'platform': 'elevenlabs_native',
        'agent_id': agent_id,
        'conversation_id': conversation_id,
        'transcripts': [],
        'agent_responses': [],
        'extracted_data': {},
        'batch_config': batch_config
    }
    
    try:
        response = requests.post(
            "https://api.elevenlabs.io/v1/convai/batch-calling/submit",
            headers=headers,
            json=batch_config
        )
        
        if response.status_code == 200:
            batch_data = response.json()
            batch_id = batch_data.get("id")
            
            # Update conversation context with batch ID
            conversation_context[conversation_id]['batch_id'] = batch_id
            conversation_context[conversation_id]['status'] = 'initiated'
            
            print_live_feedback(f"✅ ElevenLabs native call initiated! Batch ID: {batch_id}", "SUCCESS")
            print_live_feedback(f"Conversation ID: {conversation_id}", "INFO")
            return conversation_id
        else:
            error_text = response.text
            print_live_feedback(f"❌ ElevenLabs native call failed: {error_text}", "ERROR")
            
            # Check for specific setup issues
            if "batch_calling_agreement_required" in error_text:
                print_live_feedback("📋 TERMS ACCEPTANCE ISSUE:", "ERROR")
                print_live_feedback("Already accepted terms but still getting this error?", "INFO")
                print_live_feedback("", "INFO")
                print_live_feedback("🔧 TROUBLESHOOTING STEPS:", "INFO") 
                print_live_feedback("1. Check you're logged into the correct ElevenLabs account", "INFO")
                print_live_feedback("2. Verify your API key matches the account that accepted terms", "INFO")
                print_live_feedback(f"   Your API key: {ELEVENLABS_API_KEY[:8]}...", "INFO")
                print_live_feedback("3. Try logging out and back into ElevenLabs dashboard", "INFO")
                print_live_feedback("4. Go to: https://elevenlabs.io/app/conversational-ai/outbound", "INFO")
                print_live_feedback("5. Check if there's a phone number imported and active", "INFO")
                print_live_feedback("6. Wait 5-10 minutes for changes to propagate", "INFO")
                print_live_feedback("", "INFO")
                print_live_feedback("💡 The API key must be from the same account that accepted terms", "INFO")
            elif "phone_number_id_placeholder" in error_text or "phone number" in error_text.lower():
                print_live_feedback("📋 PHONE NUMBER SETUP REQUIRED:", "ERROR")
                print_live_feedback("1. Go to ElevenLabs Dashboard > Conversational AI > Phone Numbers", "INFO")
                print_live_feedback("2. Import a phone number (Twilio or SIP)", "INFO")  
                print_live_feedback("3. Update agent_phone_number_id in the code", "INFO")
                print_live_feedback("4. See: https://elevenlabs.io/docs/conversational-ai/phone-numbers/batch-calls", "INFO")
            elif "unauthorized" in error_text.lower() or "401" in error_text:
                print_live_feedback("🔑 AUTHENTICATION ERROR:", "ERROR")
                print_live_feedback("Check your ElevenLabs API key is correct", "INFO")
                print_live_feedback(f"Current key: {ELEVENLABS_API_KEY[:8]}...", "INFO")
            elif "forbidden" in error_text.lower() or "403" in error_text:
                print_live_feedback("🚫 PERMISSION ERROR:", "ERROR")
                print_live_feedback("Your plan may not include Conversational AI outbound calling", "INFO")
                print_live_feedback("Check: https://elevenlabs.io/pricing", "INFO")
            else:
                print_live_feedback("❌ Unknown error. Check the error message above.", "ERROR")
            
            return None
            
    except Exception as e:
        print_live_feedback(f"❌ ElevenLabs native call error: {e}", "ERROR")
        return None

def start_elevenlabs_conversation_simple(phone_number, agent_id=None):
    """Start ElevenLabs call using agent's default settings (no overrides)"""
    if not agent_id:
        agent_id = ELEVENLABS_AGENT_ID
    
    print_live_feedback(f"Starting ElevenLabs call with default agent settings", "INFO")
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Check if phone number ID is configured
    if not ELEVENLABS_PHONE_NUMBER_ID:
        print_live_feedback("❌ Phone number ID not configured!", "ERROR")
        return None

    # Get current Unix timestamp for immediate execution
    current_unix_time = int(time.time())
    
    # Simple batch call configuration without overrides
    batch_config = {
        "call_name": f"Simple Procurement Call - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "agent_id": agent_id,
        "agent_phone_number_id": ELEVENLABS_PHONE_NUMBER_ID,
        "scheduled_time_unix": current_unix_time,
        "recipients": [
            {
                "phone_number": phone_number
                # No overrides - use agent's default prompt and first message
            }
        ]
    }
    
    print_live_feedback(f"📋 Simple Call Config:", "INFO")
    print_live_feedback(f"   Agent ID: {agent_id}", "INFO")
    print_live_feedback(f"   Phone ID: {ELEVENLABS_PHONE_NUMBER_ID}", "INFO")
    print_live_feedback(f"   Target: {phone_number}", "INFO")
    print_live_feedback(f"   Using agent's default prompts", "INFO")
    
    # Store conversation context
    conversation_id = f"el_simple_{int(time.time())}_{phone_number[-4:]}"
    conversation_context[conversation_id] = {
        'phone_number': phone_number,
        'start_time': datetime.now().isoformat(),
        'status': 'scheduled',
        'platform': 'elevenlabs_native_simple',
        'agent_id': agent_id,
        'conversation_id': conversation_id,
        'transcripts': [],
        'agent_responses': [],
        'extracted_data': {},
        'batch_config': batch_config,
        'using_overrides': False
    }
    
    try:
        response = requests.post(
            "https://api.elevenlabs.io/v1/convai/batch-calling/submit",
            headers=headers,
            json=batch_config
        )
        
        if response.status_code == 200:
            batch_data = response.json()
            batch_id = batch_data.get("id")
            
            # Update conversation context with batch ID
            conversation_context[conversation_id]['batch_id'] = batch_id
            conversation_context[conversation_id]['status'] = 'initiated'
            
            print_live_feedback(f"✅ Simple ElevenLabs call initiated! Batch ID: {batch_id}", "SUCCESS")
            print_live_feedback(f"Conversation ID: {conversation_id}", "INFO")
            return conversation_id
        else:
            error_text = response.text
            print_live_feedback(f"❌ Simple ElevenLabs call failed: {error_text}", "ERROR")
            return None
            
    except Exception as e:
        print_live_feedback(f"❌ Simple ElevenLabs call error: {e}", "ERROR")
        return None

def make_elevenlabs_twilio_call(phone_number, ngrok_url, conversation_id, agent_id, dynamic_prompt, dynamic_first_message):
    """Make a Twilio call that connects to ElevenLabs Conversational AI"""
    print_live_feedback(f"Making Twilio call with ElevenLabs integration to {phone_number}", "CALL")
    
    # Webhook URLs using ngrok
    voice_webhook = f"{ngrok_url}/webhook/elevenlabs_twilio_voice"
    
    # Make the call with specific parameters for ElevenLabs integration
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Calls.json"
    auth = base64.b64encode(f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Store the agent configuration for this call
    global elevenlabs_call_config
    if 'elevenlabs_call_config' not in globals():
        elevenlabs_call_config = {}
    
    elevenlabs_call_config[conversation_id] = {
        'agent_id': agent_id,
        'dynamic_prompt': dynamic_prompt,
        'dynamic_first_message': dynamic_first_message,
        'phone_number': phone_number
    }
    
    data = {
        'From': TWILIO_FROM_NUMBER,
        'To': phone_number,
        'Url': voice_webhook,
        'Method': 'POST',
        'StatusCallback': f"{ngrok_url}/webhook/status",
        'StatusCallbackEvent': ['initiated', 'ringing', 'answered', 'completed'],
        'StatusCallbackMethod': 'POST',
        'Record': 'true',
        'Timeout': '30'
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 201:
            call_data = response.json()
            print_live_feedback(f"✅ ElevenLabs Twilio call started! SID: {call_data['sid']}", "SUCCESS")
            return call_data['sid']
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print_live_feedback(f"❌ ElevenLabs Twilio call failed: {error_data}", "ERROR")
            return False
            
    except Exception as e:
        print_live_feedback(f"❌ ElevenLabs Twilio call error: {e}", "ERROR")
        return False
    

def get_company_context_for_call():
    """Get dynamic company context for personalized calls"""
    # Find company with urgent procurement needs
    procurement_needs = get_procurement_requirements()
    
    if procurement_needs:
        # Use first company with needs
        company_id, data = next(iter(procurement_needs.items()))
        company = data['company']
        urgent_items = [need['item'].name for need in data['needs'][:3]]
        
        return {
            'company_name': company.name,
            'industry': company.industry,
            'contact_person': company.contact_person,
            'urgent_items': urgent_items,
            'budget': company.budget_monthly
        }
    else:
        # Default to Bio Mac Lifesciences
        return {
            'company_name': 'Bio Mac Lifesciences',
            'industry': 'Biotechnology',
            'contact_person': 'Dr. Rajesh Kumar',
            'urgent_items': ['Microscope Slides', 'Petri Dishes', 'Chemical Reagents'],
            'budget': 500000
        }

def list_elevenlabs_agents():
    """List all ElevenLabs agents"""
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{ELEVENLABS_BASE_URL}/agents", headers=headers)
        
        if response.status_code == 200:
            agents_data = response.json()
            agents = agents_data.get('agents', [])
            
            if agents:
                print(f"\n📋 Found {len(agents)} ElevenLabs agents:")
                for i, agent in enumerate(agents, 1):
                    print(f"\n{i}. 🤖 {agent.get('name', 'Unnamed Agent')}")
                    print(f"   ID: {agent.get('agent_id', 'Unknown')}")
                    print(f"   Description: {agent.get('description', 'No description')}")
                    print(f"   Created: {agent.get('created_at', 'Unknown')}")
            else:
                print("No agents found. Create one using option 1!")
        else:
            print(f"❌ Failed to list agents: {response.text}")
            
    except Exception as e:
        print(f"❌ Error listing agents: {e}")

def list_elevenlabs_phone_numbers():
    """List all phone numbers imported into ElevenLabs"""
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    print("🔍 Checking ElevenLabs phone numbers...")
    
    try:
        # Use correct endpoint with trailing slash and better connection settings
        response = requests.get(
            "https://api.elevenlabs.io/v1/convai/phone-numbers/", 
            headers=headers,
            timeout=10,
            verify=True
        )
        
        print_live_feedback(f"API Response: {response.status_code}", "INFO")
        
        if response.status_code == 200:
            # Handle both array and object responses
            try:
                phone_data = response.json()
                
                # The API returns a direct array of phone numbers
                if isinstance(phone_data, list):
                    phone_numbers = phone_data
                else:
                    # Fallback to object format
                    phone_numbers = phone_data.get('phone_numbers', [])
                
                if phone_numbers:
                    print(f"\n📞 Found {len(phone_numbers)} imported phone numbers:")
                    for i, phone in enumerate(phone_numbers, 1):
                        print(f"\n{i}. 📱 {phone.get('phone_number', 'Unknown')}")
                        print(f"   ID: {phone.get('phone_number_id', 'Unknown')}")
                        print(f"   Provider: {phone.get('provider', 'Unknown')}")
                        print(f"   Label: {phone.get('label', 'No label')}")
                        
                        # Show assigned agent if any
                        assigned_agent = phone.get('assigned_agent', {})
                        if assigned_agent:
                            print(f"   Assigned Agent: {assigned_agent.get('agent_name', 'Unknown')} ({assigned_agent.get('agent_id', 'Unknown')})")
                    
                    print(f"\n💡 To use outbound calling, update your code with one of these phone_number_id values")
                    return phone_numbers
                else:
                    print("❌ No phone numbers found!")
                    print("\n📋 SETUP REQUIRED:")
                    print("1. Go to ElevenLabs Dashboard: https://elevenlabs.io/app/conversational-ai")
                    print("2. Navigate to 'Phone Numbers' section")
                    print("3. Click 'Import Phone Number'")
                    print("4. Choose Twilio or SIP integration")
                    print("5. Follow the setup instructions")
                    print("6. Come back here and run this function again")
                    return []
                    
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse API response: {e}")
                print(f"Raw response: {response.text[:200]}...")
                return []
                
        elif response.status_code == 401:
            print("❌ Authentication failed!")
            print("💡 Check your ElevenLabs API key:")
            print(f"   Current key: {ELEVENLABS_API_KEY[:8]}...")
            print("   Get your key from: https://elevenlabs.io/app/settings/api-keys")
            return []
        elif response.status_code == 403:
            print("❌ Access forbidden!")
            print("💡 Your API key might not have Conversational AI permissions")
            print("   Upgrade your plan at: https://elevenlabs.io/pricing")
            return []
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return []
            
    except requests.exceptions.ConnectionError as e:
        print("❌ Connection error! Check your internet connection.")
        print(f"Details: {e}")
        print("💡 Try again in a moment, or check if you're behind a firewall/proxy")
        return []
    except requests.exceptions.Timeout as e:
        print("❌ Request timeout! ElevenLabs API might be slow.")
        print("💡 Try again in a few seconds")
        return []
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("💡 Please try again or check your API configuration")
        return []

def verify_elevenlabs_account_status():
    """Verify ElevenLabs account and batch calling setup"""
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    print("\n🔍 VERIFYING ELEVENLABS ACCOUNT STATUS")
    print("=" * 50)
    
    # Test API key validity
    try:
        print("1. Testing API key...")
        response = requests.get("https://api.elevenlabs.io/v1/user", headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"   ✅ API key valid")
            print(f"   👤 Account: {user_data.get('email', 'Unknown')}")
            print(f"   📊 Plan: {user_data.get('subscription', {}).get('tier', 'Unknown')}")
        else:
            print(f"   ❌ API key invalid: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ API key test failed: {e}")
        return False
    
    # Check agents
    print("2. Checking agents...")
    try:
        response = requests.get("https://api.elevenlabs.io/v1/convai/agents", headers=headers, timeout=10)
        if response.status_code == 200:
            agents = response.json().get('agents', [])
            print(f"   ✅ Found {len(agents)} agents")
            if agents:
                agent_found = any(agent.get('agent_id') == ELEVENLABS_AGENT_ID for agent in agents)
                print(f"   🤖 Your agent {ELEVENLABS_AGENT_ID}: {'✅ Found' if agent_found else '❌ Not found'}")
        else:
            print(f"   ❌ Agents check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Agents check error: {e}")
    
    # Check phone numbers
    print("3. Checking phone numbers...")
    phone_numbers = list_elevenlabs_phone_numbers()
    if phone_numbers:
        print(f"   ✅ Found {len(phone_numbers)} phone numbers")
        if ELEVENLABS_PHONE_NUMBER_ID:
            phone_found = any(phone.get('phone_number_id') == ELEVENLABS_PHONE_NUMBER_ID for phone in phone_numbers)
            print(f"   📞 Your phone ID: {'✅ Found' if phone_found else '❌ Not found'}")
        else:
            print("   ⚠️ No phone number ID configured")
    else:
        print("   ❌ No phone numbers found")
    
    # Test batch calling with minimal request
    print("4. Testing batch calling access...")
    try:
        test_batch = {
            "call_name": "Test Batch Call Access",
            "agent_id": ELEVENLABS_AGENT_ID,
            "agent_phone_number_id": ELEVENLABS_PHONE_NUMBER_ID or "test_id",
            "scheduled_time_unix": int(time.time()) + 3600,  # 1 hour from now
            "recipients": []  # Empty recipients for test
        }
        
        response = requests.post(
            "https://api.elevenlabs.io/v1/convai/batch-calling/submit",
            headers=headers,
            json=test_batch,
            timeout=10
        )
        
        if response.status_code == 200:
            print("   ✅ Batch calling access confirmed!")
            return True
        else:
            error_text = response.text
            if "batch_calling_agreement_required" in error_text:
                print("   ❌ Terms & Conditions still not accepted")
                print("   💡 Try these steps:")
                print("      - Clear browser cache and cookies for elevenlabs.io")
                print("      - Use an incognito/private browser window")
                print("      - Contact ElevenLabs support if issue persists")
            elif "recipients" in error_text.lower():
                print("   ✅ Batch calling access confirmed! (Empty recipients error expected)")
                return True
            else:
                print(f"   ❌ Batch calling test failed: {error_text}")
            
    except Exception as e:
        print(f"   ❌ Batch calling test error: {e}")
    
    return False

def check_recent_batch_calls():
    """Check status of recent batch calls to debug call issues"""
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    print("\n📞 RECENT BATCH CALLS STATUS")
    print("=" * 50)
    
    try:
        response = requests.get(
            "https://api.elevenlabs.io/v1/convai/batch-calling/list",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            batch_data = response.json()
            batch_calls = batch_data.get('batch_calls', [])
            
            if batch_calls:
                print(f"Found {len(batch_calls)} recent batch calls:")
                
                for i, batch in enumerate(batch_calls[:5], 1):  # Show last 5
                    call_name = batch.get('name', 'Unknown')
                    status = batch.get('status', 'Unknown')
                    total_scheduled = batch.get('total_calls_scheduled', 0)
                    total_dispatched = batch.get('total_calls_dispatched', 0)
                    created_at = batch.get('created_at_unix', 0)
                    
                    # Convert timestamp
                    try:
                        created_time = datetime.fromtimestamp(created_at).strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        created_time = 'Unknown'
                    
                    print(f"\n{i}. {call_name}")
                    print(f"   Status: {status}")
                    print(f"   Calls: {total_dispatched}/{total_scheduled}")
                    print(f"   Created: {created_time}")
                    
                    # Provide status explanations
                    if status == 'completed':
                        print(f"   ✅ Batch completed successfully")
                    elif status == 'failed':
                        print(f"   ❌ Batch failed - check agent/phone number config")
                    elif status == 'pending':
                        print(f"   ⏳ Batch is queued for execution")
                    elif status == 'in_progress':
                        print(f"   🔄 Batch is currently running")
                
                print(f"\n💡 If calls are completing but ending immediately:")
                print(f"   - Your agent might need conversation flow configuration")
                print(f"   - Check agent's first message and prompts in ElevenLabs dashboard")
                print(f"   - Ensure agent has proper conversation settings")
                print(f"   - Try option 2 (Default Agent Setup) for calls")
                
            else:
                print("No recent batch calls found")
                print("💡 Make a test call first, then check this status")
        else:
            print(f"❌ Failed to get batch call status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking batch calls: {e}")

def update_elevenlabs_phone_number_id():
    """Interactive function to update the phone number ID"""
    global ELEVENLABS_PHONE_NUMBER_ID
    
    phone_numbers = list_elevenlabs_phone_numbers()
    
    if phone_numbers:
        print(f"\nCurrent phone number ID: {getattr(sys.modules[__name__], 'ELEVENLABS_PHONE_NUMBER_ID', 'Not set')}")
        
        try:
            choice = int(input(f"\nSelect phone number (1-{len(phone_numbers)}): ").strip())
            if 1 <= choice <= len(phone_numbers):
                selected_phone = phone_numbers[choice - 1]
                phone_id = selected_phone.get('phone_number_id')
                phone_number = selected_phone.get('phone_number')
                
                # Update the global variable
                globals()['ELEVENLABS_PHONE_NUMBER_ID'] = phone_id
                
                print(f"✅ Phone number ID updated to: {phone_id}")
                print(f"📱 Phone number: {phone_number}")
                print("💡 ElevenLabs outbound calling is now ready!")
                return phone_id
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a valid number.")
    
    return None

# Data Classes for the platform
@dataclass
class InventoryItem:
    item_id: str
    name: str
    category: str
    current_stock: int
    minimum_required: int
    maximum_capacity: int
    unit: str
    priority: str  # high, medium, low
    last_ordered: Optional[str] = None
    average_price: float = 0.0
    preferred_vendors: Optional[List[str]] = None

@dataclass
class Company:
    company_id: str
    name: str
    industry: str
    contact_person: str
    phone: str
    email: str
    budget_monthly: float
    procurement_priority: str
    inventory: Optional[Dict[str, InventoryItem]] = None

@dataclass
class Vendor:
    vendor_id: str
    name: str
    phone: str
    email: str
    specialties: List[str]
    rating: float
    response_time: str
    price_competitiveness: str
    last_contact: Optional[str] = None

@dataclass
class Quote:
    quote_id: str
    vendor_id: str
    company_id: str
    items: List[Dict]
    total_amount: float
    validity_days: int
    delivery_time: str
    payment_terms: str
    timestamp: str
    status: str  # pending, accepted, rejected, negotiating

@dataclass
class Negotiation:
    negotiation_id: str
    quote_id: str
    rounds: List[Dict]
    current_offer: float
    target_price: float
    status: str
    last_update: str

# Global data storage
companies_db: Dict[str, Company] = {}
vendors_db: Dict[str, Vendor] = {}
quotes_db: Dict[str, Quote] = {}
negotiations_db: Dict[str, Negotiation] = {}
procurement_analytics = {
    'total_savings': 0.0,
    'active_negotiations': 0,
    'pending_orders': 0,
    'vendor_performance': {},
    'monthly_spending': {}
}

# Global state (existing)
conversation_log = []
current_call_sid = None
ngrok_url = None
server_running = False
conversation_context = {}  # Track conversation state per call
whatsapp_conversations = {}  # Track WhatsApp conversation state
failed_calls = {}  # Track failed calls for WhatsApp fallback

# Twilio credentials
TWILIO_ACCOUNT_SID = "AC820daae89092e30fee3487e80162d2e2"
TWILIO_AUTH_TOKEN = "76d105c3d0bdee08cfc97117a7c05b32"
TWILIO_FROM_NUMBER = "+14323484517"
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"  # Twilio WhatsApp sandbox number
DEFAULT_PHONE = "+918800000488"

def initialize_sample_data():
    """Initialize sample companies, vendors, and inventory data"""
    global companies_db, vendors_db
    
    # Sample Companies
    companies_db = {
        "bio_mac": Company(
            company_id="bio_mac",
            name="Bio Mac Lifesciences",
            industry="Biotechnology",
            contact_person="Dr. Rajesh Kumar",
            phone="+918800000488",
            email="procurement@biomac.in",
            budget_monthly=500000.0,
            procurement_priority="quality_first",
            inventory={
                "microscope_slides": InventoryItem(
                    item_id="mic_slides_001",
                    name="Microscope Slides",
                    category="Laboratory Consumables",
                    current_stock=50,
                    minimum_required=200,
                    maximum_capacity=1000,
                    unit="pieces",
                    priority="high",
                    average_price=2.5,
                    preferred_vendors=["lab_supply_pro", "scientific_corp"]
                ),
                "petri_dishes": InventoryItem(
                    item_id="petri_001",
                    name="Petri Dishes",
                    category="Laboratory Consumables",
                    current_stock=25,
                    minimum_required=100,
                    maximum_capacity=500,
                    unit="pieces",
                    priority="high",
                    average_price=1.8,
                    preferred_vendors=["lab_supply_pro"]
                ),
                "pipette_tips": InventoryItem(
                    item_id="pipette_tips_001",
                    name="Pipette Tips",
                    category="Laboratory Consumables",
                    current_stock=800,
                    minimum_required=500,
                    maximum_capacity=2000,
                    unit="pieces",
                    priority="medium",
                    average_price=0.15,
                    preferred_vendors=["scientific_corp", "lab_equipment_ltd"]
                )
            }
        ),
        "pharma_research": Company(
            company_id="pharma_research",
            name="Pharma Research Institute",
            industry="Pharmaceutical",
            contact_person="Dr. Priya Sharma",
            phone="+918800000499",
            email="purchase@pharmaresearch.in",
            budget_monthly=750000.0,
            procurement_priority="cost_effective",
            inventory={
                "chemical_reagents": InventoryItem(
                    item_id="reagents_001",
                    name="Chemical Reagents",
                    category="Chemicals",
                    current_stock=20,
                    minimum_required=50,
                    maximum_capacity=200,
                    unit="bottles",
                    priority="high",
                    average_price=450.0,
                    preferred_vendors=["chemical_solutions", "pharma_supply"]
                ),
                "test_tubes": InventoryItem(
                    item_id="test_tubes_001",
                    name="Test Tubes",
                    category="Glassware",
                    current_stock=150,
                    minimum_required=100,
                    maximum_capacity=500,
                    unit="pieces",
                    priority="medium",
                    average_price=3.2,
                    preferred_vendors=["lab_supply_pro", "scientific_corp"]
                )
            }
        ),
        "medical_diagnostics": Company(
            company_id="medical_diagnostics",
            name="Advanced Medical Diagnostics",
            industry="Healthcare",
            contact_person="Dr. Amit Patel",
            phone="+918800000477",
            email="ops@meddiagnostics.in",
            budget_monthly=300000.0,
            procurement_priority="urgent_delivery",
            inventory={
                "diagnostic_kits": InventoryItem(
                    item_id="diag_kits_001",
                    name="Diagnostic Test Kits",
                    category="Medical Supplies",
                    current_stock=5,
                    minimum_required=25,
                    maximum_capacity=100,
                    unit="kits",
                    priority="high",
                    average_price=1200.0,
                    preferred_vendors=["medical_supply_chain", "diagnostic_corp"]
                ),
                "syringes": InventoryItem(
                    item_id="syringes_001",
                    name="Disposable Syringes",
                    category="Medical Supplies",
                    current_stock=200,
                    minimum_required=500,
                    maximum_capacity=2000,
                    unit="pieces",
                    priority="high",
                    average_price=0.45,
                    preferred_vendors=["medical_supply_chain"]
                )
            }
        )
    }
    
    # Sample Vendors
    vendors_db = {
        "lab_supply_pro": Vendor(
            vendor_id="lab_supply_pro",
            name="Lab Supply Pro",
            phone="+918800001111",
            email="sales@labsupplypro.com",
            specialties=["Laboratory Consumables", "Glassware"],
            rating=4.5,
            response_time="24 hours",
            price_competitiveness="competitive"
        ),
        "scientific_corp": Vendor(
            vendor_id="scientific_corp",
            name="Scientific Corporation",
            phone="+918800002222",
            email="orders@scientificcorp.in",
            specialties=["Laboratory Equipment", "Laboratory Consumables"],
            rating=4.2,
            response_time="48 hours",
            price_competitiveness="premium"
        ),
        "chemical_solutions": Vendor(
            vendor_id="chemical_solutions",
            name="Chemical Solutions Ltd",
            phone="+918800003333",
            email="procurement@chemsolutions.co.in",
            specialties=["Chemicals", "Reagents"],
            rating=4.7,
            response_time="12 hours",
            price_competitiveness="competitive"
        ),
        "medical_supply_chain": Vendor(
            vendor_id="medical_supply_chain",
            name="Medical Supply Chain",
            phone="+918800004444",
            email="business@medsupplychain.in",
            specialties=["Medical Supplies", "Diagnostic Equipment"],
            rating=4.3,
            response_time="36 hours",
            price_competitiveness="budget_friendly"
        ),
        "lab_equipment_ltd": Vendor(
            vendor_id="lab_equipment_ltd",
            name="Lab Equipment Ltd",
            phone="+918800005555",
            email="sales@labequipment.in",
            specialties=["Laboratory Equipment", "Laboratory Consumables"],
            rating=3.9,
            response_time="72 hours",
            price_competitiveness="budget_friendly"
        )
    }
    
    print_live_feedback("✅ Sample data initialized: 3 companies, 5 vendors, multiple inventory items", "SUCCESS")

def get_procurement_requirements():
    """Analyze inventory and determine what needs to be procured"""
    procurement_needs = {}
    
    for company_id, company in companies_db.items():
        if not company.inventory:
            continue
            
        needs = []
        for item_id, item in company.inventory.items():
            if item.current_stock <= item.minimum_required:
                shortage = item.minimum_required - item.current_stock
                urgency = "critical" if item.current_stock < (item.minimum_required * 0.5) else "urgent"
                
                needs.append({
                    'item': item,
                    'shortage': shortage,
                    'urgency': urgency,
                    'recommended_order': min(shortage * 2, item.maximum_capacity - item.current_stock)
                })
        
        if needs:
            procurement_needs[company_id] = {
                'company': company,
                'needs': sorted(needs, key=lambda x: (x['urgency'] == 'critical', x['item'].priority == 'high'), reverse=True)
            }
    
    return procurement_needs

def find_suitable_vendors(item: InventoryItem) -> List[Vendor]:
    """Find vendors that can supply a specific item"""
    suitable_vendors = []
    
    for vendor_id, vendor in vendors_db.items():
        # Check if vendor specializes in this category
        if any(specialty in item.category for specialty in vendor.specialties):
            suitable_vendors.append(vendor)
        # Also check preferred vendors
        elif item.preferred_vendors and vendor_id in item.preferred_vendors:
            suitable_vendors.append(vendor)
    
    # Sort by rating and price competitiveness
    return sorted(suitable_vendors, key=lambda v: v.rating, reverse=True)

def generate_dynamic_company_greeting(company: Company):
    """Generate company-specific greeting"""
    if not model:
        return f"Namaste! Main {company.name} se bol raha hun. Humein {company.industry} supplies chahiye."
    
    try:
        prompt = f"""
        Generate a professional greeting for a procurement call. You are calling on behalf of {company.name}, a {company.industry} company.
        
        Requirements:
        1. Professional and friendly
        2. Use Hindi-English mix for Indian business context
        3. Introduce yourself and company briefly
        4. Mention you need supplies for {company.industry}
        5. Keep concise (2 sentences max)
        6. Sound natural for phone conversation
        7. No emojis
        
        Generate only the spoken text.
        """
        
        response = model.generate_content(prompt)
        greeting = response.text.strip()
        print_live_feedback(f"Generated greeting for {company.name}: '{greeting}'", "AI")
        return greeting
        
    except Exception as e:
        print_live_feedback(f"Greeting generation error: {e}", "ERROR")
        return f"Namaste! Main {company.name} se bol raha hun. Humein {company.industry} supplies ki requirement hai."

def print_live_feedback(message, category="INFO"):
    """Print live feedback with timestamps and minimal styling"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    colors = {
        "INFO": "37",      # White
        "SUCCESS": "32",   # Green
        "ERROR": "31",     # Red
        "SPEECH": "36",    # Cyan
        "AI": "33",        # Yellow
        "CALL": "35"       # Magenta
    }
    
    color_code = colors.get(category, "37")
    print(f"\033[{color_code}m[{timestamp}] {category}: {message}\033[0m")

def extract_requirements_from_speech(speech_text):
    """Extract specific requirements and pricing from speech using Gemini with enhanced intelligence"""
    if not model or not speech_text:
        return None
    
    try:
        extraction_prompt = f"""
        Analyze this vendor response for laboratory supplies procurement and extract ALL relevant information:
        Vendor Response: "{speech_text}"
        
        Extract and return a comprehensive JSON object with these fields:
        {{
            "items_mentioned": ["item1", "item2", "item3"],
            "prices": [
                {{"item": "item_name", "price": 45, "unit": "per piece", "currency": "INR", "details": "any additional price info"}},
                {{"item": "another_item", "price": 120, "unit": "per pack", "currency": "INR", "details": "bulk discount available"}}
            ],
            "availability": [
                {{"item": "item_name", "status": "in_stock/out_of_stock/limited", "quantity": "available quantity"}}
            ],
            "discounts": "any discount information or bulk pricing",
            "delivery_info": {{
                "time": "delivery time mentioned",
                "charges": "delivery charges if any",
                "conditions": "delivery conditions"
            }},
            "minimum_order": "minimum order requirements",
            "contact_info": {{
                "person": "contact person name",
                "phone": "phone number",
                "email": "email if mentioned",
                "company": "company name"
            }},
            "payment_terms": "payment conditions or terms",
            "quality_info": "quality standards, certifications, brands mentioned",
            "additional_services": "installation, training, support services",
            "vendor_questions": ["any questions vendor asked"],
            "next_steps": "what vendor suggested as next steps",
            "sentiment": "positive/neutral/negative - vendor's interest level",
            "other_notes": "any other important business information"
        }}
        
        Instructions:
        1. Be thorough - extract even small details
        2. If multiple items mentioned, list ALL of them
        3. If prices mentioned in different formats, normalize them
        4. Handle both Hindi and English content
        5. Extract implied information (e.g., if they say "available" assume in_stock)
        6. If vendor asks questions, capture those too
        7. If no information found for a field, use null or empty array/object
        8. For prices, try to extract numbers even if currency not explicitly stated
        9. Look for technical specifications, brands, quality mentions
        10. Identify any business relationship building language
        
        Return ONLY valid JSON, no other text.
        """
        
        response = model.generate_content(extraction_prompt)
        extracted_text = response.text.strip()
        
        # Clean up the response to ensure it's valid JSON
        if extracted_text.startswith('```json'):
            extracted_text = extracted_text.replace('```json', '').replace('```', '')
        elif extracted_text.startswith('```'):
            extracted_text = extracted_text.replace('```', '')
        
        extracted_text = extracted_text.strip()
        
        # Try to parse as JSON
        try:
            extracted_data = json.loads(extracted_text)
            
            # Validate and enhance the extracted data
            if not isinstance(extracted_data.get('items_mentioned'), list):
                extracted_data['items_mentioned'] = []
            if not isinstance(extracted_data.get('prices'), list):
                extracted_data['prices'] = []
            if not isinstance(extracted_data.get('availability'), list):
                extracted_data['availability'] = []
            
            # Add confidence score based on amount of data extracted
            confidence_score = 0
            if extracted_data['items_mentioned']:
                confidence_score += 30
            if extracted_data['prices']:
                confidence_score += 40
            if extracted_data.get('delivery_info'):
                confidence_score += 15
            if extracted_data.get('contact_info'):
                confidence_score += 15
            
            extracted_data['extraction_confidence'] = confidence_score
            extracted_data['extraction_timestamp'] = datetime.now().isoformat()
            
            print_live_feedback(f"Extraction confidence: {confidence_score}%", "SUCCESS")
            return extracted_data
            
        except json.JSONDecodeError as e:
            print_live_feedback(f"JSON parsing failed: {e}", "ERROR")
            # If JSON parsing fails, try to extract basic info with simpler approach
            return extract_basic_info_fallback(speech_text)
            
    except Exception as e:
        print_live_feedback(f"Extraction error: {e}", "ERROR")
        return extract_basic_info_fallback(speech_text)

def extract_basic_info_fallback(speech_text):
    """Fallback extraction method when main extraction fails"""
    if not model:
        return {"error": "No AI model available", "speech_text": speech_text}
    
    try:
        simple_prompt = f"""
        From this vendor response: "{speech_text}"
        
        Extract basic information and respond in this simple format:
        Items: [list any products/items mentioned]
        Prices: [any numbers or pricing info]
        Available: [yes/no/maybe based on response tone]
        
        Keep it simple and factual.
        """
        
        response = model.generate_content(simple_prompt)
        simple_extraction = response.text.strip()
        
        return {
            "extraction_method": "fallback",
            "simple_extraction": simple_extraction,
            "speech_text": speech_text,
            "extraction_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": str(e), 
            "speech_text": speech_text,
            "extraction_method": "failed",
            "extraction_timestamp": datetime.now().isoformat()
        }

def generate_dynamic_greeting():
    """Generate professional initial greeting using Gemini"""
    if not model:
        return "Namaste! Main Bio Mac Lifesciences se bol raha hun. Humein laboratory supplies chahiye."
    
    try:
        prompt = """
        Generate a professional greeting for a procurement call. You are calling on behalf of Bio Mac Lifesciences, a laboratory supplies company.
        
        Requirements:
        1. Professional and friendly
        2. Use Hindi-English mix for Indian business context
        3. Introduce yourself and company briefly
        4. Mention you need laboratory supplies
        5. Keep concise (2 sentences max)
        6. Sound natural for phone conversation
        7. No emojis
        
        Generate only the spoken text.
        """
        
        response = model.generate_content(prompt)
        greeting = response.text.strip()
        print_live_feedback(f"Generated greeting: '{greeting}'", "AI")
        return greeting
        
    except Exception as e:
        print_live_feedback(f"Greeting generation error: {e}", "ERROR")
        return "Namaste! Main Bio Mac Lifesciences se bol raha hun. Humein laboratory supplies ki requirement hai."

def generate_dynamic_follow_up(conversation_state):
    """Generate focused follow-up questions based on conversation state"""
    if not model:
        return "What items do you have available and at what price?"
    
    try:
        # Build context from conversation
        items_discussed = conversation_state.get('items_discussed', [])
        prices_received = conversation_state.get('prices_received', [])
        call_stage = conversation_state.get('stage', 'initial')
        turn_count = conversation_state.get('turn_count', 0)
        
        prompt = f"""
        Generate a single, focused follow-up question for a procurement call.
        
        Current state:
        - Stage: {call_stage}
        - Turn: {turn_count}
        - Items discussed: {items_discussed}
        - Prices received: {len(prices_received)}
        
        Rules:
        1. Ask only ONE specific question
        2. Focus on the most important missing information
        3. If no items mentioned yet: ask about laboratory supplies availability
        4. If items mentioned but no prices: ask for pricing only
        5. If basic info gathered: ask about delivery time OR minimum order (pick one)
        6. After 3+ turns: start closing the conversation
        7. Use natural business language (Hindi-English mix)
        8. Keep it brief and direct
        9. No emojis needed
        
        Generate only the question, nothing else.
        """
        
        response = model.generate_content(prompt)
        follow_up = response.text.strip()
        print_live_feedback(f"Generated follow-up: '{follow_up}'", "AI")
        return follow_up
        
    except Exception as e:
        print_live_feedback(f"Follow-up generation error: {e}", "ERROR")
        return "Aur kya items available hain aapke paas?"

def serialize_conversation_context(context):
    """Convert conversation context to JSON-serializable format"""
    serialized = context.copy()
    
    # Convert sets to lists for JSON serialization
    if 'questions_asked' in serialized and isinstance(serialized['questions_asked'], set):
        serialized['questions_asked'] = list(serialized['questions_asked'])
    
    # Ensure all fields are JSON serializable
    for key, value in serialized.items():
        if isinstance(value, set):
            serialized[key] = list(value)
    
    return serialized

def update_conversation_context(call_sid, vendor_speech, extracted_data):
    """Update conversation context with new information and prevent loops"""
    global conversation_context
    
    if call_sid not in conversation_context:
        conversation_context[call_sid] = {
            'stage': 'initial',
            'items_discussed': [],
            'prices_received': [],
            'vendor_responses': [],
            'turn_count': 0,
            'questions_asked': [],  # Changed from set to list
            'has_comprehensive_info': False,
            'vendor_engagement': 'positive',
            'last_meaningful_response': True
        }
    
    context = conversation_context[call_sid]
    context['turn_count'] += 1
    context['vendor_responses'].append(vendor_speech.lower())
    
    # Check vendor engagement
    if vendor_speech.lower().strip() in ['no', 'no.', 'nah', 'nope']:
        context['vendor_engagement'] = 'declining'
        context['last_meaningful_response'] = False
    elif len(vendor_speech.strip()) < 10:
        context['last_meaningful_response'] = False
    else:
        context['last_meaningful_response'] = True
        if context['vendor_engagement'] == 'declining':
            context['vendor_engagement'] = 'neutral'
    
    # Extract and update items and prices from the data
    if extracted_data and isinstance(extracted_data, dict):
        if 'items_mentioned' in extracted_data and extracted_data['items_mentioned']:
            for item in extracted_data['items_mentioned']:
                if item and item not in context['items_discussed']:
                    context['items_discussed'].append(item)
        
        if 'prices' in extracted_data and extracted_data['prices']:
            context['prices_received'].extend(extracted_data['prices'])
    
    # Check if we have comprehensive information
    has_items = len(context['items_discussed']) >= 2
    has_pricing = len(context['prices_received']) >= 1
    has_delivery_info = extracted_data and extracted_data.get('delivery_info')
    
    if has_items and has_pricing:
        context['has_comprehensive_info'] = True
        context['stage'] = 'comprehensive'
    elif context['turn_count'] >= 8:
        context['stage'] = 'wrapping_up'
    elif context['turn_count'] >= 5 and (has_items or has_pricing):
        context['stage'] = 'sufficient_info'
    elif context['turn_count'] >= 3:
        context['stage'] = 'information_gathering'
    
    print_live_feedback(f"Updated context: Turn {context['turn_count']}, Stage: {context['stage']}, Engagement: {context['vendor_engagement']}", "INFO")
    return context

def should_end_conversation(context, vendor_speech):
    """Determine if conversation should end based on context"""
    
    # End if vendor is clearly not engaged
    if context['vendor_engagement'] == 'declining' and context['turn_count'] >= 3:
        return True, "vendor_disengaged"
    
    # End if we have comprehensive information
    if context['has_comprehensive_info'] and context['turn_count'] >= 4:
        return True, "comprehensive_info_collected"
    
    # End if conversation is too long without meaningful progress
    if context['turn_count'] >= 10:
        return True, "conversation_too_long"
    
    # End if we have sufficient basic info and vendor seems done
    if (context['stage'] in ['sufficient_info', 'wrapping_up'] and 
        context['turn_count'] >= 6 and 
        len(context['items_discussed']) >= 1):
        return True, "sufficient_info_gathered"
    
    # End if vendor gives repeated short negative responses
    recent_responses = context['vendor_responses'][-3:]
    if len(recent_responses) >= 3 and all(len(r) < 10 for r in recent_responses):
        return True, "vendor_unresponsive"
    
    return False, None

def generate_closing_message(reason, context):
    """Generate appropriate closing message based on conversation outcome"""
    
    if reason == "comprehensive_info_collected":
        return "Perfect! Thank you for the detailed information. We have everything we need. Our procurement team will review and get back to you soon."
    
    elif reason == "vendor_disengaged":
        return "Understood. Thank you for your time. If you change your mind, please feel free to contact Bio Mac Lifesciences."
    
    elif reason == "sufficient_info_gathered":
        return "Thank you for the information provided. Our team will review the details and contact you if we need anything further."
    
    elif reason == "conversation_too_long":
        return "Thank you for all the information. Our procurement team will review everything and get back to you with our requirements."
    
    elif reason == "vendor_unresponsive":
        return "Thank you for your time. We'll reach out again if we need any laboratory supplies. Have a good day!"
    
    else:
        return "Thank you for the information. Our team will be in touch."

def generate_whatsapp_response(vendor_message, conversation_context):
    """Generate focused WhatsApp response with loop prevention"""
    if not model:
        return "Thanks for the info. Our team will review and get back to you."
    
    try:
        # Check if conversation should end
        should_end, end_reason = should_end_conversation(conversation_context, vendor_message)
        
        if should_end:
            closing_message = generate_closing_message(end_reason, conversation_context)
            print_live_feedback(f"Ending conversation: {end_reason}", "INFO")
            return closing_message
        
        # Count meaningful information received
        items_count = len(conversation_context.get('items_discussed', []))
        prices_count = len(conversation_context.get('prices_received', []))
        turn_count = conversation_context.get('turn_count', 0)
        
        prompt = f"""
        Generate a WhatsApp response for this procurement conversation.
        
        Vendor said: "{vendor_message}"
        Turn: {turn_count}
        Items collected: {items_count}
        Prices collected: {prices_count}
        Stage: {conversation_context.get('stage', 'initial')}
        
        IMPORTANT RULES:
        1. If vendor provided comprehensive product catalog already, don't ask for more items
        2. If you have 2+ items and pricing, start wrapping up
        3. If vendor says just "no" or short responses, politely close conversation
        4. Don't repeat similar questions
        5. Focus on ONE missing critical piece of info only
        6. If sufficient info collected, thank and close professionally
        7. Maximum 1 sentence
        8. Be efficient and respectful of vendor's time
        
        Priority order: Items → Pricing → Delivery → Close
        
        Generate only the message text.
        """
        
        response = model.generate_content(prompt)
        whatsapp_response = response.text.strip()
        print_live_feedback(f"Generated WhatsApp response: '{whatsapp_response}'", "AI")
        return whatsapp_response
        
    except Exception as e:
        print_live_feedback(f"WhatsApp response error: {e}", "ERROR")
        return "Thank you for the information. Our team will review and contact you."

def generate_intelligent_response(vendor_speech):
    """Generate focused response with conversation context and loop prevention"""
    if not model:
        return "Samjha sir, dhanyawad!"
    
    try:
        print_live_feedback(f"Processing speech: '{vendor_speech}'", "SPEECH")
        
        # Extract requirements first
        extracted_data = extract_requirements_from_speech(vendor_speech)
        if extracted_data:
            print_live_feedback(f"Extracted {len(extracted_data.get('items_mentioned', []))} items, {len(extracted_data.get('prices', []))} prices", "SUCCESS")
        
        # Update conversation context
        context = update_conversation_context(current_call_sid, vendor_speech, extracted_data)
        
        # Check if conversation should end
        should_end, end_reason = should_end_conversation(context, vendor_speech)
        
        if should_end:
            ai_response = generate_closing_message(end_reason, context)
            print_live_feedback(f"Ending conversation: {end_reason}", "INFO")
        else:
            prompt = f"""
            Generate a brief response for this procurement call.
            
            Context:
            - Stage: {context['stage']}
            - Turn: {context['turn_count']}
            - Items: {len(context['items_discussed'])}
            - Prices: {len(context['prices_received'])}
            - Vendor engagement: {context['vendor_engagement']}
            
            Vendor said: "{vendor_speech}"
            
            CRITICAL RULES:
            1. If vendor provided detailed catalog, don't ask for more items
            2. If 3+ items and pricing collected, thank and close
            3. If vendor unengaged (short responses), politely close
            4. Ask only ONE specific question if truly needed
            5. Respect vendor's time - be efficient
            6. Maximum 1-2 sentences
            7. No repetitive questions
            
            Generate only the response text.
            """
            
            response = model.generate_content(prompt)
            ai_response = response.text.strip()
        
        # Log the conversation with extracted data
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "vendor_said": vendor_speech,
            "ai_response": ai_response,
            "extracted_data": extracted_data,
            "conversation_context": serialize_conversation_context(context),
            "call_sid": current_call_sid,
            "type": "voice_conversation",
            "conversation_ended": should_end,
            "end_reason": end_reason if should_end else None
        }
        conversation_log.append(conversation_entry)
        
        # Save to CSV
        save_conversation_to_csv(conversation_entry)
        
        print_live_feedback(f"AI Response: '{ai_response}'", "AI")
        
        # Save to file for persistence with error handling
        try:
            with open("live_conversation_log.json", "w") as f:
                json.dump(conversation_log, f, indent=2)
        except (TypeError, ValueError) as e:
            print_live_feedback(f"JSON save error: {e}", "ERROR")
            # Save a simplified version without problematic data
            simplified_log = []
            for entry in conversation_log:
                simplified_entry = entry.copy()
                if 'conversation_context' in simplified_entry:
                    simplified_entry['conversation_context'] = serialize_conversation_context(simplified_entry['conversation_context'])
                simplified_log.append(simplified_entry)
            
            with open("live_conversation_log.json", "w") as f:
                json.dump(simplified_log, f, indent=2)
        
        return ai_response
        
    except Exception as e:
        print_live_feedback(f"AI error: {e}", "ERROR")
        return "Thank you for the information. Our team will review and contact you."

# Removed old ElevenLabs webhook handlers - now using Twilio + ElevenLabs TTS integration

def generate_intelligent_elevenlabs_response(vendor_speech, conversation_id):
    """Generate intelligent response for ElevenLabs-powered calls"""
    if not model:
        return "Thank you for the information. We will review and get back to you."
    
    try:
        # Get conversation context
        context = conversation_context.get(conversation_id, {})
        transcripts = context.get('transcripts', [])
        turn_count = len(transcripts)
        
        prompt = f"""
        Generate a brief, professional response for this procurement call conversation.
        
        Vendor just said: "{vendor_speech}"
        Turn number: {turn_count}
        
        You are calling from {context.get('company_context', {}).get('company_name', 'Bio Mac Lifesciences')}.
        
        Generate a response that:
        1. Acknowledges what the vendor said
        2. Is professional and business-appropriate
        3. Keeps the conversation moving forward
        4. Maximum 20 words
        5. Uses simple, clear language
        6. Shows interest if they mentioned products/pricing
        
        Generate ONLY the response text, nothing else.
        """
        
        response = model.generate_content(prompt)
        ai_response = response.text.strip()
        
        print_live_feedback(f"ElevenLabs AI Response: '{ai_response}'", "AI")
        return ai_response
        
    except Exception as e:
        print_live_feedback(f"ElevenLabs response error: {e}", "ERROR")
        return "Thank you for the information. Please continue."

def generate_elevenlabs_follow_up(extracted_data, turn_count):
    """Generate follow-up questions for ElevenLabs calls"""
    if not model:
        return "What other laboratory supplies do you have available?"
    
    try:
        items_mentioned = extracted_data.get('items_mentioned', []) if extracted_data else []
        prices_mentioned = extracted_data.get('prices', []) if extracted_data else []
        
        prompt = f"""
        Generate a single, focused follow-up question for a procurement call.
        
        Turn: {turn_count}
        Items mentioned: {items_mentioned}
        Prices received: {len(prices_mentioned)}
        
        Rules:
        1. Ask only ONE specific question
        2. If no items mentioned yet: ask about laboratory supplies
        3. If items mentioned but no prices: ask for pricing
        4. If both items and prices: ask about delivery or minimum order
        5. Keep under 15 words
        6. Use business-appropriate language
        7. Be direct and clear
        
        Generate ONLY the question, nothing else.
        """
        
        response = model.generate_content(prompt)
        follow_up = response.text.strip()
        
        print_live_feedback(f"ElevenLabs follow-up: '{follow_up}'", "AI")
        return follow_up
        
    except Exception as e:
        print_live_feedback(f"Follow-up generation error: {e}", "ERROR")
        return "What other products do you have available?"

def generate_elevenlabs_closing(conversation_id):
    """Generate closing message for ElevenLabs calls"""
    if not model:
        return "Thank you for your time and information. We will contact you soon with our requirements."
    
    try:
        context = conversation_context.get(conversation_id, {})
        transcripts = context.get('transcripts', [])
        company_name = context.get('company_context', {}).get('company_name', 'Bio Mac Lifesciences')
        
        prompt = f"""
        Generate a professional closing message for a procurement call.
        
        Company: {company_name}
        Conversation turns: {len(transcripts)}
        
        The closing should:
        1. Thank the vendor professionally
        2. Mention next steps (email follow-up)
        3. Be warm but business-like
        4. Use appropriate business language
        5. Maximum 25 words
        6. End positively
        
        Generate ONLY the closing message, nothing else.
        """
        
        response = model.generate_content(prompt)
        closing = response.text.strip()
        
        print_live_feedback(f"ElevenLabs closing: '{closing}'", "AI")
        return closing
        
    except Exception as e:
        print_live_feedback(f"Closing generation error: {e}", "ERROR")
        return "Thank you for your time. We will send you our detailed requirements via email."

def generate_elevenlabs_conversation_summary(conversation_id, context):
    """Generate comprehensive conversation summary using Gemini"""
    if not model:
        return "Summary generation not available - Gemini AI not configured"
    
    try:
        # Prepare conversation data for summary
        transcripts = [t['text'] for t in context.get('transcripts', [])]
        agent_responses = [r['text'] for r in context.get('agent_responses', [])]
        extracted_data = context.get('extracted_data', {})
        
        summary_prompt = f"""
        Generate a comprehensive procurement conversation summary for this ElevenLabs conversation:
        
        Conversation ID: {conversation_id}
        Phone Number: {context.get('phone_number', 'Unknown')}
        Duration: {context.get('duration_ms', 0)/1000:.1f} seconds
        End Reason: {context.get('end_reason', 'Unknown')}
        
        Vendor Statements: {transcripts}
        Agent Responses: {agent_responses}
        Extracted Data: {extracted_data}
        
        Create a detailed business summary including:
        1. **Vendor Information** - Contact details, company name if mentioned
        2. **Products Discussed** - List all items mentioned with availability status
        3. **Pricing Information** - All quotes, pricing structures, discounts
        4. **Business Terms** - Delivery times, payment terms, minimum orders
        5. **Vendor Assessment** - Responsiveness, professionalism, potential
        6. **Key Insights** - Important business intelligence gathered
        7. **Follow-up Actions** - Recommended next steps
        8. **Quote Quality Rating** - Rate the completeness of information (1-10)
        
        Format as a professional procurement report suitable for management review.
        Use clear headings and bullet points.
        """
        
        response = model.generate_content(summary_prompt)
        summary = response.text.strip()
        
        print_live_feedback(f"Generated comprehensive summary for {conversation_id[:8]}...", "SUCCESS")
        return summary
        
    except Exception as e:
        print_live_feedback(f"Summary generation error: {e}", "ERROR")
        return f"Summary generation failed: {str(e)}"

@app.route('/webhook/speech', methods=['POST'])
def handle_speech():
    """Handle speech recognition with live feedback - Legacy Twilio handler"""
    global current_call_sid
    
    # Get speech recognition results
    speech_result = request.form.get('SpeechResult', '')
    confidence = request.form.get('Confidence', '0')
    call_sid = request.form.get('CallSid', '')
    
    print_live_feedback("=" * 60, "INFO")
    print_live_feedback(f"LEGACY TWILIO SPEECH RECOGNIZED!", "SPEECH")
    print_live_feedback(f"Text: '{speech_result}'", "SPEECH")
    print_live_feedback(f"Confidence: {confidence}", "SPEECH")
    print_live_feedback(f"Call SID: {call_sid}", "SPEECH")
    print_live_feedback("=" * 60, "INFO")
    
    if speech_result:
        # Generate intelligent response using Gemini
        ai_response = generate_intelligent_response(speech_result)
        
        # Get current conversation context to determine next action
        context = conversation_context.get(call_sid, {})
        stage = context.get('stage', 'initial')
        turn_count = context.get('turn_count', 0)
        
        # Generate dynamic follow-up based on conversation state
        if stage != 'wrapping_up' and turn_count < 4:
            follow_up_question = generate_dynamic_follow_up(context)
            
            # Create TwiML response with dynamic content
            twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">{ai_response}</Say>
    <Pause length="1"/>
    
    <!-- Dynamic follow-up question -->
    <Gather input="speech" 
            language="hi-IN" 
            speechTimeout="6" 
            timeout="10"
            action="/webhook/speech"
            method="POST">
        <Say voice="Polly.Aditi" language="hi-IN">
            {follow_up_question}
        </Say>
    </Gather>
    
    <!-- Fallback if no response -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Koi response nahi mila. Main notes le liya hun. Dhanyawad sir!
    </Say>
    <Hangup/>
</Response>"""
        else:
            # Generate final closing dynamically
            if model:
                try:
                    items_list = context.get('items_discussed', [])
                    closing_prompt = f"""
                    Generate a natural, professional closing for a procurement call. 
                    Items discussed: {items_list}
                    
                    The closing should:
                    1. Thank the vendor
                    2. Confirm you have their information
                    3. Mention next steps (email, follow-up)
                    4. Use professional Hinglish
                    5. Be warm and business-like
                    6. Maximum 2 sentences
                    
                    Generate ONLY the spoken text.
                    """
                    
                    response = model.generate_content(closing_prompt)
                    dynamic_closing = response.text.strip()
                    print_live_feedback(f"Generated closing: '{dynamic_closing}'", "AI")
                except:
                    dynamic_closing = "Theek hai sir, main sab notes le liya hun. Aapko email bhejunga details ke saath. Dhanyawad!"
            else:
                dynamic_closing = "Theek hai sir, main sab notes le liya hun. Aapko email bhejunga details ke saath. Dhanyawad!"
            
            twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">{ai_response}</Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" language="hi-IN">
        {dynamic_closing}
    </Say>
    <Hangup/>
</Response>"""
    else:
        print_live_feedback("No speech detected", "ERROR")
        # Generate dynamic no-speech response
        if model:
            try:
                no_speech_prompt = """
                Generate a polite response when no speech is detected on a business call.
                Should be understanding, professional, and offer to call back.
                Use Hinglish. Maximum 1-2 sentences.
                Generate ONLY the spoken text.
                """
                response = model.generate_content(no_speech_prompt)
                no_speech_response = response.text.strip()
            except:
                no_speech_response = "Koi baat nahi sir, connection issue ho sakta hai. Main phir se call karunga."
        else:
            no_speech_response = "Koi baat nahi sir, connection issue ho sakta hai. Main phir se call karunga."
        
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">
        {no_speech_response}
    </Say>
    <Hangup/>
</Response>"""
    
    return Response(twiml_response, mimetype='text/xml')

@app.route('/webhook/elevenlabs_conversation', methods=['POST'])
def handle_elevenlabs_conversation():
    """Handle ElevenLabs Conversational AI webhook events with enhanced debugging"""
    try:
        # Log raw webhook data for debugging
        raw_data = request.get_data(as_text=True)
        print_live_feedback(f"📥 ElevenLabs webhook received: {len(raw_data)} bytes", "INFO")
        
        # Get the JSON payload from ElevenLabs
        event_data = request.get_json()
        if not event_data:
            print_live_feedback("❌ No JSON data in webhook request", "ERROR")
            return "No JSON data", 400
        
        event_type = event_data.get('event_type')
        conversation_id = event_data.get('conversation_id')
        
        print_live_feedback(f"🎤 ElevenLabs event: {event_type} for conversation {conversation_id}", "INFO")
        
        if event_type == 'conversation_start':
            print_live_feedback(f"✅ ElevenLabs conversation started: {conversation_id}", "SUCCESS")
            # Initialize conversation if not exists
            if conversation_id not in conversation_context:
                conversation_context[conversation_id] = {
                    'phone_number': event_data.get('phone_number', ''),
                    'start_time': datetime.now().isoformat(),
                    'status': 'active',
                    'platform': 'elevenlabs_native',
                    'conversation_id': conversation_id,
                    'transcripts': [],
                    'agent_responses': [],
                    'extracted_data': {}
                }
            
        elif event_type == 'transcript':
            # Handle user speech transcript
            transcript_data = event_data.get('transcript', {})
            user_text = transcript_data.get('text', '')
            confidence = transcript_data.get('confidence', 0)
            
            print_live_feedback(f"🗣️  User said: '{user_text}' (confidence: {confidence})", "SPEECH")
            
            # Store transcript in conversation context
            if conversation_id in conversation_context:
                conversation_context[conversation_id]['transcripts'].append({
                    'text': user_text,
                    'timestamp': datetime.now().isoformat(),
                    'confidence': confidence,
                    'speaker': 'user'
                })
                
                # Extract procurement data using Gemini
                extracted_data = extract_requirements_from_speech(user_text)
                if extracted_data:
                    conversation_context[conversation_id]['extracted_data'] = extracted_data
                    print_live_feedback(f"📊 Extracted data: {len(extracted_data.get('items_mentioned', []))} items", "SUCCESS")
                
                # Save conversation entry
                conversation_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "conversation_id": conversation_id,
                    "vendor_said": user_text,
                    "confidence": confidence,
                    "extracted_data": extracted_data,
                    "type": "elevenlabs_conversation",
                    "phone_number": conversation_context[conversation_id].get('phone_number', ''),
                    "platform": "elevenlabs_ai"
                }
                
                conversation_log.append(conversation_entry)
                save_conversation_to_csv(conversation_entry)
            else:
                print_live_feedback(f"⚠️  Transcript received for unknown conversation: {conversation_id}", "ERROR")
            
        elif event_type == 'response':
            # Handle agent response
            response_data = event_data.get('response', {})
            agent_text = response_data.get('text', '')
            
            print_live_feedback(f"🤖 Agent responded: '{agent_text}'", "AI")
            
            # Store agent response in conversation context
            if conversation_id in conversation_context:
                conversation_context[conversation_id]['agent_responses'].append({
                    'text': agent_text,
                    'timestamp': datetime.now().isoformat(),
                    'speaker': 'agent'
                })
            else:
                print_live_feedback(f"⚠️  Response received for unknown conversation: {conversation_id}", "ERROR")
            
        elif event_type == 'conversation_end':
            # Handle conversation completion
            end_reason = event_data.get('end_reason', 'unknown')
            duration_ms = event_data.get('duration_ms', 0)
            
            print_live_feedback(f"🏁 ElevenLabs conversation ended: {end_reason} ({duration_ms/1000:.1f}s)", "INFO")
            
            # Detailed end reason analysis
            if duration_ms < 1000:
                print_live_feedback("⚠️  Very short call - possible configuration issue!", "ERROR")
            if end_reason == 'timeout':
                print_live_feedback("⏰ Call ended due to timeout", "INFO")
            elif end_reason == 'hangup':
                print_live_feedback("📞 User hung up", "INFO")
            elif end_reason == 'error':
                print_live_feedback("❌ Call ended due to error", "ERROR")
            
            # Generate comprehensive summary
            if conversation_id in conversation_context:
                conversation_context[conversation_id]['status'] = 'completed'
                conversation_context[conversation_id]['end_reason'] = end_reason
                conversation_context[conversation_id]['duration_ms'] = duration_ms
                
                # Generate AI summary using Gemini
                summary = generate_elevenlabs_conversation_summary(conversation_id, conversation_context[conversation_id])
                
                # Save summary
                summary_entry = {
                    "type": "conversation_summary",
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat(),
                    "phone_number": conversation_context[conversation_id].get('phone_number', ''),
                    "duration_ms": duration_ms,
                    "end_reason": end_reason,
                    "platform": "elevenlabs_ai",
                    "summary_report": summary,
                    "conversation_context": serialize_conversation_context(conversation_context[conversation_id])
                }
                conversation_log.append(summary_entry)
            else:
                print_live_feedback(f"⚠️  End event for unknown conversation: {conversation_id}", "ERROR")
        
        else:
            print_live_feedback(f"🔍 Unknown event type: {event_type}", "INFO")
            print_live_feedback(f"📋 Event data: {event_data}", "INFO")
        
        return "OK", 200
        
    except Exception as e:
        print_live_feedback(f"❌ ElevenLabs webhook error: {e}", "ERROR")
        import traceback
        print_live_feedback(f"📋 Webhook traceback: {traceback.format_exc()}", "ERROR")
        return "Error", 500

# Removed old webhook handler - now using direct ElevenLabs Conversational AI webhook

# Removed audio serving route - no longer needed with direct ElevenLabs Conversational AI

@app.route('/webhook/voice', methods=['POST'])
def handle_voice():
    """Initial voice webhook with dynamic greeting - Legacy TTS version"""
    global current_call_sid
    current_call_sid = request.form.get('CallSid', '')
    
    print_live_feedback(f"NEW TTS CALL STARTED - SID: {current_call_sid}", "CALL")
    
    # Initialize conversation context for this call
    conversation_context[current_call_sid] = {
        'stage': 'initial',
        'items_discussed': [],
        'prices_received': [],
        'vendor_responses': [],
        'turn_count': 0,
        'platform': 'twilio_tts'
    }
    
    # Generate dynamic greeting
    dynamic_greeting = generate_dynamic_greeting()
    
    # Generate dynamic initial question
    initial_context = conversation_context[current_call_sid]
    initial_question = generate_dynamic_follow_up(initial_context)
    
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <!-- Dynamic greeting -->
    <Say voice="Polly.Aditi" language="hi-IN">
        {dynamic_greeting}
    </Say>
    
    <Pause length="1"/>
    
    <!-- Dynamic initial question -->
    <Gather input="speech" 
            language="hi-IN" 
            speechTimeout="6" 
            timeout="12"
            action="/webhook/speech"
            method="POST">
        <Say voice="Polly.Aditi" language="hi-IN">
            {initial_question}
        </Say>
    </Gather>
    
    <!-- Fallback if no response -->
    <Say voice="Polly.Aditi" language="hi-IN">
        Connection issue lagta hai. Main phir se call karunga. Namaste!
    </Say>
    <Hangup/>
</Response>"""
    
    return Response(twiml_response, mimetype='text/xml')

@app.route('/webhook/status', methods=['POST'])
def handle_status():
    """Handle call status with live feedback and WhatsApp fallback"""
    call_status = request.form.get('CallStatus', '')
    call_sid = request.form.get('CallSid', '')
    call_to = request.form.get('To', '')
    
    print_live_feedback(f"Call {call_sid}: {call_status}", "CALL")
    
    # Handle failed/unanswered calls with WhatsApp fallback
    if call_status in ['no-answer', 'busy', 'failed', 'canceled']:
        print_live_feedback(f"Call {call_status} - initiating WhatsApp fallback", "INFO")
        
        # Extract phone number and initiate WhatsApp
        if call_to:
            # Remove any formatting to get clean number
            clean_number = call_to.replace('+', '').replace(' ', '').replace('-', '')
            if clean_number.startswith('1'):  # Remove country code if US number
                clean_number = '+' + clean_number
            elif clean_number.startswith('91'):  # Indian number
                clean_number = '+' + clean_number
            else:
                clean_number = '+91' + clean_number  # Assume Indian if no country code
            
            # Track failed call
            failed_calls[call_sid] = {
                'phone_number': clean_number,
                'reason': call_status,
                'timestamp': datetime.now().isoformat()
            }
            
            # Start WhatsApp conversation
            whatsapp_success = initiate_whatsapp_conversation(clean_number, call_status)
            if whatsapp_success:
                print_live_feedback(f"WhatsApp fallback activated for {clean_number}", "SUCCESS")
            else:
                print_live_feedback(f"WhatsApp fallback failed for {clean_number}", "ERROR")
    
    # Generate final summary when call completes successfully
    elif call_status == 'completed' and call_sid in conversation_context:
        print_live_feedback(f"Call completed - generating summary...", "INFO")
        final_summary = generate_final_call_summary(call_sid)
        if final_summary:
            print_live_feedback(f"Final summary generated for {call_sid[:8]}...", "SUCCESS")
    
    return "OK"

@app.route('/webhook/whatsapp', methods=['GET', 'POST'])
def handle_whatsapp():
    """Handle incoming WhatsApp messages and provide endpoint info"""
    
    if request.method == 'GET':
        # Browser access - show endpoint information
        return f"""
        <h1>📱 WhatsApp Webhook Endpoint</h1>
        <p><strong>Status:</strong> ✅ Endpoint is active and ready</p>
        <p><strong>Method:</strong> This endpoint accepts POST requests from Twilio</p>
        <p><strong>URL:</strong> {request.url}</p>
        
        <h2>🔧 Configuration:</h2>
        <ul>
            <li><strong>Twilio WhatsApp From:</strong> {TWILIO_WHATSAPP_FROM}</li>
            <li><strong>Expected Method:</strong> POST</li>
            <li><strong>Content-Type:</strong> application/x-www-form-urlencoded</li>
        </ul>
        
        <h2>📊 Statistics:</h2>
        <ul>
            <li><strong>Active WhatsApp Conversations:</strong> {len(whatsapp_conversations)}</li>
            <li><strong>Total WhatsApp Messages Processed:</strong> {sum(len(conv.get('messages', [])) for conv in whatsapp_conversations.values())}</li>
        </ul>
        
        <h2>🧪 Test This Endpoint:</h2>
        <p>To test this webhook:</p>
        <ol>
            <li>Configure this URL in your Twilio WhatsApp sandbox</li>
            <li>Send a WhatsApp message to your Twilio number</li>
            <li>This endpoint will receive the POST request automatically</li>
        </ol>
        
        <p><a href="/">← Back to Dashboard</a></p>
        
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            h1 {{ color: #25D366; }}
            h2 {{ color: #2c3e50; }}
            ul {{ background-color: white; padding: 15px; border-radius: 5px; }}
            li {{ margin: 5px 0; }}
            p {{ background-color: white; padding: 10px; border-radius: 5px; }}
        </style>
        """
    
    # POST request - handle WhatsApp message
    from_number = request.form.get('From', '').replace('whatsapp:', '')
    message_body = request.form.get('Body', '')
    message_sid = request.form.get('MessageSid', '')
    
    print_live_feedback("WhatsApp message received", "SUCCESS")
    print_live_feedback(f"From: {from_number}", "INFO")
    print_live_feedback(f"Message: '{message_body}'", "INFO")
    
    if message_body and from_number:
        # Initialize WhatsApp-specific tracking if needed
        if from_number not in whatsapp_conversations:
            whatsapp_conversations[from_number] = {
                'started_at': datetime.now().isoformat(),
                'reason': 'incoming_message',
                'messages': [],
                'stage': 'active_conversation',
                'items_discussed': [],
                'prices_received': [],
                'vendor_responsive': True
            }
        
        # Add received message to conversation
        whatsapp_conversations[from_number]['messages'].append({
            'type': 'received',
            'content': message_body,
            'timestamp': datetime.now().isoformat(),
            'message_sid': message_sid
        })
        
        # Mark vendor as responsive
        whatsapp_conversations[from_number]['vendor_responsive'] = True
        
        # Extract data from WhatsApp message
        extracted_data = extract_requirements_from_speech(message_body)
        
        # Update conversation context using the enhanced system
        context = update_conversation_context(from_number, message_body, extracted_data)
        
        # Check if conversation should end
        should_end, end_reason = should_end_conversation(context, message_body)
        
        # Generate intelligent response using enhanced system
        ai_response = generate_whatsapp_response(message_body, context)
        
        # Send response via WhatsApp only if conversation shouldn't end
        if not should_end:
            response_sid = send_whatsapp_message(from_number, ai_response)
            
            if response_sid:
                # Add sent response to conversation
                whatsapp_conversations[from_number]['messages'].append({
                    'type': 'sent',
                    'content': ai_response,
                    'timestamp': datetime.now().isoformat(),
                    'message_sid': response_sid
                })
        else:
            print_live_feedback(f"WhatsApp conversation ended: {end_reason}", "INFO")
        
        # Log the WhatsApp conversation
        whatsapp_entry = {
            "type": "whatsapp_conversation",
            "timestamp": datetime.now().isoformat(),
            "vendor_number": from_number,
            "vendor_message": message_body,
            "ai_response": ai_response,
            "extracted_data": extracted_data,
            "conversation_context": serialize_conversation_context(context),
            "conversation_ended": should_end,
            "end_reason": end_reason if should_end else None
        }
        conversation_log.append(whatsapp_entry)
        
        # Save to CSV
        save_conversation_to_csv(whatsapp_entry)
        
        # Save to file with error handling
        try:
            with open("live_conversation_log.json", "w") as f:
                json.dump(conversation_log, f, indent=2)
        except (TypeError, ValueError) as e:
            print_live_feedback(f"JSON save error: {e}", "ERROR")
            # Save a simplified version without problematic data
            simplified_log = []
            for entry in conversation_log:
                simplified_entry = entry.copy()
                if 'conversation_context' in simplified_entry:
                    simplified_entry['conversation_context'] = serialize_conversation_context(simplified_entry['conversation_context'])
                simplified_log.append(simplified_entry)
            
            with open("live_conversation_log.json", "w") as f:
                json.dump(simplified_log, f, indent=2)
        
        print_live_feedback(f"WhatsApp response sent: '{ai_response}'", "SUCCESS")
    
    return "OK"

@app.route('/health')
def health():
    """Health check endpoint with WhatsApp status"""
    whatsapp_conversations_count = len(whatsapp_conversations)
    failed_calls_count = len(failed_calls)
    
    return {
        "status": "healthy", 
        "gemini": "configured" if model else "not configured",
        "endpoints": ["voice", "speech", "status", "whatsapp"],
        "ngrok_url": ngrok_url,
        "conversation_count": len(conversation_log),
        "whatsapp_conversations": whatsapp_conversations_count,
        "failed_calls_with_fallback": failed_calls_count,
        "timestamp": datetime.now().isoformat()
    }

@app.route('/conversation')
def show_conversation():
    """Show live conversation log"""
    return {"conversation_log": conversation_log}

@app.route('/')
def dashboard():
    """Main dashboard with comprehensive overview"""
    procurement_needs = get_procurement_requirements()
    total_companies = len(companies_db)
    total_vendors = len(vendors_db)
    active_negotiations = len([n for n in negotiations_db.values() if n.status == 'active'])
    
    # Generate summary statistics
    total_calls = len(set(entry.get('call_sid') for entry in conversation_log if entry.get('call_sid')))
    total_conversations = len(conversation_log)
    whatsapp_conversations_count = len(whatsapp_conversations)
    failed_calls_count = len(failed_calls)
    total_items_collected = set()
    total_vendors_with_prices = 0
    
    # Collect WhatsApp statistics
    responsive_whatsapp_vendors = sum(1 for conv in whatsapp_conversations.values() if conv.get('vendor_responsive'))
    
    for entry in conversation_log:
        extracted = entry.get('extracted_data', {})
        if isinstance(extracted, dict) and extracted.get('items_mentioned'):
            total_items_collected.update(extracted['items_mentioned'])
        if isinstance(extracted, dict) and extracted.get('prices'):
            total_vendors_with_prices += 1
    
    # Calculate savings and analytics
    total_savings = sum(neg.current_offer - neg.target_price for neg in negotiations_db.values() if neg.status == 'completed')
    
    dashboard_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Multi-Company Procurement Platform</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
            .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .stat-number {{ font-size: 2em; font-weight: bold; color: #3498db; }}
            .navigation {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .nav-button {{ display: inline-block; background: #3498db; color: white; padding: 10px 20px; margin: 5px; text-decoration: none; border-radius: 5px; }}
            .nav-button:hover {{ background: #2980b9; }}
            .urgent-items {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .company-section {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏭 Multi-Company Procurement Platform</h1>
            <p>AI-Powered Inventory Management, Vendor Negotiations & Price Comparison</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{total_companies}</div>
                <div>Active Companies</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_vendors}</div>
                <div>Registered Vendors</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{active_negotiations}</div>
                <div>Active Negotiations</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">₹{total_savings:,.0f}</div>
                <div>Total Savings</div>
            </div>
        </div>
        
        <div class="navigation">
            <h3>🎛️ Platform Control Center</h3>
            <a href="/companies" class="nav-button">🏢 Companies</a>
            <a href="/vendors" class="nav-button">🤝 Vendors</a>
            <a href="/inventory" class="nav-button">📦 Inventory</a>
            <a href="/procurement" class="nav-button">🛒 Procurement</a>
            <a href="/quotes" class="nav-button">💰 Quotes</a>
            <a href="/negotiations" class="nav-button">🤝 Negotiations</a>
            <a href="/analytics" class="nav-button">📊 Analytics</a>
            <a href="/calls" class="nav-button">📞 Call System</a>
        </div>
        
        <div class="urgent-items">
            <h3>⚠️ Urgent Procurement Requirements</h3>
            <div id="urgent-requirements">
    """
    
    # Add urgent requirements
    urgent_count = 0
    for company_id, procurement_data in procurement_needs.items():
        for need in procurement_data['needs'][:3]:  # Show top 3 urgent items
            if need['urgency'] == 'critical':
                dashboard_html += f"""
                <div style="margin: 10px 0; padding: 10px; background: #f8d7da; border-radius: 5px;">
                    <strong>{procurement_data['company'].name}</strong>: 
                    {need['item'].name} - Stock: {need['item'].current_stock}/{need['item'].minimum_required} 
                    (Shortage: {need['shortage']} {need['item'].unit})
                </div>
                """
                urgent_count += 1
    
    if urgent_count == 0:
        dashboard_html += "<p>✅ No critical inventory shortages</p>"
    
    dashboard_html += """
            </div>
        </div>
        
        <div class="company-section">
            <h3>🏢 Company Status Overview</h3>
    """
    
    # Add company overview
    for company_id, company in companies_db.items():
        total_items = len(company.inventory) if company.inventory else 0
        low_stock_items = 0
        if company.inventory:
            low_stock_items = sum(1 for item in company.inventory.values() if item.current_stock <= item.minimum_required)
        
        dashboard_html += f"""
        <div style="margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
            <h4>{company.name} ({company.industry})</h4>
            <p><strong>Contact:</strong> {company.contact_person} - {company.phone}</p>
            <p><strong>Monthly Budget:</strong> ₹{company.budget_monthly:,.0f}</p>
            <p><strong>Inventory Items:</strong> {total_items} | <strong>Low Stock:</strong> {low_stock_items}</p>
            <p><strong>Priority:</strong> {company.procurement_priority.replace('_', ' ').title()}</p>
        </div>
        """
    
    dashboard_html += f"""
        </div>
        
        <div class="company-section">
            <h3>📞 Call System Status</h3>
            <p><strong>Total Calls:</strong> {total_calls}</p>
            <p><strong>WhatsApp Conversations:</strong> {whatsapp_conversations_count}</p>
            <p><strong>Failed Calls (WhatsApp Triggered):</strong> {failed_calls_count}</p>
            <p><strong>Vendors with Pricing:</strong> {total_vendors_with_prices}</p>
        </div>
        
        <div style="background: white; padding: 20px; border-radius: 8px; margin-top: 20px;">
            <h3>🚀 Quick Actions</h3>
            <a href="/run_procurement" class="nav-button">🔄 Run Auto Procurement</a>
            <a href="/make_calls" class="nav-button">📞 Start Vendor Calls</a>
            <a href="/price_comparison" class="nav-button">💲 Compare Prices</a>
            <a href="/export_data" class="nav-button">📈 Export Analytics</a>
        </div>
        
        <script>
            // Auto-refresh every 30 seconds
            setTimeout(function(){{ location.reload(); }}, 30000);
        </script>
    </body>
    </html>
    """
    
    return dashboard_html

@app.route('/companies')
def companies_page():
    """Companies management page"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Companies - Procurement Platform</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .company-card {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .back-btn {{ background: #34495e; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <a href="/" class="back-btn">← Back to Dashboard</a>
        <div class="header">
            <h1>🏢 Companies Management</h1>
        </div>
    """
    
    for company_id, company in companies_db.items():
        inventory_count = len(company.inventory) if company.inventory else 0
        html += f"""
        <div class="company-card">
            <h3>{company.name}</h3>
            <p><strong>Industry:</strong> {company.industry}</p>
            <p><strong>Contact:</strong> {company.contact_person}</p>
            <p><strong>Phone:</strong> {company.phone}</p>
            <p><strong>Email:</strong> {company.email}</p>
            <p><strong>Monthly Budget:</strong> ₹{company.budget_monthly:,.0f}</p>
            <p><strong>Procurement Priority:</strong> {company.procurement_priority.replace('_', ' ').title()}</p>
            <p><strong>Inventory Items:</strong> {inventory_count}</p>
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    return html

@app.route('/procurement')
def procurement_page():
    """Procurement requirements and analysis page"""
    procurement_needs = get_procurement_requirements()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Procurement Analysis - Platform</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .back-btn { background: #34495e; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-bottom: 20px; }
            .procurement-card { background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .urgent { border-left: 4px solid #e74c3c; }
            .critical { border-left: 4px solid #c0392b; background: #fdf2f2; }
            .item-row { margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 5px; }
        </style>
    </head>
    <body>
        <a href="/" class="back-btn">← Back to Dashboard</a>
        <div class="header">
            <h1>🛒 Procurement Requirements Analysis</h1>
        </div>
    """
    
    if procurement_needs:
        for company_id, procurement_data in procurement_needs.items():
            company = procurement_data['company']
            needs = procurement_data['needs']
            
            html += f"""
            <div class="procurement-card">
                <h3>{company.name} - Procurement Needs</h3>
                <p><strong>Budget Available:</strong> ₹{company.budget_monthly:,.0f}/month</p>
                <p><strong>Priority:</strong> {company.procurement_priority.replace('_', ' ').title()}</p>
                <h4>Required Items:</h4>
            """
            
            for need in needs:
                item = need['item']
                urgency_class = 'critical' if need['urgency'] == 'critical' else 'urgent'
                
                html += f"""
                <div class="item-row {urgency_class}">
                    <strong>{item.name}</strong> ({item.category})
                    <br>Current Stock: {item.current_stock} {item.unit}
                    <br>Minimum Required: {item.minimum_required} {item.unit}
                    <br>Shortage: {need['shortage']} {item.unit}
                    <br>Recommended Order: {need['recommended_order']} {item.unit}
                    <br>Priority: {item.priority.title()} | Urgency: {need['urgency'].title()}
                    <br>Estimated Cost: ₹{item.average_price * need['recommended_order']:,.2f}
                </div>
                """
            
            html += "</div>"
    else:
        html += "<div class='procurement-card'><p>✅ All companies have sufficient inventory!</p></div>"
    
    html += """
    </body>
    </html>
    """
    return html

@app.route('/vendors')
def vendors_page():
    """Vendors management page"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vendors - Procurement Platform</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .vendor-card {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .back-btn {{ background: #34495e; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-bottom: 20px; }}
            .rating {{ color: #f39c12; font-weight: bold; }}
        </style>
    </head>
    <body>
        <a href="/" class="back-btn">← Back to Dashboard</a>
        <div class="header">
            <h1>🤝 Vendors Management</h1>
        </div>
    """
    
    for vendor_id, vendor in vendors_db.items():
        rating_stars = "⭐" * int(vendor.rating)
        html += f"""
        <div class="vendor-card">
            <h3>{vendor.name}</h3>
            <p><strong>Phone:</strong> {vendor.phone}</p>
            <p><strong>Email:</strong> {vendor.email}</p>
            <p><strong>Rating:</strong> <span class="rating">{rating_stars} {vendor.rating}/5</span></p>
            <p><strong>Specialties:</strong> {', '.join(vendor.specialties)}</p>
            <p><strong>Response Time:</strong> {vendor.response_time}</p>
            <p><strong>Price Competitiveness:</strong> {vendor.price_competitiveness.replace('_', ' ').title()}</p>
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    return html

@app.route('/run_procurement')
def run_auto_procurement():
    """Automatically analyze and initiate procurement"""
    procurement_needs = get_procurement_requirements()
    results = []
    
    for company_id, procurement_data in procurement_needs.items():
        company = procurement_data['company']
        
        for need in procurement_data['needs']:
            item = need['item']
            suitable_vendors = find_suitable_vendors(item)
            
            if suitable_vendors:
                # Auto-select best vendor (highest rated)
                best_vendor = suitable_vendors[0]
                
                results.append({
                    'company': company.name,
                    'item': item.name,
                    'shortage': need['shortage'],
                    'recommended_vendor': best_vendor.name,
                    'vendor_phone': best_vendor.phone,
                    'action': 'Call scheduled'
                })
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Auto Procurement Results</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .header {{ background: #27ae60; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .back-btn {{ background: #34495e; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-bottom: 20px; }}
            .result-card {{ background: white; padding: 15px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <a href="/" class="back-btn">← Back to Dashboard</a>
        <div class="header">
            <h1>🔄 Auto Procurement Results</h1>
            <p>Found {len(results)} procurement actions</p>
        </div>
    """
    
    for result in results:
        html += f"""
        <div class="result-card">
            <h4>{result['company']} - {result['item']}</h4>
            <p><strong>Shortage:</strong> {result['shortage']} units</p>
            <p><strong>Recommended Vendor:</strong> {result['recommended_vendor']}</p>
            <p><strong>Contact:</strong> {result['vendor_phone']}</p>
            <p><strong>Status:</strong> {result['action']}</p>
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    return html

@app.route('/calls')
def calls_system_page():
    """Call system control page"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Call System - Procurement Platform</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .back-btn {{ background: #34495e; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-bottom: 20px; }}
            .call-section {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .call-button {{ background: #27ae60; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 5px; }}
        </style>
    </head>
    <body>
        <a href="/" class="back-btn">← Back to Dashboard</a>
        <div class="header">
            <h1>📞 Call System Control</h1>
        </div>
        
        <div class="call-section">
            <h3>🎤 Voice + WhatsApp Integration</h3>
            <p><strong>Status:</strong> ✅ Running with Voice + WhatsApp Integration</p>
            <p><strong>Gemini AI:</strong> {'✅ Ready for Dynamic Content Generation' if model else '❌ Not configured'}</p>
            <p><strong>Ngrok URL:</strong> {ngrok_url or 'Not set'}</p>
            
            <h4>Quick Actions:</h4>
            <a href="/health" class="call-button">🏥 System Health</a>
            <a href="/conversation" class="call-button">💬 Live Conversation Log</a>
            <a href="/whatsapp" class="call-button">📱 WhatsApp Dashboard</a>
            <a href="/test-endpoints" class="call-button">🧪 Test Endpoints</a>
        </div>
    </body>
    </html>
    """

@app.route('/whatsapp')
def whatsapp_dashboard():
    """WhatsApp conversations dashboard"""
    html_content = "<h1>📱 WhatsApp Conversations</h1>"
    
    if whatsapp_conversations:
        for phone_number, conv in whatsapp_conversations.items():
            message_count = len(conv['messages'])
            last_message = conv['messages'][-1] if conv['messages'] else None
            
            html_content += f"""
            <div style="background: white; margin: 20px 0; padding: 20px; border-radius: 8px; border-left: 4px solid #25D366;">
                <h3>📱 {phone_number}</h3>
                <p><strong>Started:</strong> {conv['started_at']}</p>
                <p><strong>Reason:</strong> {conv.get('reason', 'Unknown')}</p>
                <p><strong>Stage:</strong> {conv.get('stage', 'Unknown')}</p>
                <p><strong>Messages:</strong> {message_count}</p>
                <p><strong>Vendor Responsive:</strong> {'✅ Yes' if conv.get('vendor_responsive') else '❌ No'}</p>
                
                <h4>💬 Message History:</h4>
                <div style="max-height: 300px; overflow-y: auto; background: #f8f9fa; padding: 10px; border-radius: 5px;">
            """
            
            for msg in conv['messages'][-5:]:  # Show last 5 messages
                icon = "📤" if msg['type'] == 'sent' else "📥"
                style = "text-align: right; color: #0084FF;" if msg['type'] == 'sent' else "text-align: left; color: #333;"
                html_content += f"""
                    <p style="{style}">
                        {icon} <strong>{msg['type'].title()}:</strong> {msg['content']}<br>
                        <small>{msg['timestamp']}</small>
                    </p>
                """
            
            html_content += "</div></div>"
    else:
        html_content += "<p>No WhatsApp conversations yet.</p>"
    
    # Show failed calls that triggered WhatsApp
    if failed_calls:
        html_content += "<h2>📞 Failed Calls (WhatsApp Triggered)</h2>"
        for call_sid, call_info in failed_calls.items():
            html_content += f"""
            <div style="background: #fff3cd; margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                <p><strong>Call:</strong> {call_sid[:8]}...</p>
                <p><strong>Phone:</strong> {call_info['phone_number']}</p>
                <p><strong>Reason:</strong> {call_info['reason']}</p>
                <p><strong>Time:</strong> {call_info['timestamp']}</p>
            </div>
            """
    
    html_content += f"""
    <p><a href="/">← Back to Dashboard</a></p>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        h1 {{ color: #2c3e50; }}
        h3 {{ color: #25D366; margin-bottom: 10px; }}
    </style>
    """
    
    return html_content

@app.route('/summary')
def call_summary():
    """Generate comprehensive call summaries"""
    summaries = {}
    
    # Group conversations by call_sid
    for entry in conversation_log:
        call_sid = entry.get('call_sid', 'unknown')
        if call_sid not in summaries:
            summaries[call_sid] = {
                'turns': [],
                'items_collected': set(),
                'prices_collected': [],
                'call_context': entry.get('conversation_context', {}),
                'start_time': entry.get('timestamp'),
                'sentiment': 'neutral'
            }
        
        summaries[call_sid]['turns'].append(entry)
        
        # Collect items and prices
        extracted = entry.get('extracted_data', {})
        if isinstance(extracted, dict):
            if extracted.get('items_mentioned'):
                summaries[call_sid]['items_collected'].update(extracted['items_mentioned'])
            if extracted.get('prices'):
                summaries[call_sid]['prices_collected'].extend(extracted['prices'])
            if extracted.get('sentiment'):
                summaries[call_sid]['sentiment'] = extracted['sentiment']
    
    # Generate HTML summary
    html_content = "<h1>📋 Call Summaries</h1>"
    
    for call_sid, summary in summaries.items():
        items_list = list(summary['items_collected'])
        prices_count = len(summary['prices_collected'])
        turns_count = len(summary['turns'])
        
        html_content += f"""
        <div style="background: white; margin: 20px 0; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db;">
            <h3>📞 Call: {call_sid[:8]}...</h3>
            <p><strong>Start Time:</strong> {summary['start_time']}</p>
            <p><strong>Conversation Turns:</strong> {turns_count}</p>
            <p><strong>Items Discussed:</strong> {', '.join(items_list) if items_list else 'None'}</p>
            <p><strong>Prices Received:</strong> {prices_count}</p>
            <p><strong>Vendor Sentiment:</strong> {summary['sentiment']}</p>
            <p><strong>Call Stage:</strong> {summary['call_context'].get('stage', 'Unknown')}</p>
        </div>
        """
    
    if not summaries:
        html_content += "<p>No calls completed yet.</p>"
    
    html_content += f"""
    <p><a href="/">← Back to Dashboard</a></p>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        h1 {{ color: #2c3e50; }}
        h3 {{ color: #34495e; margin-bottom: 10px; }}
    </style>
    """
    
    return html_content

def generate_final_call_summary(call_sid):
    """Generate a comprehensive summary for a completed call using Gemini"""
    if not model or call_sid not in conversation_context:
        return None
    
    try:
        # Get all data for this call
        call_entries = [entry for entry in conversation_log if entry.get('call_sid') == call_sid]
        context = conversation_context[call_sid]
        
        # Prepare summary data
        all_vendor_responses = [entry['vendor_said'] for entry in call_entries]
        all_extracted_data = [entry.get('extracted_data', {}) for entry in call_entries]
        
        summary_prompt = f"""
        Generate a comprehensive business summary for this procurement call:
        
        Call Context: {context}
        Vendor Responses: {all_vendor_responses}
        Extracted Data: {all_extracted_data}
        
        Create a professional summary that includes:
        1. Items mentioned and their availability
        2. Pricing information received
        3. Vendor responsiveness and interest level
        4. Business terms discussed (delivery, payment, discounts)
        5. Next steps and follow-up actions
        6. Overall assessment of vendor potential
        7. Key contact information
        8. Recommendations for procurement team
        
        Format as a business report suitable for management review.
        Use clear headings and bullet points.
        Keep it concise but comprehensive.
        """
        
        response = model.generate_content(summary_prompt)
        summary_report = response.text.strip()
        
        # Save summary to conversation log
        summary_entry = {
            "type": "call_summary",
            "call_sid": call_sid,
            "timestamp": datetime.now().isoformat(),
            "summary_report": summary_report,
            "call_context": serialize_conversation_context(context)
        }
        conversation_log.append(summary_entry)
        
        print_live_feedback(f"Generated final summary for call {call_sid[:8]}...", "SUCCESS")
        return summary_report
        
    except Exception as e:
        print_live_feedback(f"Summary generation error: {e}", "ERROR")
        return None

def start_ngrok():
    """Start ngrok tunnel"""
    global ngrok_url
    
    print_live_feedback("Starting ngrok tunnel...", "INFO")
    
    try:
        # Start ngrok process
        ngrok_process = subprocess.Popen(
            ['ngrok', 'http', '5000', '--log=stdout'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for ngrok to start and get URL
        time.sleep(5)
        
        # Get ngrok URL from API
        try:
            response = requests.get('http://localhost:4040/api/tunnels')
            if response.status_code == 200:
                tunnels = response.json()['tunnels']
                if tunnels:
                    ngrok_url = tunnels[0]['public_url']
                    print_live_feedback(f"Ngrok tunnel active: {ngrok_url}", "SUCCESS")
                    return ngrok_process, ngrok_url
        except:
            pass
        
        print_live_feedback("Could not get ngrok URL automatically", "ERROR")
        print_live_feedback("Please check ngrok manually and provide URL", "INFO")
        return ngrok_process, None
        
    except Exception as e:
        print_live_feedback(f"Failed to start ngrok: {e}", "ERROR")
        return None, None

def validate_twilio_credentials():
    """Validate basic Twilio credentials"""
    print_live_feedback("Validating Twilio credentials...", "INFO")
    
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}.json"
    auth = base64.b64encode(f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()).decode()
    
    headers = {'Authorization': f'Basic {auth}'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            account_data = response.json()
            print_live_feedback("✅ Twilio credentials valid!", "SUCCESS")
            print_live_feedback(f"Account: {account_data.get('friendly_name', 'Unknown')}", "INFO")
            return True
        else:
            print_live_feedback("❌ Twilio credentials invalid!", "ERROR")
            print_live_feedback(f"Error: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_live_feedback(f"❌ Credential validation failed: {e}", "ERROR")
        return False

def show_twilio_setup_instructions():
    """Display instructions for getting correct Twilio credentials"""
    print("\n🔧 TWILIO SETUP INSTRUCTIONS")
    print("=" * 60)
    print("1. 🌐 Go to Twilio Console: https://console.twilio.com")
    print("2. 📋 Copy your credentials from the main dashboard:")
    print("   - Account SID (starts with 'AC')")
    print("   - Auth Token (click 'show' to reveal)")
    print("3. 🔧 Update your credentials in the code:")
    print(f"   Current Account SID: {TWILIO_ACCOUNT_SID}")
    print(f"   Current Auth Token: {TWILIO_AUTH_TOKEN[:8]}..." if TWILIO_AUTH_TOKEN else "   Auth Token: Not set")
    print("4. 📞 Verify your Twilio phone number is active")
    print("5. 💰 Check your Twilio account balance")
    print("\n💡 Make sure you're using the correct Account SID and Auth Token from your Twilio Console!")

def make_speech_call(phone_number, ngrok_url):
    """Make a call with speech recognition and improved error handling"""
    print_live_feedback(f"Making call to {phone_number}", "CALL")
    
    # Validate credentials before making call
    if not validate_twilio_credentials():
        print_live_feedback("❌ Cannot make call - Twilio credentials invalid", "ERROR")
        show_twilio_setup_instructions()
        return False
    
    # Webhook URLs using ngrok
    voice_webhook = f"{ngrok_url}/webhook/voice"
    
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
        'StatusCallback': f"{ngrok_url}/webhook/status",
        'StatusCallbackEvent': ['initiated', 'ringing', 'answered', 'completed'],
        'StatusCallbackMethod': 'POST',
        'Record': 'true',
        'Timeout': '30'
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 201:
            call_data = response.json()
            print_live_feedback(f"✅ Call started! SID: {call_data['sid']}", "SUCCESS")
            return call_data['sid']
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print_live_feedback(f"❌ Call failed: {error_data}", "ERROR")
            
            # Provide specific error guidance
            if response.status_code == 401:
                print_live_feedback("Authentication Error - Invalid Twilio credentials", "ERROR")
                show_twilio_setup_instructions()
            elif response.status_code == 400:
                print_live_feedback("Bad Request - Check phone number format", "ERROR")
                print_live_feedback("Phone numbers should include country code (e.g., +1234567890)", "INFO")
            elif response.status_code == 403:
                print_live_feedback("Forbidden - Check account permissions or balance", "ERROR")
            elif response.status_code == 404:
                print_live_feedback("Not Found - Check Twilio phone number", "ERROR")
            
            return False
            
    except Exception as e:
        print_live_feedback(f"❌ Call error: {e}", "ERROR")
        return False

def start_webhook_server():
    """Start the Flask webhook server"""
    global server_running
    server_running = True
    print_live_feedback("Starting webhook server on port 5000...", "INFO")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def clean_existing_conversation_log():
    """Clean existing conversation log to fix JSON serialization issues"""
    global conversation_log
    
    cleaned_log = []
    for entry in conversation_log:
        cleaned_entry = entry.copy()
        
        # Fix conversation_context if it exists
        if 'conversation_context' in cleaned_entry:
            cleaned_entry['conversation_context'] = serialize_conversation_context(cleaned_entry['conversation_context'])
        
        # Fix call_context if it exists
        if 'call_context' in cleaned_entry:
            cleaned_entry['call_context'] = serialize_conversation_context(cleaned_entry['call_context'])
        
        cleaned_log.append(cleaned_entry)
    
    conversation_log = cleaned_log
    print_live_feedback("Cleaned existing conversation log for JSON compatibility", "INFO")

# Removed audio cleanup function - no longer needed with direct ElevenLabs Conversational AI

def main():
    """Main function to orchestrate everything"""
    # Global declarations for all variables that will be modified in this function
    global ELEVENLABS_API_KEY, GEMINI_API_KEY, model, ngrok_url
    
    print("MULTI-COMPANY PROCUREMENT PLATFORM")
    print("AI-Powered: Inventory Management, Vendor Negotiations & Price Comparison")
    print("=" * 70)
    
    # Initialize sample data first
    print_live_feedback("Initializing sample companies and vendors...", "INFO")
    initialize_sample_data()
    
    # Clean existing conversation log on startup
    clean_existing_conversation_log()
    
    # Step 1: Start ngrok
    print_live_feedback("Step 1: Starting ngrok tunnel", "INFO")
    ngrok_process, ngrok_url_result = start_ngrok()
    
    if not ngrok_url_result:
        manual_url = input("Enter your ngrok URL manually (e.g., https://abc123.ngrok.io): ").strip()
        if manual_url:
            global ngrok_url
            ngrok_url = manual_url
            print_live_feedback(f"Using manual ngrok URL: {ngrok_url}", "INFO")
        else:
            print_live_feedback("No ngrok URL provided. Exiting.", "ERROR")
            return
    else:
        ngrok_url = ngrok_url_result
    
    # Step 2: Start webhook server in background
    print_live_feedback("Step 2: Starting webhook server", "INFO")
    server_thread = threading.Thread(target=start_webhook_server, daemon=True)
    server_thread.start()
    time.sleep(3)  # Wait for server to start
    
    print_live_feedback("Multi-Channel AI System Ready!", "SUCCESS")
    print_live_feedback(f"Dashboard: {ngrok_url}", "INFO")
    print_live_feedback("Voice + WhatsApp integration active", "INFO")
    print_live_feedback("Auto-fallback enabled for failed calls", "INFO")
    
    # Step 3: Validate WhatsApp setup on startup
    print_live_feedback("Step 3: Validating WhatsApp configuration", "INFO")
    whatsapp_valid = validate_twilio_whatsapp_setup()
    if not whatsapp_valid:
        print_live_feedback("WhatsApp setup incomplete - see instructions above", "ERROR")
    
    # Step 4: Interactive loop
    while True:
        print("\n" + "="*70)
        print("MULTI-COMPANY PROCUREMENT PLATFORM WITH ELEVENLABS AI")
        print("Advanced AI Voice Agents + Inventory Management + Vendor Intelligence")
        print("="*70)
        print("1. 🏢 View Companies & Inventory Status")
        print("2. 🛒 Analyze Procurement Requirements")
        print("3. 🤝 View Vendors & Ratings")
        print("4. ☎️ Make Intelligent Call (Choose: TTS or ElevenLabs)")
        print("5. 📱 Send Direct WhatsApp Message")
        print("6. 🔄 Run Auto Procurement Analysis")
        print("7. 💰 View Price Comparisons")
        print("8. 📊 Live Multi-Platform Analytics")
        print("9. 🤖 ElevenLabs Agent Management")
        print("10. 📈 System Status & Features")
        print("11. 🔧 Test & Fix WhatsApp Setup")
        print("12. 📋 Export All Conversation Data")
        print("13. 🌐 Web Dashboard Info")
        print("14. 🔑 Update API Credentials")
        print("15. 🧪 Debug Call Issues (TROUBLESHOOT ENDING CALLS)")
        print("16. Exit")
        
        choice = input("\nChoose option (1-16): ").strip()
        
        if choice == "1":
            # View Companies & Inventory Status
            print("\n🏢 COMPANIES & INVENTORY STATUS")
            print("=" * 50)
            
            for company_id, company in companies_db.items():
                print(f"\n📊 {company.name} ({company.industry})")
                print(f"   Contact: {company.contact_person} - {company.phone}")
                print(f"   Budget: ₹{company.budget_monthly:,.0f}/month")
                print(f"   Priority: {company.procurement_priority.replace('_', ' ').title()}")
                
                if company.inventory:
                    print(f"   Inventory ({len(company.inventory)} items):")
                    for item_name, item in company.inventory.items():
                        status = "🔴 LOW" if item.current_stock <= item.minimum_required else "✅ OK"
                        print(f"     - {item.name}: {item.current_stock}/{item.minimum_required} {item.unit} {status}")
                else:
                    print("   No inventory data")
        
        elif choice == "2":
            # Analyze Procurement Requirements
            print("\n🛒 PROCUREMENT REQUIREMENTS ANALYSIS")
            print("=" * 50)
            
            procurement_needs = get_procurement_requirements()
            
            if procurement_needs:
                total_estimated_cost = 0
                for company_id, procurement_data in procurement_needs.items():
                    company = procurement_data['company']
                    needs = procurement_data['needs']
                    
                    print(f"\n🏢 {company.name}:")
                    company_cost = 0
                    
                    for need in needs:
                        item = need['item']
                        item_cost = item.average_price * need['recommended_order']
                        company_cost += item_cost
                        
                        urgency_icon = "🚨" if need['urgency'] == 'critical' else "⚠️"
                        print(f"   {urgency_icon} {item.name}")
                        print(f"     Current: {item.current_stock} | Required: {item.minimum_required}")
                        print(f"     Shortage: {need['shortage']} {item.unit}")
                        print(f"     Recommended Order: {need['recommended_order']} {item.unit}")
                        print(f"     Estimated Cost: ₹{item_cost:,.2f}")
                    
                    print(f"   💰 Company Total: ₹{company_cost:,.2f}")
                    total_estimated_cost += company_cost
                
                print(f"\n💰 TOTAL ESTIMATED PROCUREMENT COST: ₹{total_estimated_cost:,.2f}")
            else:
                print("✅ All companies have sufficient inventory!")
        
        elif choice == "3":
            # View Vendors & Ratings
            print("\n🤝 VENDORS & RATINGS")
            print("=" * 50)
            
            # Sort vendors by rating
            sorted_vendors = sorted(vendors_db.items(), key=lambda x: x[1].rating, reverse=True)
            
            for vendor_id, vendor in sorted_vendors:
                rating_stars = "⭐" * int(vendor.rating)
                print(f"\n📞 {vendor.name}")
                print(f"   Rating: {rating_stars} {vendor.rating}/5.0")
                print(f"   Phone: {vendor.phone}")
                print(f"   Specialties: {', '.join(vendor.specialties)}")
                print(f"   Response Time: {vendor.response_time}")
                print(f"   Price: {vendor.price_competitiveness.replace('_', ' ').title()}")
        
        elif choice == "4":
            # Unified Intelligent Call Interface
            print("\n☎️ INTELLIGENT CALL SYSTEM")
            print("=" * 50)
            print("Choose your calling method:")
            print("1. 🎤 ElevenLabs Native Outbound Calling")
            print("   • True ElevenLabs Conversational AI agent")
            print("   • Native phone calling infrastructure")
            print("   • Professional voice quality")
            print("   • Advanced turn-taking & context")
            print("   • Requires phone number setup")
            print()
            print("2. 📞 Legacy TTS Call (Twilio + Basic TTS)")
            print("   • Traditional text-to-speech")
            print("   • WhatsApp auto-fallback")
            print("   • Simple conversation flow")
            print("   • Uses existing Twilio setup")
            print()
            print("3. 🔙 Back to Main Menu")
            
            call_choice = input("\nChoose calling method (1-3): ").strip()
            
            if call_choice == "1":
                # ElevenLabs AI Call
                if not ELEVENLABS_API_KEY or ELEVENLABS_API_KEY == "your_elevenlabs_api_key_here":
                    print("❌ ElevenLabs API key not configured!")
                    print("💡 Please update ELEVENLABS_API_KEY in the code.")
                    continue
                    
                phone = input(f"Phone number for ElevenLabs AI call ({DEFAULT_PHONE}): ").strip()
                if not phone:
                    phone = DEFAULT_PHONE
                
                print_live_feedback("="*60, "INFO")
                print_live_feedback("🎤 INITIATING ELEVENLABS NATIVE OUTBOUND CALL", "CALL")
                print_live_feedback("Features: Native ElevenLabs agent, professional voice, advanced context", "INFO")
                print_live_feedback("="*60, "INFO")
                
                # Ask if user wants to use custom prompts or default agent
                print("\n🔧 Call Configuration:")
                print("1. Use Custom Prompts (requires agent override permissions)")
                print("2. Use Default Agent Setup (recommended if call ends immediately)")
                
                config_choice = input("Choose configuration (1-2): ").strip()
                
                if config_choice == "2":
                    conversation_id = start_elevenlabs_conversation_simple(phone)
                else:
                    conversation_id = start_elevenlabs_conversation(phone)
                
                if conversation_id:
                    print_live_feedback("🎤 ElevenLabs AI call initiated!", "SUCCESS")
                    print_live_feedback(f"Conversation ID: {conversation_id}", "INFO")
                    print_live_feedback("📞 Call should be connecting now...", "INFO")
                    print_live_feedback("💡 If call ends immediately, try option 2 (Default Agent Setup)", "INFO")
                else:
                    print_live_feedback("❌ ElevenLabs call failed. Check error messages above.", "ERROR")
                    
            elif call_choice == "2":
                # TTS Call (Legacy Twilio)
                if not validate_twilio_credentials():
                    print("❌ Cannot make calls - Twilio credentials invalid.")
                    print("💡 Please update your Twilio Account SID and Auth Token in the code.")
                    continue
                    
                phone = input(f"Phone number for TTS call ({DEFAULT_PHONE}): ").strip()
                if not phone:
                    phone = DEFAULT_PHONE
                
                print_live_feedback("="*60, "INFO")
                print_live_feedback("📞 Initiating TTS call with WhatsApp fallback", "CALL")
                print_live_feedback("Features: Dynamic dialogue, auto-WhatsApp on failure", "INFO")
                print_live_feedback("="*60, "INFO")
                
                call_sid = make_speech_call(phone, ngrok_url)
                if call_sid:
                    print_live_feedback("📞 TTS call initiated! Monitoring for fallback...", "SUCCESS")
                    print_live_feedback("WhatsApp will auto-trigger if call fails", "INFO")
                    print_live_feedback("Real-time tracking active for both channels", "INFO")
                else:
                    print_live_feedback("Call failed. Check error messages above.", "ERROR")
                    
            elif call_choice == "3":
                continue
            else:
                print("Invalid choice. Please select 1, 2, or 3.")
            
        elif choice == "5":
            # Direct WhatsApp Message
            if not validate_twilio_whatsapp_setup():
                print("❌ WhatsApp not properly configured. Please fix setup first (option 11).")
                continue
                
            phone = input("Enter phone number for WhatsApp: ").strip()
            if phone:
                custom_message = input("Custom message (or press Enter for AI-generated): ").strip()
                
                if custom_message:
                    message = custom_message
                    print_live_feedback(f"Sending custom message to {phone}", "INFO")
                else:
                    message = generate_whatsapp_intro_message()
                    print_live_feedback(f"Generated AI message for {phone}", "AI")
                
                success = initiate_whatsapp_conversation(phone, "manual_message")
                if success:
                    print_live_feedback("WhatsApp message sent successfully!", "SUCCESS")
                else:
                    print_live_feedback("Failed to send WhatsApp message", "ERROR")
                    print("Try option 11 to fix WhatsApp setup")
        
        elif choice == "6":
            # Run Auto Procurement Analysis
            print("\n🔄 AUTO PROCUREMENT ANALYSIS")
            print("=" * 50)
            
            procurement_needs = get_procurement_requirements()
            
            if procurement_needs:
                print("Running automated procurement analysis...")
                actions = []
                
                for company_id, procurement_data in procurement_needs.items():
                    company = procurement_data['company']
                    
                    for need in procurement_data['needs']:
                        item = need['item']
                        suitable_vendors = find_suitable_vendors(item)
                        
                        if suitable_vendors:
                            best_vendor = suitable_vendors[0]
                            actions.append({
                                'company': company.name,
                                'item': item.name,
                                'shortage': need['shortage'],
                                'vendor': best_vendor.name,
                                'vendor_phone': best_vendor.phone,
                                'vendor_rating': best_vendor.rating,
                                'estimated_cost': item.average_price * need['recommended_order']
                            })
                
                if actions:
                    total_cost = sum(action['estimated_cost'] for action in actions)
                    print(f"\n✅ Found {len(actions)} procurement actions:")
                    print(f"💰 Total estimated cost: ₹{total_cost:,.2f}")
                    
                    for action in actions:
                        print(f"\n📦 {action['company']} - {action['item']}")
                        print(f"   Shortage: {action['shortage']} units")
                        print(f"   Recommended: {action['vendor']} (Rating: {action['vendor_rating']}/5)")
                        print(f"   Contact: {action['vendor_phone']}")
                        print(f"   Cost: ₹{action['estimated_cost']:,.2f}")
                else:
                    print("No procurement actions needed.")
            else:
                print("✅ All companies have sufficient inventory!")
        
        elif choice == "7":
            # View Price Comparisons
            print("\n💰 PRICE COMPARISON ANALYSIS")
            print("=" * 50)
            
            # For demonstration, show comparison for key items
            key_items = ["Microscope Slides", "Petri Dishes", "Test Tubes", "Chemical Reagents"]
            
            for item_name in key_items:
                print(f"\n📊 {item_name}:")
                
                # Find vendors that can supply this item
                relevant_vendors = []
                for vendor_id, vendor in vendors_db.items():
                    for company in companies_db.values():
                        if company.inventory:
                            for inventory_item in company.inventory.values():
                                if item_name.lower() in inventory_item.name.lower():
                                    if any(specialty in inventory_item.category for specialty in vendor.specialties):
                                        relevant_vendors.append({
                                            'vendor': vendor,
                                            'estimated_price': inventory_item.average_price,
                                            'item': inventory_item
                                        })
                                    break
                
                if relevant_vendors:
                    sorted_vendors = sorted(relevant_vendors, key=lambda x: x['estimated_price'])
                    
                    for i, vendor_info in enumerate(sorted_vendors):
                        vendor = vendor_info['vendor']
                        price = vendor_info['estimated_price']
                        best_price_indicator = " 🏆 BEST PRICE" if i == 0 else ""
                        
                        print(f"   {vendor.name}: ₹{price:.2f}{best_price_indicator}")
                        print(f"     Rating: {'⭐' * int(vendor.rating)} {vendor.rating}/5")
                        print(f"     Response: {vendor.response_time}")
                else:
                    print("   No vendor pricing data available")
        
        elif choice == "8":
            print("\n📊 LIVE MULTI-PLATFORM ANALYTICS:")
            
            # ElevenLabs conversations
            elevenlabs_conversations = [entry for entry in conversation_log if entry.get('platform') in ['elevenlabs', 'elevenlabs_twilio']]
            # Voice conversations (legacy Twilio)
            voice_conversations = [entry for entry in conversation_log if entry.get('type') not in ['whatsapp_conversation', 'elevenlabs_conversation', 'conversation_summary'] and entry.get('platform') not in ['elevenlabs', 'elevenlabs_twilio']]
            whatsapp_conversations_log = [entry for entry in conversation_log if entry.get('type') == 'whatsapp_conversation']
            conversation_summaries = [entry for entry in conversation_log if entry.get('type') == 'conversation_summary']
            
            print(f"\n🎤 ELEVENLABS AI CONVERSATIONS ({len(elevenlabs_conversations)}):")
            if elevenlabs_conversations:
                for i, entry in enumerate(elevenlabs_conversations[-3:], 1):
                    print(f"\n--- ElevenLabs Conversation {i} ---")
                    print(f"⏰ Time: {entry['timestamp']}")
                    print(f"📞 Phone: {entry.get('phone_number', 'Unknown')}")
                    print(f"🗣️ Vendor: {entry['vendor_said']}")
                    print(f"🤖 Platform: ElevenLabs AI")
                    
                    if entry.get('extracted_data') and entry['extracted_data'].get('items_mentioned'):
                        print(f"📦 Items: {entry['extracted_data']['items_mentioned']}")
            else:
                print("No ElevenLabs conversations yet.")
            
            print(f"\n📞 LEGACY VOICE CONVERSATIONS ({len(voice_conversations)}):")
            if voice_conversations:
                for i, entry in enumerate(voice_conversations[-3:], 1):
                    print(f"\n--- Legacy Voice Conversation {i} ---")
                    print(f"⏰ Time: {entry['timestamp']}")
                    print(f"🗣️ Vendor: {entry['vendor_said']}")
                    print(f"🧠 AI Response: {entry['ai_response']}")
                    
                    if entry.get('extracted_data') and entry['extracted_data'].get('items_mentioned'):
                        print(f"📦 Items: {entry['extracted_data']['items_mentioned']}")
            else:
                print("No legacy voice conversations yet.")
            
            print(f"\n📱 WHATSAPP CONVERSATIONS ({len(whatsapp_conversations_log)}):")
            if whatsapp_conversations_log:
                for i, entry in enumerate(whatsapp_conversations_log[-3:], 1):
                    print(f"\n--- WhatsApp Conversation {i} ---")
                    print(f"⏰ Time: {entry['timestamp']}")
                    print(f"📱 Vendor ({entry['vendor_number']}): {entry['vendor_message']}")
                    print(f"🧠 AI Response: {entry['ai_response']}")
            else:
                print("No WhatsApp conversations yet.")
            
            print(f"\n📋 AI-GENERATED SUMMARIES ({len(conversation_summaries)}):")
            if conversation_summaries:
                for summary in conversation_summaries[-2:]:
                    print(f"\n--- Summary for {summary.get('conversation_id', 'Unknown')[:8]}... ---")
                    print(f"📞 Phone: {summary.get('phone_number', 'Unknown')}")
                    print(f"⏱️ Duration: {summary.get('duration_ms', 0)/1000:.1f}s")
                    print(f"📊 Platform: {summary.get('platform', 'Unknown')}")
                    print(f"📝 Summary available in logs")
            else:
                print("No conversation summaries yet.")
            
            print(f"\n📈 TOTAL ACROSS ALL PLATFORMS:")
            print(f"   🎤 ElevenLabs: {len(elevenlabs_conversations)} | 📞 Legacy Voice: {len(voice_conversations)}")
            print(f"   📱 WhatsApp: {len(whatsapp_conversations_log)} | 📋 Summaries: {len(conversation_summaries)}")
            print(f"   🔄 Failed Call Fallbacks: {len(failed_calls)}")
        
        elif choice == "9":
            # ElevenLabs Agent Management
            print("\n🤖 ELEVENLABS AGENT MANAGEMENT")
            print("=" * 50)
            
            if not ELEVENLABS_API_KEY or ELEVENLABS_API_KEY == "your_elevenlabs_api_key_here":
                print("❌ ElevenLabs API key not configured!")
                print("💡 Please update ELEVENLABS_API_KEY in the code first.")
                continue
            
            print("1. 🆕 Create New Agent")
            print("2. 📋 List Existing Agents") 
            print("3. 📞 Setup Phone Number (Required for Outbound Calls)")
            print("4. 🔍 Verify Account & Batch Calling Status")
            print("5. 🔧 Update Agent Configuration")
            print("6. 📊 View Agent Performance")
            print("7. ⚙️ Test Agent Voice")
            print("8. 🔙 Back to Main Menu")
            
            agent_choice = input("\nChoose agent option (1-8): ").strip()
            
            if agent_choice == "1":
                print("\n🆕 Creating new ElevenLabs agent...")
                agent_id = create_elevenlabs_agent()
                if agent_id:
                    print(f"✅ Agent created successfully! ID: {agent_id}")
                    print("💡 Update ELEVENLABS_AGENT_ID in your code to use this agent")
                else:
                    print("❌ Failed to create agent")
                    
            elif agent_choice == "2":
                print("\n📋 Listing ElevenLabs agents...")
                list_elevenlabs_agents()
                
            elif agent_choice == "3":
                print("\n📞 PHONE NUMBER SETUP FOR OUTBOUND CALLS")
                print("=" * 50)
                
                current_phone_id = ELEVENLABS_PHONE_NUMBER_ID
                print(f"Current Phone Number ID: {current_phone_id if current_phone_id else 'Not configured'}")
                
                phone_id = update_elevenlabs_phone_number_id()
                if phone_id:
                    print("\n✅ Phone number setup complete!")
                    print("💡 You can now use ElevenLabs outbound calling")
                else:
                    print("\n💡 If you don't have any phone numbers:")
                    print("1. Go to https://elevenlabs.io/app/conversational-ai")
                    print("2. Navigate to Phone Numbers section")
                    print("3. Import a phone number (Twilio or SIP)")
                    print("4. Come back and run this setup again")
                
            elif agent_choice == "4":
                verify_elevenlabs_account_status()
                
                # Also offer to check recent batch calls
                check_recent = input("\n🔍 Check recent batch call status? (y/n): ").strip().lower()
                if check_recent == 'y':
                    check_recent_batch_calls()
                
            elif agent_choice == "5":
                print("\n🔧 Agent configuration update coming soon...")
                print("💡 Currently, modify the agent_config in create_elevenlabs_agent() function")
                
            elif agent_choice == "6":
                print("\n📊 AGENT PERFORMANCE ANALYSIS")
                elevenlabs_conversations = [entry for entry in conversation_log if entry.get('platform') in ['elevenlabs', 'elevenlabs_twilio', 'elevenlabs_native']]
                summaries = [entry for entry in conversation_log if entry.get('type') == 'conversation_summary']
                
                print(f"Total ElevenLabs Conversations: {len(elevenlabs_conversations)}")
                print(f"Generated Summaries: {len(summaries)}")
                
                if elevenlabs_conversations:
                    avg_items = sum(len(entry.get('extracted_data', {}).get('items_mentioned', [])) for entry in elevenlabs_conversations) / len(elevenlabs_conversations)
                    print(f"Average Items per Conversation: {avg_items:.1f}")
                    
                    with_pricing = sum(1 for entry in elevenlabs_conversations if entry.get('extracted_data', {}).get('prices'))
                    print(f"Conversations with Pricing: {with_pricing}/{len(elevenlabs_conversations)} ({with_pricing/len(elevenlabs_conversations)*100:.1f}%)")
                
            elif agent_choice == "7":
                print("\n⚙️ Voice testing available through ElevenLabs dashboard")
                print("🌐 Visit: https://elevenlabs.io/app/conversational-ai")
                
            elif agent_choice == "8":
                continue
            else:
                print("Invalid choice.")
        
        elif choice == "10":
            # System Status & Features
            print(f"\n🌐 MULTI-PLATFORM AI SYSTEM STATUS:")
            print(f"   🔗 Ngrok URL: {ngrok_url}")
            print(f"   🖥️ Server: {'✅ Running' if server_running else '❌ Stopped'}")
            print(f"   🧠 Gemini AI: {'✅ Ready (Flash 2.0)' if model else '❌ Not configured'}")
            print(f"   🎤 ElevenLabs API: {'✅ Configured' if ELEVENLABS_API_KEY != 'your_elevenlabs_api_key_here' else '❌ Not configured'}")
            print(f"   📞 ElevenLabs Phone: {'✅ Ready' if ELEVENLABS_PHONE_NUMBER_ID else '❌ Setup Required'}")
            
            elevenlabs_convs = len([entry for entry in conversation_log if entry.get('platform') in ['elevenlabs', 'elevenlabs_twilio', 'elevenlabs_native']])
            legacy_convs = len([entry for entry in conversation_log if entry.get('type') not in ['whatsapp_conversation', 'elevenlabs_conversation', 'conversation_summary'] and entry.get('platform') not in ['elevenlabs', 'elevenlabs_twilio', 'elevenlabs_native']])
            whatsapp_convs = len([entry for entry in conversation_log if entry.get('type') == 'whatsapp_conversation'])
            summaries = len([entry for entry in conversation_log if entry.get('type') == 'conversation_summary'])
            
            print(f"   🎤 ElevenLabs Calls: {elevenlabs_convs}")
            print(f"   📞 Legacy Voice Calls: {legacy_convs}")
            print(f"   📱 WhatsApp Conversations: {whatsapp_convs}")
            print(f"   📋 AI Summaries Generated: {summaries}")
            print(f"   🔄 Failed Call Fallbacks: {len(failed_calls)}")
            
            print(f"\n🚀 ACTIVE FEATURES:")
            print(f"   ✅ ElevenLabs Native Outbound Calling")
            print(f"   ✅ Legacy TTS with Twilio Integration")
            print(f"   ✅ Real-time Speech Processing & Data Extraction")
            print(f"   ✅ Dynamic Procurement Context Generation")
            print(f"   ✅ Intelligent Conversation Summaries")
            print(f"   ✅ Multi-Platform Analytics Dashboard")
            print(f"   ✅ WhatsApp Auto-Fallback System")
            print(f"   ✅ CSV Export with Business Intelligence")
            print(f"   ✅ Cross-Channel Context Tracking")
        
        elif choice == "11":
            # WhatsApp Setup & Testing
            print("\n📱 WHATSAPP SETUP & CONVERSATIONS")
            print("=" * 50)
            
            # WhatsApp Status
            whatsapp_valid = validate_twilio_whatsapp_setup()
            
            print(f"\n📊 WhatsApp Status:")
            if whatsapp_conversations:
                for phone, conv in whatsapp_conversations.items():
                    print(f"\n📱 {phone}:")
                    print(f"   Status: {'✅ Responsive' if conv.get('vendor_responsive') else '❌ No response'}")
                    print(f"   Messages: {len(conv.get('messages', []))}")
                    print(f"   Stage: {conv.get('stage', 'Unknown')}")
                    print(f"   Started: {conv.get('started_at', 'Unknown')}")
                    print(f"   Reason: {conv.get('reason', 'Unknown')}")
            else:
                print("No WhatsApp conversations active.")
            
            print(f"\n🌐 View full dashboard: {ngrok_url}/whatsapp")
            print(f"🔧 WhatsApp webhook endpoint: {ngrok_url}/webhook/whatsapp")
        
        elif choice == "12":
            # Export All Conversation Data
            print("\n📋 COMPREHENSIVE DATA EXPORT")
            print("=" * 50)
            
            # Export to CSV
            csv_file = export_all_conversations_to_csv()
            print(f"✅ CSV Export completed: {csv_file}")
            
            # Generate JSON export
            json_filename = f"conversation_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            export_data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'total_conversations': len(conversation_log),
                    'platforms': ['elevenlabs', 'twilio_voice', 'whatsapp'],
                    'export_type': 'comprehensive'
                },
                'conversations': conversation_log,
                'whatsapp_contexts': whatsapp_conversations,
                'failed_calls': failed_calls,
                'system_info': {
                    'ngrok_url': ngrok_url,
                    'gemini_available': model is not None,
                    'elevenlabs_configured': ELEVENLABS_API_KEY and ELEVENLABS_API_KEY != "your_elevenlabs_api_key_here"
                }
            }
            
            try:
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, default=str)
                print(f"✅ JSON Export completed: {json_filename}")
            except Exception as e:
                print(f"❌ JSON export failed: {e}")
            
            print(f"\n📊 Export Summary:")
            elevenlabs_count = len([entry for entry in conversation_log if entry.get('platform') in ['elevenlabs', 'elevenlabs_twilio']])
            legacy_count = len([entry for entry in conversation_log if entry.get('type') not in ['whatsapp_conversation', 'elevenlabs_conversation', 'conversation_summary'] and entry.get('platform') not in ['elevenlabs', 'elevenlabs_twilio']])
            whatsapp_count = len([entry for entry in conversation_log if entry.get('type') == 'whatsapp_conversation'])
            summary_count = len([entry for entry in conversation_log if entry.get('type') == 'conversation_summary'])
            
            print(f"   🎤 ElevenLabs Conversations: {elevenlabs_count}")
            print(f"   📞 Legacy Voice Conversations: {legacy_count}")
            print(f"   📱 WhatsApp Conversations: {whatsapp_count}")
            print(f"   📋 AI-Generated Summaries: {summary_count}")
            print(f"   📁 Files Created: {csv_file}, {json_filename}")
        
        elif choice == "13":
            # Web Dashboard Info
            print("\n🌐 WEB DASHBOARD INFORMATION")
            print("=" * 50)
            print(f"Access the comprehensive web dashboard at: {ngrok_url}")
            print("\n📊 Available Dashboard Pages:")
            print("  • Main Dashboard - Real-time multi-platform overview")
            print("  • Companies Management - View all companies")
            print("  • Procurement Analysis - Requirements analysis")
            print("  • Vendors Management - Vendor ratings & info")
            print("  • Auto Procurement - Automated analysis")
            print("  • Call System Control - ElevenLabs + Legacy Voice + WhatsApp")
            print("  • ElevenLabs Analytics - Advanced conversation insights")
            print("  • Multi-Platform Conversations - Real-time monitoring")
            print("\n💡 Enhanced Features:")
            print("  • ElevenLabs Conversational AI integration")
            print("  • Real-time speech processing with Gemini")
            print("  • Intelligent conversation summaries")
            print("  • Multi-platform analytics dashboard")
            print("  • Advanced CSV exports with business intelligence")
            print("  • Cross-channel context tracking")
            
            print(f"\n🔗 Key Endpoints:")
            print(f"  • Dashboard: {ngrok_url}/")
            print(f"  • ElevenLabs Webhook: {ngrok_url}/webhook/elevenlabs_conversation")
            print(f"  • WhatsApp Webhook: {ngrok_url}/webhook/whatsapp")
            print(f"  • System Health: {ngrok_url}/health")
            
        elif choice == "14":
            # Update API Credentials
            print("\n🔑 API CREDENTIALS MANAGEMENT")
            print("=" * 50)
            
            print("Current Configuration:")
            print(f"   🧠 Gemini API: {'✅ Configured' if model else '❌ Not configured'}")
            print(f"   🎤 ElevenLabs API: {'✅ Configured' if ELEVENLABS_API_KEY != 'your_elevenlabs_api_key_here' else '❌ Not configured'}")
            print(f"   📞 Twilio: {'✅ Configured' if validate_twilio_credentials() else '❌ Not configured'}")
            
            print("\n🔧 Update Options:")
            print("1. 🎤 Update ElevenLabs API Key")
            print("2. 📞 Update Twilio Credentials")
            print("3. 🧠 Update Gemini API Key")
            print("4. 🔙 Back to Main Menu")
            
            cred_choice = input("\nChoose credential to update (1-4): ").strip()
            
            if cred_choice == "1":
                new_key = input("Enter ElevenLabs API key: ").strip()
                if new_key:
                    ELEVENLABS_API_KEY = new_key
                    print("✅ ElevenLabs API key updated!")
                    print("💡 You can now create agents and make AI calls")
                    
            elif cred_choice == "2":
                interactive_twilio_setup()
                
            elif cred_choice == "3":
                new_gemini_key = input("Enter Gemini API key: ").strip()
                if new_gemini_key:
                    os.environ['GEMINI_API_KEY'] = new_gemini_key
                    GEMINI_API_KEY = new_gemini_key
                    # Reinitialize Gemini
                    genai.configure(api_key=new_gemini_key)
                    try:
                        model = genai.GenerativeModel('models/gemini-2.0-flash')
                        print("✅ Gemini API key updated and model initialized!")
                    except:
                        try:
                            model = genai.GenerativeModel('models/gemini-1.5-flash-8b')
                            print("✅ Gemini API key updated (using Flash 1.5)!")
                        except:
                            print("❌ Failed to initialize Gemini model")
                            
            elif cred_choice == "4":
                continue
            else:
                print("Invalid choice.")
                
        elif choice == "15":
            # Debug Call Issues
            print("\n🧪 CALL DEBUGGING TOOLKIT")
            print("=" * 50)
            print("Both calling methods ending immediately? Let's troubleshoot!")
            print("\n🔧 Available Debugging Tools:")
            print("1. 🌐 Test Webhook Connectivity")
            print("2. 🤖 Debug ElevenLabs Agent Configuration") 
            print("3. 📞 Debug Twilio TTS Call Flow")
            print("4. 🧪 Create Simple Test Agent")
            print("5. 📊 Check Recent Batch Call Status")
            print("6. 🔄 Run All Diagnostics")
            print("7. 🔙 Back to Main Menu")
            
            debug_choice = input("\nChoose debugging tool (1-7): ").strip()
            
            if debug_choice == "1":
                test_webhook_connectivity()
                
            elif debug_choice == "2":
                debug_elevenlabs_agent_config()
                
            elif debug_choice == "3":
                debug_twilio_tts_call_flow()
                
            elif debug_choice == "4":
                test_agent_id = create_simple_test_agent()
                if test_agent_id:
                    print(f"\n💡 To test with this agent:")
                    print(f"1. Update ELEVENLABS_AGENT_ID = '{test_agent_id}'")
                    print(f"2. Try making a call with option 4")
                    
            elif debug_choice == "5":
                check_recent_batch_calls()
                
            elif debug_choice == "6":
                print("\n🔄 RUNNING COMPREHENSIVE DIAGNOSTICS...")
                print("This will check all systems and identify the root cause.")
                
                all_good = True
                
                # Test 1: Webhook connectivity
                print("\n[1/5] Testing webhook connectivity...")
                if not test_webhook_connectivity():
                    all_good = False
                
                # Test 2: Twilio credentials
                print("\n[2/5] Testing Twilio credentials...")
                if not validate_twilio_credentials():
                    all_good = False
                
                # Test 3: ElevenLabs agent
                print("\n[3/5] Testing ElevenLabs agent...")
                if not debug_elevenlabs_agent_config():
                    all_good = False
                
                # Test 4: ElevenLabs account status
                print("\n[4/5] Testing ElevenLabs account...")
                if not verify_elevenlabs_account_status():
                    all_good = False
                
                # Test 5: Recent call status
                print("\n[5/5] Checking recent calls...")
                check_recent_batch_calls()
                
                print("\n" + "="*60)
                if all_good:
                    print("✅ ALL SYSTEMS OPERATIONAL")
                    print("💡 If calls still end immediately, try:")
                    print("   - Create a simple test agent (option 4)")
                    print("   - Use a different phone number")
                    print("   - Check ElevenLabs dashboard for call logs")
                else:
                    print("❌ ISSUES FOUND - Check the errors above")
                    print("💡 Fix the identified issues and try calling again")
                print("="*60)
                
            elif debug_choice == "7":
                continue
            else:
                print("Invalid choice.")
                
        elif choice == "16":
            print_live_feedback("Shutting down Multi-Platform AI Procurement System...", "INFO")
            if 'ngrok_process' in locals():
                ngrok_process.terminate()
            break
        
        else:
            print("Invalid choice. Please try again.")

def generate_whatsapp_intro_message():
    """Generate concise WhatsApp introduction message using Gemini"""
    if not model:
        return "Hi! Bio Mac Lifesciences here. We tried calling but couldn't connect. We need laboratory supplies. Can you share your catalog and pricing? Thanks!"
    
    try:
        prompt = """
        Generate a professional WhatsApp business message for a procurement inquiry. This is sent because a phone call couldn't connect.
        
        Requirements:
        1. Professional but friendly tone
        2. Mention call attempt failed
        3. Introduce Bio Mac Lifesciences briefly
        4. Ask about laboratory supplies
        5. Request catalog/pricing
        6. Keep under 120 characters
        7. Use business-appropriate language
        8. Minimal or no emojis
        
        Generate only the message text.
        """
        
        response = model.generate_content(prompt)
        message = response.text.strip()
        print_live_feedback(f"Generated WhatsApp intro: '{message}'", "AI")
        return message
        
    except Exception as e:
        print_live_feedback(f"WhatsApp message generation error: {e}", "ERROR")
        return "Hi! Bio Mac Lifesciences here. Tried calling but couldn't connect. We need laboratory supplies. Can you share your catalog and pricing? Thanks!"

def validate_twilio_whatsapp_setup():
    """Validate Twilio WhatsApp configuration"""
    print("\n🔧 TWILIO WHATSAPP SETUP VALIDATION")
    print("=" * 50)
    
    # Test basic Twilio authentication first
    if not validate_twilio_credentials():
        print_live_feedback("❌ Basic Twilio authentication failed", "ERROR")
        show_twilio_setup_instructions()
        return False
    
    # Check WhatsApp sandbox status
    print("\n📱 WhatsApp Sandbox Status:")
    print(f"   From Number: {TWILIO_WHATSAPP_FROM}")
    print(f"   Sandbox URL: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
    
    return True

def setup_whatsapp_instructions():
    """Display WhatsApp setup instructions"""
    print("\n📱 WHATSAPP SETUP INSTRUCTIONS")
    print("=" * 60)
    print("1. 🌐 Go to Twilio Console: https://console.twilio.com")
    print("2. 📋 Follow these steps:")
    print("   a) Join the sandbox by sending 'join <sandbox-keyword>' to +1 415 523 8886")
    print("   b) Configure webhook URL in Twilio console:")
    print(f"      Webhook URL: {ngrok_url}/webhook/whatsapp (when ngrok is running)")
    print("   c) Set HTTP method to POST")
    print("3. 🔧 Update your credentials in the code if needed")
    print("4. ✅ Test by sending a message to your verified number")
    print("\n💡 Alternative: Set up Twilio WhatsApp Business API for production")

def send_whatsapp_message(to_number, message):
    """Send WhatsApp message via Twilio API with enhanced error handling"""
    print_live_feedback(f"Sending WhatsApp to {to_number}", "INFO")
    
    # Format phone number for WhatsApp
    if not to_number.startswith('whatsapp:'):
        whatsapp_to = f"whatsapp:{to_number}"
    else:
        whatsapp_to = to_number
    
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    auth = base64.b64encode(f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'From': TWILIO_WHATSAPP_FROM,
        'To': whatsapp_to,
        'Body': message
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 201:
            message_data = response.json()
            print_live_feedback(f"WhatsApp sent! SID: {message_data['sid']}", "SUCCESS")
            return message_data['sid']
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print_live_feedback(f"WhatsApp failed: {error_data}", "ERROR")
            
            # Provide specific error guidance
            if response.status_code == 401:
                print_live_feedback("Authentication Error - Check your Twilio credentials", "ERROR")
                setup_whatsapp_instructions()
            elif response.status_code == 400:
                if "not a valid WhatsApp number" in str(error_data):
                    print_live_feedback("Phone number not verified in WhatsApp sandbox", "ERROR")
                    print_live_feedback("Send 'join <keyword>' to +1 415 523 8886 first", "INFO")
                else:
                    print_live_feedback("Bad request - check phone number format", "ERROR")
            elif response.status_code == 403:
                print_live_feedback("Forbidden - WhatsApp sandbox may not be set up", "ERROR")
                setup_whatsapp_instructions()
            
            return False
            
    except Exception as e:
        print_live_feedback(f"WhatsApp error: {e}", "ERROR")
        return False

def initiate_whatsapp_conversation(phone_number, reason="call_failed"):
    """Start WhatsApp conversation as fallback"""
    print_live_feedback(f"Initiating WhatsApp fallback for {phone_number}", "INFO")
    
    # Generate dynamic intro message
    intro_message = generate_whatsapp_intro_message()
    
    # Send WhatsApp message
    message_sid = send_whatsapp_message(phone_number, intro_message)
    
    if message_sid:
        # Initialize WhatsApp conversation context
        whatsapp_conversations[phone_number] = {
            'started_at': datetime.now().isoformat(),
            'reason': reason,
            'messages': [{'type': 'sent', 'content': intro_message, 'timestamp': datetime.now().isoformat()}],
            'stage': 'initial_outreach',
            'items_discussed': [],
            'prices_received': [],
            'vendor_responsive': False
        }
        
        print_live_feedback(f"WhatsApp conversation started for {phone_number}", "SUCCESS")
        return True
    
    return False

@app.route('/test-endpoints')
def test_endpoints():
    """Test all webhook endpoints"""
    return f"""
    <h1>🧪 Webhook Endpoint Testing</h1>
    <p><strong>Base URL:</strong> {request.host_url}</p>
    
    <h2>📋 Available Endpoints:</h2>
    <div style="background: white; padding: 20px; border-radius: 8px; margin: 10px 0;">
        <h3>🎤 Voice Webhook</h3>
        <p><strong>URL:</strong> <a href="/webhook/voice">{request.host_url}webhook/voice</a></p>
        <p><strong>Method:</strong> POST (from Twilio calls)</p>
        <p><strong>Status:</strong> ✅ Ready for incoming calls</p>
    </div>
    
    <div style="background: white; padding: 20px; border-radius: 8px; margin: 10px 0;">
        <h3>🗣️ Speech Webhook</h3>
        <p><strong>URL:</strong> <a href="/webhook/speech">{request.host_url}webhook/speech</a></p>
        <p><strong>Method:</strong> POST (from Twilio speech recognition)</p>
        <p><strong>Status:</strong> ✅ Ready for speech processing</p>
    </div>
    
    <div style="background: white; padding: 20px; border-radius: 8px; margin: 10px 0;">
        <h3>📱 WhatsApp Webhook</h3>
        <p><strong>URL:</strong> <a href="/webhook/whatsapp">{request.host_url}webhook/whatsapp</a></p>
        <p><strong>Method:</strong> POST (from Twilio WhatsApp)</p>
        <p><strong>Status:</strong> ✅ Ready for WhatsApp messages</p>
        <p><strong>Active Conversations:</strong> {len(whatsapp_conversations)}</p>
    </div>
    
    <div style="background: white; padding: 20px; border-radius: 8px; margin: 10px 0;">
        <h3>📊 Status Webhook</h3>
        <p><strong>URL:</strong> <a href="/webhook/status">{request.host_url}webhook/status</a></p>
        <p><strong>Method:</strong> POST (from Twilio call status)</p>
        <p><strong>Status:</strong> ✅ Ready for call status updates</p>
    </div>
    
    <h2>🔧 Configuration for Twilio:</h2>
    <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 10px 0;">
        <h4>📞 Voice Calls Configuration:</h4>
        <p><strong>Voice URL:</strong> {request.host_url}webhook/voice</p>
        <p><strong>Status Callback URL:</strong> {request.host_url}webhook/status</p>
    </div>
    
    <div style="background: #d1ecf1; padding: 15px; border-radius: 5px; margin: 10px 0;">
        <h4>📱 WhatsApp Configuration:</h4>
        <p><strong>Webhook URL:</strong> {request.host_url}webhook/whatsapp</p>
        <p><strong>Method:</strong> POST</p>
    </div>
    
    <h2>📈 Current Statistics:</h2>
    <ul>
        <li><strong>Total Conversations:</strong> {len(conversation_log)}</li>
        <li><strong>WhatsApp Conversations:</strong> {len(whatsapp_conversations)}</li>
        <li><strong>Failed Calls:</strong> {len(failed_calls)}</li>
    </ul>
    
    <p><a href="/">← Back to Dashboard</a></p>
    
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        h1 {{ color: #2c3e50; }}
        h2, h3 {{ color: #34495e; }}
        div {{ margin: 15px 0; }}
        ul {{ background-color: white; padding: 15px; border-radius: 5px; }}
        li {{ margin: 5px 0; }}
    </style>
    """

def interactive_twilio_setup():
    """Interactive Twilio credential setup"""
    global TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER
    
    print("\n🔧 INTERACTIVE TWILIO SETUP")
    print("=" * 50)
    print("Current credentials:")
    print(f"   Account SID: {TWILIO_ACCOUNT_SID}")
    print(f"   Auth Token: {TWILIO_AUTH_TOKEN[:8]}..." if TWILIO_AUTH_TOKEN else "   Auth Token: Not set")
    print(f"   From Number: {TWILIO_FROM_NUMBER}")
    
    print("\n📋 To get your credentials:")
    print("1. Go to https://console.twilio.com")
    print("2. Copy Account SID and Auth Token from the dashboard")
    print("3. Get your Twilio phone number from Phone Numbers > Manage > Active numbers")
    
    # Get new credentials
    update_choice = input("\n🔄 Update credentials? (y/n): ").strip().lower()
    if update_choice == 'y':
        new_sid = input(f"Enter Account SID ({TWILIO_ACCOUNT_SID}): ").strip()
        if new_sid:
            TWILIO_ACCOUNT_SID = new_sid
        
        new_token = input("Enter Auth Token: ").strip()
        if new_token:
            TWILIO_AUTH_TOKEN = new_token
        
        new_number = input(f"Enter Twilio phone number ({TWILIO_FROM_NUMBER}): ").strip()
        if new_number:
            TWILIO_FROM_NUMBER = new_number
        
        print("\n✅ Credentials updated! Testing...")
        
        # Test the new credentials
        if validate_twilio_credentials():
            print("✅ Success! Your Twilio credentials are working.")
            print("💡 You can now make calls and send WhatsApp messages.")
            return True
        else:
            print("❌ Credentials still invalid. Please check and try again.")
            return False
    
    return False

def extract_quotation_data(extracted_data):
    """Extract and format quotation data from extracted speech data"""
    quotation = {
        'items': [],
        'total_items': 0,
        'pricing_provided': False,
        'delivery_terms': '',
        'payment_terms': '',
        'validity': '',
        'discount_info': '',
        'minimum_order': '',
        'contact_person': '',
        'contact_phone': '',
        'vendor_response_quality': 'basic'
    }
    
    if not extracted_data:
        return quotation
    
    # Extract items with detailed formatting
    items_mentioned = extracted_data.get('items_mentioned', [])
    prices = extracted_data.get('prices', [])
    
    # Format items and prices
    formatted_items = []
    for i, item in enumerate(items_mentioned):
        item_data = {
            'name': item,
            'price': '',
            'unit': '',
            'currency': '',
            'details': ''
        }
        
        # Try to match with price data
        for price in prices:
            if isinstance(price, dict) and price.get('item', '').lower() in item.lower():
                item_data['price'] = str(price.get('price', ''))
                item_data['unit'] = price.get('unit', '')
                item_data['currency'] = price.get('currency', 'INR')
                item_data['details'] = price.get('details', '')
                break
        
        formatted_items.append(item_data)
    
    quotation['items'] = formatted_items
    quotation['total_items'] = len(items_mentioned)
    quotation['pricing_provided'] = len(prices) > 0
    
    # Extract business terms
    delivery_info = extracted_data.get('delivery_info', {})
    if isinstance(delivery_info, dict):
        quotation['delivery_terms'] = f"{delivery_info.get('time', '')} | {delivery_info.get('charges', '')}".strip(' |')
    
    quotation['payment_terms'] = extracted_data.get('payment_terms', '')
    quotation['discount_info'] = extracted_data.get('discounts', '')
    quotation['minimum_order'] = extracted_data.get('minimum_order', '')
    
    # Extract contact information
    contact_info = extracted_data.get('contact_info', {})
    if isinstance(contact_info, dict):
        quotation['contact_person'] = contact_info.get('person', '')
        quotation['contact_phone'] = contact_info.get('phone', '')
    
    # Assess response quality
    quality_score = 0
    if items_mentioned: quality_score += 2
    if prices: quality_score += 3
    if delivery_info: quality_score += 1
    if contact_info: quality_score += 1
    if quotation['discount_info']: quality_score += 1
    
    if quality_score >= 6:
        quotation['vendor_response_quality'] = 'comprehensive'
    elif quality_score >= 4:
        quotation['vendor_response_quality'] = 'good'
    elif quality_score >= 2:
        quotation['vendor_response_quality'] = 'basic'
    else:
        quotation['vendor_response_quality'] = 'incomplete'
    
    return quotation

def save_conversation_to_csv(conversation_data):
    """Save conversation data to CSV file with enhanced quotation formatting for both ElevenLabs and legacy"""
    csv_filename = f"vendor_quotations_{datetime.now().strftime('%Y%m%d')}.csv"
    
    # Extract quotation data
    extracted = conversation_data.get('extracted_data', {})
    quotation = extract_quotation_data(extracted)
    
    # Determine platform and conversation identifiers
    platform = conversation_data.get('platform', 'twilio')
    # Simplify platform names for CSV readability
    if platform == 'elevenlabs_twilio':
        platform = 'elevenlabs'
    conversation_id = conversation_data.get('conversation_id', conversation_data.get('call_sid', ''))
    
    # Prepare enhanced CSV data
    csv_data = {
        'timestamp': conversation_data.get('timestamp', ''),
        'date': datetime.fromisoformat(conversation_data.get('timestamp', datetime.now().isoformat())).strftime('%Y-%m-%d'),
        'time': datetime.fromisoformat(conversation_data.get('timestamp', datetime.now().isoformat())).strftime('%H:%M:%S'),
        'conversation_id': conversation_id[:15] if conversation_id else '',  # Truncate for readability
        'platform': platform,
        'vendor_phone': conversation_data.get('vendor_number', conversation_data.get('phone_number', '')),
        'conversation_type': conversation_data.get('type', 'voice'),
        'vendor_message': conversation_data.get('vendor_said', conversation_data.get('vendor_message', '')),
        'ai_response': conversation_data.get('ai_response', ''),
        'confidence': conversation_data.get('confidence', ''),
        
        # Quotation specific fields
        'total_items_quoted': quotation['total_items'],
        'items_list': ' | '.join([item['name'] for item in quotation['items']]),
        'pricing_details': '',
        'delivery_terms': quotation['delivery_terms'],
        'payment_terms': quotation['payment_terms'],
        'discount_offers': quotation['discount_info'],
        'minimum_order_qty': quotation['minimum_order'],
        'contact_person': quotation['contact_person'],
        'contact_phone': quotation['contact_phone'],
        'quotation_quality': quotation['vendor_response_quality'],
        'pricing_provided': 'Yes' if quotation['pricing_provided'] else 'No',
        'vendor_sentiment': extracted.get('sentiment', ''),
        'extraction_confidence': str(extracted.get('extraction_confidence', ''))
    }
    
    # Format pricing details properly
    pricing_details = []
    for item in quotation['items']:
        if item['price']:
            price_str = f"{item['name']}: {item['price']} {item['currency']}"
            if item['unit']:
                price_str += f" per {item['unit']}"
            if item['details']:
                price_str += f" ({item['details']})"
            pricing_details.append(price_str)
    
    csv_data['pricing_details'] = ' | '.join(pricing_details)
    
    # Write to CSV
    file_exists = os.path.isfile(csv_filename)
    
    with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = list(csv_data.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(csv_data)
    
    print_live_feedback(f"Quotation data saved to {csv_filename}", "INFO")

def export_all_conversations_to_csv():
    """Export all conversations to a comprehensive quotation-focused CSV file"""
    csv_filename = f"vendor_quotations_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    print_live_feedback(f"Exporting all quotations to {csv_filename}", "INFO")
    
    # Prepare comprehensive data
    export_data = []
    
    for entry in conversation_log:
        extracted = entry.get('extracted_data', {})
        quotation = extract_quotation_data(extracted)
        
        # Create summary row
        row_data = {
            'date': datetime.fromisoformat(entry.get('timestamp', datetime.now().isoformat())).strftime('%Y-%m-%d'),
            'time': datetime.fromisoformat(entry.get('timestamp', datetime.now().isoformat())).strftime('%H:%M:%S'),
            'vendor_phone': entry.get('vendor_number', ''),
            'conversation_type': entry.get('type', 'voice'),
            'total_items_quoted': quotation['total_items'],
            'items_list': ' | '.join([item['name'] for item in quotation['items']]),
            'pricing_provided': 'Yes' if quotation['pricing_provided'] else 'No',
            'quotation_quality': quotation['vendor_response_quality'],
            'vendor_message': entry.get('vendor_said', entry.get('vendor_message', '')),
            'ai_response': entry.get('ai_response', ''),
            'delivery_terms': quotation['delivery_terms'],
            'payment_terms': quotation['payment_terms'],
            'discount_offers': quotation['discount_info'],
            'minimum_order_qty': quotation['minimum_order'],
            'contact_person': quotation['contact_person'],
            'contact_phone': quotation['contact_phone'],
            'vendor_sentiment': extracted.get('sentiment', ''),
            'extraction_confidence': str(extracted.get('extraction_confidence', ''))
        }
        
        # Format detailed pricing
        pricing_details = []
        for item in quotation['items']:
            if item['price']:
                price_str = f"{item['name']}: {item['price']} {item['currency']}"
                if item['unit']:
                    price_str += f" per {item['unit']}"
                if item['details']:
                    price_str += f" ({item['details']})"
                pricing_details.append(price_str)
        
        row_data['pricing_details'] = ' | '.join(pricing_details)
        export_data.append(row_data)
    
    # Write comprehensive export
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        if export_data:
            fieldnames = list(export_data[0].keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(export_data)
    
    print_live_feedback(f"Export completed: {csv_filename}", "SUCCESS")
    print_live_feedback(f"Total quotations exported: {len(export_data)}", "INFO")
    
    # Generate summary
    total_with_pricing = sum(1 for row in export_data if row['pricing_provided'] == 'Yes')
    quality_breakdown = {}
    for row in export_data:
        quality = row['quotation_quality']
        quality_breakdown[quality] = quality_breakdown.get(quality, 0) + 1
    
    print(f"\nQUOTATION SUMMARY:")
    print(f"Total vendors contacted: {len(export_data)}")
    print(f"Vendors with pricing: {total_with_pricing}")
    print(f"Quality breakdown: {quality_breakdown}")
    
    return csv_filename

def test_webhook_connectivity():
    """Test webhook connectivity and configuration"""
    print("\n🧪 COMPREHENSIVE WEBHOOK TESTING")
    print("=" * 50)
    
    if not ngrok_url:
        print("❌ Ngrok URL not set!")
        return False
    
    print(f"Testing webhooks for: {ngrok_url}")
    
    # Test basic ngrok connectivity
    try:
        response = requests.get(f"{ngrok_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Ngrok tunnel accessible")
        else:
            print(f"❌ Ngrok health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ngrok connection failed: {e}")
        print("\n💡 NGROK TROUBLESHOOTING:")
        print("1. Check if ngrok is still running")
        print("2. Restart ngrok: ngrok http 5000")
        print("3. Update the ngrok URL in the system")
        return False
    
    # Test webhook endpoints
    webhook_endpoints = [
        "/webhook/voice",
        "/webhook/speech", 
        "/webhook/status",
        "/webhook/whatsapp",
        "/webhook/elevenlabs_conversation"
    ]
    
    print("\n📋 Testing webhook endpoints:")
    for endpoint in webhook_endpoints:
        try:
            # Test GET request (should return method not allowed, but endpoint exists)
            response = requests.get(f"{ngrok_url}{endpoint}", timeout=5)
            if response.status_code in [200, 405]:  # 405 = Method Not Allowed is expected
                print(f"✅ {endpoint} - Reachable")
            else:
                print(f"❌ {endpoint} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
    
    return True

def debug_elevenlabs_agent_config():
    """Debug ElevenLabs agent configuration for call ending issues"""
    print("\n🤖 DEBUGGING ELEVENLABS AGENT CONFIGURATION")
    print("=" * 50)
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Get agent details
    try:
        response = requests.get(f"https://api.elevenlabs.io/v1/convai/agents/{ELEVENLABS_AGENT_ID}", headers=headers)
        if response.status_code == 200:
            agent_data = response.json()
            print("✅ Agent found!")
            print(f"   Name: {agent_data.get('name', 'Unknown')}")
            print(f"   Language: {agent_data.get('language', 'Unknown')}")
            
            # Check conversation configuration
            conv_config = agent_data.get('conversation_configuration', {})
            print(f"   Max Duration: {conv_config.get('max_duration_seconds', 'Not set')}s")
            print(f"   Silence Timeout: {conv_config.get('silence_timeout_ms', 'Not set')}ms")
            
            # Check if agent has a proper first message
            first_message = agent_data.get('first_message', '')
            if first_message:
                print(f"   First Message: '{first_message[:50]}...'")
            else:
                print("   ⚠️  No first message configured!")
                
            return True
        else:
            print(f"❌ Agent not found: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Agent check failed: {e}")
        return False

def create_simple_test_agent():
    """Create a minimal test agent with basic configuration"""
    print("\n🧪 CREATING SIMPLE TEST AGENT")
    print("=" * 50)
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Minimal agent configuration
    simple_agent_config = {
        "name": "Simple Test Agent",
        "description": "Basic test agent for troubleshooting",
        "first_message": "Hello! This is a test call. Can you hear me clearly?",
        "system_prompt": "You are a helpful assistant. Keep responses short and natural. Ask one simple question at a time.",
        "language": "en",
        "conversation_configuration": {
            "max_duration_seconds": 60,
            "silence_timeout_ms": 5000,
            "interruption_sensitivity": 0.5
        }
    }
    
    try:
        response = requests.post(
            "https://api.elevenlabs.io/v1/convai/agents",
            headers=headers,
            json=simple_agent_config
        )
        
        if response.status_code == 201:
            agent_data = response.json()
            agent_id = agent_data.get("agent_id")
            print(f"✅ Simple test agent created: {agent_id}")
            print("💡 Try using this agent ID for testing calls")
            return agent_id
        else:
            print(f"❌ Failed to create test agent: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Test agent creation error: {e}")
        return None

def debug_twilio_tts_call_flow():
    """Debug Twilio TTS call flow step by step"""
    print("\n📞 DEBUGGING TWILIO TTS CALL FLOW")
    print("=" * 50)
    
    # Check Twilio credentials
    print("1. Checking Twilio credentials...")
    if not validate_twilio_credentials():
        print("❌ Twilio credentials invalid - this is why TTS calls fail!")
        return False
    
    # Check ngrok connectivity  
    print("2. Checking webhook connectivity...")
    if not test_webhook_connectivity():
        print("❌ Webhook connectivity issues - this is why TTS calls fail!")
        return False
    
    # Test TwiML generation
    print("3. Testing TwiML generation...")
    try:
        dynamic_greeting = generate_dynamic_greeting()
        print(f"✅ Greeting generated: '{dynamic_greeting[:50]}...'")
        
        test_context = {'stage': 'initial', 'turn_count': 0}
        initial_question = generate_dynamic_follow_up(test_context)
        print(f"✅ Question generated: '{initial_question[:50]}...'")
        
        return True
    except Exception as e:
        print(f"❌ TwiML generation failed: {e}")
        return False

if __name__ == "__main__":
    main() 