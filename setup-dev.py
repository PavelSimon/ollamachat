#!/usr/bin/env python3
"""
Development Environment Setup Script for OLLAMA Chat
This script sets up everything needed for development.
"""

import os
import sys
import subprocess
import secrets
from pathlib import Path

def print_banner():
    """Print setup banner"""
    print(" OLLAMA Chat Development Setup")
    print("=" * 40)

def check_python_version():
    """Check if Python version is compatible"""
    print(" Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("[ERROR] Python 3.8+ required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_uv_installation():
    """Check if uv is installed"""
    print(" Checking uv installation...")
    
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] uv {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("[ERROR] uv not found")
    print("[TIP] Install uv: https://docs.astral.sh/uv/getting-started/installation/")
    return False

def install_dependencies():
    """Install project dependencies"""
    print(" Installing dependencies...")
    
    try:
        # Sync all dependencies including dev dependencies
        subprocess.run(['uv', 'sync', '--dev'], check=True, cwd=Path.cwd())
        print("[OK] Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install dependencies: {e}")
        return False

def setup_environment_file():
    """Setup .env file for development"""
    print(" Setting up environment configuration...")
    
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if env_file.exists():
        print("[WARNING]  .env file already exists")
        response = input("   Overwrite? (y/N): ").lower()
        if response != 'y':
            print("   Skipping .env setup")
            return True
    
    if not env_example.exists():
        print("[ERROR] .env.example not found")
        return False
    
    # Generate a secure secret key
    secret_key = secrets.token_hex(32)
    
    # Read example file and replace placeholder
    content = env_example.read_text()
    content = content.replace('your-secret-key-here', secret_key)
    
    # Write to .env
    env_file.write_text(content)
    print("[OK] .env file created with secure secret key")
    
    return True

def setup_database_directory():
    """Ensure database directory exists"""
    print("  Setting up database directory...")
    
    instance_dir = Path('instance')
    instance_dir.mkdir(exist_ok=True)
    
    print("[OK] Database directory ready")
    return True

def setup_logs_directory():
    """Ensure logs directory exists"""
    print(" Setting up logs directory...")
    
    logs_dir = Path('logs')
    if not logs_dir.exists():
        logs_dir.mkdir(exist_ok=True)
        
        # Create basic log files
        (logs_dir / 'ollama_chat.log').touch()
        (logs_dir / 'access.log').touch()
        (logs_dir / 'errors.log').touch()
        (logs_dir / 'performance.log').touch()
    
    print("[OK] Logs directory ready")
    return True

def test_imports():
    """Test that all required modules can be imported"""
    print(" Testing imports...")
    
    required_modules = [
        'flask', 'flask_login', 'flask_wtf', 'flask_limiter',
        'requests', 'marshmallow', 'watchdog'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   [OK] {module}")
        except ImportError:
            print(f"   [ERROR] {module}")
            return False
    
    print("[OK] All imports successful")
    return True

def display_next_steps():
    """Display next steps for the user"""
    print("\n Setup Complete!")
    print("-" * 20)
    print("Next steps:")
    print("1. Start development server:")
    print("   uv run python dev.py")
    print()
    print("2. Or start manually:")
    print("   uv run python app.py")
    print()
    print("3. Visit: http://127.0.0.1:5000")
    print()
    print("Development features:")
    print("• Auto-restart on file changes")
    print("• Enhanced console logging")
    print("• Debug mode enabled")
    print("• SQLite database in instance/")
    print()
    print("Configuration:")
    print("• Edit .env for custom settings")
    print("• Default OLLAMA: http://localhost:11434")
    print("• Logs in logs/ directory")

def main():
    """Main setup function"""
    print_banner()
    
    # Check prerequisites
    if not check_python_version():
        return 1
    
    if not check_uv_installation():
        return 1
    
    # Setup steps
    setup_steps = [
        install_dependencies,
        setup_environment_file,
        setup_database_directory,
        setup_logs_directory,
        test_imports,
    ]
    
    for step in setup_steps:
        if not step():
            print(f"\n[ERROR] Setup failed at: {step.__name__}")
            return 1
    
    display_next_steps()
    return 0

if __name__ == '__main__':
    sys.exit(main())