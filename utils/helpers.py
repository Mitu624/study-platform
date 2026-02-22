"""
Helper functions for file handling and utilities.
"""

import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from PIL import Image
import mimetypes

def get_file_extension(filename):
    """Get file extension from filename"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def is_allowed_file(filename):
    """Check if file extension is allowed"""
    ext = get_file_extension(filename)
    allowed_extensions = current_app.config['ALLOWED_IMAGE_EXTENSIONS'].union(
        current_app.config['ALLOWED_DOCUMENT_EXTENSIONS']
    )
    return ext in allowed_extensions

def is_allowed_image(filename):
    """Check if file is an allowed image type"""
    ext = get_file_extension(filename)
    return ext in current_app.config['ALLOWED_IMAGE_EXTENSIONS']

def is_allowed_document(filename):
    """Check if file is an allowed document type"""
    ext = get_file_extension(filename)
    return ext in current_app.config['ALLOWED_DOCUMENT_EXTENSIONS']

def save_uploaded_file(file, subfolder):
    """
    Save uploaded file with unique filename.
    
    Args:
        file: File object from request
        subfolder: Subfolder within uploads directory
    
    Returns:
        tuple: (relative_path, file_size)
    """
    # Generate unique filename
    original_filename = secure_filename(file.filename)
    file_ext = get_file_extension(original_filename)
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
    
    # Create subfolder if not exists
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(upload_path, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_path, unique_filename)
    file.save(file_path)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Optimize images
    if file_ext in current_app.config['ALLOWED_IMAGE_EXTENSIONS']:
        optimize_image(file_path)
    
    return os.path.join(subfolder, unique_filename), file_size

def optimize_image(file_path):
    """
    Optimize image for web viewing.
    
    Args:
        file_path: Path to the image file
    """
    try:
        img = Image.open(file_path)
        
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Resize if too large
        if img.width > 1920 or img.height > 1080:
            img.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
        
        # Save with optimization
        img.save(file_path, optimize=True, quality=85)
        
    except Exception as e:
        current_app.logger.error(f"Error optimizing image {file_path}: {e}")

def get_file_type(filename):
    """
    Determine file type category based on extension.
    
    Args:
        filename: Name of the file
    
    Returns:
        str: File type category (image, pdf, ppt, csv, text, other)
    """
    ext = get_file_extension(filename)
    
    if ext in current_app.config['ALLOWED_IMAGE_EXTENSIONS']:
        return 'image'
    elif ext in ['pdf']:
        return 'pdf'
    elif ext in ['ppt', 'pptx']:
        return 'ppt'
    elif ext in ['csv']:
        return 'csv'
    elif ext in ['txt', 'md']:
        return 'text'
    else:
        return 'other'

def format_file_size(size_bytes):
    """
    Convert bytes to human readable format.
    
    Args:
        size_bytes: File size in bytes
    
    Returns:
        str: Formatted file size
    """
    if size_bytes is None:
        return 'Unknown'
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def get_mime_type(filename):
    """
    Get MIME type for a file.
    
    Args:
        filename: Name of the file
    
    Returns:
        str: MIME type
    """
    ext = get_file_extension(filename)
    return current_app.config['MIME_TYPES'].get(ext, 'application/octet-stream')

def optimize_image(file_path):
    """Skip optimization if Pillow is not available"""
    try:
        from PIL import Image
        img = Image.open(file_path)
        
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Resize if too large
        if img.width > 1920 or img.height > 1080:
            img.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
        
        # Save with optimization
        img.save(file_path, optimize=True, quality=85)
        
    except ImportError:
        # Pillow not available - skip optimization
        pass
    except Exception as e:
        current_app.logger.error(f"Error optimizing image {file_path}: {e}")