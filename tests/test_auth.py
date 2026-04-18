import pytest

from app import app
from database_operations import UserOperations

def test_login_page(client):
    """Test login page loads correctly"""
    response = client.get('/login')
    assert response.status_code == 200
    assert 'Prihlásenie'.encode('utf-8') in response.data

def test_register_page(client):
    """Test register page loads correctly"""
    response = client.get('/register')
    assert response.status_code == 200
    assert 'Registrácia'.encode('utf-8') in response.data

VALID_PASSWORD = 'Password123!'

def test_user_registration(client):
    """Test user registration flow"""
    response = client.post('/register', data={
        'email': 'test@example.com',
        'password': VALID_PASSWORD,
        'password_confirm': VALID_PASSWORD
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Registrácia bola úspešná'.encode('utf-8') in response.data

def test_user_login(client):
    """Test user login flow"""
    # First register a user
    with app.app_context():
        UserOperations.create_user('login@example.com', VALID_PASSWORD)

    # Then try to login
    response = client.post('/login', data={
        'email': 'login@example.com',
        'password': VALID_PASSWORD
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Úspešne ste sa prihlásili'.encode('utf-8') in response.data

def test_invalid_login(client):
    """Test login with invalid credentials"""
    response = client.post('/login', data={
        'email': 'nonexistent@example.com',
        'password': 'WrongPassword123!'
    })

    assert response.status_code == 200
    assert 'Neplatný email alebo heslo'.encode('utf-8') in response.data

def test_duplicate_registration(client):
    """Test registration with existing email"""
    # First register a user
    with app.app_context():
        UserOperations.create_user('duplicate@example.com', VALID_PASSWORD)

    # Try to register with same email
    response = client.post('/register', data={
        'email': 'duplicate@example.com',
        'password': 'NewPassword123!',
        'password_confirm': 'NewPassword123!'
    })

    assert response.status_code == 200
    assert 'Tento email je už registrovaný'.encode('utf-8') in response.data

def test_password_mismatch(client):
    """Test registration with password mismatch"""
    response = client.post('/register', data={
        'email': 'mismatch@example.com',
        'password': VALID_PASSWORD,
        'password_confirm': 'DifferentPassword123!'
    })

    assert response.status_code == 200
    assert 'Heslá sa nezhodujú'.encode('utf-8') in response.data

def test_redirect_to_login_when_not_authenticated(client):
    """Test that chat page redirects to login when not authenticated"""
    response = client.get('/chat')
    assert response.status_code == 302
    assert '/login' in response.location

def test_logout(client):
    """Test user logout"""
    # First register and login a user
    with app.app_context():
        UserOperations.create_user('logout@example.com', VALID_PASSWORD)

    client.post('/login', data={
        'email': 'logout@example.com',
        'password': VALID_PASSWORD
    })
    
    # Then logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert 'Boli ste odhlásení'.encode('utf-8') in response.data

if __name__ == '__main__':
    pytest.main([__file__])