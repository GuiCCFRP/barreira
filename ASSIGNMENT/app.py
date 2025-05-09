
from flask        import Flask
from config       import Config
from extensions   import db, login_manager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # load in  stuff
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # create db
    with app.app_context():
        from models import User  # now safe
        db.create_all()

    # import bps
    from auth   import auth_bp
    from upload import upload_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(upload_bp)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
