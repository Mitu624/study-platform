"""
Main application file for Study Platform.
Handles all routes and core functionality.
"""

import os
import mimetypes
from datetime import datetime
import traceback

# Add this for production database handling
if os.environ.get('RENDER'):
    # Running on Render - use PostgreSQL
    print("Running on Render - using PostgreSQL", file=sys.stderr)

from flask import (
    Flask, render_template, request, jsonify, 
    redirect, url_for, flash, send_file, abort,
    session, g
)
from flask_login import (
    login_user, logout_user, login_required, current_user
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from utils.database import db, init_db, User, Category, StudyMaterial, Task, Solution
from utils.auth import init_auth, admin_required, authenticate_user, register_user
from utils.helpers import *

# ==================== APP INITIALIZATION ====================

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
init_db(app)
init_auth(app)

# Ensure upload directories exist
upload_folders = [
    'materials/images',
    'materials/pdfs',
    'materials/ppts',
    'materials/csvs',
    'materials/texts',
    'solutions/images',
    'solutions/documents',
    'solutions/texts',
    'tasks/images',      # New folder for task images
    'tasks/pdfs'         # New folder for task PDFs
]

for folder in upload_folders:
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], folder), exist_ok=True)

# ==================== CONTEXT PROCESSORS ====================

@app.context_processor
def utility_processor():
    """Make utility functions available to all templates"""
    def get_file_icon(file_type):
        icons = {
            'image': 'fa-image',
            'pdf': 'fa-file-pdf',
            'ppt': 'fa-file-powerpoint',
            'csv': 'fa-file-csv',
            'text': 'fa-file-alt',
            'video': 'fa-video'
        }
        return icons.get(file_type, 'fa-file')
    
    def format_datetime(dt):
        if dt:
            return dt.strftime('%Y-%m-%d %H:%M')
        return ''
    
    return dict(
        get_file_icon=get_file_icon,
        format_datetime=format_datetime,
        now=datetime.utcnow
    )

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/')
def index():
    """Home page - redirects to login or dashboard"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template('login.html')
        
        user = authenticate_user(username, password)
        if user:
            login_user(user, remember=True)
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect to the page user wanted to access
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('register.html')
        
        success, message = register_user(username, email, password)
        flash(message, 'success' if success else 'error')
        
        if success:
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    username = current_user.username
    logout_user()
    flash(f'Goodbye, {username}!', 'success')
    return redirect(url_for('login'))

# ==================== MAIN DASHBOARD ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with overview and stats"""
    try:
        # Get recent categories
        categories = Category.query.order_by(
            Category.created_at.desc()
        ).limit(6).all()
        
        # Get recent tasks
        recent_tasks = Task.query.order_by(
            Task.created_at.desc()
        ).limit(6).all()
        
        # Get stats
        stats = {
            'total_categories': Category.query.count(),
            'total_materials': StudyMaterial.query.count(),
            'total_tasks': Task.query.count(),
            'total_solutions': Solution.query.count(),
            'my_materials': StudyMaterial.query.filter_by(uploaded_by=current_user.id).count(),
            'my_tasks': Task.query.filter_by(created_by=current_user.id).count(),
            'my_solutions': Solution.query.filter_by(solved_by=current_user.id).count()
        }
        
        # Get popular materials
        popular_materials = StudyMaterial.query.order_by(
            StudyMaterial.downloads.desc()
        ).limit(5).all()
        
        return render_template(
            'dashboard.html',
            categories=categories,
            recent_tasks=recent_tasks,
            stats=stats,
            popular_materials=popular_materials
        )
    
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', categories=[], recent_tasks=[], stats={})

# ==================== CATEGORY ROUTES ====================

@app.route('/categories')
@login_required
def categories():
    """Categories page with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = app.config['ITEMS_PER_PAGE']
    
    categories_pagination = Category.query.order_by(
        Category.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'categories.html',
        categories=categories_pagination.items,
        pagination=categories_pagination
    )

@app.route('/create_category', methods=['GET', 'POST'])
@login_required
def create_category():
    """Create a new category"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        # Validate input
        if not name:
            flash('Category name is required', 'error')
            return redirect(request.url)
        
        if len(name) < 3:
            flash('Category name must be at least 3 characters long', 'error')
            return redirect(request.url)
        
        if len(name) > 100:
            flash('Category name must be less than 100 characters', 'error')
            return redirect(request.url)
        
        # Check if category already exists
        existing = Category.query.filter_by(name=name).first()
        if existing:
            flash('A category with this name already exists', 'error')
            return redirect(request.url)
        
        try:
            category = Category(
                name=name,
                description=description if description else None,
                created_by=current_user.id
            )
            db.session.add(category)
            db.session.commit()
            
            flash(f'Category "{name}" created successfully!', 'success')
            return redirect(url_for('categories'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating category: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('create_category.html')

@app.route('/api/categories/<int:category_id>/materials')
@login_required
def get_category_materials(category_id):
    """API endpoint for lazy loading materials"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = app.config['ITEMS_PER_PAGE']
        
        # Verify category exists
        category = Category.query.get_or_404(category_id)
        
        materials = StudyMaterial.query.filter_by(category_id=category_id)\
            .order_by(StudyMaterial.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        materials_data = []
        for m in materials.items:
            materials_data.append({
                'id': m.id,
                'title': m.title,
                'description': m.description[:100] + '...' if m.description and len(m.description) > 100 else m.description,
                'file_type': m.file_type,
                'file_path': m.file_path,
                'file_size': format_file_size(m.file_size) if m.file_size else 'Unknown',
                'created_at': m.created_at.strftime('%Y-%m-%d %H:%M'),
                'uploader': m.uploader.username,
                'downloads': m.downloads
            })
        
        return jsonify({
            'materials': materials_data,
            'has_next': materials.has_next,
            'total': materials.total,
            'current_page': page
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== STUDY MATERIAL ROUTES ====================

@app.route('/upload_material', methods=['GET', 'POST'])
@login_required
def upload_material():
    """Upload study material"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id', type=int)
        file = request.files.get('file')
        
        # Validate inputs
        if not title:
            flash('Title is required', 'error')
            return redirect(request.url)
        
        if not category_id:
            flash('Please select a category', 'error')
            return redirect(request.url)
        
        if not file or file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        # Verify category exists
        category = Category.query.get(category_id)
        if not category:
            flash('Invalid category', 'error')
            return redirect(request.url)
        
        # Validate file type
        if not is_allowed_file(file.filename):
            flash('Invalid file type. Allowed: pdf, ppt, pptx, csv, txt, md, png, jpg, jpeg, gif, webp', 'error')
            return redirect(request.url)
        
        try:
            # Determine file type
            file_type = get_file_type(file.filename)
            
            # Save file
            subfolder = f"materials/{file_type}s"
            file_path, file_size = save_uploaded_file(file, subfolder)
            
            # Create database record
            material = StudyMaterial(
                title=title,
                description=description if description else None,
                file_type=file_type,
                file_path=file_path,
                file_size=file_size,
                category_id=category_id,
                uploaded_by=current_user.id
            )
            db.session.add(material)
            db.session.commit()
            
            flash(f'Material "{title}" uploaded successfully!', 'success')
            return redirect(url_for('categories'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error uploading file: {str(e)}', 'error')
            return redirect(request.url)
    
    # GET request - show upload form
    categories = Category.query.all()
    selected_category = request.args.get('category', type=int)
    
    return render_template(
        'upload_material.html',
        categories=categories,
        selected_category=selected_category
    )

# ==================== TASK ROUTES ====================

@app.route('/tasks')
@login_required
def tasks():
    """Tasks page with filtering and pagination"""
    try:
        category_id = request.args.get('category', type=int)
        page = request.args.get('page', 1, type=int)
        sort = request.args.get('sort', 'newest')
        
        query = Task.query
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        # Apply sorting
        if sort == 'newest':
            query = query.order_by(Task.created_at.desc())
        elif sort == 'oldest':
            query = query.order_by(Task.created_at.asc())
        elif sort == 'most_solutions':
            # This would need a subquery, keeping simple for now
            query = query.order_by(Task.created_at.desc())
        
        tasks_pagination = query.paginate(
            page=page,
            per_page=app.config['TASKS_PER_PAGE'],
            error_out=False
        )
        
        categories = Category.query.all()
        
        # Get solution counts for each task
        tasks_with_counts = []
        for task in tasks_pagination.items:
            task_dict = {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'created_at': task.created_at,
                'creator': task.creator,
                'category': task.category,
                'solutions_count': task.solutions.count()
            }
            tasks_with_counts.append(task_dict)
        
        return render_template(
            'tasks.html',
            tasks=tasks_with_counts,
            pagination=tasks_pagination,
            categories=categories,
            selected_category=category_id,
            current_sort=sort
        )
    
    except Exception as e:
        flash(f'Error loading tasks: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    """Add a new task (text, image, or PDF)"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category_id = request.form.get('category_id', type=int)
        task_type = request.form.get('task_type', 'text')
        
        # Validate inputs
        if not title:
            flash('Task title is required', 'error')
            return redirect(request.url)
        
        if len(title) < 3:
            flash('Task title must be at least 3 characters long', 'error')
            return redirect(request.url)
        
        if not category_id:
            flash('Please select a category', 'error')
            return redirect(request.url)
        
        # Verify category exists
        category = Category.query.get(category_id)
        if not category:
            flash('Invalid category', 'error')
            return redirect(request.url)
        
        try:
            if task_type == 'text':
                description = request.form.get('description', '').strip()
                
                if not description:
                    flash('Task description is required for text tasks', 'error')
                    return redirect(request.url)
                
                if len(description) < 10:
                    flash('Task description must be at least 10 characters long', 'error')
                    return redirect(request.url)
                
                task = Task(
                    title=title,
                    description=description,
                    task_type='text',
                    category_id=category_id,
                    created_by=current_user.id
                )
                
            elif task_type == 'image':
                file = request.files.get('task_file')
                
                if not file or file.filename == '':
                    flash('Please select an image file', 'error')
                    return redirect(request.url)
                
                # Check if it's an image
                ext = get_file_extension(file.filename)
                if ext not in app.config['ALLOWED_IMAGE_EXTENSIONS']:
                    flash('Invalid image file type. Allowed: png, jpg, jpeg, gif, webp', 'error')
                    return redirect(request.url)
                
                # Save file
                file_path, file_size = save_uploaded_file(file, 'tasks/images')
                
                task = Task(
                    title=title,
                    task_type='image',
                    file_path=file_path,
                    file_size=file_size,
                    category_id=category_id,
                    created_by=current_user.id
                )
                
            elif task_type == 'pdf':
                file = request.files.get('task_file')
                
                if not file or file.filename == '':
                    flash('Please select a PDF file', 'error')
                    return redirect(request.url)
                
                # Check if it's a PDF
                ext = get_file_extension(file.filename)
                if ext != 'pdf':
                    flash('Invalid file type. Please upload a PDF file', 'error')
                    return redirect(request.url)
                
                # Save file
                file_path, file_size = save_uploaded_file(file, 'tasks/pdfs')
                
                task = Task(
                    title=title,
                    task_type='pdf',
                    file_path=file_path,
                    file_size=file_size,
                    category_id=category_id,
                    created_by=current_user.id
                )
            
            else:
                flash('Invalid task type', 'error')
                return redirect(request.url)
            
            db.session.add(task)
            db.session.commit()
            
            flash('Task created successfully!', 'success')
            return redirect(url_for('tasks'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating task: {str(e)}', 'error')
            return redirect(request.url)
    
    # GET request - show add task form
    categories = Category.query.all()
    return render_template('add_task.html', categories=categories)

@app.route('/task/<int:task_id>')
@login_required
def view_task(task_id):
    """View task details and solutions"""
    try:
        task = Task.query.get_or_404(task_id)
        
        # Get solutions with pagination
        page = request.args.get('page', 1, type=int)
        solutions = Solution.query.filter_by(task_id=task_id)\
            .order_by(Solution.created_at.desc())\
            .paginate(page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
        
        # Check if current user has already submitted a solution
        user_solution = Solution.query.filter_by(
            task_id=task_id,
            solved_by=current_user.id
        ).first()
        
        return render_template(
            'view_task.html',
            task=task,
            solutions=solutions.items,
            pagination=solutions,
            user_solution=user_solution
        )
    
    except Exception as e:
        flash(f'Error loading task: {str(e)}', 'error')
        return redirect(url_for('tasks'))

@app.route('/submit_solution/<int:task_id>', methods=['GET', 'POST'])
@login_required
def submit_solution(task_id):
    """Submit a solution for a task"""
    task = Task.query.get_or_404(task_id)
    
    # Check if user already submitted a solution
    existing = Solution.query.filter_by(
        task_id=task_id,
        solved_by=current_user.id
    ).first()
    
    if existing:
        flash('You have already submitted a solution for this task', 'warning')
        return redirect(url_for('view_task', task_id=task_id))
    
    if request.method == 'POST':
        solution_type = request.form.get('solution_type')
        
        if solution_type == 'text':
            content = request.form.get('content', '').strip()
            
            if not content:
                flash('Solution content is required', 'error')
                return redirect(request.url)
            
            try:
                solution = Solution(
                    content=content,
                    solution_type='text',
                    task_id=task_id,
                    solved_by=current_user.id
                )
                db.session.add(solution)
                db.session.commit()
                
                flash('Solution submitted successfully!', 'success')
                return redirect(url_for('view_task', task_id=task_id))
            
            except Exception as e:
                db.session.rollback()
                flash(f'Error submitting solution: {str(e)}', 'error')
                return redirect(request.url)
            
        elif solution_type == 'image':
            file = request.files.get('image')
            
            if not file or file.filename == '':
                flash('Please select an image file', 'error')
                return redirect(request.url)
            
            if not is_allowed_image(file.filename):
                flash('Invalid image file type. Allowed: png, jpg, jpeg, gif, webp', 'error')
                return redirect(request.url)
            
            try:
                file_path, _ = save_uploaded_file(file, 'solutions/images')
                
                solution = Solution(
                    file_path=file_path,
                    solution_type='image',
                    task_id=task_id,
                    solved_by=current_user.id
                )
                db.session.add(solution)
                db.session.commit()
                
                flash('Solution submitted successfully!', 'success')
                return redirect(url_for('view_task', task_id=task_id))
            
            except Exception as e:
                db.session.rollback()
                flash(f'Error uploading solution: {str(e)}', 'error')
                return redirect(request.url)
        
        elif solution_type == 'document':
            file = request.files.get('document')
            
            if not file or file.filename == '':
                flash('Please select a document file', 'error')
                return redirect(request.url)
            
            # Check file extension
            ext = get_file_extension(file.filename)
            allowed_docs = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'csv', 'txt', 'md'}
            
            if ext not in allowed_docs:
                flash('Invalid document file type. Allowed: pdf, doc, docx, ppt, pptx, csv, txt, md', 'error')
                return redirect(request.url)
            
            try:
                # Create subfolder based on document type
                subfolder = 'solutions/documents'
                file_path, _ = save_uploaded_file(file, subfolder)
                
                # Determine document type for display
                doc_type = 'document'
                if ext in ['pdf']:
                    doc_type = 'pdf'
                elif ext in ['ppt', 'pptx']:
                    doc_type = 'ppt'
                elif ext in ['csv']:
                    doc_type = 'csv'
                elif ext in ['txt', 'md']:
                    doc_type = 'text'
                
                solution = Solution(
                    file_path=file_path,
                    solution_type='document',
                    task_id=task_id,
                    solved_by=current_user.id
                )
                db.session.add(solution)
                db.session.commit()
                
                flash('Solution submitted successfully!', 'success')
                return redirect(url_for('view_task', task_id=task_id))
            
            except Exception as e:
                db.session.rollback()
                flash(f'Error uploading document: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('Invalid solution type', 'error')
            return redirect(request.url)
    
    # GET request - show submission form
    return render_template('submit_solution.html', task=task)

@app.route('/api/tasks/<int:task_id>/solutions')
@login_required
def get_task_solutions(task_id):
    """API endpoint for lazy loading solutions"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = app.config['ITEMS_PER_PAGE']
        
        # Verify task exists
        task = Task.query.get_or_404(task_id)
        
        solutions = Solution.query.filter_by(task_id=task_id)\
            .order_by(Solution.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        solutions_data = []
        for s in solutions.items:
            solution_data = {
                'id': s.id,
                'solution_type': s.solution_type,
                'created_at': s.created_at.strftime('%Y-%m-%d %H:%M'),
                'solver': s.solver.username,
                'solver_id': s.solved_by
            }
            
            if s.solution_type == 'text':
                solution_data['content'] = s.content[:200] + '...' if len(s.content) > 200 else s.content
            else:
                solution_data['file_path'] = s.file_path
            
            solutions_data.append(solution_data)
        
        return jsonify({
            'solutions': solutions_data,
            'has_next': solutions.has_next,
            'current_page': page,
            'total': solutions.total
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete/solution/<int:solution_id>')
@login_required
def delete_solution(solution_id):
    """Delete a solution (admin or solution creator only)"""
    solution = Solution.query.get_or_404(solution_id)
    task_id = solution.task_id
    
    # Check if user is admin or solution creator
    if not (current_user.is_admin or solution.solved_by == current_user.id):
        flash('You do not have permission to delete this solution', 'error')
        return redirect(url_for('view_task', task_id=task_id))
    
    try:
        # Delete file if it exists
        if solution.file_path:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], solution.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        db.session.delete(solution)
        db.session.commit()
        
        flash('Solution deleted successfully', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting solution: {str(e)}', 'error')
    
    return redirect(url_for('view_task', task_id=task_id))

# ==================== FILE VIEWING ROUTES ====================

@app.route('/view/<path:file_path>')
@login_required
def view_file(file_path):
    """View file within the application"""
    try:
        from urllib.parse import unquote
        file_path = unquote(file_path)
        
        # Find the material
        material = StudyMaterial.query.filter_by(file_path=file_path).first()
        
        if not material:
            flash('File not found in database', 'error')
            return redirect(url_for('categories'))
        
        # Construct full file path
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], file_path)
        
        # Check if file exists on disk
        if not os.path.exists(full_path):
            flash('File not found on server', 'error')
            return redirect(url_for('categories'))
        
        # For PowerPoint files, use Office Online Viewer
        if material.file_type == 'ppt':
            file_url = url_for('download_file', file_path=material.file_path, _external=True)
            office_viewer_url = f"https://view.officeapps.live.com/op/view.aspx?src={file_url}"
            return render_template('view_ppt.html', material=material, office_viewer_url=office_viewer_url)
        
        # For all other file types, use regular viewer
        return render_template('view_file.html', material=material)
        
    except Exception as e:
        app.logger.error(f"Error in view_file: {str(e)}")
        flash(f'Error viewing file: {str(e)}', 'error')
        return redirect(url_for('categories'))

# ==================== FILE DOWNLOAD ROUTES ====================

@app.route('/download/<path:file_path>')
@login_required
def download_file(file_path):
    """Serve files with permission check"""
    try:
        # Security check - prevent directory traversal
        safe_path = os.path.normpath(file_path)
        if safe_path.startswith('..') or safe_path.startswith('/'):
            abort(403)
        
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_path)
        
        # Check if file exists
        if not os.path.exists(full_path):
            abort(404)
        
        # Security: Ensure file is within uploads directory
        real_upload_path = os.path.realpath(app.config['UPLOAD_FOLDER'])
        real_file_path = os.path.realpath(full_path)
        if not real_file_path.startswith(real_upload_path):
            abort(403)
        
        # Increment download count for materials
        if 'materials' in safe_path:
            material = StudyMaterial.query.filter_by(file_path=safe_path).first()
            if material:
                material.downloads += 1
                db.session.commit()
        
        # Get filename for download
        filename = os.path.basename(file_path)
        
        # Determine if file should be displayed inline or downloaded
        as_attachment = request.args.get('download', 'false').lower() == 'true'
        
        return send_file(
            full_path,
            as_attachment=as_attachment,
            download_name=filename,
            mimetype=app.config['MIME_TYPES'].get(
                filename.split('.')[-1].lower(),
                'application/octet-stream'
            )
        )
    
    except Exception as e:
        app.logger.error(f"Error serving file: {e}")
        abort(404)

# ==================== ADMIN ROUTES ====================

@app.route('/admin/delete/material/<int:material_id>')
@login_required
@admin_required
def delete_material(material_id):
    """Delete a study material (admin only)"""
    material = StudyMaterial.query.get_or_404(material_id)
    
    try:
        # Delete file
        if material.file_path:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], material.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        db.session.delete(material)
        db.session.commit()
        
        flash('Material deleted successfully', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting material: {str(e)}', 'error')
    
    return redirect(url_for('categories'))

@app.route('/admin/delete/task/<int:task_id>')
@login_required
def delete_task(task_id):
    """Delete a task (admin or task creator only)"""
    task = Task.query.get_or_404(task_id)
    
    # Check if user is admin or task creator
    if not (current_user.is_admin or task.created_by == current_user.id):
        flash('You do not have permission to delete this task', 'error')
        return redirect(url_for('tasks'))
    
    try:
        # Delete associated solutions and files
        for solution in task.solutions:
            if solution.file_path:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], solution.file_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        db.session.delete(task)
        db.session.commit()
        
        flash('Task deleted successfully', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting task: {str(e)}', 'error')
    
    return redirect(url_for('tasks'))

@app.route('/admin/delete/category/<int:category_id>')
@login_required
@admin_required
def delete_category(category_id):
    """Delete a category and all its contents (admin only)"""
    category = Category.query.get_or_404(category_id)
    
    try:
        # Delete all associated files
        for material in category.materials:
            if material.file_path:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], material.file_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        for task in category.tasks:
            for solution in task.solutions:
                if solution.file_path:
                    sol_path = os.path.join(app.config['UPLOAD_FOLDER'], solution.file_path)
                    if os.path.exists(sol_path):
                        os.remove(sol_path)
        
        db.session.delete(category)
        db.session.commit()
        
        flash(f'Category "{category.name}" and all associated content deleted successfully', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting category: {str(e)}', 'error')
    
    return redirect(url_for('categories'))

@app.route('/view_task_file/<path:file_path>')
@login_required
def view_task_file(file_path):
    """View task file (image or PDF)"""
    try:
        from urllib.parse import unquote
        file_path = unquote(file_path)
        
        # Find the task
        task = Task.query.filter_by(file_path=file_path).first()
        
        if not task:
            flash('Task file not found in database', 'error')
            return redirect(url_for('tasks'))
        
        # Construct full file path
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], file_path)
        
        # Check if file exists on disk
        if not os.path.exists(full_path):
            flash('File not found on server', 'error')
            return redirect(url_for('tasks'))
        
        # For PDF files, use PDF viewer
        if task.task_type == 'pdf':
            return render_template('view_task_pdf.html', task=task)
        
        # For images, use image viewer
        elif task.task_type == 'image':
            return render_template('view_task_image.html', task=task)
        
        else:
            flash('Invalid task type', 'error')
            return redirect(url_for('tasks'))
        
    except Exception as e:
        app.logger.error(f"Error in view_task_file: {str(e)}")
        flash(f'Error viewing file: {str(e)}', 'error')
        return redirect(url_for('tasks'))

# ==================== SEARCH ROUTES ====================

@app.route('/api/search')
@login_required
def search():
    """Global search API endpoint"""
    try:
        query = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'all')
        
        if len(query) < 2:
            return jsonify({'results': []})
        
        results = []
        
        # Search materials
        if search_type in ['all', 'materials']:
            materials = StudyMaterial.query.filter(
                StudyMaterial.title.contains(query) | 
                StudyMaterial.description.contains(query)
            ).limit(5).all()
            
            for m in materials:
                results.append({
                    'id': m.id,
                    'title': m.title,
                    'type': 'material',
                    'subtype': m.file_type,
                    'url': url_for('view_file', file_path=m.file_path),
                    'description': m.description[:100] + '...' if m.description else '',
                    'created_at': m.created_at.strftime('%Y-%m-%d')
                })
        
        # Search tasks
        if search_type in ['all', 'tasks']:
            tasks = Task.query.filter(
                Task.title.contains(query) | 
                Task.description.contains(query)
            ).limit(5).all()
            
            for t in tasks:
                results.append({
                    'id': t.id,
                    'title': t.title,
                    'type': 'task',
                    'subtype': 'task',
                    'url': url_for('view_task', task_id=t.id),
                    'description': t.description[:100] + '...' if t.description else '',
                    'created_at': t.created_at.strftime('%Y-%m-%d')
                })
        
        # Search categories
        if search_type in ['all', 'categories']:
            categories = Category.query.filter(
                Category.name.contains(query) | 
                Category.description.contains(query)
            ).limit(5).all()
            
            for c in categories:
                results.append({
                    'id': c.id,
                    'title': c.name,
                    'type': 'category',
                    'subtype': 'category',
                    'url': url_for('categories') + f'#category-{c.id}',
                    'description': c.description[:100] + '...' if c.description else '',
                    'created_at': c.created_at.strftime('%Y-%m-%d')
                })
        
        return jsonify({'results': results})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors"""
    return render_template('403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    app.logger.error(f'Server Error: {error}')
    return render_template('500.html'), 500

# ==================== HEALTH CHECK ====================

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected' if db.engine else 'disconnected'
    })