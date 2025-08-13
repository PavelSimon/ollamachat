#!/usr/bin/env python3
"""
Configuration validation script for OLLAMA Chat
Run this script to validate your environment configuration before deployment
"""

import os
import sys
import secrets
from pathlib import Path


def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = Path('.env')
    env_example_path = Path('.env.example')
    
    print("🔍 Checking environment configuration...")
    
    if not env_example_path.exists():
        print("❌ .env.example file not found!")
        return False
    else:
        print("✅ .env.example found")
    
    if not env_path.exists():
        print("⚠️  .env file not found. Copy .env.example to .env and configure it.")
        return False
    else:
        print("✅ .env file found")
    
    return True


def validate_secret_key():
    """Validate SECRET_KEY configuration"""
    secret_key = os.environ.get('SECRET_KEY')
    
    print("\n🔐 Checking SECRET_KEY configuration...")
    
    if not secret_key:
        print("❌ SECRET_KEY not set in environment!")
        print("   Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'")
        return False
    
    if secret_key == 'your-secret-key-here':
        print("❌ SECRET_KEY is still set to default placeholder!")
        print("   Generate a secure key: python -c 'import secrets; print(secrets.token_hex(32))'")
        return False
    
    if len(secret_key) < 32:
        print("⚠️  SECRET_KEY seems too short (< 32 characters). Consider using a longer key.")
        return False
    
    if secret_key == 'dev-secret-key-change-in-production':
        print("❌ SECRET_KEY is still set to development default!")
        print("   This is insecure for production use.")
        return False
    
    print("✅ SECRET_KEY appears to be properly configured")
    return True


def validate_production_settings():
    """Validate production-specific settings"""
    flask_env = os.environ.get('FLASK_ENV', 'development')
    
    print(f"\n🏭 Checking production settings (FLASK_ENV={flask_env})...")
    
    if flask_env == 'production':
        database_url = os.environ.get('DATABASE_URL')
        session_secure = os.environ.get('SESSION_COOKIE_SECURE', '').lower()
        
        if not database_url or 'sqlite' in database_url.lower():
            print("⚠️  Using SQLite in production. Consider PostgreSQL or MySQL for better performance.")
        else:
            print("✅ Production database configured")
        
        if session_secure != 'true':
            print("⚠️  SESSION_COOKIE_SECURE not set to true. Enable this when using HTTPS.")
        else:
            print("✅ Secure session cookies enabled")
    else:
        print("ℹ️  Not in production mode - skipping production-specific checks")
    
    return True


def validate_ollama_config():
    """Validate OLLAMA configuration"""
    ollama_host = os.environ.get('DEFAULT_OLLAMA_HOST', 'http://localhost:11434')
    
    print(f"\n🤖 Checking OLLAMA configuration...")
    print(f"   DEFAULT_OLLAMA_HOST: {ollama_host}")
    
    if ollama_host == 'http://192.168.1.23:11434':
        print("⚠️  Using hardcoded IP address. Consider updating to your actual OLLAMA server.")
    
    return True


def generate_secure_key():
    """Generate and display a secure secret key"""
    key = secrets.token_hex(32)
    print(f"\n🔑 Generated secure SECRET_KEY:")
    print(f"SECRET_KEY={key}")
    print("\nAdd this to your .env file!")


def main():
    """Main validation function"""
    print("OLLAMA Chat Configuration Validator")
    print("=" * 40)
    
    # Load .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file")
    except ImportError:
        print("ℹ️  python-dotenv not installed, reading from system environment")
    except Exception as e:
        print(f"⚠️  Could not load .env file: {e}")
    
    all_good = True
    
    # Run all checks
    all_good &= check_env_file()
    all_good &= validate_secret_key()
    all_good &= validate_production_settings()
    all_good &= validate_ollama_config()
    
    print("\n" + "=" * 40)
    
    if all_good:
        print("🎉 Configuration looks good!")
        return 0
    else:
        print("❌ Configuration issues found. Please fix them before deployment.")
        
        # Offer to generate a secure key
        if not os.environ.get('SECRET_KEY') or os.environ.get('SECRET_KEY') in [
            'your-secret-key-here', 'dev-secret-key-change-in-production'
        ]:
            print("\nWould you like to generate a secure SECRET_KEY?")
            generate_secure_key()
        
        return 1


if __name__ == '__main__':
    sys.exit(main())