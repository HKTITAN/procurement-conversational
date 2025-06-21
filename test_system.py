#!/usr/bin/env python3
"""
Test script to verify the Likwid.AI Procurement Automation System setup
"""

import os
import sys

def test_file_structure():
    """Test that all required files exist"""
    required_files = [
        'main.py',
        'demo.py', 
        'config.py',
        'requirements.txt',
        'inventory.csv',
        'README.md'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_imports():
    """Test that all imports work correctly"""
    try:
        from config import config
        print("✅ Config module imported successfully")
        
        # Test config values
        print(f"   Client: {config.CLIENT_NAME}")
        print(f"   Vendor: {config.TEST_VENDOR['name']}")
        print(f"   Phone: {config.TEST_VENDOR['phone']}")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def test_csv_files():
    """Test that CSV files are readable"""
    try:
        import pandas as pd
        
        # Test inventory.csv
        df = pd.read_csv('inventory.csv')
        print(f"✅ Inventory CSV loaded: {len(df)} items")
        
        # Check for low stock items
        low_stock = df[df['current_stock'] <= df['minimum_threshold']]
        print(f"   Low stock items: {len(low_stock)}")
        
        if len(low_stock) > 0:
            print("   Items needing procurement:")
            for _, item in low_stock.head(3).iterrows():
                print(f"     • {item['item_name']}: {item['current_stock']}/{item['minimum_threshold']}")
        
        return True
    except Exception as e:
        print(f"❌ CSV test error: {e}")
        return False

def test_demo_ready():
    """Test if the demo can be run"""
    try:
        # Test if we can import the demo
        import demo
        print("✅ Demo module can be imported")
        
        # Test if demo class can be instantiated
        demo_system = demo.ProcurementDemo()
        print("✅ Demo system can be instantiated")
        
        return True
    except Exception as e:
        print(f"❌ Demo test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 Testing Likwid.AI Procurement Automation System")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports), 
        ("CSV Files", test_csv_files),
        ("Demo Ready", test_demo_ready)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ System is ready for demonstration!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run demo: python demo.py")
        print("3. For real calls: python main.py (requires ngrok setup)")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 