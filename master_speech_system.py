#!/usr/bin/env python3
"""
Multi-Company Procurement Platform
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

# Initialize Flask app
app = Flask(__name__)

# Configure Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash-8b')
        print("Gemini AI initialized")
    except:
        model = None
        print("Warning: Gemini AI not available")
else:
    model = None
    print("Warning: GEMINI_API_KEY not set")

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

@app.route('/webhook/speech', methods=['POST'])
def handle_speech():
    """Handle speech recognition with live feedback"""
    global current_call_sid
    
    # Get speech recognition results
    speech_result = request.form.get('SpeechResult', '')
    confidence = request.form.get('Confidence', '0')
    call_sid = request.form.get('CallSid', '')
    
    print_live_feedback("=" * 60, "INFO")
    print_live_feedback(f"SPEECH RECOGNIZED!", "SPEECH")
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

@app.route('/webhook/voice', methods=['POST'])
def handle_voice():
    """Initial voice webhook with dynamic greeting"""
    global current_call_sid
    current_call_sid = request.form.get('CallSid', '')
    
    print_live_feedback(f"NEW CALL STARTED - SID: {current_call_sid}", "CALL")
    
    # Initialize conversation context for this call
    conversation_context[current_call_sid] = {
        'stage': 'initial',
        'items_discussed': [],
        'prices_received': [],
        'vendor_responses': [],
        'turn_count': 0
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

def main():
    """Main function to orchestrate everything"""
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
        print("MULTI-COMPANY PROCUREMENT PLATFORM")
        print("Inventory Management, Vendor Negotiations & Price Comparison")
        print("="*70)
        print("1. 🏢 View Companies & Inventory Status")
        print("2. 🛒 Analyze Procurement Requirements")
        print("3. 🤝 View Vendors & Ratings")
        print("4. 📞 Make Smart Call (Auto-WhatsApp on failure)")
        print("5. 📱 Send Direct WhatsApp Message")
        print("6. 🔄 Run Auto Procurement Analysis")
        print("7. 💰 View Price Comparisons")
        print("8. 📊 Live Conversation Analytics")
        print("9. 📈 System Status & Features")
        print("10. 🔧 Test & Fix WhatsApp Setup")
        print("11. 🔑 Update Twilio Credentials")
        print("12. 📋 Export All Data")
        print("13. 🌐 Web Dashboard Info")
        print("14. Exit")
        
        choice = input("\nChoose option (1-14): ").strip()
        
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
            # Validate credentials before allowing call
            if not validate_twilio_credentials():
                print("❌ Cannot make calls - Twilio credentials invalid.")
                print("💡 Please update your Twilio Account SID and Auth Token in the code.")
                continue
                
            phone = input(f"Phone number ({DEFAULT_PHONE}): ").strip()
            if not phone:
                phone = DEFAULT_PHONE
            
            print_live_feedback("="*60, "INFO")
            print_live_feedback("Initiating smart call with WhatsApp fallback", "CALL")
            print_live_feedback("Features: Dynamic dialogue, auto-WhatsApp on failure", "INFO")
            print_live_feedback("="*60, "INFO")
            
            call_sid = make_speech_call(phone, ngrok_url)
            if call_sid:
                print_live_feedback("Smart call initiated! Monitoring for fallback...", "SUCCESS")
                print_live_feedback("WhatsApp will auto-trigger if call fails", "INFO")
                print_live_feedback("Real-time tracking active for both channels", "INFO")
            else:
                print_live_feedback("Call failed. Check error messages above.", "ERROR")
            
        elif choice == "5":
            # Check WhatsApp setup before sending
            if not validate_twilio_whatsapp_setup():
                print("❌ WhatsApp not properly configured. Please fix setup first (option 9).")
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
                    print("Try option 9 to fix WhatsApp setup")
        
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
            print("\n📊 LIVE MULTI-CHANNEL ANALYTICS:")
            
            # Voice conversations
            voice_conversations = [entry for entry in conversation_log if entry.get('type') != 'whatsapp_conversation']
            whatsapp_conversations_log = [entry for entry in conversation_log if entry.get('type') == 'whatsapp_conversation']
            
            print(f"\n🎤 VOICE CONVERSATIONS ({len(voice_conversations)}):")
            if voice_conversations:
                for i, entry in enumerate(voice_conversations[-3:], 1):
                    print(f"\n--- Voice Conversation {i} ---")
                    print(f"⏰ Time: {entry['timestamp']}")
                    print(f"🗣️ Vendor: {entry['vendor_said']}")
                    print(f"🧠 AI Response: {entry['ai_response']}")
                    
                    if entry.get('extracted_data') and entry['extracted_data'].get('items_mentioned'):
                        print(f"📦 Items: {entry['extracted_data']['items_mentioned']}")
            else:
                print("No voice conversations yet.")
            
            print(f"\n📱 WHATSAPP CONVERSATIONS ({len(whatsapp_conversations_log)}):")
            if whatsapp_conversations_log:
                for i, entry in enumerate(whatsapp_conversations_log[-3:], 1):
                    print(f"\n--- WhatsApp Conversation {i} ---")
                    print(f"⏰ Time: {entry['timestamp']}")
                    print(f"📱 Vendor ({entry['vendor_number']}): {entry['vendor_message']}")
                    print(f"🧠 AI Response: {entry['ai_response']}")
            else:
                print("No WhatsApp conversations yet.")
            
            print(f"\n📈 TOTAL ACROSS CHANNELS:")
            print(f"   Voice: {len(voice_conversations)} | WhatsApp: {len(whatsapp_conversations_log)}")
            print(f"   Failed Calls → WhatsApp: {len(failed_calls)}")
        
        elif choice == "9":
            print("\n📋 AI-GENERATED CALL SUMMARIES:")
            call_summaries = [entry for entry in conversation_log if entry.get('type') == 'call_summary']
            if call_summaries:
                for summary in call_summaries[-3:]:
                    print(f"\n--- Summary for Call {summary['call_sid'][:8]}... ---")
                    print(summary['summary_report'])
                    print("-" * 50)
            else:
                print("No completed calls with summaries yet.")
        
        elif choice == "10":
            print("\n📱 WHATSAPP CONVERSATIONS STATUS:")
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
        
        elif choice == "11":
            print(f"\n🌐 MULTI-CHANNEL SYSTEM STATUS:")
            print(f"   🔗 Ngrok URL: {ngrok_url}")
            print(f"   🖥️ Server: {'✅ Running' if server_running else '❌ Stopped'}")
            print(f"   🧠 Gemini AI: {'✅ Ready for Dynamic Generation' if model else '❌ Not configured'}")
            print(f"   📞 Voice Calls: {len(set(entry.get('call_sid') for entry in conversation_log if entry.get('call_sid')))}")
            print(f"   📱 WhatsApp Conversations: {len(whatsapp_conversations)}")
            print(f"   💬 Total Conversation Turns: {len(conversation_log)}")
            print(f"   🔄 Failed Call Fallbacks: {len(failed_calls)}")
            
            print(f"\n🚀 ACTIVE FEATURES:")
            print(f"   ✅ Dynamic Voice Greeting Generation")
            print(f"   ✅ Context-Aware Voice Responses")
            print(f"   ✅ Intelligent Data Extraction")
            print(f"   ✅ 📱 WhatsApp Auto-Fallback")
            print(f"   ✅ 📱 Dynamic WhatsApp Conversations")
            print(f"   ✅ Cross-Channel Context Tracking")
            print(f"   ✅ Automatic Summary Generation")
        
        elif choice == "12":
            print(f"\n🧠 AI CONTEXT TRACKING:")
            print(f"\n📞 VOICE CALL CONTEXTS:")
            if conversation_context:
                for call_sid, context in list(conversation_context.items())[-3:]:
                    print(f"   Call {call_sid[:8]}...: Stage={context['stage']}, Turns={context['turn_count']}")
            else:
                print("   No active voice call contexts.")
            
            print(f"\n📱 WHATSAPP CONTEXTS:")
            if whatsapp_conversations:
                for phone, context in list(whatsapp_conversations.items())[-3:]:
                    print(f"   {phone}: Stage={context['stage']}, Messages={len(context['messages'])}")
            else:
                print("   No active WhatsApp contexts.")
        
        elif choice == "13":
            # Web Dashboard Info
            print("\n🌐 WEB DASHBOARD INFORMATION")
            print("=" * 50)
            print(f"Access the comprehensive web dashboard at: {ngrok_url}")
            print("\n📊 Available Dashboard Pages:")
            print("  • Main Dashboard - Real-time overview")
            print("  • Companies Management - View all companies")
            print("  • Procurement Analysis - Requirements analysis")
            print("  • Vendors Management - Vendor ratings & info")
            print("  • Auto Procurement - Automated analysis")
            print("  • Call System Control - Voice & WhatsApp")
            print("\n💡 Features:")
            print("  • Live inventory tracking")
            print("  • Automated procurement recommendations")
            print("  • Vendor performance analytics")
            print("  • Price comparison tools")
            print("  • Real-time conversation monitoring")
            
        elif choice == "14":
            print_live_feedback("Shutting down multi-company procurement platform...", "INFO")
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
    """Save conversation data to CSV file with enhanced quotation formatting"""
    csv_filename = f"vendor_quotations_{datetime.now().strftime('%Y%m%d')}.csv"
    
    # Extract quotation data
    extracted = conversation_data.get('extracted_data', {})
    quotation = extract_quotation_data(extracted)
    
    # Prepare enhanced CSV data
    csv_data = {
        'timestamp': conversation_data.get('timestamp', ''),
        'date': datetime.fromisoformat(conversation_data.get('timestamp', datetime.now().isoformat())).strftime('%Y-%m-%d'),
        'time': datetime.fromisoformat(conversation_data.get('timestamp', datetime.now().isoformat())).strftime('%H:%M:%S'),
        'call_sid': conversation_data.get('call_sid', '')[:10],  # Truncate for readability
        'vendor_phone': conversation_data.get('vendor_number', ''),
        'conversation_type': conversation_data.get('type', 'voice'),
        'vendor_message': conversation_data.get('vendor_said', conversation_data.get('vendor_message', '')),
        'ai_response': conversation_data.get('ai_response', ''),
        
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

if __name__ == "__main__":
    main() 