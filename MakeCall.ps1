# PowerShell script to make Twilio call
Write-Host "📞 MAKING CALL TO YOU NOW!" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Yellow

# Twilio credentials
$account_sid = "AC820daae89092e30fee3487e80162d2e2"
$auth_token = "690636dcdd752868f4e77648dc0d49eb"
$from_number = "+14323484517"
$to_number = "+918800000488"

# TwiML content
$twiml = @"
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">
        Namaste! Main Bio Mac Lifesciences se bol raha hun. 
        Hum laboratory supplies ki company hain.
        Humein petri dishes, gloves aur slides chahiye.
        Aapka rate kya hai?
    </Say>
    <Pause length="3"/>
    <Say voice="Polly.Aditi" language="hi-IN">
        Please bataiye pricing. Main sun raha hun.
    </Say>
    <Pause length="5"/>
    <Say voice="Polly.Aditi" language="hi-IN">
        Dhanyawad sir! Main call back karunga.
    </Say>
    <Hangup/>
</Response>
"@

# API endpoint
$url = "https://api.twilio.com/2010-04-01/Accounts/$account_sid/Calls.json"

# Authentication
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("$account_sid:$auth_token"))

# Headers
$headers = @{
    Authorization = "Basic $auth"
    "Content-Type" = "application/x-www-form-urlencoded"
}

# Body
$body = @{
    From = $from_number
    To = $to_number
    Twiml = $twiml
    Record = "true"
}

try {
    Write-Host "📞 Calling $to_number..." -ForegroundColor Cyan
    Write-Host "🏢 From: Bio Mac Lifesciences ($from_number)" -ForegroundColor White
    Write-Host "⏰ $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
    
    $response = Invoke-RestMethod -Uri $url -Method POST -Headers $headers -Body $body
    
    Write-Host ""
    Write-Host "✅ CALL STARTED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "🆔 Call SID: $($response.sid)" -ForegroundColor White
    Write-Host "📊 Status: $($response.status)" -ForegroundColor White
    Write-Host ""
    Write-Host "📱 YOUR PHONE SHOULD RING NOW!" -ForegroundColor Yellow
    Write-Host "🎧 Answer and listen to the procurement call" -ForegroundColor Cyan
    Write-Host "⏱️ Duration: ~30-60 seconds" -ForegroundColor Gray
    
} catch {
    Write-Host ""
    Write-Host "❌ CALL FAILED!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 