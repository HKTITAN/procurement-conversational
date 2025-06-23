# 🏭 Multi-Company Procurement Platform

An intelligent, AI-powered procurement management system with real-time voice communication, WhatsApp integration, and comprehensive analytics. Built with a modern, scalable architecture using Flask, Gemini AI, and Twilio.

## 🌟 Key Features

### 📊 **Multi-Company Management**
- Manage inventory across multiple companies
- Real-time stock monitoring and shortage detection
- Automated budget tracking and utilization analysis
- Company-specific procurement priorities

### 🤖 **AI-Powered Intelligence**
- Gemini AI integration for dynamic conversation generation
- Intelligent vendor information extraction
- Automated response generation with fallback mechanisms
- Context-aware conversation management

### 📞 **Advanced Communication**
- **Voice Calls**: Automated Twilio-powered voice calls with speech recognition
- **WhatsApp Integration**: Two-way WhatsApp messaging with auto-fallback
- **Real-time Tracking**: Live conversation monitoring and status updates
- **Multi-channel Strategy**: Voice-to-WhatsApp fallback for failed calls

### 🛒 **Intelligent Procurement**
- Automated inventory analysis and shortage detection
- AI-powered vendor matching and recommendation
- Price comparison and negotiation assistance
- Risk assessment and budget optimization

### 🌐 **Modern Web Dashboard**
- Real-time analytics with interactive charts
- Responsive design with mobile support
- Live updates via WebSocket connections
- Comprehensive company and vendor management

## 🏗️ Architecture Overview

### **Modular Design**
The platform is built with a clean, modular architecture:

```
procurement-platform/
├── models.py           # Data structures and models
├── database.py         # Data persistence and management
├── ai_services.py      # Gemini AI integration
├── communication.py    # Twilio voice & WhatsApp handling
├── procurement.py      # Business logic and analysis
├── web_server.py       # Flask web application
├── main.py            # Platform orchestrator
├── templates/         # HTML templates
│   ├── dashboard.html # Base template
│   └── index.html     # Dashboard page
├── static/           # CSS and JavaScript
│   ├── css/style.css # Modern styling
│   └── js/main.js    # Frontend functionality
└── data/             # Data storage (auto-created)
```

### **Core Components**

#### 🗃️ **Data Layer (`models.py`, `database.py`)**
- **Thread-safe data management** with JSON persistence
- **Comprehensive models**: Companies, Vendors, Inventory, Conversations
- **Automatic data backup** and CSV export capabilities
- **Error handling and recovery** mechanisms

#### 🤖 **AI Services (`ai_services.py`)**
- **Gemini AI integration** with intelligent fallbacks
- **Dynamic content generation** for calls and messages
- **Information extraction** from vendor responses
- **Context-aware conversation** management

#### 📞 **Communication (`communication.py`)**
- **Twilio voice calls** with speech recognition (Hindi/English)
- **WhatsApp messaging** with automatic formatting
- **Call status tracking** and real-time updates
- **Fallback mechanisms** for failed communications

#### 🛒 **Procurement Engine (`procurement.py`)**
- **Intelligent shortage detection** with urgency classification
- **Vendor scoring and ranking** algorithms
- **Budget analysis** and cost optimization
- **Risk assessment** and procurement recommendations

#### 🌐 **Web Server (`web_server.py`)**
- **Flask web application** with comprehensive routing
- **RESTful API** endpoints for all operations
- **WebSocket support** for real-time updates
- **Webhook handlers** for Twilio integration

## 🚀 Quick Start

### **Prerequisites**
- Python 3.8 or higher
- Twilio account (for voice/WhatsApp features)
- Gemini AI API key (for dynamic content)
- ngrok (for webhook tunneling)

### **Installation**

1. **Clone and setup:**
```bash
git clone <repository-url>
cd procurement-conversational
pip install -r requirements.txt
```

2. **Environment Configuration:**
Create a `.env` file or set environment variables:
```bash
export GEMINI_API_KEY="your_gemini_api_key"
export TWILIO_ACCOUNT_SID="your_twilio_sid"
export TWILIO_AUTH_TOKEN="your_twilio_token"
export TWILIO_FROM_NUMBER="+1234567890"
export TWILIO_WHATSAPP_NUMBER="whatsapp:+14155238886"
```

3. **Start the Platform:**
```bash
python main.py
```

### **First Launch Experience**

The platform will automatically:
- ✅ Validate your environment and dependencies
- ✅ Initialize all components with comprehensive error handling
- ✅ Create sample companies and vendors for testing
- ✅ Start the web server on `http://localhost:5000`
- ✅ Attempt to start ngrok tunnel for webhook access
- ✅ Show comprehensive system status

## 🎛️ Usage Guide

### **Interactive Control Center**

The platform provides a comprehensive control center with 14 options:

1. **📊 System Status** - Health check and component status
2. **🏢 View Companies** - Company inventory and status overview
3. **🤝 View Vendors** - Vendor performance and ratings
4. **🛒 Procurement Analysis** - Real-time shortage analysis
5. **📞 Test Voice Calls** - Test Twilio voice functionality
6. **📱 Test WhatsApp** - Test WhatsApp integration
7. **💬 View Conversations** - Recent AI conversation logs
8. **📈 Analytics Dashboard** - Open web dashboard
9. **🔧 System Configuration** - View environment settings
10. **🌐 Web Dashboard** - Open browser dashboard
11. **📋 Export Data** - Export to CSV format
12. **🔄 Restart Components** - Component management
13. **❓ Help** - Comprehensive help documentation
14. **🛑 Shutdown** - Graceful platform shutdown

### **Web Dashboard Access**

- **Local**: `http://localhost:5000`
- **Public** (if ngrok): Automatically displayed during startup
- **Mobile-friendly**: Responsive design for all devices

### **API Endpoints**

The platform exposes comprehensive RESTful APIs:

```
GET  /api/stats              # System statistics
GET  /api/companies          # Company data
GET  /api/vendors            # Vendor information
POST /api/calls/initiate     # Start voice call
POST /api/whatsapp/send      # Send WhatsApp message
POST /api/procurement/analyze # Run procurement analysis
GET  /api/calls/{sid}/status # Call status tracking
```

## 🔧 Configuration

### **Twilio Setup**
1. Create a [Twilio account](https://twilio.com)
2. Get your Account SID and Auth Token
3. Purchase a phone number for voice calls
4. Enable WhatsApp sandbox or get approved number

### **Gemini AI Setup**
1. Get API key from [Google AI Studio](https://makersuite.google.com)
2. Set the `GEMINI_API_KEY` environment variable
3. The system includes comprehensive fallbacks if AI is unavailable

### **ngrok Setup (Optional)**
1. Install [ngrok](https://ngrok.com)
2. The platform will auto-start ngrok for webhook access
3. Manual URL configuration is supported

## 📊 Sample Data

The platform includes comprehensive sample data:

### **Companies**
- **Bio Mac Lifesciences** (Biotech, ₹5L budget)
- **Pharma Research Institute** (Pharmaceutical, ₹7.5L budget)  
- **Advanced Medical Diagnostics** (Healthcare, ₹3L budget)

### **Vendors**
- **Lab Supply Pro** (4.5★, Laboratory Consumables)
- **Scientific Corporation** (4.2★, Chemicals & Equipment)
- **Chemical Solutions Ltd** (4.7★, Laboratory Chemicals)
- **Medical Supply Chain** (4.3★, Medical Supplies)
- **Lab Equipment Ltd** (3.9★, Laboratory Equipment)

### **Inventory Items**
Complete inventory with stock levels, pricing, and procurement requirements across all categories.

## 🚨 Error Handling & Fallbacks

### **Comprehensive Error Management**
- **Database**: Automatic backup and recovery
- **AI Services**: Predefined fallback responses
- **Communication**: WhatsApp fallback for failed calls
- **Web Server**: Graceful error pages and API responses
- **Platform**: Automatic component restart and health monitoring

### **Fallback Mechanisms**
- **AI Unavailable**: Pre-defined intelligent responses
- **Twilio Errors**: Detailed error reporting and retry logic
- **Network Issues**: Offline mode with data sync
- **Component Failures**: Isolated error handling

## 🔍 Monitoring & Analytics

### **Real-time Monitoring**
- Live conversation tracking
- System health monitoring
- Performance metrics
- Budget utilization alerts

### **Analytics Dashboard**
- Interactive charts and graphs
- Procurement trend analysis
- Vendor performance metrics
- Company-wise breakdowns

## 🛠️ Development

### **Architecture Principles**
- **Modular Design**: Clean separation of concerns
- **Error Resilience**: Comprehensive error handling
- **Scalability**: Thread-safe, stateless design
- **Maintainability**: Clear documentation and structure

### **Adding New Features**
1. **Models**: Add data structures to `models.py`
2. **Business Logic**: Implement in appropriate service modules
3. **API Endpoints**: Add routes to `web_server.py`
4. **Frontend**: Update templates and JavaScript
5. **Testing**: Use the interactive control center

### **Database Schema**
The platform uses a flexible JSON-based schema with automatic migrations and backup.

## 📈 Performance

### **Optimizations**
- Efficient data structures with caching
- Asynchronous communication handling
- Real-time updates via WebSockets
- Lazy loading and pagination

### **Scalability**
- Thread-safe operations
- Modular component architecture
- RESTful API design
- Horizontal scaling ready

## 🔐 Security

### **Data Protection**
- Environment variable configuration
- Secure credential handling
- Input validation and sanitization
- Error message sanitization

### **Communication Security**
- Twilio webhook validation
- Secure API endpoints
- HTTPS support (with proper deployment)

## 🚀 Deployment

### **Production Deployment**
1. Set up proper environment variables
2. Configure reverse proxy (nginx)
3. Use WSGI server (gunicorn)
4. Set up SSL certificates
5. Configure domain for webhooks

### **Docker Support**
```dockerfile
# Dockerfile example for containerization
FROM python:3.9-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### **Troubleshooting**
- Use the system status check (#1 in control center)
- Verify environment variables and API keys
- Check network connectivity for webhooks
- Review logs in the control center

### **Common Issues**
- **Twilio calls failing**: Check credentials and phone number format
- **AI responses generic**: Verify Gemini API key
- **Webhooks not working**: Ensure ngrok is running
- **Database errors**: Check file permissions in data directory

### **Getting Help**
- Check the help documentation (#13 in control center)
- Review error messages in the platform logs
- Use the interactive troubleshooting tools
- Check component health status

---

**🎉 Built with ❤️ for efficient procurement management**

Transform your procurement operations with AI-powered intelligence, real-time communication, and comprehensive analytics. The platform scales from small businesses to enterprise operations with its modular, resilient architecture. 