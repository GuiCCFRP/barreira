from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, current_user , login_required
from models import User , PdfHistory
import os
from flask import current_app
from extensions import db, login_manager


auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('upload.index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@auth_bp.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    email = request.form['email']
    password = generate_password_hash(request.form['password'])

    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'danger')
        return redirect(url_for('auth.login'))

    new_user = User(username=username, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    flash('Account created! Please log in.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/settings', methods=['GET', 'POST'])
 #@login_required
def settings():
    return render_template('settings.html')

@auth_bp.route('/update-profile', methods=['POST'])
 #@login_required
def update_profile():
    new_email = request.form.get('email', '').strip()
    
    if not new_email:
        flash('Email cannot be empty', 'danger')
        return redirect(url_for('auth.settings'))
    
    if new_email == current_user.email:
        flash('No changes made', 'info')
        return redirect(url_for('auth.settings'))
    
    # Check if email is already in use
    existing_user = User.query.filter_by(email=new_email).first()
    if existing_user and existing_user.id != current_user.id:
        flash('Email address is already in use', 'danger')
        return redirect(url_for('auth.settings'))
    
    try:
        current_user.email = new_email
        db.session.commit()
        flash('Profile updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating profile', 'danger')
    
    return redirect(url_for('auth.settings'))

@auth_bp.route('/change-password', methods=['POST'])
 #@login_required
def change_password():
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validate inputs
    if not current_password or not new_password or not confirm_password:
        flash('All fields are required', 'danger')
        return redirect(url_for('auth.settings'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('auth.settings'))
    
    if len(new_password) < 8:
        flash('Password must be at least 8 characters', 'danger')
        return redirect(url_for('auth.settings'))
    
    # Verify current password
    if not check_password_hash(current_user.password, current_password):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('auth.settings'))
    
    try:
        current_user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Password changed successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error changing password', 'danger')
    
    return redirect(url_for('auth.settings'))

@auth_bp.route('/delete-account', methods=['GET'])
#@login_required
def delete_account():
    try:
        # Delete user's history entries first
        history_entries = PdfHistory.query.filter_by(user_id=current_user.id).all()
        for entry in history_entries:
            # Delete associated files
            files_to_delete = []
            
            if entry.filename:
                pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], entry.filename)
                if os.path.exists(pdf_path):
                    files_to_delete.append(pdf_path)
            
            if entry.json_path:
                json_path = os.path.join(current_app.config['UPLOAD_FOLDER'], entry.json_path)
                if os.path.exists(json_path):
                    files_to_delete.append(json_path)
            
            if entry.latex_path:
                latex_path = os.path.join(current_app.config['UPLOAD_FOLDER'], entry.latex_path)
                if os.path.exists(latex_path):
                    files_to_delete.append(latex_path)
            
            # Delete files
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                except Exception as e:
                    current_app.logger.error(f"Error deleting file {file_path}: {str(e)}")
            
            # Delete database entry
            db.session.delete(entry)
        
        # Delete user account
        user_to_delete = User.query.get(current_user.id)
        db.session.delete(user_to_delete)
        db.session.commit()
        
        logout_user()
        flash('Your account has been permanently deleted', 'success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        db.session.rollback()
        flash('Error deleting account', 'danger')
        return redirect(url_for('auth.settings'))
    


@auth_bp.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@auth_bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    new_email = request.form.get('email', '').strip()
    
    if not new_email:
        flash('Email cannot be empty', 'danger')
        return redirect(url_for('auth.settings'))
    
    if new_email == current_user.email:
        flash('No changes made', 'info')
        return redirect(url_for('auth.settings'))
    
    # Check if email is already in use
    existing_user = User.query.filter_by(email=new_email).first()
    if existing_user and existing_user.id != current_user.id:
        flash('Email address is already in use', 'danger')
        return redirect(url_for('auth.settings'))
    
    try:
        current_user.email = new_email
        db.session.commit()
        flash('Profile updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating profile', 'danger')
    
    return redirect(url_for('auth.settings'))

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validate inputs
    if not current_password or not new_password or not confirm_password:
        flash('All fields are required', 'danger')
        return redirect(url_for('auth.settings'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('auth.settings'))
    
    if len(new_password) < 8:
        flash('Password must be at least 8 characters', 'danger')
        return redirect(url_for('auth.settings'))
    
    # Verify current password
    if not check_password_hash(current_user.password, current_password):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('auth.settings'))
    
    try:
        current_user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Password changed successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error changing password', 'danger')
    
    return redirect(url_for('auth.settings'))

@auth_bp.route('/delete-account')
@login_required
def delete_account():
    try:
        # Delete user's history entries first
        history_entries = PdfHistory.query.filter_by(user_id=current_user.id).all()
        for entry in history_entries:
            # Delete associated files
            files_to_delete = []
            
            if entry.filename:
                pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], entry.filename)
                if os.path.exists(pdf_path):
                    files_to_delete.append(pdf_path)
            
            if entry.json_path:
                json_path = os.path.join(current_app.config['UPLOAD_FOLDER'], entry.json_path)
                if os.path.exists(json_path):
                    files_to_delete.append(json_path)
            
            if entry.latex_path:
                latex_path = os.path.join(current_app.config['UPLOAD_FOLDER'], entry.latex_path)
                if os.path.exists(latex_path):
                    files_to_delete.append(latex_path)
            
            # Delete files
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                except Exception as e:
                    current_app.logger.error(f"Error deleting file {file_path}: {str(e)}")
            
            # Delete database entry
            db.session.delete(entry)
        
        # Delete user account
        user_to_delete = User.query.get(current_user.id)
        db.session.delete(user_to_delete)
        db.session.commit()
        
        logout_user()
        flash('Your account has been permanently deleted', 'success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        db.session.rollback()
        flash('Error deleting account', 'danger')
        return redirect(url_for('auth.settings'))
