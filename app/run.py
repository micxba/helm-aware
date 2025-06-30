#!/usr/bin/env python3
"""
Helm Aware - ArgoCD Chart Analysis Application
Main entry point for the Flask application
"""

import os
import logging
import sys
from app import create_app

def setup_logging():
    """Setup comprehensive logging configuration"""
    # Get log level from environment
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/tmp/helm-aware.log') if os.path.exists('/tmp') else logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers to DEBUG if needed
    if log_level == 'DEBUG':
        logging.getLogger('app').setLevel(logging.DEBUG)
        logging.getLogger('app.services').setLevel(logging.DEBUG)
        logging.getLogger('kubernetes').setLevel(logging.DEBUG)
        logging.getLogger('urllib3').setLevel(logging.DEBUG)

def main():
    """Main application entry point"""
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Helm Aware application...")
    
    try:
        app = create_app()
        logger.info("Flask application created successfully")
        
        # Get configuration from environment variables
        host = os.environ.get('HOST', '0.0.0.0')
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('DEBUG', 'false').lower() == 'true'
        
        logger.info(f"Configuration - Host: {host}, Port: {port}, Debug: {debug}")
        
        print(f"🚀 Starting Helm Aware application on {host}:{port}")
        print(f"📊 ArgoCD Chart Analysis Dashboard")
        print(f"🔗 Access the application at: http://{host}:{port}")
        print(f"📝 Log level: {os.environ.get('LOG_LEVEL', 'INFO')}")
        
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True  # Enable threading for better performance
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        print(f"❌ Failed to start application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 