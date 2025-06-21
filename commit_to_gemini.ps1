# PowerShell script to commit changes to gemini branch
Write-Host "🚀 COMMITTING CHANGES TO GEMINI BRANCH" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Yellow

# Check current directory
$currentDir = Get-Location
Write-Host "📁 Current directory: $currentDir" -ForegroundColor Cyan

# Check if we're in a git repository
if (Test-Path ".git") {
    Write-Host "✅ Git repository found" -ForegroundColor Green
} else {
    Write-Host "❌ Not in a git repository!" -ForegroundColor Red
    Read-Host "Press any key to exit"
    exit
}

# Check current branch
try {
    $currentBranch = git branch --show-current
    Write-Host "📋 Current branch: $currentBranch" -ForegroundColor White
    
    # Switch to gemini branch if not already on it
    if ($currentBranch -ne "gemini") {
        Write-Host "🔄 Switching to gemini branch..." -ForegroundColor Yellow
        git checkout gemini
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️ Creating new gemini branch..." -ForegroundColor Yellow
            git checkout -b gemini
        }
    }
} catch {
    Write-Host "❌ Error checking git branch: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press any key to exit"
    exit
}

# Show git status
Write-Host "`n📊 Git Status:" -ForegroundColor Cyan
git status --short

# Add all files
Write-Host "`n📁 Adding all files..." -ForegroundColor Yellow
git add .

# Show what will be committed
Write-Host "`n📋 Files to be committed:" -ForegroundColor Cyan
git status --short

# Create comprehensive commit message
$commitMessage = @"
feat: Complete Gemini AI Speech Recognition System

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
- call_now.bat - Windows batch launcher
- run_master_system.bat - System launcher
- MakeCall.ps1 - PowerShell calling script
- RunMasterSystem.ps1 - PowerShell system launcher
- commit_to_gemini.ps1 - Git commit automation

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
processing to AI-powered intelligent conversation system.
"@

# Commit changes
Write-Host "`n💾 Committing changes..." -ForegroundColor Green
git commit -m $commitMessage

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ COMMIT SUCCESSFUL!" -ForegroundColor Green
    Write-Host "🌟 All Gemini AI features have been committed to the gemini branch" -ForegroundColor Cyan
    
    # Show commit info
    Write-Host "`n📋 Commit Details:" -ForegroundColor Yellow
    git log --oneline -1
    
    # Ask about pushing
    $push = Read-Host "`nPush to remote gemini branch? (y/N)"
    if ($push -eq 'y' -or $push -eq 'Y') {
        Write-Host "`n📤 Pushing to remote..." -ForegroundColor Yellow
        git push origin gemini
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Successfully pushed to remote gemini branch!" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Push failed - you may need to set up remote first" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "`n❌ COMMIT FAILED!" -ForegroundColor Red
    Write-Host "Check the error messages above" -ForegroundColor Yellow
}

Write-Host "`n🎉 GEMINI BRANCH COMMIT COMPLETE!" -ForegroundColor Green
Read-Host "Press any key to exit" 