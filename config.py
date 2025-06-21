"""
Configuration file for Likwid.AI Procurement Automation System
"""

import os
from typing import Dict, Any

class Config:
    """Configuration class for the procurement automation system"""
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID = "AC820daae89092e30fee3487e80162d2e2"
    TWILIO_AUTH_TOKEN = "690636dcdd752868f4e77648dc0d49eb"
    TWILIO_PHONE_NUMBER = "+14323484517"
    TWILIO_API_KEY_SID = "SKd4e4a70facd2bceb446e402b062fed07"
    
    # Webhook Configuration
    WEBHOOK_HOST = "0.0.0.0"
    WEBHOOK_PORT = 5000
    
    # Replace with your actual ngrok URL when running
    BASE_WEBHOOK_URL = "https://your-ngrok-url.ngrok.io"
    
    # Client Information
    CLIENT_NAME = "Bio Mac Lifesciences"
    
    # Test Vendor Information
    TEST_VENDOR = {
        "name": "Harshit Khemani",
        "phone": "+918800000488",
        "company": "Test Vendor Co.",
        "email": "harshit@testvendor.com"
    }
    
    # File Paths
    INVENTORY_FILE = "inventory.csv"
    REQUIREMENTS_FILE = "requirements.csv"
    QUOTES_FILE = "quotes.csv"
    FINAL_ORDERS_FILE = "final_orders.csv"
    
    # Logging Configuration
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    
    # Conversation Parameters
    CONVERSATION_TIMEOUT = 300  # 5 minutes
    QUOTE_CONFIRMATION_TIMEOUT = 30  # 30 seconds
    
    # AI Conversation Templates
    AI_INTRODUCTION_TEMPLATE = """
    Hi, this is an AI assistant calling on behalf of {client_name}. 
    I'm reaching out to get quotes for some laboratory supplies we need to order. 
    Is this a good time to discuss pricing for a few items?
    """
    
    AI_ITEM_INQUIRY_TEMPLATE = """
    We're looking for {item_name}. The specifications are: {specifications}.
    We need approximately {quantity} units. Do you carry this item?
    """
    
    AI_PRICE_CONFIRMATION_TEMPLATE = """
    Let me confirm that - you're quoting ${price:.2f} per unit for {quantity} {item_name}, 
    is that correct?
    """
    
    @classmethod
    def get_webhook_url(cls, endpoint: str) -> str:
        """Get full webhook URL for given endpoint"""
        return f"{cls.BASE_WEBHOOK_URL}/webhook/{endpoint}"
    
    @classmethod
    def get_ai_introduction(cls) -> str:
        """Get AI introduction message"""
        return cls.AI_INTRODUCTION_TEMPLATE.format(client_name=cls.CLIENT_NAME)
    
    @classmethod
    def get_ai_item_inquiry(cls, item_name: str, specifications: str, quantity: int) -> str:
        """Get AI item inquiry message"""
        return cls.AI_ITEM_INQUIRY_TEMPLATE.format(
            item_name=item_name,
            specifications=specifications,
            quantity=quantity
        )
    
    @classmethod
    def get_ai_price_confirmation(cls, price: float, quantity: int, item_name: str) -> str:
        """Get AI price confirmation message"""
        return cls.AI_PRICE_CONFIRMATION_TEMPLATE.format(
            price=price,
            quantity=quantity,
            item_name=item_name
        )

# Environment-specific configurations
class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    LOG_LEVEL = "INFO"
    
    # Override with environment variables in production
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', Config.TWILIO_ACCOUNT_SID)
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', Config.TWILIO_AUTH_TOKEN)
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', Config.TWILIO_PHONE_NUMBER)
    BASE_WEBHOOK_URL = os.getenv('WEBHOOK_BASE_URL', Config.BASE_WEBHOOK_URL)

# Default configuration
config = DevelopmentConfig() 