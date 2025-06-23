"""
Data Models for Multi-Company Procurement Platform
Defines all data structures used throughout the system
"""

try:
    from dataclasses import dataclass, asdict, field
except ImportError:
    # Fallback for older Python versions
    def dataclass(cls):
        return cls
    
    def asdict(obj):
        return obj.__dict__
    
    def field(**kwargs):
        return None

from typing import Dict, List, Optional
from datetime import datetime
import json

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
    preferred_vendors: Optional[List[str]] = field(default_factory=list)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    def is_low_stock(self) -> bool:
        """Check if item is below minimum required stock"""
        return self.current_stock <= self.minimum_required
    
    def get_shortage(self) -> int:
        """Calculate shortage amount"""
        return max(0, self.minimum_required - self.current_stock)
    
    def get_urgency(self) -> str:
        """Determine urgency level based on current stock"""
        if self.current_stock < (self.minimum_required * 0.5):
            return "critical"
        elif self.current_stock <= self.minimum_required:
            return "urgent"
        return "normal"

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
    inventory: Optional[Dict[str, InventoryItem]] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        if self.inventory:
            data['inventory'] = {k: v.to_dict() if hasattr(v, 'to_dict') else v 
                               for k, v in self.inventory.items()}
        return data
    
    def get_low_stock_items(self) -> List[InventoryItem]:
        """Get all items that are below minimum stock"""
        if not self.inventory:
            return []
        return [item for item in self.inventory.values() if item.is_low_stock()]
    
    def get_total_inventory_value(self) -> float:
        """Calculate total inventory value"""
        if not self.inventory:
            return 0.0
        return sum(item.current_stock * item.average_price for item in self.inventory.values())

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
    total_orders: int = 0
    successful_deliveries: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    def get_success_rate(self) -> float:
        """Calculate delivery success rate"""
        if self.total_orders == 0:
            return 0.0
        return (self.successful_deliveries / self.total_orders) * 100
    
    def can_supply_category(self, category: str) -> bool:
        """Check if vendor can supply items in given category"""
        return any(specialty.lower() in category.lower() for specialty in self.specialties)

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
    notes: str = ""
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    def is_expired(self) -> bool:
        """Check if quote has expired"""
        from datetime import datetime, timedelta
        quote_date = datetime.fromisoformat(self.timestamp)
        expiry_date = quote_date + timedelta(days=self.validity_days)
        return datetime.now() > expiry_date

@dataclass
class Negotiation:
    negotiation_id: str
    quote_id: str
    rounds: List[Dict]
    current_offer: float
    target_price: float
    status: str
    last_update: str
    savings_achieved: float = 0.0
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    def add_round(self, offer: float, response: str, party: str):
        """Add a negotiation round"""
        round_data = {
            'round': len(self.rounds) + 1,
            'offer': offer,
            'response': response,
            'party': party,  # 'buyer' or 'vendor'
            'timestamp': datetime.now().isoformat()
        }
        self.rounds.append(round_data)
        self.current_offer = offer
        self.last_update = datetime.now().isoformat()

@dataclass
class ConversationEntry:
    entry_id: str
    timestamp: str
    type: str  # voice, whatsapp, system
    vendor_message: str
    ai_response: str
    extracted_data: Optional[Dict]
    conversation_context: Optional[Dict]
    call_sid: Optional[str] = None
    vendor_number: Optional[str] = None
    company_id: Optional[str] = None
    conversation_ended: bool = False
    end_reason: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

@dataclass
class SystemMetrics:
    total_companies: int = 0
    total_vendors: int = 0
    active_conversations: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    whatsapp_conversations: int = 0
    total_savings: float = 0.0
    average_response_time: float = 0.0
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

class ProcurementError(Exception):
    """Custom exception for procurement-related errors"""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class DatabaseError(Exception):
    """Custom exception for database-related errors"""
    pass

class CommunicationError(Exception):
    """Custom exception for communication-related errors"""
    pass

class AIServiceError(Exception):
    """Custom exception for AI service-related errors"""
    pass 