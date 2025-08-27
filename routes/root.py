from flask import Blueprint,abort,render_template,url_for,redirect
from flask_login import  current_user, login_required
from models import  User
from services.subscription_service import SubscriptionService
from utils.date import format_job_posted_date
root_bp = Blueprint("root",__name__)


@root_bp.route('/')
def home():

    try:
        if current_user.is_authenticated:
            return redirect(url_for('root.dashboard'))
            
        else:
            return render_template('home.html')
    except Exception as e:
        print(f"Error rendering home page: {e}")  # Debug print
        abort(500)

@root_bp.route('/dashboard')
@login_required
def dashboard():
   pass


@root_bp.route('/optimize', methods=['GET'])
def optimize_page():
    """Display the resume optimization page - no authentication required."""
    try:
        return render_template('optimize.html')
    except Exception as e:
        print(f"Error rendering optimize page: {e}")
        abort(500)
    