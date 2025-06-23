#!/usr/bin/env python3
"""
Dependency Installation Script for Multi-Company Procurement Platform
Automatically installs required packages
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Main installation function"""
    print("🔧 Installing Multi-Company Procurement Platform Dependencies...")
    print("=" * 60)
    
    # Required packages
    packages = [
        "Flask==2.3.3",
        "Flask-SocketIO==5.3.6", 
        "google-generativeai==0.8.3",
        "requests==2.31.0",
        "python-socketio==5.10.0",
        "Werkzeug==2.3.7",
        "python-dotenv==1.0.0",
        "twilio==8.2.0"
    ]
    
    successful = 0
    failed = []
    
    for package in packages:
        package_name = package.split("==")[0]
        print(f"📦 Installing {package_name}...")
        
        if install_package(package):
            print(f"   ✅ {package_name} installed successfully")
            successful += 1
        else:
            print(f"   ❌ Failed to install {package_name}")
            failed.append(package_name)
    
    print("\n" + "=" * 60)
    print(f"📊 Installation Summary:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {len(failed)}")
    
    if failed:
        print(f"   Failed packages: {', '.join(failed)}")
        print("\n💡 Try installing failed packages manually:")
        for pkg in failed:
            print(f"   pip install {pkg}")
    else:
        print("\n🎉 All dependencies installed successfully!")
        print("📝 You can now run the platform with: python main.py")
    
    return len(failed) == 0

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 