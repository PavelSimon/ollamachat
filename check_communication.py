#!/usr/bin/env python3
"""
Quick check to verify OLLAMA communication is working
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ollama_client import OllamaClient

def quick_test():
    """Quick test of OLLAMA communication"""
    print("🔍 Quick OLLAMA Communication Test")
    print("=" * 50)
    
    try:
        # Test connection
        client = OllamaClient("http://192.168.1.23:11434")
        print("1. Testing connection...")
        
        connected = client.test_connection()
        if connected:
            print("   ✅ Connection successful")
        else:
            print("   ❌ Connection failed")
            return False
        
        # Test models
        print("2. Getting models...")
        models = client.get_models()
        print(f"   ✅ Found {len(models)} models")
        
        # Find a fast model for testing
        fast_models = ['llama3.2:latest', 'llama3.1:8b', 'codellama:7b']
        test_model = None
        
        for fast_model in fast_models:
            if any(m['name'] == fast_model for m in models):
                test_model = fast_model
                break
        
        if not test_model and models:
            # Use smallest available model
            smallest = min(models, key=lambda x: x['size'])
            test_model = smallest['name']
        
        if test_model:
            print(f"3. Testing chat with {test_model}...")
            conversation = [{"role": "user", "content": "Say 'Hello!' in one word"}]
            
            import time
            start_time = time.time()
            response = client.chat(test_model, conversation)
            duration = time.time() - start_time
            
            ai_response = response.get('message', {}).get('content', 'No response')
            print(f"   ✅ Response in {duration:.1f}s: {ai_response[:50]}...")
            
            if duration > 30:
                print("   ⚠️  Response was slow (>30s) - this might feel unresponsive")
            elif duration > 10:
                print("   ⚠️  Response was moderate (>10s) - normal for larger models")
            else:
                print("   ✅ Response was fast (<10s)")
                
        else:
            print("   ❌ No suitable model found for testing")
            
        print("\n🎉 OLLAMA communication is working!")
        print("If the web app seems unresponsive, try:")
        print("- Using a smaller/faster model (llama3.2:latest)")
        print("- Waiting longer for responses (20-30 seconds is normal)")
        print("- Checking browser console for JavaScript errors")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    quick_test()