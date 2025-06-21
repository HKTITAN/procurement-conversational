# Master Speech Recognition System Launcher
Write-Host "🚀 MASTER SPEECH RECOGNITION SYSTEM" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "This comprehensive system will:" -ForegroundColor Cyan
Write-Host "✅ 1. Automatically start ngrok tunnel" -ForegroundColor White
Write-Host "✅ 2. Start speech recognition webhook server" -ForegroundColor White
Write-Host "✅ 3. Provide LIVE FEEDBACK during calls" -ForegroundColor White
Write-Host "✅ 4. Extract requirements automatically using Gemini AI" -ForegroundColor White
Write-Host "✅ 5. Log all conversations with structured data" -ForegroundColor White
Write-Host ""
Write-Host "🎤 LIVE FEEDBACK FEATURES:" -ForegroundColor Magenta
Write-Host "   • Real-time speech recognition display" -ForegroundColor Gray
Write-Host "   • Automatic requirement extraction (items, prices, delivery)" -ForegroundColor Gray
Write-Host "   • Intelligent AI response generation" -ForegroundColor Gray
Write-Host "   • Color-coded terminal output" -ForegroundColor Gray
Write-Host "   • JSON export of all conversations" -ForegroundColor Gray
Write-Host ""

$continue = Read-Host "Ready to start the master system? (y/N)"

if ($continue -eq 'y' -or $continue -eq 'Y') {
    Write-Host ""
    Write-Host "🔧 Checking prerequisites..." -ForegroundColor Yellow
    
    # Check if Python is available
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Python not found! Please install Python first." -ForegroundColor Red
        Read-Host "Press any key to exit"
        exit
    }
    
    # Check if ngrok is available
    try {
        $ngrokVersion = ngrok version 2>&1
        Write-Host "✅ Ngrok found: $ngrokVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Ngrok not found! Please install ngrok first." -ForegroundColor Red
        Read-Host "Press any key to exit"
        exit
    }
    
    Write-Host ""
    Write-Host "🚀 Starting Master Speech Recognition System..." -ForegroundColor Green
    Write-Host "   Watch for live feedback during calls!" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        # Run the master system
        python master_speech_system.py
    } catch {
        Write-Host ""
        Write-Host "❌ Error running master system: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "👋 Cancelled by user" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press any key to exit" 