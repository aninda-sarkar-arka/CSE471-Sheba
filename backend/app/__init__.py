from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask import session
from flask_socketio import SocketIO
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO(cors_allowed_origins="*")
mail = Mail()


def create_app(config_object='config.Config'):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    # ensure instance path exists
    try:
        app.instance_path
    except Exception:
        pass

    # Enable CORS for the frontend and allow credentials (cookies)
    # Allow both Vite dev server (5173) and production (3000)
    CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:3001"])

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    mail.init_app(app)

    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    # Skip demo data during tests
    if app.config.get('TESTING'):
        return app

    # create demo users and providers
    with app.app_context():

        
        # Check if schema is ready (email column exists) before creating demo users
        try:
            import sqlite3
            conn = sqlite3.connect(os.path.join(app.instance_path, 'app.db'))
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(user)")
            columns = [row[1] for row in cursor.fetchall()]
            schema_ready = 'email' in columns
            conn.close()
            # #region agent log
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"pre-fix","hypothesisId":"D","location":"app/__init__.py:60","message":"Schema readiness check","data":{"schema_ready":schema_ready,"has_email":schema_ready},"timestamp":int(__import__('time').time()*1000)})+'\n')
            except: pass
            # #endregion
        except Exception as e:
            schema_ready = False
            # #region agent log
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"pre-fix","hypothesisId":"D","location":"app/__init__.py:67","message":"Schema check failed","data":{"error":str(e)},"timestamp":int(__import__('time').time()*1000)})+'\n')
            except: pass
            # #endregion
        
        if not schema_ready:
            # #region agent log
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"pre-fix","hypothesisId":"E","location":"app/__init__.py:73","message":"Skipping demo user creation - schema not ready","data":{},"timestamp":int(__import__('time').time()*1000)})+'\n')
            except: pass
            # #endregion
            return app
        
        from .models import User
        
        # Demo user with email
        # #region agent log
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"pre-fix","hypothesisId":"B","location":"app/__init__.py:82","message":"Before User query","data":{"querying":"user_demo"},"timestamp":int(__import__('time').time()*1000)})+'\n')
        except: pass
        # #endregion
        try:
            # Demo users - all use same email
            demo_users = [
                {'username': 'user_demo', 'password': 'demo123', 'name': 'Demo User'},
                {'username': 'user1', 'password': 'pass123', 'name': 'John Doe'},
                {'username': 'user2', 'password': 'pass123', 'name': 'Jane Smith'},
                {'username': 'user3', 'password': 'pass123', 'name': 'Bob Johnson'},
            ]
            for user_data in demo_users:
                if not User.query.filter_by(username=user_data['username']).first():
                    user = User(username=user_data['username'])
                    user.set_password(user_data['password'])
                    user.name = user_data['name']
                    user.email = 'aninda.sarkar11@gmail.com'  # All demo users use same email
                    db.session.add(user)
            
            # Demo providers - all use same email, one for each category
            demo_providers = [
                {'username': 'provider_electrician', 'password': 'demo123', 'name': 'Demo Electrician', 'category': 'electrician'},
                {'username': 'provider_barber', 'password': 'demo123', 'name': 'Demo Barber', 'category': 'barber'},
                {'username': 'provider_ac', 'password': 'demo123', 'name': 'Demo AC Repair', 'category': 'ac repair'},
                {'username': 'provider_plumber', 'password': 'demo123', 'name': 'Demo Plumber', 'category': 'plumber'},
                {'username': 'provider_fridge', 'password': 'demo123', 'name': 'Demo Fridge Repair', 'category': 'fridge repair'},
            ]
            
            # Get the next provider unique ID
            existing_providers = User.query.filter(User.provider_unique_id.isnot(None)).all()
            next_id = len(existing_providers) + 1
            
            for provider_data in demo_providers:
                existing_provider = User.query.filter_by(username=provider_data['username']).first()
                if not existing_provider:
                    provider = User(username=provider_data['username'])
                    provider.set_password(provider_data['password'])
                    provider.name = provider_data['name']
                    provider.role = 'provider'
                    provider.partner_category = provider_data['category']
                    provider.email = 'aninda.sarkar.arka@g.bracu.ac.bd'  # All demo providers use same email
                    provider.provider_unique_id = f'PROV-{next_id:03d}'
                    next_id += 1
                    db.session.add(provider)
                elif existing_provider.role == 'provider' and not existing_provider.provider_unique_id:
                    # Assign ID to existing providers that don't have one
                    existing_provider.provider_unique_id = f'PROV-{next_id:03d}'
                    next_id += 1
            
            # Create admin user
            admin_user = User.query.filter_by(username='admin1').first()
            if not admin_user:
                admin = User(username='admin1')
                admin.set_password('admin123')
                admin.name = 'Admin User'
                admin.role = 'admin'
                admin.email = 'admin@servicehub.com'
                db.session.add(admin)
            
            try:
                db.session.commit()
                print('[INIT] Demo users and providers created successfully')
            except Exception as e:
                db.session.rollback()
                # #region agent log
                import json
                import os
                log_path = r'c:\Users\HAVOC\OneDrive\Desktop\cse471\.cursor\debug.log'
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"pre-fix","hypothesisId":"C","location":"app/__init__.py:140","message":"Error during User query/creation","data":{"error":str(e),"error_type":type(e).__name__},"timestamp":int(__import__('time').time()*1000)})+'\n')
                except: pass
                # #endregion
                print(f'[INIT] Error creating demo users: {e}')
        except Exception as e:
            # Handle schema mismatch errors gracefully (e.g., during migrations)
            # #region agent log
            import json
            import os
            log_path = r'c:\Users\HAVOC\OneDrive\Desktop\cse471\.cursor\debug.log'
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"pre-fix","hypothesisId":"F","location":"app/__init__.py:150","message":"Schema mismatch - skipping demo user creation","data":{"error":str(e),"error_type":type(e).__name__},"timestamp":int(__import__('time').time()*1000)})+'\n')
            except: pass
            # #endregion
            print(f'[INIT] Schema not ready for demo users (this is normal during migrations): {type(e).__name__}')

    return app
