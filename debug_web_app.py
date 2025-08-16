#!/usr/bin/env python3
"""
Debug the web app to see where requests are getting stuck
"""

import os
import sys
import time
import requests
import json

def test_web_app_api():
    """Test the web app API endpoints directly"""
    print("🔍 Testing Web App API Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Test 1: Check if app is running
    print("1. Testing if app is running...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   ✅ App is running (status: {response.status_code})")
    except Exception as e:
        print(f"   ❌ App not running: {e}")
        print("   Please start the app with: python app.py")
        return False
    
    # Test 2: Test models endpoint
    print("2. Testing models endpoint...")
    try:
        response = requests.get(f"{base_url}/api/models", timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"   ✅ Models endpoint working ({len(models)} models)")
        else:
            print(f"   ❌ Models endpoint failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Models endpoint error: {e}")
    
    # Test 3: Test connection endpoint
    print("3. Testing connection endpoint...")
    try:
        response = requests.get(f"{base_url}/api/test-connection", timeout=10)
        if response.status_code == 200:
            data = response.json()
            connected = data.get('connected', False)
            print(f"   ✅ Connection test: {'Connected' if connected else 'Not connected'}")
        else:
            print(f"   ❌ Connection test failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection test error: {e}")
    
    # Test 4: Test chat creation (requires login)
    print("4. Testing chat creation...")
    print("   ⚠️  This requires authentication - testing with curl might be needed")
    
    print("\n" + "=" * 50)
    print("Web App API Test Complete!")
    print("\nTo debug further:")
    print("1. Check browser Network tab (F12) for failed requests")
    print("2. Look for JavaScript errors in Console tab")
    print("3. Try with VERBOSE_LOGS=true LOG_TO_CONSOLE=true python app.py")
    
    return True

def test_with_curl():
    """Provide curl commands for testing"""
    print("\n🔧 Manual Testing Commands:")
    print("=" * 50)
    
    print("# Test models endpoint:")
    print("curl -X GET http://localhost:5000/api/models")
    
    print("\n# Test connection:")
    print("curl -X GET http://localhost:5000/api/test-connection")
    
    print("\n# Test with verbose logging:")
    print("VERBOSE_LOGS=true LOG_TO_CONSOLE=true python app.py")

if __name__ == "__main__":
    test_web_app_api()
    test_with_curl()