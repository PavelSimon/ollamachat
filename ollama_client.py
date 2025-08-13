import requests
import json
import os
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for communicating with OLLAMA API"""
    
    def __init__(self, base_url: str = None):
        if base_url is None:
            base_url = os.environ.get('DEFAULT_OLLAMA_HOST', 'http://localhost:11434')
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        # Remove global timeout, set per-request timeouts instead
    
    def test_connection(self) -> bool:
        """Test if OLLAMA server is accessible"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_models(self) -> List[Dict]:
        """Get list of available models from OLLAMA server"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            models = data.get('models', [])
            
            # Extract model names and info
            model_list = []
            for model in models:
                model_info = {
                    'name': model.get('name', ''),
                    'size': model.get('size', 0),
                    'modified_at': model.get('modified_at', ''),
                    'digest': model.get('digest', '')
                }
                model_list.append(model_info)
            
            return model_list
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get models: {e}")
            raise OllamaConnectionError(f"Nepodarilo sa načítať modely: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise OllamaConnectionError("Neplatná odpoveď zo servera")
    
    def get_version(self) -> Dict:
        """Get OLLAMA server version information"""
        try:
            response = self.session.get(f"{self.base_url}/api/version", timeout=5)
            response.raise_for_status()
            
            data = response.json()
            return {
                'version': data.get('version', 'unknown'),
                'llama_cpp_version': data.get('details', {}).get('llama_cpp_version', 'unknown'),
                'architecture': data.get('details', {}).get('architecture', 'unknown'),
                'cuda_version': data.get('details', {}).get('cuda_version', None),
                'git_commit': data.get('details', {}).get('git_commit', 'unknown')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get version: {e}")
            raise OllamaConnectionError(f"Nepodarilo sa získať verziu: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise OllamaConnectionError("Neplatná odpoveď zo servera")
    
    def chat(self, model: str, messages: List[Dict], stream: bool = False) -> Dict:
        """Send chat request to OLLAMA model"""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream
            }
            
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120  # Extended timeout for chat responses (2 minutes)
            )
            response.raise_for_status()
            
            if stream:
                # Handle streaming response
                return self._handle_stream_response(response)
            else:
                # Handle regular response
                data = response.json()
                return {
                    'message': data.get('message', {}),
                    'done': data.get('done', True),
                    'total_duration': data.get('total_duration', 0),
                    'load_duration': data.get('load_duration', 0),
                    'prompt_eval_count': data.get('prompt_eval_count', 0),
                    'eval_count': data.get('eval_count', 0)
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"Chat request timed out for model {model}")
            raise OllamaConnectionError("Požiadavka vypršala. Model možno potrebuje viac času na odpoveď. Skúste to znovu alebo použite iný model.")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise OllamaConnectionError("Chyba pripojenia k OLLAMA serveru. Skontrolujte, či je server spustený.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Chat request failed: {e}")
            raise OllamaConnectionError(f"Chyba komunikácie s OLLAMA serverom: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise OllamaConnectionError("Neplatná odpoveď zo servera. Server možno nie je správne nakonfigurovaný.")
    
    def _handle_stream_response(self, response) -> Dict:
        """Handle streaming response from OLLAMA"""
        full_content = ""
        last_response = {}
        
        try:
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode('utf-8'))
                    if 'message' in data and 'content' in data['message']:
                        full_content += data['message']['content']
                    last_response = data
                    if data.get('done', False):
                        break
            
            # Return the complete response
            return {
                'message': {'role': 'assistant', 'content': full_content},
                'done': True,
                'total_duration': last_response.get('total_duration', 0),
                'load_duration': last_response.get('load_duration', 0),
                'prompt_eval_count': last_response.get('prompt_eval_count', 0),
                'eval_count': last_response.get('eval_count', 0)
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing streaming response: {e}")
            raise OllamaConnectionError("Chyba pri spracovaní odpovede")
    
    def generate(self, model: str, prompt: str, stream: bool = False) -> Dict:
        """Generate text using OLLAMA model (alternative to chat)"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream
            }
            
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120  # Extended timeout for generate responses (2 minutes)
            )
            response.raise_for_status()
            
            if stream:
                return self._handle_generate_stream(response)
            else:
                data = response.json()
                return {
                    'response': data.get('response', ''),
                    'done': data.get('done', True),
                    'total_duration': data.get('total_duration', 0),
                    'load_duration': data.get('load_duration', 0),
                    'prompt_eval_count': data.get('prompt_eval_count', 0),
                    'eval_count': data.get('eval_count', 0)
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Generate request failed: {e}")
            raise OllamaConnectionError(f"Chyba generovania: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise OllamaConnectionError("Neplatná odpoveď zo servera")
    
    def _handle_generate_stream(self, response) -> Dict:
        """Handle streaming response from generate endpoint"""
        full_response = ""
        last_response = {}
        
        try:
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode('utf-8'))
                    if 'response' in data:
                        full_response += data['response']
                    last_response = data
                    if data.get('done', False):
                        break
            
            return {
                'response': full_response,
                'done': True,
                'total_duration': last_response.get('total_duration', 0),
                'load_duration': last_response.get('load_duration', 0),
                'prompt_eval_count': last_response.get('prompt_eval_count', 0),
                'eval_count': last_response.get('eval_count', 0)
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing generate stream: {e}")
            raise OllamaConnectionError("Chyba pri spracovaní odpovede")

class OllamaConnectionError(Exception):
    """Custom exception for OLLAMA connection errors"""
    pass