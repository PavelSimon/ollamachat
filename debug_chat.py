#!/usr/bin/env python3
"""
Debug script to test chat functionality directly
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ollama_client import OllamaClient, OllamaConnectionError
from database_operations import ChatOperations, MessageOperations, SettingsOperations
from models import db, User
from app import app

def test_chat_flow():
    """Test the complete chat flow"""
    print("Testing Chat Flow")
    print("=" * 50)
    
    with app.app_context():
        # Initialize database
        db.create_all()
        
        # Test OLLAMA client
        print("\n1. Testing OLLAMA client...")
        try:
            client = OllamaClient("http://192.168.1.23:11434")
            connected = client.test_connection()
            print(f"   Connection: {'✓' if connected else '✗'}")
            
            if connected:
                models = client.get_models()
                print(f"   Models available: {len(models)}")
                
                # Test chat with a small model
                test_models = ['llama3.2:latest', 'llama3.1:8b', 'codellama:7b']
                model_to_use = None
                
                for test_model in test_models:
                    if any(m['name'] == test_model for m in models):
                        model_to_use = test_model
                        break
                
                if not model_to_use and models:
                    model_to_use = models[0]['name']
                
                if model_to_use:
                    print(f"   Testing with model: {model_to_use}")
                    
                    conversation = [{"role": "user", "content": "Hello, just say 'Hi!' back"}]
                    response = client.chat(model_to_use, conversation)
                    
                    print(f"   Response: {response.get('message', {}).get('content', 'No content')[:100]}...")
                    print("   ✓ OLLAMA client working")
                else:
                    print("   ✗ No suitable model found")
            else:
                print("   ✗ Cannot connect to OLLAMA server")
                
        except Exception as e:
            print(f"   ✗ OLLAMA client error: {e}")
        
        # Test database operations
        print("\n2. Testing database operations...")
        try:
            # Create a test user if not exists
            test_user = User.query.filter_by(email='test@example.com').first()
            if not test_user:
                test_user = User(email='test@example.com')
                test_user.set_password('testpass')
                db.session.add(test_user)
                db.session.commit()
                print("   ✓ Test user created")
            else:
                print("   ✓ Test user exists")
            
            # Test chat creation
            chat = ChatOperations.create_chat(test_user.id, "Test Chat")
            print(f"   ✓ Chat created: ID {chat.id}")
            
            # Test message creation
            message = MessageOperations.add_message(
                chat_id=chat.id,
                content="Test message",
                is_user=True
            )
            print(f"   ✓ Message created: ID {message.id}")
            
            # Test settings
            settings = SettingsOperations.get_user_settings(test_user.id)
            print(f"   ✓ Settings loaded: OLLAMA host {settings.ollama_host}")
            
        except Exception as e:
            print(f"   ✗ Database error: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 50)
        print("Debug test completed!")

if __name__ == "__main__":
    test_chat_flow()