#!/usr/bin/env python3
"""
Development Environment Checker for OLLAMA Chat
This script verifies that the development environment is properly configured.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_file_exists(file_path, description, required=True):
    """Check if a file exists and report status"""
    path = Path(file_path)
    if path.exists():
        print(f"[OK] {description}: {file_path}")
        return True
    else:
        status = "[MISSING]" if required else "[OPTIONAL]"
        print(f"{status} {description}: {file_path} {'(missing - required)' if required else '(missing - optional)'}")
        return not required

def check_directory_exists(dir_path, description, create_if_missing=False):
    """Check if a directory exists and optionally create it"""
    path = Path(dir_path)
    if path.exists() and path.is_dir():
        print(f"[OK] {description}: {dir_path}")
        return True
    else:
        if create_if_missing:
            path.mkdir(parents=True, exist_ok=True)
            print(f"[CREATED] {description}: {dir_path}")
            return True
        else:
            print(f"[MISSING] {description}: {dir_path} (missing)")
            return False

def check_python_modules():
    """Check if required Python modules are available"""
    print("\nPython Modules:")
    modules = {
        'flask': 'Flask web framework',
        'flask_login': 'Flask-Login for authentication',
        'flask_wtf': 'Flask-WTF for forms',
        'flask_limiter': 'Flask-Limiter for rate limiting',
        'requests': 'HTTP requests library',
        'marshmallow': 'Data serialization',
        'watchdog': 'File system monitoring (dev only)',
        'pytest': 'Testing framework (dev only)',
    }
    
    all_good = True
    for module, description in modules.items():
        try:
            __import__(module)
            print(f"[OK] {module}: {description}")
        except ImportError:
            print(f"[MISSING] {module}: {description} (missing)")
            all_good = False
    
    return all_good

def check_configuration_files():
    """Check if configuration files exist"""
    print("\nConfiguration Files:")
    files = [
        ('.env.example', 'Environment template', True),
        ('.env', 'Environment configuration', False),
        ('pyproject.toml', 'Project configuration', True),
        ('uv.lock', 'Dependencies lock file', False),
    ]
    
    all_good = True
    for file_path, description, required in files:
        if not check_file_exists(file_path, description, required):
            all_good = False
    
    return all_good

def check_application_files():
    """Check if core application files exist"""
    print("\nApplication Files:")
    files = [
        ('app.py', 'Main application', True),
        ('config.py', 'Configuration module', True),
        ('models.py', 'Database models', True),
        ('forms.py', 'Web forms', True),
        ('dev.py', 'Development server', True),
        ('setup-dev.py', 'Development setup', True),
    ]
    
    all_good = True
    for file_path, description, required in files:
        if not check_file_exists(file_path, description, required):
            all_good = False
    
    return all_good

def check_directories():
    """Check if required directories exist"""
    print("\nDirectories:")
    dirs = [
        ('routes', 'Route blueprints', False),
        ('templates', 'HTML templates', False),
        ('static', 'Static assets', False),
        ('static/css', 'CSS files', False),
        ('static/js', 'JavaScript files', False),
        ('tests', 'Test files', False),
        ('instance', 'Database directory', True),
        ('logs', 'Log files', True),
    ]
    
    all_good = True
    for dir_path, description, create_if_missing in dirs:
        if not check_directory_exists(dir_path, description, create_if_missing):
            all_good = False
    
    return all_good

def check_environment_variables():
    """Check development environment variables"""
    print("\nEnvironment Variables:")
    
    # Check if .env file exists and load it
    env_file = Path('.env')
    if env_file.exists():
        print("[OK] .env file found")
        # Could load and check specific variables here
    else:
        print("[OPTIONAL] .env file not found (will use defaults)")
    
    # Check important environment variables
    important_vars = {
        'FLASK_ENV': 'Flask environment',
        'SECRET_KEY': 'Application secret key',
        'DATABASE_URL': 'Database connection',
        'DEFAULT_OLLAMA_HOST': 'OLLAMA server URL',
    }
    
    for var_name, description in important_vars.items():
        value = os.environ.get(var_name)
        if value:
            print(f"[OK] {var_name}: {description}")
        else:
            print(f"[DEFAULT] {var_name}: {description} (not set - will use default)")
    
    return True

def check_external_tools():
    """Check if external tools are available"""
    print("\nExternal Tools:")
    tools = {
        'uv': 'Python package manager',
        'python': 'Python interpreter',
    }
    
    all_good = True
    for tool, description in tools.items():
        try:
            result = subprocess.run([tool, '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print(f"[OK] {tool}: {description} ({version})")
            else:
                print(f"[ERROR] {tool}: {description} (not working)")
                all_good = False
        except FileNotFoundError:
            print(f"[MISSING] {tool}: {description} (not found)")
            all_good = False
    
    return all_good

def provide_recommendations():
    """Provide recommendations for fixing issues"""
    print("\nRecommendations:")
    print("If you see any [MISSING] or [ERROR] items above:")
    print()
    print("1. Missing dependencies:")
    print("   uv sync --dev")
    print()
    print("2. Missing .env file:")
    print("   cp .env.example .env")
    print("   # Then edit .env with your settings")
    print()
    print("3. Missing directories:")
    print("   Will be created automatically by setup-dev.py")
    print()
    print("4. To set up everything:")
    print("   uv run python setup-dev.py")
    print()
    print("5. To start development server:")
    print("   uv run python dev.py")

def main():
    """Main checking function"""
    print("OLLAMA Chat Development Environment Check")
    print("=" * 50)
    
    checks = [
        check_configuration_files,
        check_application_files,
        check_directories,
        check_python_modules,
        check_environment_variables,
        check_external_tools,
    ]
    
    all_checks_passed = True
    for check in checks:
        if not check():
            all_checks_passed = False
    
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("Environment check passed!")
        print("Ready for development")
        print("\nStart development server with:")
        print("  uv run python dev.py")
    else:
        print("Some issues found")
        provide_recommendations()
    
    return 0 if all_checks_passed else 1

if __name__ == '__main__':
    sys.exit(main())