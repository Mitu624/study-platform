from flask_login import LoginManager, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash, redirect, url_for
from functools import wraps
from .database import User, db

login_manager = LoginManager()

def init_auth(app):
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if not current_user.is_admin:
            flash('You need admin privileges to access this page.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def authenticate_user(username, password):
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        return user
    return None

def register_user(username, email, password):
    # Check if username already exists
    if User.query.filter_by(username=username).first():
        return False, 'Username already exists'
    
    # Check if email already registered
    if User.query.filter_by(email=email).first():
        return False, 'Email already registered'
    
    # Validate password strength
    if len(password) < 6:
        return False, 'Password must be at least 6 characters long'
    
    try:
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        return True, 'Registration successful! You can now log in.'
    except Exception as e:
        db.session.rollback()
        return False, f'Registration failed: {str(e)}'