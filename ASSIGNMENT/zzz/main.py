from zzz.pdf_extract import extract_font_segments
from flask import Flask, request, render_template ,redirect ,url_for, jsonify , flash
import os
from os import chdir , path
import tempfile
from sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

workdir = os.path.dirname(os.path.abspath(__file__))
chdir(workdir)

DATABASE_FILE = 'database.sqlite'
DATABASE_PATH = path.join(workdir, DATABASE_FILE)

db = SQLAlchemy()



# MODELS
class pdf_history(db.Model):
    __tablename__ = 'pdf_history'

    user = db.Column(db.String, nullable=False)
    pdf1 = db.Column(db.String, nullable=False , default= None)
    pdf2 = db.Column(db.String, nullable=False, default= None)
    pdf3 = db.Column(db.String, nullable=False, default=None)
    pdf4 = db.Column(db.String, nullable=False, default= None)
    pdf5 = db.Column(db.String, nullable=False, default=None)
    last_created = db.Column(db.Integer)

    def __repr__(self):
        return f'<recent pdfs from {self.user} : {self.pdf1}, {self.pdf2}, {self.pdf3}>'
# END MODELS

    
    
#login model
class user_infos(db.Model):
    __tablename__ = 'user_infos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, nullable=False , default= None)
    password = db.Column(db.String, nullable=False , default= None)
    email = db.Column(db.String, nullable=False, default= None)

    def __repr__(self):
        return f'<login {self.username} : {self.password}>'
# end login model
#config
class Config:
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'rodrigues_luzzrodrigues_luzzrodrigues_luzz_rodrigues_luzz_rodrigues_luzz_rodrigues_luzz_rodrigues_luzz'
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB limit for file uploads
#end config

#create app
def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app

app = create_app()

# end create app


@app.route('/', methods=['POST' , 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username and password:
            user = user_infos.query.filter_by(username=username).first()
            if user.password == password:
                return redirect(url_for('index', user=username))
            else:
                return flash('user or password are incorrect','danger')
        else:
            return flash('Please fill all fields','danger')
    return 'post only'

@app.route('/signup', methods=['POST'])
def signup(username=None , password=None , email=None):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        if username and password and email:
            new_user = user_infos(username=username, password=password, email=email)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('index'))
        else:
            return flash('Please fill all fields','danger')
    return 'post only'



@app.route('/homepage')
def index(user):
    if user == None:
        flash('Something went wrong during login','danger')

    return render_template('homepage.html', user=user)

@app.route('/upload', methods=['POST'])
def upload(user):
    if request.content_length > app.config['MAX_CONTENT_LENGTH']: 
        flash('File size exceeds the limit of 10 MB', 'danger')
        return redirect(url_for('index', user=user))
    if request.method == 'POST':
        pdf_file = request.files['file']
        if pdf_file and pdf_file.filename.lower().endswith('.pdf'):
            current_pdf_count = pdf_history.query.filter_by(user=user).count()
            
            if current_pdf_count == 5:
                pass
            #PENSAR EM COMO APAGAR O PDF MAIS ANTIGO E ADICIONAR O NOVO PDF
                
                
                    
            

        



