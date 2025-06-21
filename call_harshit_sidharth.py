#!/usr/bin/env python3
"""
Direct caller for Harshit Khemani and Sidharth Sharma
Uses the improved master system with intelligent speech recognition
"""

import os
import sys
import time
import threading
import subprocess
import requests
import base64
import json
import csv
from datetime import datetime
from flask import Flask, request, Response
import google.generativeai as genai

# Import the improved master system
from improved_master_system import (
    app, model, print_live_feedback, start_ngrok, start_webhook_server,
    call_multiple_contacts, CONTACT_LIST, ngrok_url, required_items
)

def main():
    """Direct call to both Harshit and Sidharth"""
    print("📞 CALLING HARSHIT KHEMANI & SIDHARTH SHARMA")
    print("🧠 Using Improved Master System with AI")
    print("=" * 60)
    
    # Target contacts
    target_contacts = ["Harshit Khemani", "Sidharth Sharma"]
    
    # Verify contacts exist
    print("📋 VERIFYING CONTACTS:")
    for contact in target_contacts:
        if contact in CONTACT_LIST:
            phone = CONTACT_LIST[contact]
            print(f"✅ {contact}: {phone}")
        else:
            print(f"❌ {contact}: Not found!")
            return
    
    print("\n🚀 STARTING SYSTEM...")
    
    # Step 1: Start ngrok
    print_live_feedback("Starting ngrok tunnel...", "INFO")
    ngrok_process, ngrok_url_result = start_ngrok()
    
    if not ngrok_url_result:
        print_live_feedback("❌ Could not start ngrok automatically", "ERROR")
        manual_url = input("Enter your ngrok URL (e.g., https://abc123.ngrok.io): ").strip()
        if manual_url:
            ngrok_url_result = manual_url
        else:
            print_live_feedback("No ngrok URL provided. Exiting.", "ERROR")
            return
    
    # Step 2: Start webhook server
    print_live_feedback("Starting webhook server...", "INFO")
    server_thread = threading.Thread(target=start_webhook_server, daemon=True)
    server_thread.start()
    time.sleep(3)
    
    # Step 3: Make the calls
    print_live_feedback("="*60, "INFO")
    print_live_feedback("INITIATING CALLS TO BOTH CONTACTS", "CALL")
    print_live_feedback(f"Items to collect: {', '.join(required_items)}", "INFO")
    print_live_feedback("="*60, "INFO")
    
    # Ask for delay between calls
    delay_input = input("\nDelay between calls in seconds (default 30): ").strip()
    try:
        delay = int(delay_input) if delay_input else 30
    except ValueError:
        delay = 30
    
    print(f"\n⏰ Will wait {delay} seconds between calls")
    print("🎯 Each call will automatically collect procurement quotes")
    print("📊 All data will be saved to CSV automatically")
    
    # Confirm before proceeding
    confirm = input("\nProceed with calls? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled by user")
        return
    
    # Make the calls
    successful_calls = call_multiple_contacts(target_contacts, ngrok_url_result, delay)
    
    # Report results
    print("\n" + "="*60)
    print("📊 CALL RESULTS")
    print("="*60)
    
    if successful_calls:
        print(f"✅ Successfully initiated {len(successful_calls)} calls:")
        for call_info in successful_calls:
            print(f"   📞 {call_info['name']}: {call_info['phone']}")
            print(f"      Call SID: {call_info['call_sid']}")
            print(f"      Time: {call_info['timestamp']}")
        
        print("\n🎤 LIVE MONITORING:")
        print("   • Watch terminal for real-time speech recognition")
        print("   • AI will automatically ask for each item")
        print("   • Data will be saved to CSV automatically")
        print(f"   • Dashboard: {ngrok_url_result}")
        
        print("\n⏳ Calls are now active. Press Ctrl+C to stop monitoring...")
        
        try:
            # Keep the script running to monitor calls
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n👋 Stopping monitoring. Calls may still be active.")
    else:
        print("❌ No calls were successful")
    
    # Cleanup
    if ngrok_process:
        ngrok_process.terminate()

if __name__ == "__main__":
    main() 