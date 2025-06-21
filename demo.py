"""
Demo script for Likwid.AI Procurement Automation System
Simulates the entire workflow without making actual phone calls
"""

import csv
import json
import logging
from datetime import datetime
from typing import List, Dict
import pandas as pd
import time
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProcurementDemo:
    def __init__(self):
        self.client_name = config.CLIENT_NAME
        self.test_vendor = config.TEST_VENDOR
        
        # File paths
        self.inventory_file = config.INVENTORY_FILE
        self.requirements_file = config.REQUIREMENTS_FILE
        self.quotes_file = config.QUOTES_FILE
        self.final_orders_file = config.FINAL_ORDERS_FILE
        
        # Simulated vendor responses for demo
        self.simulated_quotes = {
            "Petri Dishes (100mm)": 2.75,
            "Micropipette Tips (1000μL)": 0.45,
            "Laboratory Gloves (Nitrile)": 12.50,
            "pH Buffer Solution (7.0)": 15.25,
            "Eppendorf Tubes (1.5ml)": 0.85,
            "Autoclave Tape": 8.75,
            "Cell Culture Media": 45.00,
            "Microscope Slides": 1.25,
            "Laboratory Beakers (250ml)": 18.50,
            "Centrifuge Tubes (50ml)": 2.30,
            "Incubator Filters": 125.00,
            "PCR Reaction Tubes": 0.65,
            "Safety Goggles": 22.00,
            "Bunsen Burner Gas": 35.00,
            "Analytical Balance Calibration Weights": 450.00
        }
        
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
                        'required_quantity': max(1, row['minimum_threshold'] - row['current_stock'] + row.get('buffer_stock', 10)),
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
    
    def simulate_conversation(self, requirements: List[Dict]):
        """Simulate AI conversation with vendor and generate quotes"""
        logger.info("🎤 Simulating AI conversation with vendor...")
        
        print("\n" + "="*80)
        print("🤖 AI CONVERSATION SIMULATION")
        print("="*80)
        
        # Introduction
        print(f"\n🤖 AI: {config.get_ai_introduction()}")
        print(f"👤 {self.test_vendor['name']}: Hi! Yes, this is a good time. What items do you need quotes for?")
        
        quotes_collected = []
        
        for i, item in enumerate(requirements, 1):
            print(f"\n--- Item {i}/{len(requirements)} ---")
            
            # AI asks about item
            item_inquiry = config.get_ai_item_inquiry(
                item['item_name'], 
                item['specifications'], 
                item['required_quantity']
            )
            print(f"🤖 AI: {item_inquiry}")
            
            # Vendor response
            if item['item_name'] in self.simulated_quotes:
                price = self.simulated_quotes[item['item_name']]
                print(f"👤 {self.test_vendor['name']}: Yes, we have that in stock. For {item['required_quantity']} units, I can offer ${price:.2f} per unit.")
                
                # AI confirmation
                confirmation = config.get_ai_price_confirmation(
                    price, 
                    item['required_quantity'], 
                    item['item_name']
                )
                print(f"🤖 AI: {confirmation}")
                print(f"👤 {self.test_vendor['name']}: That's correct!")
                
                # Log quote
                quote_data = {
                    'timestamp': datetime.now().isoformat(),
                    'vendor_name': self.test_vendor['name'],
                    'item_name': item['item_name'],
                    'price': price,
                    'quantity': item['required_quantity'],
                    'call_sid': f"DEMO_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'raw_text': f"${price:.2f} per unit for {item['required_quantity']} {item['item_name']}"
                }
                quotes_collected.append(quote_data)
                
                # Simulate processing delay
                time.sleep(1)
            else:
                print(f"👤 {self.test_vendor['name']}: Sorry, I don't carry that item currently.")
        
        # Conversation closing
        print(f"\n🤖 AI: Thank you for all the quotes! I'll process these and get back to you with our order confirmation.")
        print(f"👤 {self.test_vendor['name']}: Sounds great! Looking forward to working with Bio Mac Lifesciences.")
        
        print("="*80)
        
        return quotes_collected
    
    def log_quotes_to_csv(self, quotes: List[Dict]):
        """Log collected quotes to quotes.csv"""
        try:
            with open(self.quotes_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'vendor_name', 'item_name', 'price', 'quantity', 'call_sid', 'raw_text']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(quotes)
            
            logger.info(f"Logged {len(quotes)} quotes to {self.quotes_file}")
            
        except Exception as e:
            logger.error(f"Error logging quotes: {str(e)}")
    
    def compare_quotes_and_generate_orders(self):
        """Compare quotes and generate final_orders.csv with best prices"""
        try:
            df_quotes = pd.read_csv(self.quotes_file)
            df_requirements = pd.read_csv(self.requirements_file)
            
            best_quotes = []
            
            for _, req in df_requirements.iterrows():
                item_name = req['item_name']
                required_qty = req['required_quantity']
                
                # Find quotes for this item
                item_quotes = df_quotes[df_quotes['item_name'] == item_name]
                
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
                else:
                    logger.warning(f"No quotes found for {item_name}")
            
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
    
    def display_results(self, final_orders: List[Dict]):
        """Display the final results in a formatted way"""
        if not final_orders:
            print("\n❌ No orders generated")
            return
        
        total_value = sum(order['total_price'] for order in final_orders)
        total_items = len(final_orders)
        
        print("\n" + "="*80)
        print("📋 FINAL PROCUREMENT ORDERS - LIKWID.AI DEMO")
        print("="*80)
        print(f"Client: {self.client_name}")
        print(f"Vendor: {self.test_vendor['name']} ({self.test_vendor['phone']})")
        print(f"Order Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Items: {total_items}")
        print(f"Total Value: ${total_value:.2f}")
        print("-" * 80)
        
        for i, order in enumerate(final_orders, 1):
            print(f"{i:2d}. {order['item_name']}")
            print(f"     Quantity: {order['quantity']:>8}")
            print(f"     Unit Price: ${order['unit_price']:>6.2f}")
            print(f"     Total: ${order['total_price']:>10.2f}")
            print()
        
        print("="*80)
        print("✅ Procurement workflow completed successfully!")
        print("📁 Files generated:")
        print(f"   • {self.requirements_file}")
        print(f"   • {self.quotes_file}")
        print(f"   • {self.final_orders_file}")
        print("="*80)
    
    def run_demo(self):
        """Execute the complete demo workflow"""
        print("\n🚀 Starting Likwid.AI Procurement Automation Demo")
        print(f"   Client: {self.client_name}")
        print(f"   Vendor: {self.test_vendor['name']} ({self.test_vendor['phone']})")
        print()
        
        # Step 1: Read inventory
        logger.info("📊 Step 1: Analyzing inventory...")
        low_stock_items = self.read_inventory()
        
        if not low_stock_items:
            print("✅ All items are adequately stocked. No procurement needed!")
            return
        
        print(f"   Found {len(low_stock_items)} items requiring procurement")
        
        # Step 2: Generate requirements
        logger.info("📝 Step 2: Generating procurement requirements...")
        self.generate_requirements_csv(low_stock_items)
        print(f"   Generated {self.requirements_file}")
        
        # Step 3: Simulate conversation
        logger.info("🎤 Step 3: Simulating AI conversation with vendor...")
        quotes = self.simulate_conversation(low_stock_items)
        
        # Step 4: Log quotes
        logger.info("💾 Step 4: Logging quotes to CSV...")
        self.log_quotes_to_csv(quotes)
        print(f"   Collected {len(quotes)} quotes")
        
        # Step 5: Generate final orders
        logger.info("🔄 Step 5: Comparing quotes and generating orders...")
        final_orders = self.compare_quotes_and_generate_orders()
        
        # Step 6: Display results
        self.display_results(final_orders)

def main():
    """Main function to run the demo"""
    demo = ProcurementDemo()
    
    try:
        demo.run_demo()
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo error: {str(e)}")

if __name__ == "__main__":
    main() 