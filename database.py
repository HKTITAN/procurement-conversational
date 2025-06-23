"""
Database Management for Multi-Company Procurement Platform
Handles all data operations with error handling and fallbacks
"""

import json
import os
import csv
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from models import (
    Company, Vendor, InventoryItem, Quote, Negotiation, 
    ConversationEntry, SystemMetrics, DatabaseError
)

class ProcurementDatabase:
    """Thread-safe database manager with JSON persistence and CSV export"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.lock = threading.RLock()
        
        # Initialize data storage
        self.companies: Dict[str, Company] = {}
        self.vendors: Dict[str, Vendor] = {}
        self.quotes: Dict[str, Quote] = {}
        self.negotiations: Dict[str, Negotiation] = {}
        self.conversations: List[ConversationEntry] = []
        self.metrics: SystemMetrics = SystemMetrics()
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Load existing data
        self._load_all_data()
        
        # Initialize with sample data if empty
        if not self.companies:
            self._initialize_sample_data()
    
    def _get_file_path(self, filename: str) -> str:
        """Get full file path for data file"""
        return os.path.join(self.data_dir, filename)
    
    def _save_to_file(self, data: Any, filename: str) -> bool:
        """Save data to JSON file with error handling"""
        try:
            filepath = self._get_file_path(filename)
            
            # Create backup if file exists
            if os.path.exists(filepath):
                backup_path = f"{filepath}.backup"
                os.rename(filepath, backup_path)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving {filename}: {e}")
            
            # Restore backup if save failed
            backup_path = f"{filepath}.backup"
            if os.path.exists(backup_path):
                os.rename(backup_path, filepath)
            
            return False
    
    def _load_from_file(self, filename: str, default: Any = None) -> Any:
        """Load data from JSON file with error handling"""
        try:
            filepath = self._get_file_path(filename)
            
            if not os.path.exists(filepath):
                return default
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            
            # Try backup file
            backup_path = f"{filepath}.backup"
            if os.path.exists(backup_path):
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        print(f"Loaded backup for {filename}")
                        return json.load(f)
                except:
                    pass
            
            return default
    
    def _load_all_data(self):
        """Load all data from files"""
        try:
            # Load companies
            companies_data = self._load_from_file('companies.json', {})
            for company_id, company_data in companies_data.items():
                # Convert inventory items
                if 'inventory' in company_data and company_data['inventory']:
                    inventory = {}
                    for item_id, item_data in company_data['inventory'].items():
                        inventory[item_id] = InventoryItem(**item_data)
                    company_data['inventory'] = inventory
                
                self.companies[company_id] = Company(**company_data)
            
            # Load vendors
            vendors_data = self._load_from_file('vendors.json', {})
            for vendor_id, vendor_data in vendors_data.items():
                self.vendors[vendor_id] = Vendor(**vendor_data)
            
            # Load quotes
            quotes_data = self._load_from_file('quotes.json', {})
            for quote_id, quote_data in quotes_data.items():
                self.quotes[quote_id] = Quote(**quote_data)
            
            # Load negotiations
            negotiations_data = self._load_from_file('negotiations.json', {})
            for neg_id, neg_data in negotiations_data.items():
                self.negotiations[neg_id] = Negotiation(**neg_data)
            
            # Load conversations
            conversations_data = self._load_from_file('conversations.json', [])
            self.conversations = [ConversationEntry(**conv) for conv in conversations_data]
            
            # Load metrics
            metrics_data = self._load_from_file('metrics.json', {})
            if metrics_data:
                self.metrics = SystemMetrics(**metrics_data)
            
            print(f"Loaded data: {len(self.companies)} companies, {len(self.vendors)} vendors")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            raise DatabaseError(f"Failed to load database: {e}")
    
    def save_all_data(self) -> bool:
        """Save all data to files"""
        with self.lock:
            try:
                # Save companies
                companies_data = {cid: company.to_dict() for cid, company in self.companies.items()}
                self._save_to_file(companies_data, 'companies.json')
                
                # Save vendors
                vendors_data = {vid: vendor.to_dict() for vid, vendor in self.vendors.items()}
                self._save_to_file(vendors_data, 'vendors.json')
                
                # Save quotes
                quotes_data = {qid: quote.to_dict() for qid, quote in self.quotes.items()}
                self._save_to_file(quotes_data, 'quotes.json')
                
                # Save negotiations
                negotiations_data = {nid: neg.to_dict() for nid, neg in self.negotiations.items()}
                self._save_to_file(negotiations_data, 'negotiations.json')
                
                # Save conversations
                conversations_data = [conv.to_dict() for conv in self.conversations]
                self._save_to_file(conversations_data, 'conversations.json')
                
                # Update and save metrics
                self._update_metrics()
                self._save_to_file(self.metrics.to_dict(), 'metrics.json')
                
                return True
                
            except Exception as e:
                print(f"Error saving data: {e}")
                return False
    
    def _update_metrics(self):
        """Update system metrics"""
        self.metrics.total_companies = len(self.companies)
        self.metrics.total_vendors = len(self.vendors)
        self.metrics.active_conversations = len([c for c in self.conversations if not c.conversation_ended])
        self.metrics.total_savings = sum(neg.savings_achieved for neg in self.negotiations.values())
        self.metrics.last_updated = datetime.now().isoformat()
    
    # Company operations
    def add_company(self, company: Company) -> bool:
        """Add a new company"""
        with self.lock:
            try:
                self.companies[company.company_id] = company
                return self.save_all_data()
            except Exception as e:
                raise DatabaseError(f"Failed to add company: {e}")
    
    def get_company(self, company_id: str) -> Optional[Company]:
        """Get company by ID"""
        return self.companies.get(company_id)
    
    def get_all_companies(self) -> Dict[str, Company]:
        """Get all companies"""
        return self.companies.copy()
    
    def update_company(self, company_id: str, updates: Dict[str, Any]) -> bool:
        """Update company data"""
        with self.lock:
            try:
                if company_id not in self.companies:
                    return False
                
                company = self.companies[company_id]
                for key, value in updates.items():
                    if hasattr(company, key):
                        setattr(company, key, value)
                
                return self.save_all_data()
            except Exception as e:
                raise DatabaseError(f"Failed to update company: {e}")
    
    # Vendor operations
    def add_vendor(self, vendor: Vendor) -> bool:
        """Add a new vendor"""
        with self.lock:
            try:
                self.vendors[vendor.vendor_id] = vendor
                return self.save_all_data()
            except Exception as e:
                raise DatabaseError(f"Failed to add vendor: {e}")
    
    def get_vendor(self, vendor_id: str) -> Optional[Vendor]:
        """Get vendor by ID"""
        return self.vendors.get(vendor_id)
    
    def get_all_vendors(self) -> Dict[str, Vendor]:
        """Get all vendors"""
        return self.vendors.copy()
    
    def find_vendors_by_specialty(self, specialty: str) -> List[Vendor]:
        """Find vendors by specialty"""
        return [vendor for vendor in self.vendors.values() 
                if vendor.can_supply_category(specialty)]
    
    # Inventory operations
    def update_inventory_item(self, company_id: str, item_id: str, updates: Dict[str, Any]) -> bool:
        """Update inventory item"""
        with self.lock:
            try:
                company = self.companies.get(company_id)
                if not company or not company.inventory or item_id not in company.inventory:
                    return False
                
                item = company.inventory[item_id]
                for key, value in updates.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
                
                return self.save_all_data()
            except Exception as e:
                raise DatabaseError(f"Failed to update inventory: {e}")
    
    def get_low_stock_items(self, company_id: str = None) -> Dict[str, List[InventoryItem]]:
        """Get low stock items for all or specific company"""
        low_stock = {}
        
        companies_to_check = [self.companies[company_id]] if company_id else self.companies.values()
        
        for company in companies_to_check:
            if company.inventory:
                low_items = company.get_low_stock_items()
                if low_items:
                    low_stock[company.company_id] = low_items
        
        return low_stock
    
    # Conversation operations
    def add_conversation(self, conversation: ConversationEntry) -> bool:
        """Add conversation entry"""
        with self.lock:
            try:
                self.conversations.append(conversation)
                
                # Keep only last 1000 conversations to prevent memory issues
                if len(self.conversations) > 1000:
                    self.conversations = self.conversations[-1000:]
                
                return self.save_all_data()
            except Exception as e:
                raise DatabaseError(f"Failed to add conversation: {e}")
    
    def get_conversations(self, limit: int = 100, conversation_type: str = None) -> List[ConversationEntry]:
        """Get recent conversations"""
        conversations = self.conversations[-limit:]
        
        if conversation_type:
            conversations = [c for c in conversations if c.type == conversation_type]
        
        return conversations
    
    # Export operations
    def export_to_csv(self, export_type: str = "all") -> str:
        """Export data to CSV file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            if export_type == "companies":
                filename = f"companies_export_{timestamp}.csv"
                self._export_companies_csv(filename)
            elif export_type == "vendors":
                filename = f"vendors_export_{timestamp}.csv"
                self._export_vendors_csv(filename)
            elif export_type == "conversations":
                filename = f"conversations_export_{timestamp}.csv"
                self._export_conversations_csv(filename)
            else:
                filename = f"full_export_{timestamp}.csv"
                self._export_full_csv(filename)
            
            return filename
            
        except Exception as e:
            raise DatabaseError(f"Failed to export data: {e}")
    
    def _export_companies_csv(self, filename: str):
        """Export companies to CSV"""
        filepath = self._get_file_path(filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['company_id', 'name', 'industry', 'contact_person', 'phone', 
                         'email', 'budget_monthly', 'procurement_priority', 'inventory_items',
                         'low_stock_items', 'total_inventory_value']
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for company in self.companies.values():
                low_stock = company.get_low_stock_items()
                inventory_count = len(company.inventory) if company.inventory else 0
                
                writer.writerow({
                    'company_id': company.company_id,
                    'name': company.name,
                    'industry': company.industry,
                    'contact_person': company.contact_person,
                    'phone': company.phone,
                    'email': company.email,
                    'budget_monthly': company.budget_monthly,
                    'procurement_priority': company.procurement_priority,
                    'inventory_items': inventory_count,
                    'low_stock_items': len(low_stock),
                    'total_inventory_value': company.get_total_inventory_value()
                })
    
    def _export_vendors_csv(self, filename: str):
        """Export vendors to CSV"""
        filepath = self._get_file_path(filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['vendor_id', 'name', 'phone', 'email', 'specialties', 
                         'rating', 'response_time', 'price_competitiveness', 
                         'total_orders', 'success_rate']
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for vendor in self.vendors.values():
                writer.writerow({
                    'vendor_id': vendor.vendor_id,
                    'name': vendor.name,
                    'phone': vendor.phone,
                    'email': vendor.email,
                    'specialties': ', '.join(vendor.specialties),
                    'rating': vendor.rating,
                    'response_time': vendor.response_time,
                    'price_competitiveness': vendor.price_competitiveness,
                    'total_orders': vendor.total_orders,
                    'success_rate': vendor.get_success_rate()
                })
    
    def _export_conversations_csv(self, filename: str):
        """Export conversations to CSV"""
        filepath = self._get_file_path(filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'type', 'vendor_number', 'company_id', 
                         'vendor_message', 'ai_response', 'conversation_ended', 'end_reason']
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for conv in self.conversations:
                writer.writerow({
                    'timestamp': conv.timestamp,
                    'type': conv.type,
                    'vendor_number': conv.vendor_number or '',
                    'company_id': conv.company_id or '',
                    'vendor_message': conv.vendor_message,
                    'ai_response': conv.ai_response,
                    'conversation_ended': conv.conversation_ended,
                    'end_reason': conv.end_reason or ''
                })
    
    def get_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        self._update_metrics()
        return self.metrics
    
    def _initialize_sample_data(self):
        """Initialize with sample data"""
        print("Initializing sample data...")
        
        # Sample companies with inventory
        sample_companies = {
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
                        preferred_vendors=["chemical_solutions"]
                    )
                }
            )
        }
        
        # Sample vendors
        sample_vendors = {
            "lab_supply_pro": Vendor(
                vendor_id="lab_supply_pro",
                name="Lab Supply Pro",
                phone="+918800001111",
                email="sales@labsupplypro.com",
                specialties=["Laboratory Consumables", "Glassware"],
                rating=4.5,
                response_time="24 hours",
                price_competitiveness="competitive",
                total_orders=45,
                successful_deliveries=42
            ),
            "chemical_solutions": Vendor(
                vendor_id="chemical_solutions",
                name="Chemical Solutions Ltd",
                phone="+918800003333",
                email="procurement@chemsolutions.co.in",
                specialties=["Chemicals", "Reagents"],
                rating=4.7,
                response_time="12 hours",
                price_competitiveness="competitive",
                total_orders=38,
                successful_deliveries=37
            )
        }
        
        # Add sample data
        self.companies.update(sample_companies)
        self.vendors.update(sample_vendors)
        
        # Save sample data
        self.save_all_data()
        print("Sample data initialized successfully!")

# Global database instance
db = ProcurementDatabase() 