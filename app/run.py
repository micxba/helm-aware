#!/usr/bin/env python3
"""
Helm Aware - ArgoCD Chart Analysis Application
Main entry point for the Flask application
"""

import os
import logging
from app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main application entry point"""
    app = create_app()
    
    # Get configuration from environment variables
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    print(f"🚀 Starting Helm Aware application on {host}:{port}")
    print(f"📊 ArgoCD Chart Analysis Dashboard")
    print(f"🔗 Access the application at: http://{host}:{port}")
    
    app.run(
        host=host,
        port=port,
        debug=debug
    )

if __name__ == '__main__':
    main() 