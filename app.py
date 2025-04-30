
from dotenv import load_dotenv
load_dotenv(dotenv_path='python-dotenv.env')
from flask import Flask,request,render_template,jsonify,send_file,g
from flask_login import LoginManager
import os
import io
from io import BytesIO
from weasyprint import HTML
import spacy

from datetime import datetime
from supabase import create_client, Client
from db import db
from models import  User,Resume
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_assets import Bundle,Environment
from helpers.resume_helper import generate_resume
from config import scss_config
from config.config import Config
os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib:' + os.environ.get('DYLD_LIBRARY_PATH', '')


app = Flask(__name__,template_folder="pages")
csrf = CSRFProtect(app)

app.config.from_object(Config)
# Initialize Flask-Assets
assets = Environment(app)
assets.url = '/static'
assets.debug = True


try:
    # Configure Flask-Assets for multiple templates
    for template_name, config in scss_config.items():
        template_scss = Bundle(
            config['css'],
            filters='libsass',
            output=config['output_css']
        )
        assets.register(f'{template_name}_css', template_scss)
        template_scss.build()
   
except Exception as e:
     print("Error registering or building css files from scss")
     print(e)

@app.before_request
def before_request():
    g.assets = assets
    g.app = app
@app.route('/test-assets')
def test_assets():
    return render_template('test_assets.html')

# Register all routes
from routes import register_routes 
register_routes(app)

supabase: Client = create_client(app.config['SUPABASE_URL'],app.config['SUPABASE_KEY'])

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







