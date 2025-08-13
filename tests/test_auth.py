import pytest
import tempfile
import os
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db
from database_operations import UserOperations

@pytest.fixture
def client():
    # Create temporary database
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE']
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
    
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

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

def test_user_registration(client):
    """Test user registration flow"""
    response = client.post('/register', data={
        'email': 'test@example.com',
        'password': 'password123',
        'password_confirm': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert 'Registrácia bola úspešná'.encode('utf-8') in response.data

def test_user_login(client):
    """Test user login flow"""
    # First register a user
    with app.app_context():
        UserOperations.create_user('login@example.com', 'password123')
    
    # Then try to login
    response = client.post('/login', data={
        'email': 'login@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert 'Úspešne ste sa prihlásili'.encode('utf-8') in response.data

def test_invalid_login(client):
    """Test login with invalid credentials"""
    response = client.post('/login', data={
        'email': 'nonexistent@example.com',
        'password': 'wrongpassword'
    })
    
    assert response.status_code == 200
    assert 'Neplatný email alebo heslo'.encode('utf-8') in response.data

def test_duplicate_registration(client):
    """Test registration with existing email"""
    # First register a user
    with app.app_context():
        UserOperations.create_user('duplicate@example.com', 'password123')
    
    # Try to register with same email
    response = client.post('/register', data={
        'email': 'duplicate@example.com',
        'password': 'newpassword123',
        'password_confirm': 'newpassword123'
    })
    
    assert response.status_code == 200
    assert 'Tento email je už registrovaný'.encode('utf-8') in response.data

def test_password_mismatch(client):
    """Test registration with password mismatch"""
    response = client.post('/register', data={
        'email': 'mismatch@example.com',
        'password': 'password123',
        'password_confirm': 'differentpassword'
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
        UserOperations.create_user('logout@example.com', 'password123')
    
    client.post('/login', data={
        'email': 'logout@example.com',
        'password': 'password123'
    })
    
    # Then logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert 'Boli ste odhlásení'.encode('utf-8') in response.data

if __name__ == '__main__':
    pytest.main([__file__])