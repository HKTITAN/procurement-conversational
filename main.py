#!/usr/bin/env python3
"""
Multi-Company Procurement Platform - Main Entry Point
Orchestrates all components with proper error handling and startup sequence
"""

import os
import sys
import time
import threading
import subprocess
import signal
from datetime import datetime

# Set up environment variables for Twilio (from working system)
if not os.getenv('TWILIO_ACCOUNT_SID'):
    os.environ['TWILIO_ACCOUNT_SID'] = 'AC820daae89092e30fee3487e80162d2e2'
    
if not os.getenv('TWILIO_AUTH_TOKEN'):
    os.environ['TWILIO_AUTH_TOKEN'] = '76d105c3d0bdee08cfc97117a7c05b32'
    
if not os.getenv('TWILIO_FROM_NUMBER'):
    os.environ['TWILIO_FROM_NUMBER'] = '+14323484517'
    
if not os.getenv('TWILIO_WHATSAPP_FROM'):
    os.environ['TWILIO_WHATSAPP_FROM'] = 'whatsapp:+14155238886'

# Set up Gemini API key if not already set
if not os.getenv('GEMINI_API_KEY'):
    os.environ['GEMINI_API_KEY'] = 'AIzaSyBCXNuaO9VlL5z1phh4mWGEVnnmRFk9TNg'

# Import our modules
from database import db
from ai_services import ai_service
from communication import comm_service
from procurement import procurement_engine
from web_server import web_server

class ProcurementPlatform:
    """Main platform orchestrator"""
    
    def __init__(self):
        self.ngrok_process = None
        self.ngrok_url = None
        self.running = False
        self.startup_errors = []
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def print_banner(self):
        """Print startup banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🏭 MULTI-COMPANY PROCUREMENT PLATFORM                     ║
║                                                              ║
║    AI-Powered Inventory Management                           ║
║    📞 Voice + WhatsApp Communication                         ║
║    📊 Real-Time Analytics & Insights                         ║
║    🤖 Intelligent Vendor Negotiations                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
        print(f"🕐 Startup Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
    
    def validate_environment(self):
        """Validate environment and dependencies"""
        print("🔍 Validating environment...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            self.startup_errors.append("Python 3.8 or higher required")
        
        # Check required modules (only essential ones)
        required_modules = [
            'flask', 'requests'
        ]
        
        optional_modules = [
            'google.generativeai', 'twilio', 'flask_socketio'
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                __import__(module.replace('.', '_') if '.' in module else module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            self.startup_errors.append(f"Missing essential modules: {', '.join(missing_modules)}")
        
        # Check optional modules and warn
        missing_optional = []
        for module in optional_modules:
            try:
                __import__(module.replace('.', '_') if '.' in module else module)
            except ImportError:
                missing_optional.append(module)
        
        if missing_optional:
            print(f"⚠️  Optional modules missing: {', '.join(missing_optional)}")
            print("   Some features will be limited. Install with: pip install -r requirements.txt")
        
        # Check environment variables
        gemini_key = os.getenv('GEMINI_API_KEY')
        if not gemini_key:
            print("⚠️  GEMINI_API_KEY not set - AI features will use fallbacks")
        
        if self.startup_errors:
            print("❌ Environment validation failed:")
            for error in self.startup_errors:
                print(f"   • {error}")
            return False
        
        print("✅ Environment validation passed")
        return True
    
    def initialize_components(self):
        """Initialize all platform components"""
        print("🔧 Initializing platform components...")
        
        try:
            # Initialize database first
            print("📊 Initializing database...")
            # Database is auto-initialized on import
            companies = db.get_all_companies()
            vendors = db.get_all_vendors()
            print(f"   ✅ Database ready: {len(companies)} companies, {len(vendors)} vendors")
            
            # Initialize AI services
            print("🤖 Initializing AI services...")
            ai_status = ai_service.get_health_status()
            if ai_status['model_available']:
                print("   ✅ Gemini AI ready for dynamic content generation")
            else:
                print("   ⚠️  AI in fallback mode - using predefined responses")
            
            # Initialize communication services
            print("📞 Initializing communication services...")
            comm_stats = comm_service.get_statistics()
            if comm_stats['credentials_valid']:
                print("   ✅ Twilio credentials validated - Voice & WhatsApp ready")
            else:
                print("   ⚠️  Twilio credentials invalid - Communication features disabled")
            
            # Initialize procurement engine
            print("🛒 Initializing procurement engine...")
            # Procurement engine is auto-initialized on import
            print("   ✅ Procurement analysis engine ready")
            
            # Initialize web server
            print("🌐 Initializing web server...")
            print("   ✅ Flask web server ready")
            
            return True
            
        except Exception as e:
            print(f"❌ Component initialization failed: {e}")
            return False
    
    def start_ngrok(self):
        """Start ngrok tunnel for webhooks"""
        print("🔗 Starting ngrok tunnel...")
        
        try:
            # Check if ngrok is available
            result = subprocess.run(['ngrok', 'version'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                print("⚠️  ngrok not found - webhook features will be limited")
                return False
            
            # Start ngrok tunnel
            self.ngrok_process = subprocess.Popen(
                ['ngrok', 'http', '5000', '--log=stdout'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for ngrok to start
            print("   ⏳ Waiting for ngrok tunnel...")
            time.sleep(3)
            
            # Get ngrok URL
            try:
                import requests
                response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
                if response.status_code == 200:
                    tunnels = response.json()['tunnels']
                    if tunnels:
                        self.ngrok_url = tunnels[0]['public_url']
                        web_server.set_ngrok_url(self.ngrok_url)
                        print(f"   ✅ Ngrok tunnel active: {self.ngrok_url}")
                        return True
            except:
                pass
            
            print("   ⚠️  Could not get ngrok URL automatically")
            manual_url = input("Enter ngrok URL manually (or press Enter to skip): ").strip()
            
            if manual_url:
                self.ngrok_url = manual_url
                web_server.set_ngrok_url(manual_url)
                print(f"   ✅ Using manual ngrok URL: {manual_url}")
                return True
            else:
                print("   ⚠️  Continuing without ngrok - webhook features limited")
                return False
                
        except subprocess.TimeoutExpired:
            print("   ⚠️  ngrok startup timeout - continuing without webhooks")
            return False
        except Exception as e:
            print(f"   ⚠️  ngrok error: {e} - continuing without webhooks")
            return False
    
    def start_web_server(self):
        """Start the web server"""
        print("🚀 Starting web server...")
        
        try:
            # Start web server in background thread
            server_thread = threading.Thread(
                target=web_server.run,
                kwargs={'debug': False},
                daemon=True
            )
            server_thread.start()
            
            # Wait for server to start
            time.sleep(2)
            
            local_url = "http://localhost:5000"
            print(f"   ✅ Web server running on {local_url}")
            if self.ngrok_url:
                print(f"   🌐 Public URL: {self.ngrok_url}")
            
            # Auto-open local dashboard in browser
            try:
                import webbrowser
                
                def open_browser():
                    time.sleep(1)  # Wait a bit more for server to be ready
                    try:
                        webbrowser.open(local_url)
                        print(f"   🌐 Browser opened to: {local_url}")
                    except Exception as e:
                        print(f"   💡 Please manually open: {local_url}")
                
                # Start browser opening in background
                browser_thread = threading.Thread(target=open_browser, daemon=True)
                browser_thread.start()
                
            except ImportError:
                print(f"   💡 Please manually open: {local_url}")
            except Exception as e:
                print(f"   💡 Could not auto-open browser: {e}")
                print(f"   🌐 Please manually open: {local_url}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to start web server: {e}")
            return False
    
    def show_system_status(self):
        """Show comprehensive system status"""
        print("\n" + "=" * 70)
        print("📊 SYSTEM STATUS SUMMARY")
        print("=" * 70)
        
        # Component status
        components = {
            "Database": "✅ Ready",
            "AI Services": "✅ Ready" if ai_service.is_available() else "⚠️  Fallback Mode",
            "Communication": "✅ Ready" if comm_service.credentials_valid else "❌ Invalid Credentials",
            "Procurement Engine": "✅ Ready",
            "Web Server": "✅ Running",
            "Ngrok Tunnel": "✅ Active" if self.ngrok_url else "❌ Not Available"
        }
        
        for component, status in components.items():
            print(f"{component:20} {status}")
        
        print("\n📋 PLATFORM CAPABILITIES:")
        capabilities = [
            "✅ Multi-company inventory management",
            "✅ AI-powered vendor conversations",
            "✅ Real-time procurement analysis",
            "✅ Web dashboard with analytics",
            "✅ Voice call automation" if comm_service.credentials_valid else "❌ Voice calls (credentials needed)",
            "✅ WhatsApp integration" if comm_service.credentials_valid else "❌ WhatsApp (credentials needed)",
            "✅ Webhook endpoints" if self.ngrok_url else "❌ Webhooks (ngrok needed)"
        ]
        
        for capability in capabilities:
            print(f"  {capability}")
        
        print(f"\n🌐 ACCESS POINTS:")
        print(f"  🏠 Local Dashboard:    http://localhost:5000")
        print(f"  🏠 Local API Health:   http://localhost:5000/health")
        if self.ngrok_url:
            print(f"  🌍 Public Dashboard:   {self.ngrok_url}")
            print(f"  🌍 Public Webhooks:    {self.ngrok_url}/webhook/*")
        else:
            print(f"  🌍 Public Access:      Not available (ngrok not running)")
        
        # Quick statistics
        companies = db.get_all_companies()
        vendors = db.get_all_vendors()
        
        print(f"\n📈 CURRENT DATA:")
        print(f"  Companies:     {len(companies)}")
        print(f"  Vendors:       {len(vendors)}")
        print(f"  Conversations: {len(db.get_conversations(limit=50))}")
        
        # Procurement alerts
        try:
            analysis = procurement_engine.analyze_procurement_requirements(companies)
            critical_items = analysis['summary']['critical_items']
            urgent_items = analysis['summary']['urgent_items']
            
            if critical_items > 0 or urgent_items > 0:
                print(f"\n⚠️  PROCUREMENT ALERTS:")
                if critical_items > 0:
                    print(f"  🚨 {critical_items} critical items need immediate attention")
                if urgent_items > 0:
                    print(f"  ⚠️  {urgent_items} urgent items require procurement")
            else:
                print(f"\n✅ No urgent procurement requirements")
                
        except Exception as e:
            print(f"\n⚠️  Could not analyze procurement status: {e}")
    
    def show_interactive_menu(self):
        """Show interactive management menu"""
        while self.running:
            print("\n" + "=" * 70)
            print("🎛️  PROCUREMENT PLATFORM CONTROL CENTER")
            print("=" * 70)
            print("1.  📊 System Status & Health Check")
            print("2.  🏢 View Companies & Inventory")
            print("3.  🤝 View Vendors & Performance")
            print("4.  🛒 Run Procurement Analysis")
            print("5.  📞 Test Voice Call System")
            print("6.  📱 Test WhatsApp Integration")
            print("7.  💬 View Recent Conversations")
            print("8.  📈 View Analytics Dashboard")
            print("9.  🔧 System Configuration")
            print("10. 🌐 Open Web Dashboard")
            print("11. 📋 Export Data")
            print("12. 🔄 Restart Components")
            print("13. ❓ Help & Documentation")
            print("14. 🛑 Shutdown Platform")
            
            try:
                choice = input("\nSelect option (1-14): ").strip()
                
                if choice == "1":
                    self.show_system_status()
                
                elif choice == "2":
                    self.show_companies_info()
                
                elif choice == "3":
                    self.show_vendors_info()
                
                elif choice == "4":
                    self.run_procurement_analysis()
                
                elif choice == "5":
                    self.test_voice_calls()
                
                elif choice == "6":
                    self.test_whatsapp()
                
                elif choice == "7":
                    self.show_conversations()
                
                elif choice == "8":
                    self.open_web_dashboard()
                
                elif choice == "9":
                    self.show_configuration()
                
                elif choice == "10":
                    self.open_web_dashboard()
                
                elif choice == "11":
                    self.export_data()
                
                elif choice == "12":
                    self.restart_components()
                
                elif choice == "13":
                    self.show_help()
                
                elif choice == "14":
                    self.shutdown()
                    break
                
                else:
                    print("❌ Invalid choice. Please select 1-14.")
                
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\n\n🛑 Shutdown requested...")
                self.shutdown()
                break
            except Exception as e:
                print(f"❌ Menu error: {e}")
    
    def show_companies_info(self):
        """Show companies information"""
        print("\n🏢 COMPANIES OVERVIEW")
        print("-" * 50)
        
        companies = db.get_all_companies()
        for company in companies.values():
            low_stock = company.get_low_stock_items()
            print(f"\n📊 {company.name}")
            print(f"   Industry: {company.industry}")
            print(f"   Contact: {company.contact_person}")
            print(f"   Budget: ₹{company.budget_monthly:,.0f}/month")
            print(f"   Inventory Items: {len(company.inventory) if company.inventory else 0}")
            print(f"   Low Stock Items: {len(low_stock)}")
            
            if low_stock:
                print("   ⚠️  Items needing attention:")
                for item in low_stock[:3]:
                    print(f"     • {item.name}: {item.current_stock}/{item.minimum_required}")
    
    def show_vendors_info(self):
        """Show vendors information"""
        print("\n🤝 VENDORS OVERVIEW")
        print("-" * 50)
        
        vendors = db.get_all_vendors()
        for vendor in vendors.values():
            print(f"\n📞 {vendor.name}")
            print(f"   Rating: {'⭐' * int(vendor.rating)} {vendor.rating}/5.0")
            print(f"   Phone: {vendor.phone}")
            print(f"   Specialties: {', '.join(vendor.specialties)}")
            print(f"   Response Time: {vendor.response_time}")
            print(f"   Success Rate: {vendor.get_success_rate():.1f}%")
    
    def run_procurement_analysis(self):
        """Run procurement analysis"""
        print("\n🛒 RUNNING PROCUREMENT ANALYSIS")
        print("-" * 50)
        
        try:
            companies = db.get_all_companies()
            analysis = procurement_engine.analyze_procurement_requirements(companies)
            
            print(f"📊 Analysis Results:")
            print(f"   Companies analyzed: {analysis['summary']['total_companies']}")
            print(f"   Companies needing procurement: {analysis['summary']['companies_needing_procurement']}")
            print(f"   Critical items: {analysis['summary']['critical_items']}")
            print(f"   Urgent items: {analysis['summary']['urgent_items']}")
            print(f"   Total estimated cost: ₹{analysis['summary']['total_estimated_cost']:,.2f}")
            
            if analysis['recommendations']:
                print(f"\n💡 Recommendations:")
                for rec in analysis['recommendations']:
                    print(f"   • {rec}")
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
    
    def test_voice_calls(self):
        """Test voice call system"""
        print("\n📞 VOICE CALL SYSTEM TEST")
        print("-" * 50)
        
        if not comm_service.credentials_valid:
            print("❌ Twilio credentials invalid - cannot test calls")
            return
        
        phone = input("Enter phone number to test (+91xxxxxxxxxx): ").strip()
        if not phone:
            print("❌ No phone number provided")
            return
        
        companies = db.get_all_companies()
        if not companies:
            print("❌ No companies available")
            return
        
        company = next(iter(companies.values()))
        
        print(f"📞 Testing call to {phone}...")
        success, result = comm_service.make_voice_call(phone, company, "http://localhost:5000")
        
        if success:
            print(f"✅ Call initiated successfully! Call SID: {result}")
        else:
            print(f"❌ Call failed: {result}")
    
    def test_whatsapp(self):
        """Test WhatsApp integration"""
        print("\n📱 WHATSAPP INTEGRATION TEST")
        print("-" * 50)
        
        if not comm_service.credentials_valid:
            print("❌ Twilio credentials invalid - cannot test WhatsApp")
            return
        
        phone = input("Enter phone number for WhatsApp (+91xxxxxxxxxx): ").strip()
        if not phone:
            print("❌ No phone number provided")
            return
        
        companies = db.get_all_companies()
        company = next(iter(companies.values())) if companies else None
        
        message = ai_service.generate_whatsapp_message(company) if company else "Test message from Procurement Platform"
        
        print(f"📱 Sending WhatsApp to {phone}...")
        print(f"Message: {message}")
        
        success, result = comm_service.send_whatsapp_message(phone, message, company)
        
        if success:
            print(f"✅ WhatsApp sent successfully! Message SID: {result}")
        else:
            print(f"❌ WhatsApp failed: {result}")
    
    def show_conversations(self):
        """Show recent conversations"""
        print("\n💬 RECENT CONVERSATIONS")
        print("-" * 50)
        
        conversations = db.get_conversations(limit=10)
        
        if not conversations:
            print("No conversations found.")
            return
        
        for conv in conversations[-5:]:  # Show last 5
            print(f"\n🕐 {conv.timestamp}")
            print(f"Type: {conv.type.upper()}")
            if conv.vendor_number:
                print(f"Vendor: {conv.vendor_number}")
            print(f"Message: {conv.vendor_message[:100]}...")
            print(f"Response: {conv.ai_response[:100]}...")
    
    def open_web_dashboard(self):
        """Open web dashboard in browser"""
        try:
            import webbrowser
            local_url = "http://localhost:5000"
            
            # Always prefer local access for direct user interaction
            print(f"🌐 Opening local dashboard: {local_url}")
            webbrowser.open(local_url)
            
            if self.ngrok_url:
                print(f"💡 Public URL also available: {self.ngrok_url}")
                
        except Exception as e:
            print(f"❌ Could not open browser: {e}")
            print(f"🌐 Manual access:")
            print(f"   Local:  http://localhost:5000")
            if self.ngrok_url:
                print(f"   Public: {self.ngrok_url}")
    
    def show_configuration(self):
        """Show system configuration"""
        print("\n🔧 SYSTEM CONFIGURATION")
        print("-" * 50)
        
        print(f"Python Version: {sys.version}")
        print(f"Platform: {sys.platform}")
        print(f"Working Directory: {os.getcwd()}")
        
        print(f"\nEnvironment Variables:")
        env_vars = ['GEMINI_API_KEY', 'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN']
        for var in env_vars:
            value = os.getenv(var)
            if value:
                print(f"  {var}: {'*' * 8}...{value[-4:] if len(value) > 8 else '***'}")
            else:
                print(f"  {var}: Not set")
    
    def export_data(self):
        """Export platform data"""
        print("\n📋 DATA EXPORT")
        print("-" * 50)
        
        try:
            filename = db.export_to_csv("all")
            print(f"✅ Data exported to: {filename}")
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def restart_components(self):
        """Restart platform components"""
        print("\n🔄 RESTARTING COMPONENTS")
        print("-" * 50)
        print("⚠️  This feature is not implemented yet.")
        print("To restart, please stop the platform and run main.py again.")
    
    def show_help(self):
        """Show help and documentation"""
        help_text = """
❓ PROCUREMENT PLATFORM HELP

🏗️  ARCHITECTURE:
• models.py - Data structures and models
• database.py - Data persistence and management
• ai_services.py - Gemini AI integration with fallbacks
• communication.py - Twilio voice & WhatsApp handling
• procurement.py - Business logic for procurement analysis
• web_server.py - Flask web application
• main.py - Platform orchestrator

📞 COMMUNICATION FEATURES:
• Voice calls with speech recognition
• WhatsApp integration with auto-fallback
• Real-time conversation tracking
• AI-powered responses with fallbacks

🛒 PROCUREMENT FEATURES:
• Multi-company inventory management
• Automated shortage detection
• Vendor recommendation engine
• Price comparison and negotiation

🌐 WEB DASHBOARD:
• Real-time analytics and insights
• Interactive company and vendor management
• Live conversation monitoring
• Procurement analysis tools

🔧 TROUBLESHOOTING:
• Check system status (#1 in menu)
• Verify Twilio credentials for communication
• Ensure ngrok is running for webhooks
• Check AI service status for dynamic responses

📚 For detailed documentation, visit the project repository.
        """
        print(help_text)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def shutdown(self):
        """Graceful shutdown"""
        print("\n🛑 Shutting down Procurement Platform...")
        
        self.running = False
        
        # Stop ngrok
        if self.ngrok_process:
            print("   🔗 Stopping ngrok tunnel...")
            self.ngrok_process.terminate()
            try:
                self.ngrok_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ngrok_process.kill()
        
        # Save any pending data
        try:
            print("   💾 Saving data...")
            db.save_all_data()
        except Exception as e:
            print(f"   ⚠️  Error saving data: {e}")
        
        # Cleanup communication
        try:
            print("   📞 Cleaning up communication...")
            comm_service.cleanup_old_conversations()
        except Exception as e:
            print(f"   ⚠️  Error cleaning up: {e}")
        
        print("✅ Platform shutdown complete")
    
    def run(self):
        """Main platform run method"""
        self.print_banner()
        
        # Validate environment
        if not self.validate_environment():
            print("❌ Environment validation failed. Please fix errors and restart.")
            return False
        
        # Initialize components
        if not self.initialize_components():
            print("❌ Component initialization failed. Please check errors and restart.")
            return False
        
        # Start ngrok (optional)
        self.start_ngrok()
        
        # Start web server
        if not self.start_web_server():
            print("❌ Web server startup failed. Exiting.")
            return False
        
        # Mark as running
        self.running = True
        
        # Show system status
        self.show_system_status()
        
        print("\n🎉 Platform startup complete!")
        print("🌐 Access the web dashboard to begin managing your procurement operations.")
        
        # Start interactive menu
        try:
            self.show_interactive_menu()
        except KeyboardInterrupt:
            self.shutdown()
        
        return True

def main():
    """Main entry point"""
    platform = ProcurementPlatform()
    
    try:
        success = platform.run()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Platform error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 