#!/usr/bin/env python3
"""
Test the fixed app
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Enable console logging to see what's happening
os.environ['LOG_TO_CONSOLE'] = 'true'
os.environ['VERBOSE_LOGS'] = 'true'

print("🔧 Testing Fixed App")
print("=" * 50)
print("Changes made:")
print("✅ Removed complex connection pooling")
print("✅ Simplified validation")
print("✅ Disabled internet search temporarily")
print("✅ Direct OLLAMA client usage")
print("✅ Simplified error handling")
print("=" * 50)
print()
print("Starting app... Try sending a message now!")
print("Watch this console for any errors.")
print()

try:
    from app import app
    app.run(debug=True, host='0.0.0.0', port=5000)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()