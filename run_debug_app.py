#!/usr/bin/env python3
"""
Run the app with maximum debugging to see where requests get stuck
"""

import os
import sys

# Enable maximum debugging
os.environ['VERBOSE_LOGS'] = 'true'
os.environ['LOG_TO_CONSOLE'] = 'true'
os.environ['LOG_LEVEL'] = 'DEBUG'
os.environ['FLASK_ENV'] = 'development'

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔍 Starting app with MAXIMUM debugging enabled")
print("=" * 60)
print("Environment variables set:")
print(f"  VERBOSE_LOGS = {os.environ.get('VERBOSE_LOGS')}")
print(f"  LOG_TO_CONSOLE = {os.environ.get('LOG_TO_CONSOLE')}")
print(f"  LOG_LEVEL = {os.environ.get('LOG_LEVEL')}")
print("=" * 60)
print()
print("When you make a request in the browser, watch this console")
print("for detailed logs to see where the request gets stuck.")
print()
print("Press Ctrl+C to stop the server")
print("=" * 60)

try:
    from app import app
    app.run(debug=True, host='0.0.0.0', port=5000)
except Exception as e:
    print(f"❌ Error starting app: {e}")
    import traceback
    traceback.print_exc()