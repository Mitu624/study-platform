#!/usr/bin/env python3
"""
Complete database reset script
Run this to completely reset your database
"""

import os
import sys
import shutil

def reset_database():
    print("=" * 50)
    print("DATABASE RESET UTILITY")
    print("=" * 50)
    
    # Find and delete database file
    db_files = ['database.db', 'instance/database.db']
    for db_file in db_files:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"✅ Deleted: {db_file}")
    
    # Delete pycache directories
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            shutil.rmtree(pycache_path)
            print(f"✅ Deleted: {pycache_path}")
    
    # Delete .pyc files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))
                print(f"✅ Deleted: {os.path.join(root, file)}")
    
    print("=" * 50)
    print("✅ Reset complete! Now run your app to recreate the database.")
    print("=" * 50)

if __name__ == "__main__":
    response = input("This will delete your database and all data. Continue? (y/n): ")
    if response.lower() == 'y':
        reset_database()
    else:
        print("Cancelled.")