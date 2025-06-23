#!/usr/bin/env python3
"""
Simple startup script for Multi-Company Procurement Platform
"""

import sys
import os
import subprocess

def install_dependencies():
    """Try to install dependencies automatically"""
    print("🔧 Missing dependencies detected. Attempting auto-installation...")
    
    try:
        # Try to run the dependency installer
        result = subprocess.run([sys.executable, "install_dependencies.py"], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully!")
            return True
        else:
            print("❌ Auto-installation failed.")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Installation timed out.")
        return False
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False

def main():
    """Simple entry point that runs the main platform"""
    print("🏭 Starting Multi-Company Procurement Platform...")
    print("=" * 60)
    
    # Try to import and run the main platform
    try:
        from main import main as platform_main
        return platform_main()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n💡 Attempting to install missing dependencies...")
        
        # Try auto-installation
        choice = input("Install dependencies automatically? (y/n): ").strip().lower()
        
        if choice in ['y', 'yes', '']:
            if install_dependencies():
                print("\n🔄 Retrying platform startup...")
                try:
                    from main import main as platform_main
                    return platform_main()
                except ImportError:
                    print("❌ Still missing dependencies after installation.")
                    print("💡 Please install manually: pip install -r requirements.txt")
                    return 1
            else:
                print("💡 Please install dependencies manually:")
                print("   pip install -r requirements.txt")
                print("   or run: python install_dependencies.py")
                return 1
        else:
            print("💡 Please install dependencies manually:")
            print("   pip install -r requirements.txt")
            return 1
            
    except Exception as e:
        print(f"❌ Platform error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 