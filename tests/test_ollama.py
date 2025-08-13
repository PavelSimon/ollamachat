import pytest
import json
from unittest.mock import Mock, patch
import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ollama_client import OllamaClient, OllamaConnectionError

@pytest.fixture
def ollama_client():
    return OllamaClient("http://localhost:11434")

@pytest.fixture
def mock_models_response():
    return {
        "models": [
            {
                "name": "llama2:latest",
                "size": 3825819519,
                "digest": "sha256:abc123",
                "modified_at": "2023-12-01T10:00:00Z"
            },
            {
                "name": "codellama:latest", 
                "size": 3825819519,
                "digest": "sha256:def456",
                "modified_at": "2023-12-01T11:00:00Z"
            }
        ]
    }

@pytest.fixture
def mock_chat_response():
    return {
        "message": {
            "role": "assistant",
            "content": "Hello! How can I help you today?"
        },
        "done": True,
        "total_duration": 1234567890,
        "load_duration": 123456,
        "prompt_eval_count": 10,
        "eval_count": 25
    }

def test_ollama_client_initialization():
    """Test OllamaClient initialization"""
    client = OllamaClient()
    assert client.base_url == "http://192.168.1.23:11434"
    
    client_custom = OllamaClient("http://localhost:11434/")
    assert client_custom.base_url == "http://localhost:11434"

@patch('requests.Session.get')
def test_connection_success(mock_get, ollama_client):
    """Test successful connection to OLLAMA server"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    result = ollama_client.test_connection()
    assert result is True
    mock_get.assert_called_once_with("http://localhost:11434/api/tags", timeout=5)

@patch('requests.Session.get')
def test_connection_failure(mock_get, ollama_client):
    """Test connection failure to OLLAMA server"""
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
    
    result = ollama_client.test_connection()
    assert result is False

@patch('requests.Session.get')
def test_get_models_success(mock_get, ollama_client, mock_models_response):
    """Test successful retrieval of models"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_models_response
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    models = ollama_client.get_models()
    
    assert len(models) == 2
    assert models[0]['name'] == 'llama2:latest'
    assert models[1]['name'] == 'codellama:latest'
    assert 'size' in models[0]
    assert 'digest' in models[0]

@patch('requests.Session.get')
def test_get_models_connection_error(mock_get, ollama_client):
    """Test get_models with connection error"""
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
    
    with pytest.raises(OllamaConnectionError):
        ollama_client.get_models()

@patch('requests.Session.get')
def test_get_models_invalid_json(mock_get, ollama_client):
    """Test get_models with invalid JSON response"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    with pytest.raises(OllamaConnectionError):
        ollama_client.get_models()

@patch('requests.Session.post')
def test_chat_success(mock_post, ollama_client, mock_chat_response):
    """Test successful chat request"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_chat_response
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    messages = [{"role": "user", "content": "Hello"}]
    result = ollama_client.chat("llama2:latest", messages)
    
    assert result['message']['content'] == "Hello! How can I help you today?"
    assert result['done'] is True
    assert 'total_duration' in result

@patch('requests.Session.post')
def test_chat_timeout(mock_post, ollama_client):
    """Test chat request timeout"""
    mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
    
    messages = [{"role": "user", "content": "Hello"}]
    
    with pytest.raises(OllamaConnectionError) as exc_info:
        ollama_client.chat("llama2:latest", messages)
    
    assert "vypršala" in str(exc_info.value)

@patch('requests.Session.post')
def test_chat_connection_error(mock_post, ollama_client):
    """Test chat request connection error"""
    mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
    
    messages = [{"role": "user", "content": "Hello"}]
    
    with pytest.raises(OllamaConnectionError):
        ollama_client.chat("llama2:latest", messages)

@patch('requests.Session.post')
def test_generate_success(mock_post, ollama_client):
    """Test successful generate request"""
    mock_response_data = {
        "response": "This is a generated response.",
        "done": True,
        "total_duration": 1234567890,
        "load_duration": 123456,
        "prompt_eval_count": 10,
        "eval_count": 25
    }
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    result = ollama_client.generate("llama2:latest", "Generate a response")
    
    assert result['response'] == "This is a generated response."
    assert result['done'] is True
    assert 'total_duration' in result

@patch('requests.Session.post')
def test_chat_streaming_response(mock_post, ollama_client):
    """Test streaming chat response"""
    # Mock streaming response
    stream_data = [
        b'{"message":{"role":"assistant","content":"Hello"},"done":false}\n',
        b'{"message":{"role":"assistant","content":" there"},"done":false}\n',
        b'{"message":{"role":"assistant","content":"!"},"done":true,"total_duration":1234567890}\n'
    ]
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.iter_lines.return_value = stream_data
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    messages = [{"role": "user", "content": "Hello"}]
    result = ollama_client.chat("llama2:latest", messages, stream=True)
    
    assert result['message']['content'] == "Hello there!"
    assert result['done'] is True

def test_ollama_connection_error():
    """Test OllamaConnectionError exception"""
    error = OllamaConnectionError("Test error message")
    assert str(error) == "Test error message"

if __name__ == '__main__':
    pytest.main([__file__])