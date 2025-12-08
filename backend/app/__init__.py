from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask import session

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_object='config.Config'):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    # ensure instance path exists
    try:
        app.instance_path
    except Exception:
        pass

    # Enable CORS for the frontend and allow credentials (cookies)
    CORS(app, supports_credentials=True, origins=["http://localhost:3000"]) 

    db.init_app(app)
    migrate.init_app(app, db)

    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    # create a dummy user for demo (arka/12345)
    with app.app_context():
        from .models import User
        try:
            if not User.query.filter_by(username='arka').first():
                u = User(username='arka')
                u.set_password('12345')
                db.session.add(u)
                db.session.commit()
        except Exception:
            # DB schema may not be ready (migrations pending). Skip seeding.
            pass

    return app
