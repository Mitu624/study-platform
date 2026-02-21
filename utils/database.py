from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import os

db = SQLAlchemy()

# Association tables for many-to-many relationships
user_category_access = db.Table('user_category_access',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    uploaded_materials = db.relationship('StudyMaterial', backref='uploader', lazy='dynamic', foreign_keys='StudyMaterial.uploaded_by')
    created_categories = db.relationship('Category', backref='creator', lazy='dynamic', foreign_keys='Category.created_by')
    created_tasks = db.relationship('Task', backref='creator', lazy='dynamic', foreign_keys='Task.created_by')
    solutions = db.relationship('Solution', backref='solver', lazy='dynamic', foreign_keys='Solution.solved_by')
    accessible_categories = db.relationship('Category', secondary=user_category_access, 
                                          lazy='subquery', backref=db.backref('accessible_users', lazy=True))

class Category(db.Model):
    __tablename__ = 'category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    materials = db.relationship('StudyMaterial', backref='category', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='category', lazy='dynamic', cascade='all, delete-orphan')
    
    # Index for faster queries
    __table_args__ = (
        db.Index('idx_category_created_at', 'created_at'),
        db.Index('idx_category_name', 'name'),
    )

class StudyMaterial(db.Model):
    __tablename__ = 'study_material'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_type = db.Column(db.String(20), nullable=False)  # image, pdf, ppt, csv, text
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # Size in bytes
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    downloads = db.Column(db.Integer, default=0)
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_material_category', 'category_id'),
        db.Index('idx_material_uploaded_by', 'uploaded_by'),
        db.Index('idx_material_created_at', 'created_at'),
        db.Index('idx_material_file_type', 'file_type'),
    )

class Task(db.Model):
    __tablename__ = 'task'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)  # Now optional
    task_type = db.Column(db.String(20), default='text')  # 'text', 'image', 'pdf'
    file_path = db.Column(db.String(500))  # For image/pdf tasks
    file_size = db.Column(db.Integer)  # Size in bytes for file tasks
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    solutions = db.relationship('Solution', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_task_category', 'category_id'),
        db.Index('idx_task_created_by', 'created_by'),
        db.Index('idx_task_created_at', 'created_at'),
        db.Index('idx_task_type', 'task_type'),
    )

class Solution(db.Model):
    __tablename__ = 'solution'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)  # For text solutions
    file_path = db.Column(db.String(500))  # For image/document solutions
    solution_type = db.Column(db.String(20), nullable=False)  # 'text', 'image', or 'document'
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    solved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_solution_task', 'task_id'),
        db.Index('idx_solution_solved_by', 'solved_by'),
    )

# Initialize database
def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        from werkzeug.security import generate_password_hash
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@studyplatform.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")