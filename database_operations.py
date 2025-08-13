from models import db, User, Chat, Message, UserSettings
from flask import current_app
from sqlalchemy.exc import IntegrityError

class UserOperations:
    @staticmethod
    def create_user(email, password):
        """Create new user with email and password"""
        try:
            user = User(email=email.lower().strip())
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # Create default settings for user
            settings = UserSettings(user_id=user.id)
            db.session.add(settings)
            db.session.commit()
            
            return user
        except IntegrityError:
            db.session.rollback()
            return None
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email"""
        return User.query.filter_by(email=email.lower().strip()).first()
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def authenticate_user(email, password):
        """Authenticate user with email and password"""
        user = UserOperations.get_user_by_email(email)
        if user and user.check_password(password):
            return user
        return None

class ChatOperations:
    @staticmethod
    def create_chat(user_id, title=None):
        """Create new chat for user"""
        chat = Chat(user_id=user_id, title=title)
        db.session.add(chat)
        db.session.commit()
        return chat
    
    @staticmethod
    def get_user_chats(user_id):
        """Get all chats for user, ordered by creation date (newest first)"""
        return Chat.query.filter_by(user_id=user_id).order_by(Chat.created_at.desc()).all()
    
    @staticmethod
    def get_chat_by_id(chat_id, user_id):
        """Get chat by ID, ensuring it belongs to the user"""
        return Chat.query.filter_by(id=chat_id, user_id=user_id).first()
    
    @staticmethod
    def delete_chat(chat_id, user_id):
        """Delete chat and all its messages"""
        chat = ChatOperations.get_chat_by_id(chat_id, user_id)
        if chat:
            db.session.delete(chat)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def update_chat_title(chat_id, user_id, title):
        """Update chat title"""
        chat = ChatOperations.get_chat_by_id(chat_id, user_id)
        if chat:
            chat.title = title
            db.session.commit()
            return chat
        return None

class MessageOperations:
    @staticmethod
    def add_message(chat_id, content, is_user, model_name=None):
        """Add message to chat"""
        message = Message(
            chat_id=chat_id,
            content=content,
            is_user=is_user,
            model_name=model_name
        )
        db.session.add(message)
        db.session.commit()
        return message
    
    @staticmethod
    def get_chat_messages(chat_id, user_id):
        """Get all messages for a chat, ensuring user owns the chat"""
        chat = ChatOperations.get_chat_by_id(chat_id, user_id)
        if chat:
            return Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at.asc()).all()
        return []
    
    @staticmethod
    def get_latest_messages(chat_id, limit=50):
        """Get latest messages from chat"""
        return Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at.desc()).limit(limit).all()

class SettingsOperations:
    @staticmethod
    def get_user_settings(user_id):
        """Get user settings, create default if not exists"""
        settings = UserSettings.query.filter_by(user_id=user_id).first()
        if not settings:
            settings = UserSettings(user_id=user_id)
            db.session.add(settings)
            db.session.commit()
        return settings
    
    @staticmethod
    def update_ollama_host(user_id, ollama_host):
        """Update OLLAMA host for user"""
        settings = SettingsOperations.get_user_settings(user_id)
        settings.ollama_host = ollama_host
        db.session.commit()
        return settings
    
    @staticmethod
    def get_ollama_host(user_id):
        """Get OLLAMA host for user"""
        settings = SettingsOperations.get_user_settings(user_id)
        return settings.ollama_host