import pytest
from unittest.mock import patch, MagicMock

from app import app
from models import db
from database_operations import UserOperations, SettingsOperations


def _make_ollama_client_mock(**attrs):
    """Build a MagicMock that works as an OllamaClient context manager."""
    mock = MagicMock()
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = False
    for key, value in attrs.items():
        getattr(mock, key).return_value = value
    return mock


@pytest.fixture
def logged_in_user(client):
    """Create and login a test user. Returns a dict of primitive values
    so tests don't hold a detached ORM instance after the fixture exits.
    """
    with app.app_context():
        user = UserOperations.create_user('settings@example.com', 'Password123!')
        user_info = {'id': user.id, 'email': user.email}

    client.post('/login', data={
        'email': 'settings@example.com',
        'password': 'Password123!'
    })

    return user_info

def test_settings_page_requires_login(client):
    """Test that settings page requires authentication"""
    response = client.get('/settings')
    assert response.status_code == 302
    assert '/login' in response.location

def test_settings_page_loads(client, logged_in_user):
    """Test settings page loads for authenticated user"""
    response = client.get('/settings')
    assert response.status_code == 200
    assert 'Nastavenia'.encode('utf-8') in response.data
    assert 'OLLAMA Server'.encode('utf-8') in response.data

def test_settings_form_displays_current_values(client, logged_in_user):
    """Test that settings form shows current user settings"""
    response = client.get('/settings')
    assert response.status_code == 200
    # Should contain the OLLAMA host form field (value or placeholder)
    assert b'11434' in response.data
    assert b'ollama_host' in response.data

def test_update_ollama_host(client, logged_in_user):
    """Test updating OLLAMA host setting"""
    new_host = 'http://localhost:11434'
    
    response = client.post('/settings', data={
        'ollama_host': new_host
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert 'Nastavenia boli úspešne uložené'.encode('utf-8') in response.data
    
    # Verify setting was updated in database
    with app.app_context():
        settings = SettingsOperations.get_user_settings(logged_in_user['id'])
        assert settings.ollama_host == new_host

def test_invalid_ollama_host_validation(client, logged_in_user):
    """Test validation of invalid OLLAMA host URLs"""
    invalid_hosts = [
        'not-a-url',
        'ftp://invalid.com',
        'http://',
        'https://',
        ''
    ]
    
    for invalid_host in invalid_hosts:
        response = client.post('/settings', data={
            'ollama_host': invalid_host
        })
        
        assert response.status_code == 200
        # Should show validation error
        response_text = response.data.decode('utf-8').lower()
        assert 'error' in response_text or 'neplatný' in response_text

def test_valid_ollama_host_formats(client, logged_in_user):
    """Test validation accepts valid OLLAMA host URLs"""
    valid_hosts = [
        'http://localhost:11434',
        'https://example.com:8080',
        'http://192.168.1.100:11434',
        'https://ollama.example.com'
    ]
    
    for valid_host in valid_hosts:
        response = client.post('/settings', data={
            'ollama_host': valid_host
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'úspešne uložené'.encode('utf-8') in response.data

@patch('routes.api.get_user_ollama_client')
def test_api_test_connection_success(mock_get_client, client, logged_in_user):
    """Test API endpoint for testing OLLAMA connection - success"""
    mock_get_client.return_value = _make_ollama_client_mock(test_connection=True)

    response = client.get('/api/test-connection')
    assert response.status_code == 200

    data = response.get_json()
    assert data['connected'] is True
    assert 'host' in data

@patch('routes.api.get_user_ollama_client')
def test_api_test_connection_failure(mock_get_client, client, logged_in_user):
    """Test API endpoint for testing OLLAMA connection - failure"""
    mock_get_client.return_value = _make_ollama_client_mock(test_connection=False)

    response = client.get('/api/test-connection')
    assert response.status_code == 200

    data = response.get_json()
    assert data['connected'] is False

@patch('routes.api.get_user_ollama_client')
def test_api_test_connection_exception(mock_get_client, client, logged_in_user):
    """Test API endpoint handles exceptions during connection test.

    Unexpected exceptions (not OllamaConnectionError) are routed through
    ErrorHandler.external_service_error which returns 503.
    """
    mock_get_client.side_effect = Exception("Connection error")

    response = client.get('/api/test-connection')
    assert response.status_code == 503

    data = response.get_json()
    assert 'error' in data or 'user_message' in data

@patch('routes.api.get_user_ollama_client')
def test_api_get_models_success(mock_get_client, client, logged_in_user):
    """Test API endpoint for getting models - success"""
    mock_models = [
        {'name': 'llama2:latest', 'size': 3825819519},
        {'name': 'codellama:latest', 'size': 3825819519}
    ]
    mock_client = _make_ollama_client_mock(
        get_models=mock_models,
        get_version={'version': 'test'},
    )
    mock_get_client.return_value = mock_client

    response = client.get('/api/models')
    assert response.status_code == 200

    data = response.get_json()
    assert 'models' in data
    assert len(data['models']) == 2
    assert data['models'][0]['name'] == 'llama2:latest'

@patch('routes.api.get_user_ollama_client')
def test_api_get_models_connection_error(mock_get_client, client, logged_in_user):
    """Test API endpoint handles OLLAMA connection errors.

    OllamaConnectionError routes through ErrorHandler.external_service_error → 503.
    Backward-compat: response includes empty models list.
    """
    from ollama_client import OllamaConnectionError

    mock_client = _make_ollama_client_mock()
    mock_client.get_models.side_effect = OllamaConnectionError("Connection failed")
    mock_get_client.return_value = mock_client

    response = client.get('/api/models')
    assert response.status_code == 503

    data = response.get_json()
    assert data['models'] == []

@patch('routes.api.get_user_ollama_client')
def test_api_get_models_unexpected_error(mock_get_client, client, logged_in_user):
    """Test API endpoint handles unexpected errors.

    Non-OllamaConnectionError exceptions route through ErrorHandler.internal_error → 500.
    """
    mock_get_client.side_effect = Exception("Unexpected error")

    response = client.get('/api/models')
    assert response.status_code == 500

    data = response.get_json()
    assert data['models'] == []

def test_settings_isolation_between_users(client):
    """Test that users have isolated settings"""
    with app.app_context():
        user1 = UserOperations.create_user('user1@example.com', 'Password123!')
        user2 = UserOperations.create_user('user2@example.com', 'Password123!')
        
        # Update user1 settings
        SettingsOperations.update_ollama_host(user1.id, 'http://user1-server:11434')

        # Update user2 settings
        SettingsOperations.update_ollama_host(user2.id, 'http://user2-server:11434')

        # Expire session to force fresh reads (avoid stale cached attributes)
        db.session.expire_all()
        
        # Verify settings are isolated
        user1_settings = SettingsOperations.get_user_settings(user1.id)
        user2_settings = SettingsOperations.get_user_settings(user2.id)
        
        assert user1_settings.ollama_host == 'http://user1-server:11434'
        assert user2_settings.ollama_host == 'http://user2-server:11434'

if __name__ == '__main__':
    pytest.main([__file__])