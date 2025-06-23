"""
Communication Services for Multi-Company Procurement Platform
Handles Twilio voice calls and WhatsApp with error handling and fallbacks
"""

import os
import base64
import requests
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# Try to import Twilio with fallback
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TwilioClient = None
    TWILIO_AVAILABLE = False
    print("⚠️  twilio not installed. Voice and WhatsApp features will be limited.")

from models import Company, Vendor, CommunicationError

class CommunicationService:
    """Communication service manager for voice and WhatsApp"""
    
    def __init__(self):
        # Twilio credentials with fallback
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID', 'AC820daae89092e30fee3487e80162d2e2')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN', '76d105c3d0bdee08cfc97117a7c05b32')
        self.from_number = os.getenv('TWILIO_FROM_NUMBER', '+14323484517')
        self.whatsapp_from = os.getenv('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
        
        # Communication state
        self.active_calls: Dict[str, Dict] = {}
        self.whatsapp_conversations: Dict[str, Dict] = {}
        self.failed_calls: Dict[str, Dict] = {}
        self.conversation_contexts: Dict[str, Dict] = {}
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Validate credentials on initialization
        if TWILIO_AVAILABLE:
            self.credentials_valid = self._validate_credentials()
        else:
            self.credentials_valid = False
        
        print(f"🔗 Communication Service initialized")
        print(f"📞 Voice calls: {'✅ Ready' if self.credentials_valid else '❌ Not available' if not TWILIO_AVAILABLE else '❌ Invalid credentials'}")
        print(f"📱 WhatsApp: {'✅ Ready' if self.credentials_valid else '❌ Not available' if not TWILIO_AVAILABLE else '❌ Invalid credentials'}")
    
    def _validate_credentials(self) -> bool:
        """Validate Twilio credentials"""
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}.json"
            auth = base64.b64encode(f"{self.account_sid}:{self.auth_token}".encode()).decode()
            headers = {'Authorization': f'Basic {auth}'}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                account_data = response.json()
                print(f"✅ Twilio credentials validated for: {account_data.get('friendly_name', 'Unknown')}")
                return True
            else:
                print(f"❌ Twilio credentials invalid: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to validate Twilio credentials: {e}")
            return False
    
    def make_voice_call(self, phone_number: str, company: Company, webhook_base_url: str) -> Tuple[bool, str]:
        """
        Make a voice call to vendor with error handling
        Returns: (success, call_sid_or_error_message)
        """
        if not TWILIO_AVAILABLE:
            return False, "Twilio not available - install twilio package"
            
        if not self.credentials_valid:
            return False, "Twilio credentials not valid"
        
        try:
            # Prepare webhook URLs
            voice_webhook = f"{webhook_base_url}/webhook/voice"
            status_callback = f"{webhook_base_url}/webhook/status"
            
            # Prepare call data
            call_data = {
                'From': self.from_number,
                'To': phone_number,
                'Url': voice_webhook,
                'Method': 'POST',
                'StatusCallback': status_callback,
                'StatusCallbackEvent': ['initiated', 'ringing', 'answered', 'completed', 'busy', 'no-answer', 'failed'],
                'StatusCallbackMethod': 'POST',
                'Record': 'true',
                'Timeout': '30',
                'FallbackUrl': f"{webhook_base_url}/webhook/fallback",
                'FallbackMethod': 'POST'
            }
            
            # Make API request
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Calls.json"
            auth = base64.b64encode(f"{self.account_sid}:{self.auth_token}".encode()).decode()
            headers = {
                'Authorization': f'Basic {auth}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(url, headers=headers, data=call_data, timeout=30)
            
            if response.status_code == 201:
                call_info = response.json()
                call_sid = call_info['sid']
                
                # Track call
                with self.lock:
                    self.active_calls[call_sid] = {
                        'phone_number': phone_number,
                        'company_id': company.company_id,
                        'company_name': company.name,
                        'started_at': datetime.now().isoformat(),
                        'status': 'initiated'
                    }
                
                print(f"✅ Call initiated to {phone_number} for {company.name}")
                return True, call_sid
                
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                error_msg = self._parse_twilio_error(response.status_code, error_data)
                print(f"❌ Call failed: {error_msg}")
                return False, error_msg
                
        except requests.exceptions.Timeout:
            error_msg = "Call request timed out"
            print(f"⏰ {error_msg}")
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Call error: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def send_whatsapp_message(self, phone_number: str, message: str, company: Company = None) -> Tuple[bool, str]:
        """
        Send WhatsApp message with error handling
        Returns: (success, message_sid_or_error)
        """
        if not TWILIO_AVAILABLE:
            return False, "Twilio not available - install twilio package"
            
        if not self.credentials_valid:
            return False, "Twilio credentials not valid"
        
        try:
            # Format phone number
            whatsapp_to = f"whatsapp:{phone_number}" if not phone_number.startswith('whatsapp:') else phone_number
            
            # Prepare message data
            message_data = {
                'From': self.whatsapp_from,
                'To': whatsapp_to,
                'Body': message
            }
            
            # Make API request
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
            auth = base64.b64encode(f"{self.account_sid}:{self.auth_token}".encode()).decode()
            headers = {
                'Authorization': f'Basic {auth}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(url, headers=headers, data=message_data, timeout=30)
            
            if response.status_code == 201:
                message_info = response.json()
                message_sid = message_info['sid']
                
                # Track WhatsApp conversation
                with self.lock:
                    if phone_number not in self.whatsapp_conversations:
                        self.whatsapp_conversations[phone_number] = {
                            'company_id': company.company_id if company else None,
                            'company_name': company.name if company else 'Unknown',
                            'started_at': datetime.now().isoformat(),
                            'messages': [],
                            'status': 'active'
                        }
                    
                    self.whatsapp_conversations[phone_number]['messages'].append({
                        'type': 'sent',
                        'content': message,
                        'timestamp': datetime.now().isoformat(),
                        'message_sid': message_sid
                    })
                
                print(f"✅ WhatsApp sent to {phone_number}")
                return True, message_sid
                
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                error_msg = self._parse_whatsapp_error(response.status_code, error_data)
                print(f"❌ WhatsApp failed: {error_msg}")
                return False, error_msg
                
        except requests.exceptions.Timeout:
            error_msg = "WhatsApp request timed out"
            print(f"⏰ {error_msg}")
            return False, error_msg
            
        except Exception as e:
            error_msg = f"WhatsApp error: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def handle_call_status_update(self, call_sid: str, status: str, call_to: str = None) -> bool:
        """Handle call status updates with fallback logic"""
        try:
            with self.lock:
                if call_sid in self.active_calls:
                    self.active_calls[call_sid]['status'] = status
                    self.active_calls[call_sid]['last_update'] = datetime.now().isoformat()
                
                # Handle failed calls with WhatsApp fallback
                if status in ['no-answer', 'busy', 'failed', 'canceled']:
                    print(f"📞 Call {status} - initiating WhatsApp fallback")
                    
                    # Get call info
                    call_info = self.active_calls.get(call_sid, {})
                    phone_number = call_info.get('phone_number') or call_to
                    company_id = call_info.get('company_id')
                    
                    if phone_number:
                        # Track failed call
                        self.failed_calls[call_sid] = {
                            'phone_number': phone_number,
                            'company_id': company_id,
                            'reason': status,
                            'timestamp': datetime.now().isoformat(),
                            'whatsapp_fallback_attempted': False
                        }
                        
                        return True
                
                elif status == 'completed':
                    print(f"✅ Call {call_sid} completed successfully")
                    
                return True
                
        except Exception as e:
            print(f"❌ Error handling call status: {e}")
            return False
    
    def initiate_whatsapp_fallback(self, failed_call_sid: str, company: Company) -> bool:
        """Initiate WhatsApp fallback for failed call"""
        try:
            with self.lock:
                if failed_call_sid not in self.failed_calls:
                    return False
                
                failed_call = self.failed_calls[failed_call_sid]
                
                if failed_call['whatsapp_fallback_attempted']:
                    print(f"⚠️ WhatsApp fallback already attempted for {failed_call_sid}")
                    return False
                
                phone_number = failed_call['phone_number']
                
                # Generate fallback message
                from ai_services import ai_service
                message = ai_service.generate_whatsapp_message(company, context="call_failed")
                
                # Send WhatsApp message
                success, result = self.send_whatsapp_message(phone_number, message, company)
                
                # Update failed call record
                failed_call['whatsapp_fallback_attempted'] = True
                failed_call['whatsapp_success'] = success
                failed_call['whatsapp_result'] = result
                failed_call['fallback_timestamp'] = datetime.now().isoformat()
                
                if success:
                    print(f"✅ WhatsApp fallback successful for {phone_number}")
                else:
                    print(f"❌ WhatsApp fallback failed for {phone_number}: {result}")
                
                return success
                
        except Exception as e:
            print(f"❌ Error in WhatsApp fallback: {e}")
            return False
    
    def handle_whatsapp_incoming(self, from_number: str, message_body: str) -> Dict[str, Any]:
        """Handle incoming WhatsApp message"""
        try:
            clean_number = from_number.replace('whatsapp:', '')
            
            with self.lock:
                # Initialize conversation if new
                if clean_number not in self.whatsapp_conversations:
                    self.whatsapp_conversations[clean_number] = {
                        'company_id': None,
                        'company_name': 'Unknown',
                        'started_at': datetime.now().isoformat(),
                        'messages': [],
                        'status': 'active'
                    }
                
                # Add received message
                conversation = self.whatsapp_conversations[clean_number]
                conversation['messages'].append({
                    'type': 'received',
                    'content': message_body,
                    'timestamp': datetime.now().isoformat()
                })
                
                conversation['last_activity'] = datetime.now().isoformat()
                conversation['vendor_responsive'] = True
            
            print(f"📱 WhatsApp received from {clean_number}: {message_body[:50]}...")
            
            return {
                'success': True,
                'phone_number': clean_number,
                'message': message_body,
                'conversation_exists': True
            }
            
        except Exception as e:
            print(f"❌ Error handling WhatsApp message: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_twilio_error(self, status_code: int, error_data: Any) -> str:
        """Parse Twilio error response"""
        if status_code == 401:
            return "Authentication failed - Check Twilio credentials"
        elif status_code == 400:
            return "Bad request - Check phone number format"
        elif status_code == 403:
            return "Forbidden - Check account permissions or balance"
        elif status_code == 404:
            return "Not found - Check Twilio phone number"
        elif status_code == 429:
            return "Rate limited - Too many requests"
        else:
            if isinstance(error_data, dict) and 'message' in error_data:
                return error_data['message']
            return f"Twilio error {status_code}: {error_data}"
    
    def _parse_whatsapp_error(self, status_code: int, error_data: Any) -> str:
        """Parse WhatsApp error response"""
        if status_code == 400:
            if isinstance(error_data, dict):
                message = error_data.get('message', '')
                if 'not a valid WhatsApp number' in message:
                    return "Phone number not verified in WhatsApp sandbox"
                elif 'sandbox' in message.lower():
                    return "WhatsApp sandbox not configured properly"
            return "Bad request - Check phone number or message format"
        elif status_code == 403:
            return "WhatsApp sandbox not set up or phone not verified"
        else:
            return self._parse_twilio_error(status_code, error_data)
    
    def get_active_calls(self) -> Dict[str, Dict]:
        """Get all active calls"""
        with self.lock:
            return self.active_calls.copy()
    
    def get_whatsapp_conversations(self) -> Dict[str, Dict]:
        """Get all WhatsApp conversations"""
        with self.lock:
            return self.whatsapp_conversations.copy()
    
    def get_failed_calls(self) -> Dict[str, Dict]:
        """Get all failed calls"""
        with self.lock:
            return self.failed_calls.copy()
    
    def get_conversation_context(self, identifier: str) -> Optional[Dict]:
        """Get conversation context by call_sid or phone_number"""
        with self.lock:
            return self.conversation_contexts.get(identifier)
    
    def update_conversation_context(self, identifier: str, context: Dict):
        """Update conversation context"""
        with self.lock:
            self.conversation_contexts[identifier] = context
    
    def cleanup_old_conversations(self, max_age_hours: int = 24):
        """Cleanup old conversations and calls"""
        try:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            with self.lock:
                # Cleanup old calls
                old_calls = []
                for call_sid, call_info in self.active_calls.items():
                    call_time = datetime.fromisoformat(call_info['started_at'])
                    if call_time < cutoff_time:
                        old_calls.append(call_sid)
                
                for call_sid in old_calls:
                    del self.active_calls[call_sid]
                
                # Cleanup old WhatsApp conversations (mark as inactive)
                for phone, conversation in self.whatsapp_conversations.items():
                    if 'last_activity' in conversation:
                        last_activity = datetime.fromisoformat(conversation['last_activity'])
                        if last_activity < cutoff_time:
                            conversation['status'] = 'inactive'
                
                if old_calls:
                    print(f"🧹 Cleaned up {len(old_calls)} old conversations")
                
        except Exception as e:
            print(f"❌ Error cleaning up conversations: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get communication statistics"""
        with self.lock:
            active_calls_count = len([c for c in self.active_calls.values() if c['status'] in ['initiated', 'ringing', 'in-progress']])
            completed_calls = len([c for c in self.active_calls.values() if c['status'] == 'completed'])
            failed_calls_count = len(self.failed_calls)
            whatsapp_conversations_count = len(self.whatsapp_conversations)
            responsive_vendors = len([c for c in self.whatsapp_conversations.values() if c.get('vendor_responsive', False)])
            
            return {
                'credentials_valid': self.credentials_valid,
                'active_calls': active_calls_count,
                'completed_calls': completed_calls,
                'failed_calls': failed_calls_count,
                'whatsapp_conversations': whatsapp_conversations_count,
                'responsive_whatsapp_vendors': responsive_vendors,
                'total_calls_attempted': len(self.active_calls),
                'whatsapp_fallback_rate': (failed_calls_count / max(len(self.active_calls), 1)) * 100,
                'last_updated': datetime.now().isoformat()
            }
    
    def test_connectivity(self) -> Dict[str, Any]:
        """Test Twilio connectivity"""
        results = {
            'account_validation': False,
            'voice_capability': False,
            'whatsapp_capability': False,
            'errors': []
        }
        
        try:
            # Test account
            if self._validate_credentials():
                results['account_validation'] = True
                results['voice_capability'] = True
                results['whatsapp_capability'] = True
            else:
                results['errors'].append("Invalid Twilio credentials")
                
        except Exception as e:
            results['errors'].append(f"Connectivity test failed: {e}")
        
        return results
    
    def get_setup_instructions(self) -> Dict[str, List[str]]:
        """Get setup instructions for Twilio"""
        return {
            'twilio_setup': [
                "1. Go to https://console.twilio.com",
                "2. Copy Account SID and Auth Token from dashboard",
                "3. Get Twilio phone number from Phone Numbers > Manage > Active numbers",
                "4. Update environment variables or credentials in code"
            ],
            'whatsapp_setup': [
                "1. Go to Twilio Console WhatsApp sandbox",
                "2. Send 'join <keyword>' to +1 415 523 8886",
                "3. Configure webhook URL in Twilio console",
                "4. Set HTTP method to POST",
                "5. Test with verified phone number"
            ],
            'webhook_configuration': [
                "Voice URL: {base_url}/webhook/voice",
                "Status Callback: {base_url}/webhook/status", 
                "WhatsApp URL: {base_url}/webhook/whatsapp",
                "Method: POST for all webhooks"
            ]
        }

# Global communication service instance
comm_service = CommunicationService() 