import sys
import os

# Add your project directory to the path
path = '/home/Mitu624/study-platform'
if path not in sys.path:
    sys.path.append(path)

# Set environment variable
os.environ['SECRET_KEY'] = 'your-secret-key-here'

# Import your Flask app
from app import app as application