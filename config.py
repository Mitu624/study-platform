import os
from datetime import timedelta

class Config:
    # PythonAnywhere can use SQLite (simpler) or MySQL (better for multiple users)
    # For SQLite (simpler, works out of the box):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
    
    # If you want MySQL instead (better for multiple concurrent users), uncomment:
    # SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://{username}:{password}@{host}/{databasename}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')
    
    # Upload configurations
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    
    # Pagination
    ITEMS_PER_PAGE = 20
    TASKS_PER_PAGE = 15
    
    # File extensions
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'ppt', 'pptx', 'csv', 'txt', 'md'}
    
    # MIME types
    MIME_TYPES = {
        'pdf': 'application/pdf',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'csv': 'text/csv',
        'txt': 'text/plain',
        'md': 'text/markdown',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'webp': 'image/webp'
    }