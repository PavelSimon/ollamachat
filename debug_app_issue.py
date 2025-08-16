#!/usr/bin/env python3
"""
Debug script to identify where the web app is getting stuck
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Enable verbose logging for debugging
os.environ['VERBOSE_LOGS'] = 'true'
os.environ['LOG_TO_CONSOLE'] = 'true'

from app import app
from models import db
import logging

def debug_app():
    """Debug the app configuration"""
    print("🔍 Debugging Web App Configuration")
    print("=" * 50)
    
    with app.app_context():
        # Check database
        try:
            db.create_all()
            print("✅ Database initialized")
        except Exception as e:
            print(f"❌ Database error: {e}")
        
        # Check imports
        try:
            from routes.chat import chat_bp
            from ollama_client import OllamaClient
            from search_service import search_service
            print("✅ All imports successful")
        except Exception as e:
            print(f"❌ Import error: {e}")
            import traceback
            traceback.print_exc()
        
        # Check OLLAMA client
        try:
            client = OllamaClient()
            connected = client.test_connection()
            print(f"✅ OLLAMA client: {'Connected' if connected else 'Not connected'}")
        except Exception as e:
            print(f"❌ OLLAMA client error: {e}")
        
        # List registered routes
        print("\n📋 Registered Routes:")
        for rule in app.url_map.iter_rules():
            if '/api/' in rule.rule:
                print(f"   {rule.methods} {rule.rule} -> {rule.endpoint}")
    
    print("\n🚀 Starting app with verbose logging...")
    print("Check the console output for any errors when you make a request")
    print("=" * 50)
    
    # Start the app
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    debug_app()