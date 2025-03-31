
from dotenv import load_dotenv
from flask import Flask,request,render_template,jsonify
from flask_login import LoginManager
import os
import io

import spacy
import secrets
from datetime import datetime
from supabase import create_client, Client
from db import db
from models import  User
from flask_wtf.csrf import CSRFProtect, CSRFError

os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib:' + os.environ.get('DYLD_LIBRARY_PATH', '')

app = Flask(__name__,template_folder="pages")

csrf = CSRFProtect(app)
load_dotenv(dotenv_path='python-dotenv.env')

# Register all routes
from routes import register_routes 
register_routes(app)

app.config['SECRET_KEY'] = secrets.token_hex(16) #TODOO Replace with a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_KEY')

supabase: Client = create_client(supabase_url, supabase_key)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'


@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    if request.is_json:
        return jsonify({"success": False, "error": "CSRF token missing or invalid"}), 400
    else:
        return render_template('error.html', error=e.description), 400

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error=str(e), error_code=404), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error_code=500), 500


if __name__ == '__main__':
    app.run(debug=True)







