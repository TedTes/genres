
from flask import Blueprint,flash,url_for,redirect,render_template,current_app,session
from flask_login import current_user
from flask_mail import Mail, Message
from models import  Job, Resume
from datetime import datetime
from forms import JobSearchForm
from db import db
from helpers.resume_helper import calculate_skill_match,extract_skills_from_text
from helpers.job_helper import find_similar_jobs,extract_job_tags,process_jobs_for_display
from services.job_service import JobService

job_bp = Blueprint("job", __name__)
# Create job service instance
job_service = JobService()

@job_bp.route('/job', methods=['GET', 'POST'])
def job():
    form = JobSearchForm()
    
    try:
        if form.validate_on_submit():
            # Get form data for filtering
            search_term = form.search.data
            location = form.location.data
            remote_only = form.remote.data
            
            # Fetch jobs with filters using job service
            jobs_data = job_service.get_jobs(search_term, location, remote_only)
        else:
            # Default fetch with no filters
            jobs_data = job_service.get_jobs()
        
        # Process job data using job service
        processed_jobs = process_jobs_for_display(jobs_data)
        
        return render_template('jobs.html', jobs=processed_jobs, form=form)
        
    except Exception as e:
        print(f"Error in jobs route: {e}")
        flash(f"Error fetching jobs: {str(e)}", 'danger')
        return render_template('jobs.html', jobs=[], form=form)

@job_bp.route('/job/<slug>')
def job_detail(slug):
        try: 
            mail = Mail(current_app)
            # First, check if job exists in the database
            job = Job.query.filter_by(slug=slug).first()
            # Convert the SQLAlchemy model to a dictionary for template rendering
            job = {
                'id': job.id,
                'slug': job.slug,
                'title': job.title,
                'company_name': job.company,
                'location': job.location,
                'description': job.description or '',
                'remote': True if 'remote' in job.location.lower() else False,
                'posted_at': "Today" if (datetime.now() - job.posted_at).days == 0 else 
                            "Yesterday" if (datetime.now() - job.posted_at).days == 1 else
                            f"{(datetime.now() - job.posted_at).days} days ago",
                'tags': extract_job_tags(job.title, job.description),
                'apply_url': f"https://www.arbeitnow.com/view/{job.slug}" if job.slug else None
            }
            job_skills = extract_skills_from_text(job.get('description'))
            # For authenticated users, calculate skills match
            skills_match = []
            match_percentage = 0
            
            if current_user.is_authenticated:
                # Get user skills
                user_resume = Resume.query.filter_by(user_id=current_user.id).first()
                
                user_skills = []
                
                if user_resume and user_resume.resume_data and 'skills' in user_resume.resume_data:
                   user_skills_data = user_resume.resume_data['skills']

                # Handle different formats of skills data
                if isinstance(user_skills_data, str):
                    user_skills = [skill.strip() for skill in user_skills_data.split(',')]
                elif isinstance(user_skills_data, list):
                    user_skills = user_skills_data

                match_percentage, skills_match = calculate_skill_match(user_skills, job_skills)
            
            # Add job skills to the session for use in resume creation
            session['job_skills'] = list(job_skills.keys())
            # Find similar jobs using skills overlap
            # similar_jobs = find_similar_jobs(slug, job_skills, limit=3)
            
            
            return render_template(
                'job_detail.html',
                job=job,
                skills_match=skills_match,
                match_percentage=match_percentage,
                # similar_jobs=similar_jobs
            )
        
        except Exception as e:
            print(f"Error in job detail route: {e}")
            flash(f"Error loading job details: {str(e)}", 'danger')
            return redirect(url_for('job.job'))
            
            
            # Send email
            msg = Message(
                subject='Password Reset Request',
                recipients=[user.email],
                html=render_template('email/reset_password.html', reset_url=reset_url, user=user),
                sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@resumematch.com')
            )
            mail.send(msg)
            
        # Always to show this message even if email is not found (security best practice)
        flash('If an account exists with that email, you will receive password reset instructions.', 'info')
        return redirect(url_for('auth.login'))