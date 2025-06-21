@echo off
echo ========================================
echo COMMITTING TO GEMINI BRANCH ON GITHUB
echo ========================================
echo.

echo Checking current branch...
git branch --show-current

echo.
echo Switching to gemini branch...
git checkout gemini
if errorlevel 1 (
    echo Creating new gemini branch...
    git checkout -b gemini
)

echo.
echo Adding all files...
git add .

echo.
echo Current status:
git status --short

echo.
echo Committing changes...
git commit -m "feat: Complete Gemini AI Speech Recognition System

🎤 Major Features Added:
- Master speech recognition system with live feedback
- Improved speech processing with item progression
- Automatic CSV recording of procurement quotes
- Real-time terminal feedback with color coding
- Smart conversation flow that doesn't get stuck in loops

📁 New Files:
- master_speech_system.py - Complete system orchestration
- improved_master_system.py - Enhanced speech processing
- start_speech_server.py - Dedicated webhook server
- speech_demo_call.py - Demonstration system
- enable_speech_recognition.py - Setup guide
- direct_ngrok_call.py - Direct calling with ngrok
- ngrok_call.py - Ngrok-enabled calling
- quick_speech_call.py - Quick test calls
- make_call_now.py - Immediate calling
- Various launcher scripts (.bat, .ps1 files)

🧠 AI Enhancements:
- Gemini API integration for intelligent responses
- Speech-to-text processing with context awareness
- Automatic requirement extraction (items, prices, delivery)
- Hindi-English bilingual conversation support
- Smart progression through procurement items

📊 Data Management:
- Structured CSV export with all procurement details
- Real-time conversation logging
- Automatic price and requirement extraction
- Call status tracking and monitoring

🔧 Technical Improvements:
- Ngrok integration for public webhook access
- Flask webhook server with proper endpoints
- Twilio speech recognition integration
- Live terminal feedback system
- Error handling and fallback mechanisms

✅ System Capabilities:
- Makes real calls with natural Hindi voice
- Understands mixed Hindi-English responses
- Records pricing, minimum orders, delivery times
- Progresses through items systematically
- Concludes calls professionally when complete
- Saves all data to CSV for analysis

This represents a complete transformation from basic regex-based 
processing to AI-powered intelligent conversation system."

echo.
echo Pushing to GitHub...
git push origin gemini

echo.
echo ========================================
echo COMMIT TO GEMINI BRANCH COMPLETE!
echo ========================================
echo.
echo Your Gemini AI speech recognition system has been committed to GitHub!
echo.
pause 