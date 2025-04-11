from flask import Blueprint,abort,render_template,url_for,redirect
from helpers.job_helper import get_recent_job_matches
from helpers.resume_helper import calculate_resume_completeness
from flask_login import  current_user, login_required
from models import  User, Job, Resume,Application
from services.subscription_service import SubscriptionService
from utils.date import format_job_posted_date
root_bp = Blueprint("root",__name__)


@root_bp.route('/')
def home():

    try:
        if current_user.is_authenticated:
            return redirect(url_for('root.dashboard'))
            
        else:
            job_count = Job.query.count()
            user_count = User.query.count()
            resume_count = Resume.query.count()
            return render_template('home.html',  job_count=job_count, user_count=user_count, resume_count=resume_count)
    except Exception as e:
        print(f"Error rendering home page: {e}")  # Debug print
        abort(500)

@root_bp.route('/dashboard')
@login_required
def dashboard():
    # Get user's resumes
    resumes = Resume.query.filter_by(user_id=current_user.id).all()
    subscription =  SubscriptionService.get_user_subscription(current_user.id)
    # Process resumes for display
    for resume in resumes:
        # Handle general resumes (without a job)
        if resume.job:
            resume.display_title = f"Resume for {resume.job.title}"
            resume.display_company = resume.job.company
            resume.display_match = 85  # Or calculate actual match
        else:
            resume.display_title = resume.title or "General Resume"
            resume.display_company = "Multiple Companies"
            resume.display_match = 30  # General resumes show 100%
            
            # Add match score for general resumes (could be based on completeness)
        resume.match_score = calculate_resume_completeness(resume.resume_data)
        
        # Get job matches from the database
    job_matches_list = get_recent_job_matches(current_user.id, limit=3)

    # Format dates for display
    for job in job_matches_list:
        job['posted_at'] = format_job_posted_date(job['posted_at'])

    # Placeholder for applications count
    applications_count = Application.query.filter_by(user_id=current_user.id).count()

    return render_template(
        'dashboard.html', 
        resumes=resumes,
        job_matches=len(job_matches_list),
        job_matches_list=job_matches_list,
        applications=applications_count,
        subscription=subscription,
        show_upgrade_banner=True)
    