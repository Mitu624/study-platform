#!/usr/bin/env python3
"""
Entry point for the Study Platform application.
Run this file to start the server.
"""

from app import app

if __name__ == '__main__':
    print("=" * 50)
    print("Study Platform Starting...")
    print("=" * 50)
    print(f" * Debug mode: {app.debug}")
    print(f" * Database: SQLite")
    print(f" * Upload folder: {app.config['UPLOAD_FOLDER']}")
    print("=" * 50)
    print(" * Server will be available at: http://localhost:5000")
    print(" * Press CTRL+C to stop")
    print("=" * 50)
    
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )