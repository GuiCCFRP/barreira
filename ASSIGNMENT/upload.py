import os
import time
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import PdfHistory
from extensions import db
#from pdf_processor import LatexGenerator

upload_bp = Blueprint('upload', __name__, url_prefix='/upload')

@upload_bp.route('/')
@login_required
def index():
    history = PdfHistory.query.filter_by(user_id=current_user.id).order_by(PdfHistory.created_at.desc()).limit(5).all()
    return render_template('index.html', user=current_user.username, history=history)

@upload_bp.route('/file', methods=['POST'])
@login_required
def upload_file():
    file = request.files.get('file')
    if not file or not file.filename.lower().endswith('.pdf'):
        flash('Invalid file type', 'danger')
        return redirect(url_for('upload.index'))

    # Generate unique filename
    timestamp = str(int(time.time()))
    filename = secure_filename(file.filename)
    unique_filename = f"{current_user.id}_{timestamp}_{filename}"
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
    
    # directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    file.save(save_path)
    
     #database entry
    new_entry = PdfHistory(
        user_id=current_user.id,
        filename=filename,
        status='processing'
    )
    db.session.add(new_entry)
    db.session.commit()
    
    try:
        # Process PDF in background
        latex_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], 
            f"latex_{unique_filename}.tex"
        )
        
        #processor = LatexGenerator()
        processor.process_pdf(save_path, latex_path)
        
        # Update database with result
        new_entry.latex_path = latex_path
        new_entry.status = 'completed'
        db.session.commit()
        
        flash('PDF processed successfully!', 'success')
    except Exception as e:
        new_entry.status = 'failed'
        db.session.commit()
        current_app.logger.error(f"PDF processing failed: {str(e)}")
        flash('Error processing PDF', 'danger')
    
    return redirect(url_for('upload.index'))

@upload_bp.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    file_entry = PdfHistory.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not file_entry or not file_entry.latex_path or not os.path.exists(file_entry.latex_path):
        flash('File not found', 'danger')
        return redirect(url_for('upload.index'))
    
    return send_file(
        file_entry.latex_path,
        as_attachment=True,
        download_name=f"{os.path.splitext(file_entry.filename)[0]}.tex"
    )
