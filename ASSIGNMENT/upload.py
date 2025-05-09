import os
from flask            import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login      import login_required, current_user
from werkzeug.utils   import secure_filename
from models           import PdfHistory
from extensions       import db

upload_bp = Blueprint('upload', __name__, url_prefix='/upload')


@upload_bp.route('/')
@login_required
def index():
    history = PdfHistory.query.filter_by(user_id=current_user.id).order_by(PdfHistory.created_at.desc()).limit(5).all()
    return render_template('homepage.html', user=current_user.username, history=history)

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

    history = PdfHistory.query.filter_by(user_id=current_user.id).order_by(PdfHistory.created_at).all()
    if len(history) >= 5:
        db.session.delete(history[0])  # delete oldest
        db.session.commit()

    new_entry = PdfHistory(user_id=current_user.id, filename=filename)
    db.session.add(new_entry)
    db.session.commit()

    return redirect(url_for('upload.index'))
