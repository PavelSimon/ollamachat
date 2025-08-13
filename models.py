from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

db = SQLAlchemy()

def get_default_ollama_host():
    """Get default OLLAMA host from environment or fallback"""
    return os.environ.get('DEFAULT_OLLAMA_HOST', 'http://localhost:11434')

class User(UserMixin, db.Model):
    """User model for authentication and user management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    chats = db.relationship('Chat', backref='user', lazy=True, cascade='all, delete-orphan')
    settings = db.relationship('UserSettings', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'

class UserSettings(db.Model):
    """User-specific settings"""
    __tablename__ = 'user_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    ollama_host = db.Column(db.String(255), default=get_default_ollama_host)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserSettings user_id={self.user_id} host={self.ollama_host}>'

class Chat(db.Model):
    """Chat conversation model"""
    __tablename__ = 'chats'
    __table_args__ = (
        # Index for sorting chats by update time for specific users
        db.Index('idx_chats_user_updated', 'user_id', 'updated_at'),
        # Index for sorting chats by creation time for specific users  
        db.Index('idx_chats_user_created', 'user_id', 'created_at'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('Message', backref='chat', lazy=True, cascade='all, delete-orphan', order_by='Message.created_at')
    
    def get_title(self):
        """Get chat title or generate from first message"""
        if self.title:
            return self.title
        if self.messages:
            first_message = self.messages[0].content
            return first_message[:50] + '...' if len(first_message) > 50 else first_message
        return f'Chat {self.id}'
    
    def __repr__(self):
        return f'<Chat {self.id}: {self.get_title()}>'

class Message(db.Model):
    """Individual message in a chat"""
    __tablename__ = 'messages'
    __table_args__ = (
        # Composite index for efficiently retrieving messages by chat and ordering by time
        db.Index('idx_messages_chat_created', 'chat_id', 'created_at'),
        # Index for filtering messages by user/AI type within chats
        db.Index('idx_messages_chat_user', 'chat_id', 'is_user'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, nullable=False, default=True)
    model_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        sender = 'User' if self.is_user else f'AI({self.model_name})'
        content_preview = self.content[:30] + '...' if len(self.content) > 30 else self.content
        return f'<Message {self.id}: {sender}: {content_preview}>'