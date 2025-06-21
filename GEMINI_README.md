# 🤖 Gemini-Enhanced Bilingual Webhook System

An intelligent voice conversation system that combines **Google Gemini 2.0 AI** with **Twilio Voice** to create natural, context-aware conversations in Hindi, English, and Hinglish for procurement quote collection.

## ✨ Key Features

### 🧠 **Intelligent Conversation Understanding**
- **Context Awareness**: Understands what users really mean, not just what they say
- **Intent Analysis**: Recognizes emotions, confusion, agreement, pricing, questions
- **Smart Response Generation**: Creates natural, contextually appropriate responses
- **Conversation Memory**: Maintains conversation history and context

### 🗣️ **Natural Bilingual Communication**
- **Hindi-English-Hinglish Mix**: Handles code-switching naturally
- **Cultural Understanding**: Knows Indian business communication patterns
- **Realistic Flow**: Adapts to interruptions, clarifications, side conversations
- **Voice Activity Detection**: Can handle interruptions naturally

### 💰 **Enhanced Quote Processing**
- **Smart Price Extraction**: Uses AI to understand pricing in context
- **Confidence Scoring**: Rates how sure it is about extracted information
- **Contextual Understanding**: "Same as before", "usual rate", implicit pricing
- **Structured Logging**: Enhanced CSV logging with AI insights

## 🚀 Quick Start

### 1. **Get Your Gemini API Key**
```bash
# Go to https://aistudio.google.com/
# Sign in and create an API key
export GEMINI_API_KEY="your_api_key_here"
```

### 2. **Install & Setup**
```bash
# Run the setup script
python setup_gemini.py

# Or manually install dependencies
pip install -r requirements.txt
```

### 3. **Configure**
```bash
# Copy and edit configuration
cp gemini_config_example.py gemini_config.py
# Edit gemini_config.py with your API key
```

### 4. **Run**
```bash
# Start the enhanced webhook server
python gemini_enhanced_webhook.py
```

### 5. **Test**
```bash
# Check health
curl http://localhost:5000/health

# View conversation insights
curl http://localhost:5000/quotes
```

## 🔧 Configuration Options

### Environment Variables
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (for Vertex AI instead)
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Optional (for Twilio)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
```

## 🎯 How It Works

### Traditional vs Gemini-Enhanced Flow

**Traditional Approach:**
```
User speaks → Basic speech recognition → Fixed response → Log
```

**Gemini-Enhanced Approach:**
```
User speaks → AI Analysis → Context Understanding → Intelligent Response → Enhanced Logging
     ↓              ↓               ↓                    ↓                  ↓
- Raw text    - Intent analysis  - Conversation    - Natural flow     - Confidence scores
- Language    - Emotion detection  context         - Cultural adapt   - AI insights
- Basic price - Price extraction  - Memory         - Dynamic TwiML    - Structured context
```

### AI Analysis Pipeline

1. **Speech Intent Analysis**
   ```python
   {
     "intent": "quote_given",
     "extracted_price": 25.0,
     "item_discussed": "Petri dishes",
     "emotional_tone": "cooperative",
     "confidence": 0.85
   }
   ```

2. **Context-Aware Response Generation**
   ```python
   {
     "hindi_text": "Samjha sir, Petri dishes 25 rupees per piece. Bahut accha rate hai.",
     "english_text": "Got it sir, Petri dishes 25 rupees per piece. Very good rate.",
     "action": "continue_to_next_item",
     "confidence": 0.9
   }
   ```

3. **Enhanced Logging**
   ```csv
   timestamp,vendor,item,price,currency,speech,confidence,context,ai_insights
   2024-01-15T10:30:00,Harshit,Petri Dishes,25.0,INR,"twenty five rupees",0.85,"{conversation_context}","gemini_enhanced"
   ```

## 📊 Conversation Examples

### Example 1: Natural Price Quote
```
🤖: "Petri dishes ka rate batayiye sir. Per piece kitne rupees?"
👤: "Bees paanch rupaye mein de sakte hain" (Twenty-five rupees)

AI Analysis:
- Intent: quote_given
- Price: 25.0 (high confidence)
- Language: Hindi-primary
- Tone: cooperative

Response:
🤖: "Samjha sir, Petri dishes 25 rupees per piece. Bahut accha rate hai!"
```

### Example 2: Handling Confusion
```
🤖: "Laboratory gloves ka rate per piece batayiye sir."
👤: "Kya? Kaun sa gloves? Size kya hai?" (What? Which gloves? What size?)

AI Analysis:
- Intent: confusion/question
- Needs: clarification
- Tone: confused

Response:
🤖: "Sorry sir, nitrile gloves, powder-free, medium size. Laboratory use ke liye. Rate kya hai?"
```

### Example 3: Implicit Pricing
```
🤖: "Next item sir - Laboratory gloves..."
👤: "Same rate sir, twenty five only"

AI Analysis:
- Intent: quote_given
- Price: 25.0 (inferred from context)
- Reference: "same as previous item"
- Confidence: 0.75

Response:
🤖: "Perfect! Gloves bhi 25 rupees per piece. Consistent pricing, very good!"
```

## 🛠️ Advanced Features

### Custom System Instructions
The AI understands Indian business culture:
```python
system_instruction="""
You are conducting professional yet friendly conversations with Indian vendors.
- Understand Hindi-English code-switching
- Handle interruptions and clarifications naturally  
- Be polite but persistent in getting accurate quotes
- Adapt to vendor's communication style
"""
```

### Conversation Context Management
```python
context = {
    'conversation_stage': 'price_discussion',
    'current_item': 'Petri Dishes 100mm',
    'expected_quantity': 30,
    'vendor_mood': 'cooperative',
    'quotes_received': [...]
}
```

### Intelligent Price Extraction
```python
# Handles complex pricing scenarios:
"Bees paanch rupaye" → 25.0
"Same as before" → (uses context)
"Around twenty five" → 25.0 (confidence: 0.7)
"Twenty to twenty five range" → 22.5 (confidence: 0.6)
```

## 📈 Benefits Over Traditional System

| Feature | Traditional | Gemini-Enhanced |
|---------|-------------|-----------------|
| **Understanding** | Literal text matching | Contextual AI analysis |
| **Response Quality** | Fixed scripts | Dynamic, natural responses |
| **Price Extraction** | Regex patterns | AI-powered context understanding |
| **Language Handling** | Basic Hindi/English | Natural code-switching |
| **Error Recovery** | Limited fallbacks | Intelligent clarification |
| **Learning** | Static | Conversation memory & adaptation |
| **Insights** | Basic logs | Rich conversation analytics |

## 🔍 Monitoring & Analytics

### Health Check Endpoint
```bash
GET /health
{
  "status": "healthy",
  "ai_engine": "Google Gemini 2.0 Flash", 
  "features": ["intelligent_conversation", "context_awareness"],
  "gemini_status": "connected"
}
```

### Enhanced Quote Logs
```bash
GET /quotes
# Shows:
- Conversation transcripts
- AI analysis insights  
- Confidence scores
- Context evolution
- Performance metrics
```

## 🚨 Troubleshooting

### Common Issues

1. **API Key Not Working**
   ```bash
   # Check if key is valid
   curl -H "Authorization: Bearer $GEMINI_API_KEY" \
        https://generativelanguage.googleapis.com/v1beta/models
   ```

2. **Dependencies Issues**
   ```bash
   # Clean install
   pip uninstall google-generativeai google-genai
   pip install -r requirements.txt
   ```

3. **Audio Processing Issues**
   ```bash
   # Install audio dependencies
   # On Ubuntu/Debian:
   sudo apt-get install portaudio19-dev python3-pyaudio
   
   # On macOS:
   brew install portaudio
   ```

### Debug Mode
```python
# Add to gemini_enhanced_webhook.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📞 Twilio Integration

### Webhook Configuration
```bash
# Set your Twilio webhook URL to:
https://your-domain.com/webhook/voice

# Or for local testing with ngrok:
ngrok http 5000
# Then use: https://your-ngrok-url.ngrok.io/webhook/voice
```

### TwiML Flow
```
/webhook/voice → Initial greeting
/webhook/gather_gemini → AI-enhanced response processing  
/webhook/item1_gemini → Smart first item handling
/webhook/item2_gemini → Intelligent conversation closure
```

## 🔐 Security & Best Practices

### API Key Security
```python
# ✅ Good: Environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# ❌ Bad: Hardcoded in source
GEMINI_API_KEY = "actual_key_here"
```

### Rate Limiting
- Gemini API has built-in rate limits
- Monitor usage in Google AI Studio
- Implement exponential backoff for errors

### Data Privacy
- Conversation logs contain sensitive business data
- Ensure secure storage and access controls
- Consider data retention policies

## 🛣️ Roadmap

### Planned Enhancements
- [ ] **Real-time Audio Streaming** with Gemini Live API
- [ ] **Multi-vendor Context** tracking across calls
- [ ] **Sentiment Analysis** for vendor relationship insights
- [ ] **Automated Quote Comparison** and recommendations
- [ ] **Voice Synthesis** using Gemini's native audio
- [ ] **Advanced Function Calling** for external integrations

### Integration Possibilities
- [ ] CRM systems integration
- [ ] Purchase order automation  
- [ ] Inventory management sync
- [ ] Analytics dashboard
- [ ] Mobile app companion

## 📝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Google Gemini Team** for the powerful AI capabilities
- **Twilio** for robust voice infrastructure
- **Indian Business Community** for inspiration and use case validation

---

**Made with ❤️ for the Indian business ecosystem**

🤖 **"Namaste ji! Ab AI ke saath business kijiye!"** 🇮🇳 