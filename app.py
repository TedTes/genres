from dotenv import load_dotenv
load_dotenv(dotenv_path='python-dotenv.env')

import os
from datetime import datetime
from flask import Flask, request, render_template, jsonify
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, CSRFError
from supabase import create_client, Client

from db import db
from models import User
from config.config import Config

# system libs for WeasyPrint on macOS
os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib:' + os.environ.get('DYLD_LIBRARY_PATH', '')

# --- App-level singletons (defer binding to app) ---
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__, template_folder="pages")
    app.config.from_object(Config)

    # init extensions
    csrf.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

   

    # create tables + set up heavy services inside an app context
    with app.app_context():
        db.create_all()
        app.extensions = getattr(app, "extensions", {})
     # register routes/blueprints
    from routes import register_routes
    register_routes(app)
    # user loader can be declared here after login_manager is bound
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # context processors
    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.now().year}

    # error handlers
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        if request.is_json:
            return jsonify({"success": False, "error": "CSRF token missing or invalid"}), 400
        return render_template('error.html', error=e.description), 400

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error=str(e), error_code=404), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('error.html', error_code=500), 500

    # optional: validate LLM config at startup (uses class/static config, no context needed)
    try:
        Config.validate_llm_config()
        print(f"✓ LLM Provider: {Config.MODEL_PROVIDER}")
        print(f"✓ LLM Model: {Config.LLM_MODEL}")
    except ValueError as err:
        print(f"⚠️  LLM Config Warning: {err}")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
