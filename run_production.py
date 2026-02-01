#!/usr/bin/env python
"""
EstradaBot - Production Server Launcher

This script starts the production server using Waitress (Windows-compatible).
For Linux/Unix servers, you can also use Gunicorn.

Usage:
    python run_production.py

Environment Variables (set in .env file):
    - SECRET_KEY: Secret key for sessions (required, generate random string)
    - ADMIN_USERNAME: Admin username (default: admin)
    - ADMIN_PASSWORD: Admin password (required, change from default)
    - HOST: Server host (default: 0.0.0.0)
    - PORT: Server port (default: 5000)
    - BEHIND_PROXY: Set to 'true' if behind HTTPS reverse proxy

For HTTPS:
    Use a reverse proxy (nginx, Apache, IIS) to handle SSL termination.
    Set BEHIND_PROXY=true in your .env file.

Example nginx configuration is provided in deployment/nginx.conf.example
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify required settings
if os.environ.get('SECRET_KEY', '').startswith('dev-') or not os.environ.get('SECRET_KEY'):
    print("=" * 60)
    print("WARNING: No SECRET_KEY set in environment!")
    print("Please set a random SECRET_KEY in your .env file.")
    print("Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\"")
    print("=" * 60)
    sys.exit(1)

if os.environ.get('ADMIN_PASSWORD', 'admin') == 'admin':
    print("=" * 60)
    print("WARNING: Using default admin password!")
    print("Please set ADMIN_PASSWORD in your .env file.")
    print("=" * 60)
    # Don't exit, but warn

# Set production environment
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'false'

# Import and run
from app import app, run_production

if __name__ == '__main__':
    run_production()
