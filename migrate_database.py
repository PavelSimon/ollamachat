#!/usr/bin/env python3
"""
Database migration script for OLLAMA Chat
Adds performance indexes to existing tables
"""

import os
import sqlite3
import time
import shutil
from pathlib import Path
from app import app
from models import db


def backup_database():
    """Create a backup of the current database"""
    db_path = Path('instance/chat.db')
    if db_path.exists():
        backup_path = Path(f'instance/chat_backup_{int(time.time())}.db')
        shutil.copy2(db_path, backup_path)
        print(f"Database backed up to: {backup_path}")
        return backup_path
    return None


def check_indexes_exist():
    """Check if the new indexes already exist"""
    db_path = 'instance/chat.db'
    if not os.path.exists(db_path):
        print("Database does not exist yet")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for our new indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
    existing_indexes = [row[0] for row in cursor.fetchall()]
    
    required_indexes = [
        'idx_chats_user_updated',
        'idx_chats_user_created', 
        'idx_messages_chat_created',
        'idx_messages_chat_user'
    ]
    
    missing_indexes = [idx for idx in required_indexes if idx not in existing_indexes]
    
    conn.close()
    
    if missing_indexes:
        print(f"Missing indexes: {missing_indexes}")
        return False
    else:
        print("All required indexes already exist")
        return True


def create_indexes_manually():
    """Create indexes manually on existing database"""
    db_path = 'instance/chat.db'
    if not os.path.exists(db_path):
        print("Database does not exist, indexes will be created automatically")
        return True
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_chats_user_updated ON chats(user_id, updated_at)",
        "CREATE INDEX IF NOT EXISTS idx_chats_user_created ON chats(user_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_messages_chat_created ON messages(chat_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_messages_chat_user ON messages(chat_id, is_user)"
    ]
    
    try:
        for sql in indexes_sql:
            print(f"Creating index: {sql}")
            cursor.execute(sql)
        
        conn.commit()
        print("All indexes created successfully")
        return True
        
    except Exception as e:
        print(f"Error creating indexes: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def analyze_performance():
    """Analyze database performance after adding indexes"""
    db_path = 'instance/chat.db'
    if not os.path.exists(db_path):
        print("Database does not exist for performance analysis")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table statistics
    cursor.execute("SELECT COUNT(*) FROM chats")
    chat_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM messages")
    message_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    print(f"\nDatabase Statistics:")
    print(f"   Users: {user_count}")
    print(f"   Chats: {chat_count}")
    print(f"   Messages: {message_count}")
    
    # Test query performance with EXPLAIN QUERY PLAN
    test_queries = [
        ("User chats by update time", "SELECT * FROM chats WHERE user_id = 1 ORDER BY updated_at DESC LIMIT 10"),
        ("Chat messages by time", "SELECT * FROM messages WHERE chat_id = 1 ORDER BY created_at ASC LIMIT 50"),
        ("Latest messages", "SELECT * FROM messages WHERE chat_id = 1 ORDER BY created_at DESC LIMIT 10")
    ]
    
    print(f"\nQuery Execution Plans:")
    for desc, query in test_queries:
        cursor.execute(f"EXPLAIN QUERY PLAN {query}")
        plan = cursor.fetchall()
        print(f"\n{desc}:")
        for row in plan:
            print(f"   {row[3]}")
    
    conn.close()


def main():
    """Main migration function"""
    
    print("Database Migration: Adding Performance Indexes")
    print("=" * 50)
    
    # Check if indexes already exist
    if check_indexes_exist():
        print("Database migration not needed - indexes already exist")
        analyze_performance()
        return
    
    # Backup database if it exists
    backup_path = backup_database()
    
    # Create indexes
    if create_indexes_manually():
        print("Database migration completed successfully!")
        analyze_performance()
    else:
        print("Database migration failed!")
        if backup_path:
            print(f"Database backup available at: {backup_path}")
        return False
    
    return True


if __name__ == '__main__':
    main()