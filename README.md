# Likwid.AI Procurement Automation System

An intelligent voice-driven procurement automation system that uses Twilio's ConversationRelay API to handle end-to-end purchasing through natural voice conversations with vendors.

## Overview

This system automates the procurement process for **Bio Mac Lifesciences** by:

1. **Reading inventory data** to identify low or out-of-stock items
2. **Generating procurement requirements** automatically
3. **Initiating voice conversations** with vendors using AI
4. **Collecting quotes** through natural dialogue
5. **Comparing prices** and generating optimal purchase orders

## Features

- 🎤 **Voice-First Workflow**: Natural conversations with vendors via Twilio ConversationRelay
- 📊 **Intelligent Inventory Management**: Automatic detection of low-stock items
- 💰 **Real-time Quote Collection**: AI extracts and logs pricing during calls
- 🔄 **Automated Comparison**: Finds best prices across vendors
- 📋 **Order Generation**: Creates final purchase orders with optimal selections
- 🌐 **Webhook Integration**: Real-time data processing during conversations

## System Architecture

```
Inventory.csv → Requirements.csv → AI Voice Call → Quotes.csv → Final_Orders.csv
     ↓              ↓                    ↓             ↓              ↓
  Low Stock    Procurement       Natural Voice    Price Logging   Best Prices
  Detection    Requirements      Conversation     via Webhooks    & Orders
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Webhook URL

You'll need to expose your local server to the internet for Twilio webhooks. Use ngrok:

```bash
# Install ngrok (if not already installed)
# Download from https://ngrok.com/

# Start ngrok tunnel
ngrok http 5000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

### 3. Update Webhook URLs

In `main.py`, replace the placeholder URLs with your ngrok URL:

```python
# Line ~125 and ~145
"webhook_url": "https://your-actual-ngrok-url.ngrok.io/webhook/quote"
url='https://your-actual-ngrok-url.ngrok.io/webhook/voice'
```

### 4. Twilio Configuration

The system is pre-configured with the provided Twilio credentials:
- **Account SID**: `AC820daae89092e30fee3487e80162d2e2`
- **Auth Token**: `690636dcdd752868f4e77648dc0d49eb`
- **Phone Number**: `+14323484517`
- **API Key SID**: `SKd4e4a70facd2bceb446e402b062fed07`

## Running the System

### Quick Start

```bash
python main.py
```

### Step-by-Step Process

1. **Inventory Analysis**: System reads `inventory.csv` and identifies items below minimum threshold
2. **Requirements Generation**: Creates `requirements.csv` with procurement needs
3. **Webhook Server**: Starts Flask server on port 5000 for real-time data processing
4. **Voice Conversation**: Initiates AI-powered call to vendor (Harshit Khemani: +918800000488)
5. **Quote Collection**: AI extracts pricing information and logs to `quotes.csv`
6. **Order Optimization**: Compares quotes and generates `final_orders.csv` with best prices

## File Structure

```
procurement-conversational/
├── main.py                 # Main application
├── requirements.txt        # Python dependencies
├── inventory.csv          # Current inventory levels
├── requirements.csv       # Generated procurement needs
├── quotes.csv            # Collected quotes from vendors
├── final_orders.csv      # Optimized purchase orders
└── README.md             # This documentation
```

## CSV File Formats

### inventory.csv
```csv
item_name,current_stock,minimum_threshold,buffer_stock,category,specifications
Petri Dishes (100mm),5,20,15,Lab Supplies,Sterile polystyrene with lid
```

### requirements.csv (Generated)
```csv
item_name,required_quantity,category,specifications,priority
Petri Dishes (100mm),30,Lab Supplies,Sterile polystyrene with lid,Medium
```

### quotes.csv (Generated)
```csv
timestamp,vendor_name,item_name,price,quantity,call_sid,raw_text
2024-01-15T10:30:00,Harshit Khemani,Petri Dishes,2.50,30,CAxxxx,That's $2.50 per dish
```

### final_orders.csv (Generated)
```csv
item_name,vendor_name,quantity,unit_price,total_price,order_date,status
Petri Dishes (100mm),Harshit Khemani,30,2.50,75.00,2024-01-15T10:35:00,Ready to Order
```

## AI Conversation Flow

The AI assistant conducts natural conversations with vendors:

1. **Introduction**: "Hi, this is an AI assistant calling on behalf of Bio Mac Lifesciences..."
2. **Item Inquiry**: "We're looking to order some lab supplies. Do you have Petri Dishes available?"
3. **Quantity Discussion**: "We need about 30 units. What's your pricing for that quantity?"
4. **Quote Confirmation**: "So that's $2.50 per dish for 30 units, correct?"
5. **Additional Items**: Naturally transitions to next items on the list
6. **Closing**: Thanks vendor and confirms next steps

## Webhook Endpoints

- **GET /health**: System health check
- **POST /webhook/voice**: Handles voice conversation updates from ConversationRelay
- **POST /webhook/quote**: Processes quote data during conversations

## Demo Configuration

**Client**: Bio Mac Lifesciences  
**Test Vendor**: Harshit Khemani (+918800000488)  
**Demo Items**: Laboratory supplies (see inventory.csv)

## Troubleshooting

### Common Issues

1. **"Inventory file not found"**: Ensure `inventory.csv` exists in the project directory
2. **Webhook timeout**: Verify ngrok is running and URLs are updated in code
3. **Twilio authentication error**: Check that credentials are correctly configured

### Logs

The system provides detailed logging:
- INFO: Normal operations and workflow progress
- ERROR: Issues with file operations, API calls, or data processing
- DEBUG: Detailed conversation and webhook data

## Production Considerations

For production deployment:

1. **Environment Variables**: Move credentials to environment variables
2. **Database Integration**: Replace CSV files with proper database
3. **Error Handling**: Implement comprehensive error recovery
4. **Scaling**: Add support for multiple vendors and concurrent calls
5. **Security**: Implement webhook authentication and rate limiting

## Support

For technical support or questions about the Likwid.AI Procurement Automation System, please contact the development team.

---

**Powered by Likwid.AI** - Transforming procurement through intelligent automation 