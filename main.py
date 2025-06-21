import os
import csv
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
import asyncio
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from flask import Flask, request, jsonify
import threading
import time
import pandas as pd
from config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL), 
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

class ProcurementAutomationSystem:
    def __init__(self):
        # Twilio Configuration from config
        self.account_sid = config.TWILIO_ACCOUNT_SID
        self.auth_token = config.TWILIO_AUTH_TOKEN
        self.phone_number = config.TWILIO_PHONE_NUMBER
        self.api_key_sid = config.TWILIO_API_KEY_SID
        
        # Initialize Twilio client
        self.twilio_client = Client(self.account_sid, self.auth_token)
        
        # Test vendor details from config
        self.test_vendor = config.TEST_VENDOR
        
        # Client details from config
        self.client_name = config.CLIENT_NAME
        
        # File paths from config
        self.inventory_file = config.INVENTORY_FILE
        self.requirements_file = config.REQUIREMENTS_FILE
        self.quotes_file = config.QUOTES_FILE
        self.final_orders_file = config.FINAL_ORDERS_FILE
        
        # Webhook server
        self.app = Flask(__name__)
        self.setup_webhook_routes()
        
        # Current conversation state
        self.conversation_state = {}
        
    def setup_webhook_routes(self):
        """Setup Flask routes for webhook handling"""
        
        @self.app.route('/webhook/voice', methods=['POST'])
        def handle_voice_webhook():
            """Handle incoming voice webhook from ConversationRelay"""
            data = request.get_json()
            logger.info(f"Voice webhook received: {data}")
            
            # Process the conversation data
            self.process_conversation_update(data)
            
            return jsonify({"status": "success"})
        
        @self.app.route('/webhook/quote', methods=['POST'])
        def handle_quote_webhook():
            """Handle quote updates during conversation"""
            data = request.get_json()
            logger.info(f"Quote webhook received: {data}")
            
            # Log quote to CSV
            self.log_quote_to_csv(data)
            
            return jsonify({"status": "quote_logged"})
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})
    
    def read_inventory(self) -> List[Dict]:
        """Read inventory.csv and identify low/out-of-stock items"""
        try:
            df = pd.read_csv(self.inventory_file)
            low_stock_items = []
            
            for _, row in df.iterrows():
                if row['current_stock'] <= row['minimum_threshold']:
                    low_stock_items.append({
                        'item_name': row['item_name'],
                        'current_stock': row['current_stock'],
                        'minimum_threshold': row['minimum_threshold'],
                        'required_quantity': row['minimum_threshold'] - row['current_stock'] + row.get('buffer_stock', 10),
                        'category': row.get('category', 'General'),
                        'specifications': row.get('specifications', '')
                    })
            
            logger.info(f"Found {len(low_stock_items)} items requiring procurement")
            return low_stock_items
            
        except FileNotFoundError:
            logger.error(f"Inventory file {self.inventory_file} not found")
            return []
        except Exception as e:
            logger.error(f"Error reading inventory: {str(e)}")
            return []
    
    def generate_requirements_csv(self, low_stock_items: List[Dict]):
        """Generate requirements.csv from low stock items"""
        try:
            with open(self.requirements_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['item_name', 'required_quantity', 'category', 'specifications', 'priority']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for item in low_stock_items:
                    writer.writerow({
                        'item_name': item['item_name'],
                        'required_quantity': item['required_quantity'],
                        'category': item['category'],
                        'specifications': item['specifications'],
                        'priority': 'High' if item['current_stock'] == 0 else 'Medium'
                    })
            
            logger.info(f"Generated requirements.csv with {len(low_stock_items)} items")
            
        except Exception as e:
            logger.error(f"Error generating requirements CSV: {str(e)}")
    
    def create_conversation_relay_call(self, vendor_phone: str, requirements: List[Dict]) -> str:
        """Create a ConversationRelay call to vendor"""
        try:
            # Prepare the conversation context
            conversation_context = {
                "client_name": self.client_name,
                "vendor_name": self.test_vendor["name"],
                "items_to_quote": requirements,
                "conversation_goal": "Get quotes for required items",
                "webhook_url": "https://543a-2401-4900-1c30-31b1-c11a-e61b-78b3-ce01.ngrok-free.app/webhook/quote"  # Replace with actual webhook URL
            }
            
            # AI prompt for natural conversation
            ai_instructions = f"""
            You are an AI procurement assistant for {self.client_name}. You're calling {self.test_vendor['name']} to get quotes for items we need to order.
            
            Be natural and conversational. Start by introducing yourself and explaining the purpose of your call.
            Ask about each item one by one, including quantity needed and any specifications.
            When vendor provides a price, confirm it by repeating back: "So that's $X.XX per unit for [quantity] [item], correct?"
            After confirmation, immediately send the quote data to the webhook.
            
            Items to quote:
            {json.dumps(requirements, indent=2)}
            
            Keep the conversation flowing naturally - don't just read a list. Ask follow-up questions about availability, delivery times, and bulk discounts when appropriate.
            """
            
            # Create ConversationRelay call
            call = self.twilio_client.calls.create(
                url='https://543a-2401-4900-1c30-31b1-c11a-e61b-78b3-ce01.ngrok-free.app/webhook/voice',  # Replace with actual webhook URL
                to=vendor_phone,
                from_=self.phone_number,
                method='POST'
            )
            
            logger.info(f"ConversationRelay call initiated: {call.sid}")
            return call.sid
            
        except Exception as e:
            logger.error(f"Error creating ConversationRelay call: {str(e)}")
            return None
    
    def process_conversation_update(self, webhook_data: Dict):
        """Process conversation updates from ConversationRelay"""
        try:
            call_sid = webhook_data.get('CallSid')
            conversation_text = webhook_data.get('SpeechResult', '')
            
            # Store conversation state
            if call_sid not in self.conversation_state:
                self.conversation_state[call_sid] = {
                    'start_time': datetime.now(),
                    'messages': [],
                    'quotes_received': []
                }
            
            self.conversation_state[call_sid]['messages'].append({
                'timestamp': datetime.now(),
                'text': conversation_text,
                'type': 'speech_result'
            })
            
            # Parse for price information
            self.extract_quotes_from_conversation(call_sid, conversation_text)
            
        except Exception as e:
            logger.error(f"Error processing conversation update: {str(e)}")
    
    def extract_quotes_from_conversation(self, call_sid: str, text: str):
        """Extract quote information from conversation text"""
        import re
        
        # Simple regex patterns for price extraction
        price_patterns = [
            r'\$(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*dollars?',
            r'(\d+\.?\d*)\s*per\s+unit',
            r'(\d+\.?\d*)\s*each'
        ]
        
        item_patterns = [
            r'for\s+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+(?:costs?|is|will be)'
        ]
        
        for price_pattern in price_patterns:
            price_matches = re.findall(price_pattern, text.lower())
            if price_matches:
                for item_pattern in item_patterns:
                    item_matches = re.findall(item_pattern, text.lower())
                    if item_matches:
                        # Found potential quote
                        quote_data = {
                            'call_sid': call_sid,
                            'item_name': item_matches[0],
                            'price': float(price_matches[0]),
                            'timestamp': datetime.now().isoformat(),
                            'raw_text': text
                        }
                        self.log_quote_to_csv(quote_data)
                        break
    
    def log_quote_to_csv(self, quote_data: Dict):
        """Log quote data to quotes.csv"""
        try:
            file_exists = os.path.isfile(self.quotes_file)
            
            with open(self.quotes_file, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'vendor_name', 'item_name', 'price', 'quantity', 'call_sid', 'raw_text']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow({
                    'timestamp': quote_data.get('timestamp', datetime.now().isoformat()),
                    'vendor_name': self.test_vendor['name'],
                    'item_name': quote_data.get('item_name', ''),
                    'price': quote_data.get('price', 0),
                    'quantity': quote_data.get('quantity', 1),
                    'call_sid': quote_data.get('call_sid', ''),
                    'raw_text': quote_data.get('raw_text', '')
                })
            
            logger.info(f"Quote logged: {quote_data.get('item_name')} - ${quote_data.get('price')}")
            
        except Exception as e:
            logger.error(f"Error logging quote: {str(e)}")
    
    def compare_quotes_and_generate_orders(self):
        """Compare quotes and generate final_orders.csv with best prices"""
        try:
            df_quotes = pd.read_csv(self.quotes_file)
            df_requirements = pd.read_csv(self.requirements_file)
            
            best_quotes = []
            
            for _, req in df_requirements.iterrows():
                item_name = req['item_name']
                required_qty = req['required_quantity']
                
                # Find all quotes for this item
                item_quotes = df_quotes[df_quotes['item_name'].str.contains(item_name, case=False, na=False)]
                
                if not item_quotes.empty:
                    # Get the best (lowest) price
                    best_quote = item_quotes.loc[item_quotes['price'].idxmin()]
                    
                    best_quotes.append({
                        'item_name': item_name,
                        'vendor_name': best_quote['vendor_name'],
                        'quantity': required_qty,
                        'unit_price': best_quote['price'],
                        'total_price': best_quote['price'] * required_qty,
                        'order_date': datetime.now().isoformat(),
                        'status': 'Ready to Order'
                    })
            
            # Write final orders CSV
            with open(self.final_orders_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['item_name', 'vendor_name', 'quantity', 'unit_price', 'total_price', 'order_date', 'status']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(best_quotes)
            
            logger.info(f"Generated final orders for {len(best_quotes)} items")
            return best_quotes
            
        except Exception as e:
            logger.error(f"Error comparing quotes: {str(e)}")
            return []
    
    def start_webhook_server(self):
        """Start the webhook server in a separate thread"""
        def run_server():
            self.app.run(host=config.WEBHOOK_HOST, port=config.WEBHOOK_PORT, debug=False)
        
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        logger.info(f"Webhook server started on {config.WEBHOOK_HOST}:{config.WEBHOOK_PORT}")
    
    def run_procurement_workflow(self):
        """Execute the complete procurement workflow"""
        logger.info("Starting Likwid.AI Procurement Automation System")
        logger.info(f"Client: {self.client_name}")
        logger.info(f"Test Vendor: {self.test_vendor['name']} ({self.test_vendor['phone']})")
        
        # Step 1: Start webhook server
        self.start_webhook_server()
        time.sleep(2)  # Give server time to start
        
        # Step 2: Read inventory and identify low stock items
        logger.info("Step 1: Reading inventory and identifying low stock items...")
        low_stock_items = self.read_inventory()
        
        if not low_stock_items:
            logger.info("No items require procurement at this time")
            return
        
        # Step 3: Generate requirements CSV
        logger.info("Step 2: Generating requirements.csv...")
        self.generate_requirements_csv(low_stock_items)
        
        # Step 4: Initiate ConversationRelay call with vendor
        logger.info("Step 3: Initiating voice conversation with vendor...")
        call_sid = self.create_conversation_relay_call(
            self.test_vendor['phone'], 
            low_stock_items
        )
        
        if call_sid:
            logger.info(f"Call initiated successfully: {call_sid}")
            logger.info("Waiting for conversation to complete and quotes to be collected...")
            
            # Wait for conversation to complete (in real implementation, this would be event-driven)
            time.sleep(60)  # Placeholder wait time
        else:
            logger.error("Failed to initiate call")
            return
        
        # Step 5: Compare quotes and generate final orders
        logger.info("Step 4: Comparing quotes and generating final orders...")
        final_orders = self.compare_quotes_and_generate_orders()
        
        if final_orders:
            total_value = sum(order['total_price'] for order in final_orders)
            logger.info(f"Procurement workflow completed successfully!")
            logger.info(f"Total orders: {len(final_orders)}")
            logger.info(f"Total value: ${total_value:.2f}")
            
            # Display final orders
            print("\n" + "="*60)
            print("FINAL PROCUREMENT ORDERS")
            print("="*60)
            for order in final_orders:
                print(f"Item: {order['item_name']}")
                print(f"Vendor: {order['vendor_name']}")
                print(f"Quantity: {order['quantity']}")
                print(f"Unit Price: ${order['unit_price']:.2f}")
                print(f"Total: ${order['total_price']:.2f}")
                print("-" * 40)
        else:
            logger.warning("No quotes were collected or processed")

def main():
    """Main function to run the procurement automation system"""
    system = ProcurementAutomationSystem()
    
    try:
        system.run_procurement_workflow()
    except KeyboardInterrupt:
        logger.info("System interrupted by user")
    except Exception as e:
        logger.error(f"System error: {str(e)}")

if __name__ == "__main__":
    main()
