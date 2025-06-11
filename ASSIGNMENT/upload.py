import os
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import PdfHistory
from extensions import db
from pdf_extract import extract_font_segments, str_to_latex  

def generate_latex(segments):
    """Generate LaTeX from segments using your existing str_to_latex function"""
    return str_to_latex(segments)

def escape_latex(text):
    """Escape LaTeX special characters"""
    if not text:
        return ""
    
    replacements = {
        '\\': '\\textbackslash{}',
        '{': '\\{',
        '}': '\\}',
        '$': '\\$',
        '&': '\\&',
        '%': '\\%',
        '#': '\\#',
        '^': '\\textasciicircum{}',
        '_': '\\_',
        '~': '\\textasciitilde{}'
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    return text

upload_bp = Blueprint('upload', __name__, url_prefix='/upload')

@upload_bp.route('/')
@login_required
def index():
    history = PdfHistory.query.filter_by(user_id=current_user.id).order_by(PdfHistory.created_at.desc()).all()
    return render_template('index.html', user=current_user.username, history=history)

@upload_bp.route('/file', methods=['POST'])
@login_required
def upload_file():
    file = request.files.get('file')
    if not file or not file.filename.lower().endswith('.pdf'):
        flash('Invalid file type', 'danger')
        return redirect(url_for('upload.index'))

    filename = secure_filename(file.filename)
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    file.save(save_path)
    
    # Process the PDF
    try:
        segments = extract_font_segments(save_path)
        json_filename = filename.replace('.pdf', '.json')
        json_path = os.path.join(current_app.config['UPLOAD_FOLDER'], json_filename)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(segments, f, ensure_ascii=False, indent=2)
        
        # Store processing result in database
        new_entry = PdfHistory(
            user_id=current_user.id,
            filename=filename,
            json_path=json_filename
        )
        
        # Delete oldest if more than 5 entries
        history = PdfHistory.query.filter_by(user_id=current_user.id).order_by(PdfHistory.created_at).all()
        db.session.add(new_entry)
        db.session.commit()
        
        flash('PDF processed successfully!', 'success')
        return redirect(url_for('upload.view_results', filename=json_filename))
        
    except Exception as e:
        current_app.logger.error(f"Error processing PDF: {str(e)}")
        flash('Error processing PDF', 'danger')
        return redirect(url_for('upload.index'))

@upload_bp.route('/results/<filename>')
@login_required
def view_results(filename):
    """View processing results for a specific PDF"""
    try:
        # Verify the file belongs to the current user
        history_entry = PdfHistory.query.filter_by(
            user_id=current_user.id,
            json_path=filename
        ).first()
        
        if not history_entry:
            flash('File not found or access denied', 'danger')
            return redirect(url_for('upload.index'))
        
        # Load the JSON data
        json_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(json_path):
            flash('Results file not found', 'danger')
            return redirect(url_for('upload.index'))
        
        with open(json_path, 'r', encoding='utf-8') as f:
            segments = json.load(f)
        
        # Categorize segments by font size (matching your original logic)
        structure = {
            'newsession': [],  # Large fonts (28pt equivalent)
            'subsession': [],  # Medium fonts (18pt equivalent) 
            'content': []      # Regular fonts (12pt equivalent)
        }
        
        for segment in segments:
            size = segment.get('size', 12)
            text = segment.get('text', '').strip()
            
            if not text or text.isspace():
                continue
            
            # Find closest font size to target sizes
            target_sizes = [28, 18, 12]
            closest_size = min(target_sizes, key=lambda x: abs(x - size))
            
            if closest_size == 28:
                structure['newsession'].append(text)
            elif closest_size == 18:
                structure['subsession'].append(text)
            elif closest_size == 12:
                structure['content'].append(text)
        
        return render_template('results.html', 
                             filename=history_entry.filename,
                             structure=structure,
                             segments=segments,
                             user=current_user.username)
        
    except Exception as e:
        current_app.logger.error(f"Error viewing results: {str(e)}")
        flash('Error loading results', 'danger')
        return redirect(url_for('upload.index'))

@upload_bp.route('/generate-latex/<filename>')
@login_required
def generate_latex_route(filename):
    """Generate LaTeX from processed PDF data"""
    try:
        # Verify the file belongs to the current user
        history_entry = PdfHistory.query.filter_by(
            user_id=current_user.id,
            json_path=filename
        ).first()
        
        if not history_entry:
            return jsonify({'error': 'File not found or access denied'}), 404
        
        # Load the JSON data
        json_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(json_path):
            return jsonify({'error': 'Results file not found'}), 404
        
        with open(json_path, 'r', encoding='utf-8') as f:
            segments = json.load(f)
        
        # Generate LaTeX using your existing function
        latex_content = generate_latex(segments)
        
        return jsonify({
            'latex': latex_content,
            'filename': history_entry.filename.replace('.pdf', '.tex')
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating LaTeX: {str(e)}")
        return jsonify({'error': 'Error generating LaTeX'}), 500

@upload_bp.route('/delete/<int:history_id>')
@login_required
def delete_file(history_id):
    """Delete a processed file"""
    try:
        # Find the history entry belonging to current user
        history_entry = PdfHistory.query.filter_by(
            id=history_id,
            user_id=current_user.id
        ).first()
        
        if not history_entry:
            flash('File not found', 'danger')
            return redirect(url_for('upload.index'))
        
        # Delete the JSON file
        json_path = os.path.join(current_app.config['UPLOAD_FOLDER'], history_entry.json_path)
        if os.path.exists(json_path):
            os.remove(json_path)
        
        # Delete the original PDF file
        pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], history_entry.filename)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        
        # Delete from database
        db.session.delete(history_entry)
        db.session.commit()
        
        flash('File deleted successfully', 'success')
        return redirect(url_for('upload.index'))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting file: {str(e)}")
        flash('Error deleting file', 'danger')
        return redirect(url_for('upload.index'))
