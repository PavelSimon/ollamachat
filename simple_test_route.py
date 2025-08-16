#!/usr/bin/env python3
"""
Create a simple test route to bypass complex features and test basic OLLAMA communication
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify
from ollama_client import OllamaClient

app = Flask(__name__)

@app.route('/test-simple-chat', methods=['POST'])
def test_simple_chat():
    """Simple test route that bypasses all complex features"""
    try:
        data = request.get_json()
        message = data.get('message', 'Hello')
        model = data.get('model', 'llama3.2:latest')
        
        print(f"🔍 Received request: message='{message}', model='{model}'")
        
        # Direct OLLAMA client test
        client = OllamaClient("http://192.168.1.23:11434")
        
        print("🔍 Testing connection...")
        connected = client.test_connection()
        if not connected:
            return jsonify({'error': 'OLLAMA not connected'}), 500
        
        print("🔍 Sending chat request...")
        conversation = [{"role": "user", "content": message}]
        response = client.chat(model, conversation)
        
        ai_content = response.get('message', {}).get('content', 'No response')
        print(f"🔍 Got response: {ai_content[:100]}...")
        
        return jsonify({
            'success': True,
            'response': ai_content,
            'model': model
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/test-form')
def test_form():
    """Simple HTML form for testing"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple OLLAMA Test</title>
    </head>
    <body>
        <h1>Simple OLLAMA Test</h1>
        <div>
            <input type="text" id="message" placeholder="Type your message" value="Hello">
            <select id="model">
                <option value="llama3.2:latest">llama3.2:latest (fast)</option>
                <option value="llama3.1:8b">llama3.1:8b</option>
                <option value="gpt-oss:20b">gpt-oss:20b (slow)</option>
            </select>
            <button onclick="sendMessage()">Send</button>
        </div>
        <div id="response" style="margin-top: 20px; padding: 10px; border: 1px solid #ccc;"></div>
        
        <script>
        function sendMessage() {
            const message = document.getElementById('message').value;
            const model = document.getElementById('model').value;
            const responseDiv = document.getElementById('response');
            
            responseDiv.innerHTML = 'Sending...';
            
            fetch('/test-simple-chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message, model: model})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    responseDiv.innerHTML = '<strong>Response:</strong><br>' + data.response;
                } else {
                    responseDiv.innerHTML = '<strong>Error:</strong><br>' + data.error;
                }
            })
            .catch(error => {
                responseDiv.innerHTML = '<strong>Network Error:</strong><br>' + error;
            });
        }
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("🧪 Starting Simple OLLAMA Test Server")
    print("=" * 50)
    print("Open browser to: http://localhost:5001/test-form")
    print("This bypasses all complex features and tests direct OLLAMA communication")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5001)