#!/usr/bin/env python3
"""
Simple test script for OLLAMA connection and chat functionality
"""

import sys
import os
import time

# Add parent directory to path to import ollama_client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ollama_client import OllamaClient, OllamaConnectionError

def test_connection(host="http://192.168.1.23:11434"):
    """Test basic connection to OLLAMA server"""
    print(f"Testing connection to {host}...")
    
    client = OllamaClient(host)
    
    try:
        connected = client.test_connection()
        if connected:
            print("✓ Connection successful!")
            return True
        else:
            print("✗ Connection failed!")
            return False
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

def test_models(host="http://192.168.1.23:11434"):
    """Test getting available models"""
    print(f"\nTesting models endpoint...")
    
    client = OllamaClient(host)
    
    try:
        models = client.get_models()
        print(f"✓ Found {len(models)} models:")
        for model in models:
            size_gb = model['size'] / (1024 * 1024 * 1024)
            print(f"  - {model['name']} ({size_gb:.2f} GB)")
        return models
    except Exception as e:
        print(f"✗ Models error: {e}")
        return []

def test_chat(host="http://192.168.1.23:11434", model_name=None):
    """Test chat functionality"""
    print(f"\nTesting chat functionality...")
    
    client = OllamaClient(host)
    
    # Get available models if no model specified
    if not model_name:
        try:
            models = client.get_models()
            if not models:
                print("✗ No models available for testing")
                return False
            
            # Prefer smaller, faster models for testing
            preferred_models = ['llama3.2:latest', 'llama3.1:8b', 'codellama:7b', 'gpt-oss:20b']
            model_name = None
            
            for preferred in preferred_models:
                for model in models:
                    if model['name'] == preferred:
                        model_name = preferred
                        break
                if model_name:
                    break
            
            # If no preferred model found, use the smallest available
            if not model_name:
                smallest_model = min(models, key=lambda x: x['size'])
                model_name = smallest_model['name']
                
        except Exception as e:
            print(f"✗ Could not get models: {e}")
            return False
    
    print(f"Using model: {model_name}")
    
    # Simple test message
    test_message = "Hello! Please respond with just 'Hi there!' to confirm you're working."
    conversation = [{"role": "user", "content": test_message}]
    
    try:
        print("Sending test message...")
        start_time = time.time()
        
        response = client.chat(model_name, conversation)
        
        end_time = time.time()
        duration = end_time - start_time
        
        ai_content = response.get('message', {}).get('content', '')
        
        print(f"✓ Chat successful!")
        print(f"  Response time: {duration:.2f} seconds")
        print(f"  Response: {ai_content[:100]}{'...' if len(ai_content) > 100 else ''}")
        
        # Check response stats
        if 'total_duration' in response:
            total_ms = response['total_duration'] / 1000000  # Convert nanoseconds to milliseconds
            print(f"  Total duration: {total_ms:.0f}ms")
        
        if 'eval_count' in response:
            print(f"  Tokens generated: {response['eval_count']}")
            
        return True
        
    except OllamaConnectionError as e:
        print(f"✗ Chat error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def main():
    """Main test function"""
    print("OLLAMA Connection Test")
    print("=" * 50)
    
    # Get host from command line or use default
    host = sys.argv[1] if len(sys.argv) > 1 else "http://192.168.1.23:11434"
    
    # Test connection
    if not test_connection(host):
        print("\n❌ Connection test failed. Check if OLLAMA server is running.")
        return False
    
    # Test models
    models = test_models(host)
    if not models:
        print("\n❌ No models available. Install some models first.")
        return False
    
    # Test chat with first available model
    model_name = models[0]['name']
    if not test_chat(host, model_name):
        print(f"\n❌ Chat test failed with model {model_name}")
        return False
    
    print("\n✅ All tests passed! OLLAMA is working correctly.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)