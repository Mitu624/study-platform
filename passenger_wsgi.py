# passenger_wsgi.py
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/study-platform'  # Change 'yourusername' to your PythonAnywhere username
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Import your Flask app
from app import app as application  # noqa