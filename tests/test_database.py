import pytest
import tempfile
import os
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, User, Chat, Message, UserSettings
from database_operations import UserOperations, ChatOperations, MessageOperations, SettingsOperations

@pytest.fixture
def client():
    # Create temporary database
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE']
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
    
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

def test_user_operations(client):
    """Test user CRUD operations"""
    with app.app_context():
        # Test user creation
        user = UserOperations.create_user("test@example.com", "password123")
        assert user is not None
        assert user.email == "test@example.com"
        
        # Test duplicate email
        duplicate_user = UserOperations.create_user("test@example.com", "password456")
        assert duplicate_user is None
        
        # Test user authentication
        auth_user = UserOperations.authenticate_user("test@example.com", "password123")
        assert auth_user is not None
        assert auth_user.id == user.id
        
        # Test wrong password
        wrong_auth = UserOperations.authenticate_user("test@example.com", "wrongpassword")
        assert wrong_auth is None
        
        # Test get user by email
        found_user = UserOperations.get_user_by_email("test@example.com")
        assert found_user.id == user.id

def test_chat_operations(client):
    """Test chat CRUD operations"""
    with app.app_context():
        # Create test user
        user = UserOperations.create_user("chat@example.com", "password123")
        
        # Test chat creation
        chat = ChatOperations.create_chat(user.id, "Test Chat")
        assert chat is not None
        assert chat.title == "Test Chat"
        assert chat.user_id == user.id
        
        # Test get user chats
        chats = ChatOperations.get_user_chats(user.id)
        assert len(chats) == 1
        assert chats[0].id == chat.id
        
        # Test get chat by id
        found_chat = ChatOperations.get_chat_by_id(chat.id, user.id)
        assert found_chat.id == chat.id
        
        # Test update chat title
        updated_chat = ChatOperations.update_chat_title(chat.id, user.id, "Updated Title")
        assert updated_chat.title == "Updated Title"

def test_message_operations(client):
    """Test message CRUD operations"""
    with app.app_context():
        # Create test user and chat
        user = UserOperations.create_user("msg@example.com", "password123")
        chat = ChatOperations.create_chat(user.id, "Message Test Chat")
        
        # Test add user message
        user_msg = MessageOperations.add_message(chat.id, "Hello AI!", True)
        assert user_msg is not None
        assert user_msg.content == "Hello AI!"
        assert user_msg.is_user == True
        
        # Test add AI message
        ai_msg = MessageOperations.add_message(chat.id, "Hello human!", False, "llama2")
        assert ai_msg is not None
        assert ai_msg.content == "Hello human!"
        assert ai_msg.is_user == False
        assert ai_msg.model_name == "llama2"
        
        # Test get chat messages
        messages = MessageOperations.get_chat_messages(chat.id, user.id)
        assert len(messages) == 2
        assert messages[0].content == "Hello AI!"  # First message (chronological order)
        assert messages[1].content == "Hello human!"

def test_settings_operations(client):
    """Test settings CRUD operations"""
    with app.app_context():
        # Create test user
        user = UserOperations.create_user("settings@example.com", "password123")
        
        # Test get default settings
        settings = SettingsOperations.get_user_settings(user.id)
        assert settings is not None
        assert settings.ollama_host == "http://192.168.1.23:11434"
        
        # Test update OLLAMA host
        updated_settings = SettingsOperations.update_ollama_host(user.id, "http://localhost:11434")
        assert updated_settings.ollama_host == "http://localhost:11434"
        
        # Test get OLLAMA host
        host = SettingsOperations.get_ollama_host(user.id)
        assert host == "http://localhost:11434"

if __name__ == '__main__':
    pytest.main([__file__])