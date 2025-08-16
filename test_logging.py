#!/usr/bin/env python3
"""
Test script to verify logging configuration
"""

import os
import logging
from enhanced_logging import setup_enhanced_logging
from flask import Flask

def test_logging():
    """Test the logging configuration"""
    print("Testing Logging Configuration")
    print("=" * 50)
    
    # Create a test Flask app
    app = Flask(__name__)
    
    # Test different log levels
    print("\n1. Testing with default settings (ERROR only):")
    with app.app_context():
        setup_enhanced_logging(app)
        
        logger = logging.getLogger('test')
        logger.debug("This DEBUG message should NOT appear")
        logger.info("This INFO message should NOT appear")
        logger.warning("This WARNING message should NOT appear")
        logger.error("This ERROR message SHOULD appear")
    
    print("\n2. Testing with VERBOSE_LOGS=true:")
    os.environ['VERBOSE_LOGS'] = 'true'
    os.environ['LOG_TO_CONSOLE'] = 'true'
    
    app2 = Flask(__name__)
    with app2.app_context():
        setup_enhanced_logging(app2)
        
        logger = logging.getLogger('test_verbose')
        logger.debug("This DEBUG message should NOT appear")
        logger.info("This INFO message SHOULD appear")
        logger.warning("This WARNING message SHOULD appear")
        logger.error("This ERROR message SHOULD appear")
    
    # Clean up environment
    os.environ.pop('VERBOSE_LOGS', None)
    os.environ.pop('LOG_TO_CONSOLE', None)
    
    print("\n" + "=" * 50)
    print("Logging test completed!")
    print("Check logs/ directory for log files")

if __name__ == "__main__":
    test_logging()