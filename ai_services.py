"""
AI Services for Multi-Company Procurement Platform
Handles all Gemini AI interactions with error handling and fallbacks
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

# Try to import Gemini AI with fallback
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai not installed. AI features will use fallbacks.")

from models import Company, InventoryItem, Vendor, AIServiceError

class AIService:
    """AI service manager with fallback mechanisms"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyBCXNuaO9VlL5z1phh4mWGEVnnmRFk9TNg')
        self.model = None
        self.retry_count = 3
        self.retry_delay = 1
        self.fallback_responses = self._load_fallback_responses()
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Gemini AI model with error handling"""
        if not GEMINI_AVAILABLE:
            print("⚠️  google-generativeai not available - using fallback responses")
            self.model = None
            return
            
        try:
            if self.api_key:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('models/gemini-1.5-flash-8b')
                print("✅ Gemini AI initialized successfully")
            else:
                print("⚠️ Warning: GEMINI_API_KEY not set")
                self.model = None
        except Exception as e:
            print(f"❌ Failed to initialize Gemini AI: {e}")
            self.model = None
    
    def _load_fallback_responses(self) -> Dict[str, List[str]]:
        """Load fallback responses for when AI is unavailable"""
        return {
            "greetings": [
                "Namaste! Main {company_name} se bol raha hun. Humein {industry} supplies chahiye.",
                "Hello! This is {company_name}. We need supplies for our {industry} operations.",
                "Good day! {company_name} here. We require procurement for {industry} items."
            ],
            "follow_ups": [
                "What items do you have available and at what price?",
                "Can you share your catalog and pricing?",
                "What are your current stock levels and delivery terms?",
                "Please provide quotation for laboratory supplies."
            ],
            "whatsapp_intro": [
                "Hi! {company_name} here. We tried calling but couldn't connect. We need {industry} supplies. Can you share your catalog and pricing?",
                "Hello from {company_name}. Call didn't go through. Need supplies for {industry}. Please send quotation.",
                "Greetings! {company_name} procurement team. Phone call failed. Seeking {industry} supplies quotes."
            ],
            "closing": [
                "Thank you for the information. Our procurement team will review and contact you.",
                "Appreciate your response. We'll be in touch with our requirements.",
                "Thanks for the details. Our team will review and get back to you."
            ]
        }
    
    def _make_ai_request(self, prompt: str, max_retries: int = None) -> Optional[str]:
        """Make AI request with retry logic and error handling"""
        if not self.model:
            return None
        
        retries = max_retries or self.retry_count
        
        for attempt in range(retries):
            try:
                response = self.model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
                
            except Exception as e:
                print(f"AI request attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    print(f"All AI request attempts failed for prompt")
        
        return None
    
    def generate_company_greeting(self, company: Company) -> str:
        """Generate company-specific greeting with fallback"""
        if not self.model:
            return self._get_fallback_response("greetings", company=company)
        
        prompt = f"""
        Generate a professional greeting for a procurement call from {company.name}, a {company.industry} company.
        
        Requirements:
        1. Professional and friendly tone
        2. Use Hindi-English mix for Indian business context
        3. Introduce company briefly
        4. Mention need for {company.industry} supplies
        5. Keep concise (2 sentences max)
        6. Sound natural for phone conversation
        7. No emojis
        
        Generate only the spoken text.
        """
        
        ai_response = self._make_ai_request(prompt)
        
        if ai_response:
            print(f"✅ Generated AI greeting for {company.name}")
            return ai_response
        else:
            print(f"⚠️ Using fallback greeting for {company.name}")
            return self._get_fallback_response("greetings", company=company)
    
    def generate_follow_up_question(self, conversation_context: Dict[str, Any], company: Company) -> str:
        """Generate contextual follow-up question with fallback"""
        if not self.model:
            return self._get_fallback_response("follow_ups")
        
        stage = conversation_context.get('stage', 'initial')
        turn_count = conversation_context.get('turn_count', 0)
        items_discussed = conversation_context.get('items_discussed', [])
        prices_received = conversation_context.get('prices_received', [])
        
        prompt = f"""
        Generate a focused follow-up question for {company.name} procurement call.
        
        Context:
        - Company: {company.name} ({company.industry})
        - Conversation stage: {stage}
        - Turn: {turn_count}
        - Items discussed: {items_discussed}
        - Prices received: {len(prices_received)}
        - Priority: {company.procurement_priority}
        
        Rules:
        1. Ask only ONE specific question
        2. Focus on most important missing information
        3. If no items mentioned: ask about {company.industry} supplies
        4. If items mentioned but no prices: ask for pricing
        5. If basic info gathered: ask about delivery or minimum order
        6. After 3+ turns: start closing conversation
        7. Use business language (Hindi-English mix)
        8. Keep brief and direct
        9. No emojis
        
        Generate only the question.
        """
        
        ai_response = self._make_ai_request(prompt)
        
        if ai_response:
            return ai_response
        else:
            return self._get_fallback_response("follow_ups")
    
    def generate_whatsapp_message(self, company: Company, context: str = "initial") -> str:
        """Generate WhatsApp message with fallback"""
        if not self.model:
            return self._get_fallback_response("whatsapp_intro", company=company)
        
        prompt = f"""
        Generate a professional WhatsApp message for {company.name} procurement inquiry.
        
        Context: {context}
        Company: {company.name} ({company.industry})
        
        Requirements:
        1. Professional but friendly tone
        2. Mention call attempt if applicable
        3. Introduce {company.name} briefly
        4. Ask about {company.industry} supplies
        5. Request catalog/pricing
        6. Keep under 120 characters
        7. Business-appropriate language
        8. Minimal emojis
        
        Generate only the message text.
        """
        
        ai_response = self._make_ai_request(prompt)
        
        if ai_response:
            return ai_response
        else:
            return self._get_fallback_response("whatsapp_intro", company=company)
    
    def extract_vendor_information(self, vendor_speech: str, company: Company) -> Dict[str, Any]:
        """Extract structured information from vendor speech with fallback"""
        if not self.model:
            return self._extract_basic_fallback(vendor_speech)
        
        prompt = f"""
        Extract procurement information from this vendor response for {company.name}:
        
        Vendor Speech: "{vendor_speech}"
        
        Extract and return JSON with these fields:
        {{
            "items_mentioned": ["item1", "item2"],
            "prices": [
                {{"item": "item_name", "price": 45, "unit": "per piece", "currency": "INR", "details": "details"}}
            ],
            "availability": [
                {{"item": "item_name", "status": "in_stock", "quantity": "available quantity"}}
            ],
            "delivery_info": {{
                "time": "delivery time",
                "charges": "delivery charges",
                "conditions": "conditions"
            }},
            "contact_info": {{
                "person": "contact person",
                "phone": "phone number",
                "company": "company name"
            }},
            "payment_terms": "payment conditions",
            "discounts": "discount information",
            "minimum_order": "minimum order requirements",
            "sentiment": "positive/neutral/negative",
            "quality_info": "quality standards mentioned"
        }}
        
        Instructions:
        1. Extract all relevant business information
        2. Handle Hindi and English content
        3. Normalize prices to consistent format
        4. If no information found, use null/empty
        5. Assess vendor engagement level
        
        Return ONLY valid JSON.
        """
        
        ai_response = self._make_ai_request(prompt)
        
        if ai_response:
            try:
                # Clean up response
                if ai_response.startswith('```json'):
                    ai_response = ai_response.replace('```json', '').replace('```', '')
                elif ai_response.startswith('```'):
                    ai_response = ai_response.replace('```', '')
                
                extracted_data = json.loads(ai_response.strip())
                
                # Add metadata
                extracted_data['extraction_method'] = 'ai'
                extracted_data['extraction_timestamp'] = datetime.now().isoformat()
                extracted_data['company_context'] = company.company_id
                
                return extracted_data
                
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parsing failed: {e}, using fallback extraction")
                return self._extract_basic_fallback(vendor_speech)
        else:
            return self._extract_basic_fallback(vendor_speech)
    
    def generate_intelligent_response(self, vendor_speech: str, conversation_context: Dict, company: Company) -> str:
        """Generate intelligent response to vendor with fallback"""
        if not self.model:
            return self._get_fallback_response("closing")
        
        stage = conversation_context.get('stage', 'initial')
        turn_count = conversation_context.get('turn_count', 0)
        vendor_engagement = conversation_context.get('vendor_engagement', 'positive')
        
        prompt = f"""
        Generate a response for {company.name} procurement conversation.
        
        Vendor said: "{vendor_speech}"
        
        Context:
        - Stage: {stage}
        - Turn: {turn_count}
        - Vendor engagement: {vendor_engagement}
        - Company: {company.name} ({company.industry})
        - Priority: {company.procurement_priority}
        
        Rules:
        1. If vendor provided catalog, don't ask for more items
        2. If sufficient info collected, thank and close
        3. If vendor unengaged, politely close
        4. Ask only ONE specific question if needed
        5. Be efficient and respectful
        6. Maximum 1-2 sentences
        7. Use professional Hinglish
        8. No repetitive questions
        
        Generate only the response text.
        """
        
        ai_response = self._make_ai_request(prompt)
        
        if ai_response:
            return ai_response
        else:
            return self._get_fallback_response("closing")
    
    def generate_negotiation_message(self, current_offer: float, target_price: float, vendor_rating: float) -> str:
        """Generate negotiation message with fallback"""
        if not self.model:
            return f"We appreciate your quote of ₹{current_offer:,.2f}. Could we discuss the pricing for a long-term partnership?"
        
        prompt = f"""
        Generate a professional negotiation message for procurement.
        
        Context:
        - Current offer: ₹{current_offer:,.2f}
        - Our target: ₹{target_price:,.2f}
        - Vendor rating: {vendor_rating}/5.0
        
        Requirements:
        1. Professional and respectful
        2. Don't reveal exact target price
        3. Mention value proposition
        4. Business-focused
        5. Indian business context
        6. Concise
        
        Generate only the message text.
        """
        
        ai_response = self._make_ai_request(prompt)
        
        if ai_response:
            return ai_response
        else:
            return f"We appreciate your quote of ₹{current_offer:,.2f}. Could we discuss the pricing for a long-term partnership?"
    
    def _get_fallback_response(self, response_type: str, company: Company = None) -> str:
        """Get fallback response when AI is unavailable"""
        responses = self.fallback_responses.get(response_type, ["Thank you for your time."])
        
        import random
        response = random.choice(responses)
        
        if company:
            response = response.format(
                company_name=company.name,
                industry=company.industry
            )
        
        return response
    
    def _extract_basic_fallback(self, vendor_speech: str) -> Dict[str, Any]:
        """Basic fallback extraction when AI is unavailable"""
        # Simple keyword-based extraction
        speech_lower = vendor_speech.lower()
        
        # Extract items (basic keywords)
        item_keywords = ['slides', 'petri', 'reagent', 'chemical', 'syringe', 'tube', 'kit']
        items_found = [keyword for keyword in item_keywords if keyword in speech_lower]
        
        # Extract prices (basic regex)
        import re
        price_pattern = r'₹?\s*(\d+(?:,\d+)*(?:\.\d+)?)'
        prices = re.findall(price_pattern, vendor_speech)
        price_data = []
        
        for price in prices:
            try:
                price_val = float(price.replace(',', ''))
                price_data.append({
                    "item": "unknown",
                    "price": price_val,
                    "unit": "unknown",
                    "currency": "INR"
                })
            except ValueError:
                pass
        
        # Basic sentiment analysis
        positive_words = ['yes', 'available', 'good', 'quality', 'best']
        negative_words = ['no', 'not available', 'sorry', 'cannot']
        
        positive_count = sum(1 for word in positive_words if word in speech_lower)
        negative_count = sum(1 for word in negative_words if word in speech_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "items_mentioned": items_found,
            "prices": price_data,
            "availability": [],
            "delivery_info": {},
            "contact_info": {},
            "payment_terms": "",
            "discounts": "",
            "minimum_order": "",
            "sentiment": sentiment,
            "quality_info": "",
            "extraction_method": "fallback",
            "extraction_timestamp": datetime.now().isoformat()
        }
    
    def generate_procurement_summary(self, company: Company, requirements: List[Dict]) -> str:
        """Generate procurement summary with fallback"""
        if not self.model:
            items_count = len(requirements)
            return f"Procurement summary for {company.name}: {items_count} items requiring attention. Please review requirements manually."
        
        prompt = f"""
        Generate a comprehensive procurement summary for {company.name}.
        
        Company: {company.name} ({company.industry})
        Budget: ₹{company.budget_monthly:,.2f}/month
        Priority: {company.procurement_priority}
        
        Requirements: {requirements}
        
        Create a business summary including:
        1. Critical items needing immediate procurement
        2. Estimated costs and budget impact
        3. Recommended vendor priorities
        4. Risk assessment
        5. Next steps
        
        Format as professional report.
        """
        
        ai_response = self._make_ai_request(prompt)
        
        if ai_response:
            return ai_response
        else:
            total_items = len(requirements)
            critical_items = len([r for r in requirements if r.get('urgency') == 'critical'])
            return f"""
            Procurement Summary for {company.name}
            
            Total Items: {total_items}
            Critical Items: {critical_items}
            Company Budget: ₹{company.budget_monthly:,.2f}/month
            Priority: {company.procurement_priority.replace('_', ' ').title()}
            
            Immediate Action Required: {critical_items} critical items
            Recommendation: Initiate vendor outreach for critical items immediately.
            """
    
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return self.model is not None
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get AI service health status"""
        return {
            "status": "healthy" if self.model else "fallback_mode",
            "model_available": self.model is not None,
            "api_key_configured": bool(self.api_key),
            "fallback_responses_loaded": bool(self.fallback_responses),
            "last_checked": datetime.now().isoformat()
        }

# Global AI service instance
ai_service = AIService() 