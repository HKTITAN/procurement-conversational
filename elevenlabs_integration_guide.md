# 🎤 ElevenLabs Conversational AI Integration Guide

## Overview

Your Multi-Company Procurement Platform now includes **ElevenLabs Conversational AI** integration, providing advanced voice agents with real-time speech processing, intelligent conversation management, and seamless webhook integration with Gemini AI for data extraction and CSV recording.

## 🚀 What's New

### ElevenLabs Features Integrated:
- **Advanced Voice Agents** - Professional conversation management
- **Real-time Speech Processing** - Instant transcription and response
- **Dynamic Context Generation** - Personalized conversations based on procurement needs
- **Intelligent Conversation Summaries** - AI-generated business reports
- **Multi-Platform Analytics** - Combined ElevenLabs + Twilio + WhatsApp insights
- **Enhanced CSV Exports** - Business intelligence from voice conversations

### Architecture:
```
ElevenLabs Agent → Webhooks → Gemini Processing → CSV Recording
     ↓                ↓            ↓              ↓
Voice Calls     Real-time      Data          Business
                Events      Extraction     Intelligence
```

## 🔧 Setup Instructions

### 1. Get ElevenLabs API Key

1. **Sign up at ElevenLabs:**
   - Visit: https://elevenlabs.io
   - Create account and verify email
   - Navigate to **Conversational AI** section

2. **Get API Key:**
   - Go to **Profile** → **API Keys**
   - Generate new API key
   - Copy the key (starts with `sk-...`)

3. **Update Configuration:**
   ```python
   # In master_speech_system.py, line 18:
   ELEVENLABS_API_KEY = "sk-your-actual-api-key-here"
   ```

### 2. Create Your First Agent

1. **Run the system:**
   ```bash
   python master_speech_system.py
   ```

2. **Create Agent:**
   - Choose option `10` (ElevenLabs Agent Management)
   - Select `1` (Create New Agent)
   - Copy the generated Agent ID

3. **Update Agent Configuration:**
   ```python
   # In master_speech_system.py, line 19:
   ELEVENLABS_AGENT_ID = "your-agent-id-here"
   ```

### 3. Configure Webhooks

1. **Set up ngrok (already integrated):**
   - The system automatically starts ngrok
   - Webhook URL: `https://your-ngrok-url.ngrok.io/webhook/elevenlabs`

2. **ElevenLabs Agent Configuration:**
   - The agent is automatically configured with your webhook URL
   - Events tracked: conversation start, transcripts, responses, end

### 4. Test the Integration

1. **Make an ElevenLabs AI Call:**
   - Choose option `4` (ElevenLabs AI Call)
   - Enter phone number
   - The AI agent will make an intelligent procurement call

2. **Monitor Real-time Processing:**
   - Watch console for live feedback
   - Gemini processes speech in real-time
   - CSV data is automatically recorded

## 📊 Enhanced Analytics

### Multi-Platform Dashboard

Access comprehensive analytics at: `http://your-ngrok-url/`

**New Analytics Include:**
- ElevenLabs conversation metrics
- Voice quality and confidence scores
- AI-generated conversation summaries
- Cross-platform performance comparison
- Enhanced business intelligence exports

### CSV Export Features

**Enhanced Quotation Data:**
- Platform tracking (ElevenLabs vs Legacy)
- Conversation confidence scores
- Detailed business terms extraction
- AI summary quality ratings
- Multi-channel vendor tracking

## 🎯 Key Features Explained

### 1. Dynamic Context Generation

**Before each call, the system:**
- Analyzes current inventory shortages
- Identifies urgent procurement needs
- Generates personalized company context
- Customizes agent prompts in real-time

```python
company_context = {
    'company_name': 'Bio Mac Lifesciences',
    'industry': 'Biotechnology',
    'urgent_items': ['Microscope Slides', 'Petri Dishes'],
    'budget': 500000
}
```

### 2. Intelligent Speech Processing

**Real-time Pipeline:**
1. **ElevenLabs** captures and transcribes speech
2. **Webhook** receives transcript with confidence scores
3. **Gemini AI** extracts business data and pricing
4. **CSV Recording** saves structured quotation data
5. **Context Tracking** maintains conversation state

### 3. Enhanced Conversation Summaries

**AI-Generated Reports Include:**
- Vendor information and contact details
- Complete product catalog discussed
- Detailed pricing information
- Business terms (delivery, payment, discounts)
- Vendor assessment and recommendations
- Follow-up action items
- Quote quality rating (1-10)

## 🔄 Workflow Integration

### ElevenLabs vs Legacy Calls

**ElevenLabs AI Calls (Recommended):**
- Advanced conversation management
- Better speech recognition
- Real-time processing
- Professional voice quality
- Intelligent turn-taking

**Legacy Twilio Calls:**
- Basic speech recognition
- Manual conversation flow
- WhatsApp fallback on failure
- Good for simple inquiries

### WhatsApp Integration

**Maintained Features:**
- Auto-fallback for failed calls
- Direct WhatsApp messaging
- Cross-channel conversation tracking
- Unified analytics dashboard

## 📋 Menu Navigation

### Updated Menu Options:

1. **🏢 Companies & Inventory** - View procurement needs
2. **🛒 Procurement Analysis** - Identify urgent requirements
3. **🤝 Vendors & Ratings** - Manage vendor database
4. **☎️ Intelligent Call System** - **ENHANCED:** Choose TTS or ElevenLabs
5. **📱 WhatsApp Message** - Direct messaging
6. **🔄 Auto Procurement** - Automated analysis
7. **💰 Price Comparisons** - Vendor pricing analysis
8. **📊 Multi-Platform Analytics** - **ENHANCED:** All platforms
9. **🤖 ElevenLabs Agent Management** - **NEW:** Agent control
10. **📈 System Status** - **ENHANCED:** Multi-platform status
11. **🔧 WhatsApp Setup** - Communication setup
12. **📋 Export Data** - **ENHANCED:** Comprehensive exports
13. **🌐 Web Dashboard** - **ENHANCED:** Multi-platform UI
14. **🔑 API Credentials** - **NEW:** Manage all API keys
15. **Exit** - Shutdown system

## 🚨 Troubleshooting

### Common Issues:

**1. ElevenLabs API Key Invalid:**
```
❌ ElevenLabs API key not configured!
```
**Solution:** Update `ELEVENLABS_API_KEY` in the code

**2. Agent Creation Failed:**
```
❌ Failed to create agent: 401 Unauthorized
```
**Solution:** Verify API key is correct and has Conversational AI access

**3. Webhooks Not Received:**
```
No webhook events received
```
**Solution:** 
- Ensure ngrok is running
- Check webhook URL in agent configuration
- Verify firewall settings

**4. Gemini Processing Errors:**
```
❌ Summary generation failed
```
**Solution:** Check Gemini API key and model availability

### Debug Mode:

Monitor real-time processing:
```bash
# Watch for webhook events
tail -f live_conversation_log.json

# Check CSV exports
ls -la vendor_quotations_*.csv
```

## 🎯 Best Practices

### 1. Agent Configuration
- Use professional, business-appropriate prompts
- Set appropriate conversation timeouts (180 seconds)
- Configure interruption sensitivity for natural flow

### 2. Data Quality
- Monitor extraction confidence scores
- Review AI-generated summaries for accuracy
- Validate pricing information manually

### 3. Performance Optimization
- Use ElevenLabs for important vendor calls
- Reserve legacy calls for basic inquiries
- Leverage WhatsApp for follow-ups

### 4. Business Intelligence
- Export data regularly for analysis
- Track vendor response patterns
- Monitor conversation success rates

## 🔮 Future Enhancements

**Planned Features:**
- Multi-voice agent support for different companies
- Advanced sentiment analysis
- Automated follow-up scheduling
- Integration with procurement systems
- Voice biometric vendor identification
- Multi-language support for international vendors

## 📞 Support

**Integration Support:**
- ElevenLabs Documentation: https://elevenlabs.io/docs/conversational-ai
- Gemini AI Guide: https://ai.google.dev/docs
- System Issues: Check console logs and webhook endpoints

**Business Logic:**
- Procurement workflows
- Inventory management
- Vendor relationship management
- Quote comparison and analysis

---

**Your procurement platform is now powered by cutting-edge AI voice technology! 🚀** 