from flask import make_response,render_template, request, redirect, url_for, flash, session, abort, send_file
from helpers import fetch_jobs,extract_job_tags,calculate_resume_completeness,get_recent_job_matches,extract_skills_from_text,fetch_job_by_slug,find_similar_jobs,calculate_skill_match,analyze_job_description
from flask import render_template, request, redirect, url_for, flash, session, abort, send_file
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import io
from sqlalchemy.orm import attributes
from forms import RegistrationForm, LoginForm, JobSearchForm, ContactForm, SummaryForm, ExperienceForm, EducationForm, SkillsForm,ResetPasswordForm,ResetPasswordRequestForm
from db import db
from models import  User, Job, Resume,Application
import json
from flask import jsonify

from io import BytesIO

from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import os
from template_registry import TemplateRegistry
from weasyprint import HTML, CSS
import weasyprint
# Import NLP analyzer 
import spacy
weasyprint.DEBUG = True
nlp = spacy.load('en_core_web_sm')

app = None

def init_routes(flask_app):
    global app
    app = flask_app
    mail = Mail(app)
    #serializer for generating secure tokens
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    @app.route('/')
    def home():
        try:
            job_count = Job.query.count()
            user_count = User.query.count()
            resume_count = Resume.query.count()
            return render_template('home.html', job_count=job_count, user_count=user_count, resume_count=resume_count)
        except Exception as e:
             print(f"Error rendering home page: {e}")  # Debug print
             abort(500)

    @app.route('/jobs', methods=['GET', 'POST'])
    def jobs():
        form = JobSearchForm()
        jobs_data = []
        
        try:
            if form.validate_on_submit():
                # Get form data for filtering
                search_term = form.search.data
                location = form.location.data
                remote_only = form.remote.data
                
                # Fetch jobs with filters
                jobs_data = fetch_jobs(search_term, location, remote_only)
            else:
                # Default fetch with no filters
                jobs_data = fetch_jobs()

            # Process job data to extract tags and format dates
            processed_jobs = []
            for job in jobs_data:
                # Extract tags from job title and description
                tags = extract_job_tags(job.get('title', ''), job.get('description', ''))
                
                # Format the date
                created_at = job.get('created_at')
                if created_at:
                    # Convert ISO date to more readable format
                    try:
                        if created_at and isinstance(created_at,str):
                           date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            date_obj = datetime.now()
                        days_ago = (datetime.now(date_obj.tzinfo) - date_obj).days
                        
                        if days_ago == 0:
                            formatted_date = "Today"
                        elif days_ago == 1:
                            formatted_date = "Yesterday"
                        else:
                            formatted_date = f"{days_ago} days ago"
                    except:
                        formatted_date = "Recently"
                else:
                    formatted_date = "Recently"
                
                # Create processed job object
                processed_job = {
                    **job,  # Include all original job data
                    'tags': tags[:3],  # Limit to top 3 tags
                    'created_at': formatted_date
                }
                
                processed_jobs.append(processed_job)
            
            return render_template('jobs.html', jobs=processed_jobs, form=form)
        
        except Exception as e:
            print(f"Error in jobs route: {e}")
            flash(f"Error fetching jobs: {str(e)}", 'danger')
            return render_template('jobs.html', jobs=[], form=form)

    @app.route('/job/<slug>')
    def job_detail(slug):

            try:
                # First, check if job exists in the database
                job = Job.query.filter_by(slug=slug).first()
                
                # If not in database, fetch from API
                if not job:
                    job_data = fetch_job_by_slug(slug)

                    if not job_data:
                        flash('Job not found.', 'danger')
                        return redirect(url_for('jobs'))
                    
                    created_at = job_data.get('created_at')
                   
                    # Create a new Job record in the database
                    jobRes = Job(
                        slug=job_data.get('slug'),
                        title=job_data.get('title', 'Untitled Position'),
                        company=job_data.get('company_name', 'Unknown Company'),
                        location=job_data.get('location', 'Remote'),
                        description=job_data.get('description', ''),
                        posted_at=datetime.fromisoformat(job_data.get('created_at', datetime.now().isoformat()).replace('Z', '+00:00')) if created_at and isinstance(created_at,str) else datetime.now()
                    )
                   
                    # Add additional attributes from API data
                    job_data['remote'] = job_data.get('remote', False)
                    job_data['apply_url'] = job_data.get('url', '')
                    job_data['tags'] = extract_job_tags(job_data.get('title', ''), job_data.get('description', ''))
                    
                    # Format the date
                    if created_at:
                        try: 
                            if created_at and isinstance(created_at,str):
                               date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            else:
                               date_obj = datetime.now()
                            days_ago = (datetime.now(date_obj.tzinfo) - date_obj).days
                            
                            if days_ago == 0:
                                job_data['created_at'] = "Today"
                            elif days_ago == 1:
                                job_data['created_at'] = "Yesterday"
                            else:
                                job_data['created_at'] = f"{days_ago} days ago"
                        except:
                            job_data['created_at'] = "Recently"
                    else:
                        job_data['created_at'] = "Recently"

                    # Save to database
                    db.session.add(jobRes)
                    db.session.commit()
                    job_data['id'] = jobRes.id
                    job = job_data
                else:

                    # Convert the SQLAlchemy model to a dictionary for template rendering
                    job = {
                        'id': job.id,
                        'slug': job.slug,
                        'title': job.title,
                        'company_name': job.company,
                        'location': job.location,
                        'description': job.description or '',
                        'remote': True if 'remote' in job.location.lower() else False,
                        'created_at': "Today" if (datetime.now() - job.posted_at).days == 0 else 
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
                return redirect(url_for('jobs'))
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        # Redirect if user is already logged in
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = RegistrationForm()
        
        if form.validate_on_submit():
            try:
                # Check if email already exists using SQLAlchemy
                existing_user = User.query.filter_by(email=form.email.data).first()
                
                if existing_user:
                    flash('Email already registered. Please log in.', 'danger')
                    return redirect(url_for('login'))
                
                hashed_password = generate_password_hash(form.password.data)
                # Create new user with SQLAlchemy model
                new_user = User(
                    username=form.username.data,
                    email=form.email.data,
                    password_hash=hashed_password,
                    verified=False,
                    verification_sent_at=datetime.now()
                )
                
                # Add and commit to database
                db.session.add(new_user)
                db.session.commit()
                
                # Generate verification token
                token = serializer.dumps(new_user.email, salt='email-verification-salt')

                # Create verification URL
                verification_url = url_for(
                    'verify_email',
                    token=token,
                    _external=True
                )
                # Send verification email
                msg = Message(
                    subject='Verify Your ResumeMatch Account',
                    recipients=[new_user.email],
                    html=render_template('email/verify_email.html', verification_url=verification_url, user=new_user),
                    sender=app.config.get('MAIL_DEFAULT_SENDER', 'noreply@resumematch.com')
                )
                mail.send(msg)
                flash('Account created successfully! Please log in.', 'success')
                return redirect(url_for('login'))
                
            except Exception as e:
                db.session.rollback()  # Roll back the session on error
                print(f"Registration error: {e}")
                flash('An error occurred during registration. Please try again.', 'danger')
        
        return render_template('register.html', form=form)

    @app.route('/verify-email/<token>')
    def verify_email(token):
        try:
            # Verify token - valid for 7 days
            email = serializer.loads(token, salt='email-verification-salt', max_age=604800)
            user = User.query.filter_by(email=email).first()
            
            if not user:
                flash('Invalid verification link.', 'danger')
                return redirect(url_for('login'))
                
            if user.verified:
                flash('Your account is already verified. Please log in.', 'info')
                return redirect(url_for('login'))
            
            # Verify user
            user.verified = True
            db.session.commit()
            
            flash('Your account has been verified! You can now log in.', 'success')
            return redirect(url_for('login'))
            
        except (SignatureExpired, BadSignature):
            flash('The verification link is invalid or has expired.', 'danger')
            return redirect(url_for('login'))
    
    @app.route('/resend-verification')
    def resend_verification():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        return render_template('resend_verification.html')
   
    @app.route('/resend-verification', methods=['POST'])
    def process_resend_verification():
        email = request.form.get('email')
        
        if not email:
            flash('Please provide your email address.', 'danger')
            return redirect(url_for('resend_verification'))
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Not to reveal if email exists or not for security
            flash('If your email is registered, you will receive a verification link shortly.', 'info')
            return redirect(url_for('login'))
        
        if user.verified:
            flash('Your account is already verified. Please log in.', 'info')
            return redirect(url_for('login'))
        
        # Check if last verification was sent less than 10 minutes ago
        if user.verification_sent_at and (datetime.now() - user.verification_sent_at).total_seconds() < 600:
            flash('A verification email was recently sent. Please check your inbox or wait a few minutes before requesting another.', 'info')
            return redirect(url_for('login'))
        
        # Generate new verification token
        token = serializer.dumps(user.email, salt='email-verification-salt')
        
        # Create verification URL
        verification_url = url_for(
            'verify_email',
            token=token,
            _external=True
        )
        
        # Send verification email
        msg = Message(
            subject='Verify Your ResumeMatch Account',
            recipients=[user.email],
            html=render_template('email/verify_email.html', verification_url=verification_url, user=user),
            sender=app.config.get('MAIL_DEFAULT_SENDER', 'noreply@resumematch.com')
        )
        mail.send(msg)
        
        # Update verification sent time
        user.verification_sent_at = datetime.now()
        db.session.commit()
        
        flash('Verification email sent. Please check your inbox.', 'success')
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # Redirect if user is already logged in
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = LoginForm()
        
        if form.validate_on_submit():
            try:
                # Get user by email using SQLAlchemy
                user = User.query.filter_by(email=form.email.data).first()
                
                if user:
                    # Verify password
                    if check_password_hash(user.password_hash, form.password.data):

                        # if not user.verified:
                        #     flash('Please verify your email address before logging in.', 'warning')
                        #     return render_template('login.html', form=form, show_resend=True, email=user.email)
                        # Log in user
                        login_user(user)
                        
                        # Get next page or default to dashboard
                        next_page = request.args.get('next')
                        flash('Login successful!', 'success')
                        return redirect(next_page or url_for('dashboard'))
                    else:
                        flash('Invalid password. Please try again.', 'danger')
                else:
                    flash('Email not found. Please check your email or register.', 'danger')
            
            except Exception as e:
                print(f"Login error: {e}")
                flash('An error occurred during login. Please try again.', 'danger')
        
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'success')
        return redirect(url_for('login'))


    @app.route('/reset-password', methods=['GET', 'POST'])
    def reset_password_request():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = ResetPasswordRequestForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user:
                # Generate a token
                token = serializer.dumps(user.email, salt='password-reset-salt')
                
                # Build reset URL
                reset_url = url_for(
                    'reset_password',
                    token=token,
                    _external=True
                )
                
                # Send email
                msg = Message(
                    subject='Password Reset Request',
                    recipients=[user.email],
                    html=render_template('email/reset_password.html', reset_url=reset_url, user=user),
                    sender=app.config.get('MAIL_DEFAULT_SENDER', 'noreply@resumematch.com')
                )
                mail.send(msg)
                
            # Always to show this message even if email is not found (security best practice)
            flash('If an account exists with that email, you will receive password reset instructions.', 'info')
            return redirect(url_for('login'))
        
        return render_template('reset_password_request.html', form=form)

    @app.route('/reset-password/<token>', methods=['GET', 'POST'])
    def reset_password(token):
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        # Verify token - valid for 24 hours
        try:
            email = serializer.loads(token, salt='password-reset-salt', max_age=86400)
            user = User.query.filter_by(email=email).first()
            if not user:
                flash('Invalid or expired reset link.', 'danger')
                return redirect(url_for('reset_password_request'))
        except (SignatureExpired, BadSignature):
            flash('Invalid or expired reset link.', 'danger')
            return redirect(url_for('reset_password_request'))
        
        form = ResetPasswordForm()
        if form.validate_on_submit():
            # Update password
            user.password_hash = generate_password_hash(form.password.data)
            db.session.commit()
            
            flash('Your password has been reset! You can now log in.', 'success')
            return redirect(url_for('login'))
        
        return render_template('reset_password.html', form=form)

    @app.route('/resume/start/<int:job_id>')
    @login_required
    def start_resume(job_id):
        job = Job.query.get_or_404(job_id)
        
        # Get user's previous resume data for pre-population
        last_resume = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.updated_at.desc()).first()
        # Initialize with empty or previous data
        resume_data = {}
        if last_resume and last_resume.resume_data:
            resume_data = last_resume.resume_data.copy()
            # Create new resume with pre-populated data
            last_resume = Resume(user_id=current_user.id, job_id=job.id, resume_data=resume_data)
            db.session.add(last_resume)
            db.session.commit()
        else: 
            # Create a new resume without a job_id
            last_resume = Resume(
                user_id=current_user.id,
                resume_data={},
                title=job.title
            )
            
            # Add to database
            db.session.add(last_resume)
            db.session.commit()
        # Extract relevant skills from job description
        skills = analyze_job_description(job.description)
        session['skills'] = skills
        
        flash('Resume created with your information! Customize it for this job posting.', 'success')
        return redirect(url_for('resume_contact', resume_id=last_resume.id))

    @app.route('/resume/<int:resume_id>/contact', methods=['GET', 'POST'])
    @login_required
    def resume_contact(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        form = ContactForm()

        if form.validate_on_submit():
            if resume.resume_data is None:
               resume.resume_data = {}
            resume.resume_data['contact'] = {
                'name': form.name.data,
                'email': form.email.data,
                'phone': form.phone.data,
                'location': request.form.get('location', ''),
                'linkedin': request.form.get('linkedin', ''),
                'website': request.form.get('website', '')
            }
            try:
              attributes.flag_modified(resume, 'resume_data')
              db.session.commit()
              flash('Contact information saved successfully!', 'success')
              return redirect(url_for('resume_skills', resume_id=resume.id))
            except Exception as e:
              db.session.rollback()
              print(f"Error saving contact info: {str(e)}")
              flash(f"Error saving contact information: {str(e)}", 'danger')
    
        if resume.resume_data and 'contact' in resume.resume_data:
            form.name.data = resume.resume_data['contact'].get('name', '')
            form.email.data = resume.resume_data['contact'].get('email', '')
            form.phone.data = resume.resume_data['contact'].get('phone', '')
        return render_template('resume_contact.html', form=form, resume=resume)

    @app.route('/resume/<int:resume_id>/summary', methods=['GET', 'POST'])
    @login_required
    def resume_summary(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        
        if resume.resume_data is None:
            resume.resume_data = {}
        
        form = SummaryForm()
        # Handle form submission
        if form.validate_on_submit():
            # Store summary as structured data
            resume.resume_data['summary'] = {
                'content': form.summary.data,
                'last_updated': datetime.now().isoformat()
            }
            attributes.flag_modified(resume, 'resume_data')
            # Save changes
            try:
                # Save changes
                db.session.commit()
                flash('Summary saved successfully!', 'success')
                return redirect(url_for('resume_preview', resume_id=resume.id))
            except Exception as e:
                db.session.rollback()
                print(f"Error saving summary: {str(e)}")
                flash(f"Error saving summary: {str(e)}", 'danger')
        
        # Pre-populate form for GET requests
        if 'summary' in resume.resume_data:
            # Handle both formats (string or dictionary)
            if isinstance(resume.resume_data['summary'], dict):
                form.summary.data = resume.resume_data['summary'].get('content', '')
            else:
                form.summary.data = resume.resume_data['summary']
        
        # Render the form template
        return render_template(
            'resume_summary.html', 
            form=form, 
            resume=resume, 
            skills=session.get('skills', [])
        )

    @app.route('/resume/<int:resume_id>/experience', methods=['GET', 'POST'])
    @login_required
    def resume_experience(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        
        form = ExperienceForm()
        if request.method == 'POST' and request.form.get('experience_data'):
            if form.csrf_token.validate(form):
                try:
                    if resume.resume_data is None:
                       resume.resume_data = {}
                    # Get and debug the experience data
                    experience_data = request.form.get('experience_data')
                    print(f"Received experience_data: {experience_data}")
                    
                    if experience_data and experience_data.strip():
                        # Store as parsed JSON
                        experiences_json = json.loads(experience_data)
                        resume.resume_data['experience'] = experiences_json
                        print(f"Saved experiences: {experiences_json}")
                        attributes.flag_modified(resume, 'resume_data')
                        # Commit and redirect
                        db.session.commit()
                        flash('Experience information saved successfully!', 'success')
                        return redirect(url_for('resume_education', resume_id=resume.id))
                    else:
                        print("No experience data received")
                        flash("Please add at least one work experience", "warning")
                except Exception as e:
                    db.session.rollback()
                    print(f"Error processing experience data: {str(e)}")
                    flash(f"Error saving experiences: {str(e)}", "danger")
            else:
               flash('CSRF validation failed.', 'danger')
    
        # Extract experiences from resume data for rendering
        experiences = []
        if resume.resume_data and 'experience' in resume.resume_data:
            experiences_data = resume.resume_data['experience']
            if isinstance(experiences_data, list):
                experiences = experiences_data
            else:
                # Handle single experience object
                experiences = [experiences_data]
        
        print(f"Rendering with experiences: {experiences}")
    
        return render_template('resume_experience.html', form=form, resume=resume, 
                          experiences=experiences, skills=session.get('skills', []))

    @app.route('/resume/<int:resume_id>/education', methods=['GET', 'POST'])
    @login_required
    def resume_education(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        form = EducationForm()

        if request.method == 'POST' and request.form.get('education_data'):
            if resume.resume_data is None:
              resume.resume_data = {}
            try:
                educations_json = json.loads(request.form.get('education_data'))
                resume.resume_data['education'] = educations_json
                attributes.flag_modified(resume, 'resume_data')
                db.session.commit()
                flash('Education information saved successfully!', 'success')
                return redirect(url_for('resume_summary', resume_id=resume.id))
            except Exception as e:
                db.session.rollback()
                print(f"Error processing education data: {str(e)}")
                flash(f"Error saving education: {str(e)}", 'danger')
                
        # Find existing educations to pass to the template
        educations = []
        if resume.resume_data and 'education' in resume.resume_data:
            edu_data = resume.resume_data['education']
            if isinstance(edu_data, list):
                educations = edu_data
            elif isinstance(edu_data, dict):
                educations = [edu_data]  # Convert single education to list format
                
        
        if resume.resume_data and 'education' in resume.resume_data:
            edu = resume.resume_data['education']
            # Handle different formats properly
            if isinstance(edu, dict):
                # Single education as dictionary
                form.degree.data = edu.get('degree', '')
                form.school.data = edu.get('school', '')
                form.year.data = edu.get('year', '')
         
                
        return render_template('resume_education.html', form=form, resume=resume, educations=educations)

    @app.route('/resume/<int:resume_id>/skills', methods=['GET', 'POST'])
    @login_required
    def resume_skills(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        form = SkillsForm()
        if form.validate_on_submit() and form.skills.data :
            if resume.resume_data is None:
              resume.resume_data = {}
            resume.resume_data['skills'] = form.skills.data
            attributes.flag_modified(resume, 'resume_data')
            try:
               db.session.commit()
               flash('Skills saved successfully!', 'success')
               return redirect(url_for('resume_experience', resume_id=resume.id))
            except Exception as e:
               db.session.rollback()
               print(f"Error saving skills: {str(e)}")
               flash(f"Error saving skills: {str(e)}", 'danger')
            # Get suggested skills
        suggested_skills = []
        if resume.job:
            # Extract skills from job description
            job_skills = extract_skills_from_text(resume.job.description)
            # Sort by importance and take top skills
            suggested_skills = sorted(job_skills.items(), key=lambda x: x[1], reverse=True)
            suggested_skills = [skill for skill, _ in suggested_skills[:15]]
        # Pre-populate form
        if resume.resume_data and 'skills' in resume.resume_data:
            form.skills.data = resume.resume_data['skills']
        return render_template('resume_skills.html', form=form, resume=resume, suggested_skills=suggested_skills)

    @app.route('/resume/<int:resume_id>/preview')
    @login_required
    def resume_preview(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        
        # Get all available templates
        template_registry = TemplateRegistry('./templates')
        templates = template_registry.get_all_templates()
        
        return render_template(
            'resume_preview.html', 
            resume=resume,
            templates=templates,
            selected_template=resume.template or 'standard'  # Default to modern if none selected
        )
    @app.route('/resume/<int:resume_id>/download')
    @login_required
    def download_resume(resume_id):
        
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        
        # Get template ID
        template_id = resume.template or 'standard'
        
        try:
            
            # Generate absolute CSS file path
            css_path = os.path.join(app.root_path, 'static', 'css', 'templates', template_id, 'style.css')
            
            with open(css_path, 'r') as f:
                css_content = f.read()
            # Render HTML template without embedded CSS
            html_string = render_template(
                f'{template_id}/template.html',
                resume=resume.resume_data,
                template=template_id,
                css_content=css_content
            )
            # Create a BytesIO object to store the PDF
            pdf_file = BytesIO()
            
            html = HTML(string=html_string, base_url=request.url_root)
            html.write_pdf(pdf_file)
            pdf_file.seek(0)

            # Create a filename
            name = resume.resume_data.get('contact', {}).get('name', 'resume')
            filename = f"{name.replace(' ', '_').lower()}_resume.pdf"
           
            # Send the PDF as a response
            return send_file(
                pdf_file,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
        except Exception as e:
            print(f"Error generating PDF: {e}")
            flash(f"Error generating PDF: {str(e)}", 'danger')
            return redirect(url_for('resume_preview', resume_id=resume_id))

    @app.route('/resume/<int:resume_id>/update-template', methods=['POST'])
    @login_required
    def update_resume_template(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        
        # Get the selected template
        template = request.form.get('template')
        
        # Update the resume with the new template
        if template:
            resume.template = template
            db.session.commit()
            # flash('Template updated successfully!', 'success')
        
        return redirect(url_for('resume_preview', resume_id=resume_id))
    
    @app.route('/resume/<int:resume_id>/render')
    @login_required
    def resume_render(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        
        # Default to standard template if none specified
        template_id = resume.template or 'standard'
        # Render the resume template
        return render_template(
            f'{template_id}/template.html',
            resume=resume.resume_data,
            template=template_id
        )

    @app.route('/resume/<int:resume_id>/delete', methods=['POST'])
    @login_required
    def delete_resume(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)  # Forbidden if not the owner

        try:
            db.session.delete(resume)
            db.session.commit()
            return jsonify({"success": True,"message": "Resume deleted successfully"})
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting resume: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Get user's resumes
        resumes = Resume.query.filter_by(user_id=current_user.id).all()
        
        # Process resumes for display
        for resume in resumes:
            # Handle general resumes (without a job)
                   # Set display values explicitly
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
            days_ago = job.get('created_at', 0)
            if days_ago == 0:
                job['created_at'] = "Today"
            elif days_ago == 1:
                job['created_at'] = "Yesterday"
            else:
                job['created_at'] = f"{days_ago} days ago"
        
        # Placeholder for applications count
        applications_count = Application.query.filter_by(user_id=current_user.id).count()
        
        return render_template(
            'dashboard.html', 
            resumes=resumes,
            job_matches=len(job_matches_list),
            job_matches_list=job_matches_list,
            applications=applications_count
        )

    @app.route('/pricing')
    def pricing():
        return render_template('pricing.html')

    @app.route('/resume/<int:resume_id>/view')
    @login_required
    def view_resume(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        # Check if the resume belongs to the current user
        if resume.user_id != current_user.id:
            flash('You do not have permission to view this resume.', 'danger')
            return redirect(url_for('dashboard'))
        
        # return render_template('view_resume.html', resume=resume)
        # Temp
        return render_template('resume_template.html', resume=resume)
    

    @app.route('/resume/<int:resume_id>/pdf', methods=['GET', 'POST'])
    @login_required
    def generate_pdf(resume_id):
        """Generate and download a PDF version of the resume.
        
        Supports both GET and POST methods:
        - GET: Simple PDF generation with default settings
        - POST: Enhanced PDF generation with optional profile image upload
        """
        resume = Resume.query.get_or_404(resume_id)
    
        # Check if the resume belongs to the current user
        if resume.user_id != current_user.id:
            flash('You do not have permission to access this resume.', 'danger')
            return redirect(url_for('dashboard'))
        
        # If this is a POST request from the template selection page
        if request.method == 'POST':
            # Update the template if selected
            selected_template = request.form.get('template')
            # If template was selected and is valid, update the resume
            if selected_template and selected_template in RESUME_TEMPLATES:
                resume.template = selected_template
                db.session.commit()
                flash('Template updated successfully!', 'success')
        # Import the PDF generator       
        from pdf_generator import generate_resume_pdf      
        # Generate the PDF
        pdf_buffer, result = generate_resume_pdf(resume_id, current_user, db, Resume)
        
        if pdf_buffer is None:
            # Error occurred
            flash(f"Error generating PDF: {result}", 'danger')
            return redirect(url_for('resume_preview', resume_id=resume_id))
        
        # Create response with PDF
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=result
        )


    @app.route('/resume/create/general')
    @login_required
    def create_general_resume():
        """
        Create a general resume not tied to any specific job
        """
        try:
            # Create a new resume without a job_id
            resume = Resume(
                user_id=current_user.id,
                resume_data={},
                title="General Resume"  # Default title for general resumes
            )
            
            # Add to database
            db.session.add(resume)
            db.session.commit()
            
            # Set default skills list (empty for general resume)
            session['skills'] = []
            
            # Redirect to the first step of resume creation
            flash('General resume creation started! Let\'s add your contact information.', 'success')
            return redirect(url_for('resume_contact', resume_id=resume.id))
        
        except Exception as e:
            print(f"Error creating general resume: {e}")
            flash(f"Error creating resume: {str(e)}", 'danger')
            return redirect(url_for('dashboard'))

    @app.route('/resume/<int:resume_id>/preview-pdf')
    @login_required
    def preview_pdf(resume_id):
        """Preview the PDF in the browser instead of downloading it."""
        resume = Resume.query.get_or_404(resume_id)
        
        # Check if the resume belongs to the current user
        if resume.user_id != current_user.id:
            flash('You do not have permission to access this resume.', 'danger')
            return redirect(url_for('dashboard'))
        
        # Import the PDF generator
        from pdf_generator import generate_resume_pdf
        
        # Generate the PDF
        pdf_buffer, result = generate_resume_pdf(resume_id, current_user, db, Resume)
        
        if pdf_buffer is None:
            # Error occurred
            flash(f"Error generating PDF preview: {result}", 'danger')
            return redirect(url_for('resume_preview', resume_id=resume_id))
        
        # Create response with PDF for display in browser
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline'
        
        return response

    @app.route('/applications')
    @login_required
    def applications():
        # Get all applications for current user
        user_applications = Application.query.filter_by(user_id=current_user.id).order_by(Application.applied_date.desc()).all()
        
        # Group by status
        applications_by_status = {
            'applied': [],
            'interviewing': [],
            'offered': [],
            'rejected': [],
            'accepted': []
        }
        
        for app in user_applications:
            applications_by_status[app.status].append(app)
        
        return render_template('applications.html', applications=user_applications, grouped=applications_by_status)

    @app.route('/jobs/<slug>/apply', methods=['GET', 'POST'])
    @login_required
    def apply_to_job(slug):
        job = Job.query.filter_by(slug=slug).first_or_404()
        
        # Check if already applied
        existing_application = Application.query.filter_by(
            user_id=current_user.id,
            job_id=job.id
        ).first()
        
        if existing_application:
            flash('You have already applied to this job.', 'info')
            return redirect(url_for('application_details', application_id=existing_application.id))
        
        # Get user's resumes
        resumes = Resume.query.filter_by(user_id=current_user.id).all()
        
        if request.method == 'POST':
            resume_id = request.form.get('resume_id')
            
            # Create application
            application = Application(
                user_id=current_user.id,
                job_id=job.id,
                resume_id=resume_id if resume_id else None,
                status='applied'
            )
            try:
              db.session.add(application)
              db.session.commit()
              flash('Application submitted successfully!', 'success')
              return redirect(url_for('application_details', application_id=application.id))
            except Exception as e:
              db.session.rollback()
              print(f'error creating application:{e}')
              flash(f'Error creating application: {str(e)}', 'danger')
              
            
            
        
        return render_template('apply_job.html', job=job, resumes=resumes)


    @app.route('/applications/<int:application_id>', methods=['GET', 'POST'])
    @login_required
    def application_details(application_id):
        application = Application.query.get_or_404(application_id)
        
        # Check if current user owns this application
        if application.user_id != current_user.id:
            abort(403)
        
        form = ApplicationForm(obj=application)
        
        if form.validate_on_submit():
            # Update application
            application.status = form.status.data
            application.notes = form.notes.data
            
            db.session.commit()
            flash('Application updated successfully!', 'success')
            return redirect(url_for('applications'))
        
        # Get application timeline TODO:
        timeline = []
        
        return render_template('application_details.html', application=application, form=form, timeline=timeline)


    

    @app.route('/resume/<int:resume_id>/save-field', methods=['POST'])
    @login_required
    def save_resume_field(resume_id):
        """Save a single field from a resume form via AJAX."""
        resume = Resume.query.get_or_404(resume_id)
        
        # Check if the resume belongs to the current user
        if resume.user_id != current_user.id:
            return jsonify({"success": False, "error": "Unauthorized"}), 403
        
        # Get field data from request
        data = request.get_json()
        if not data or 'field_name' not in data or 'field_value' not in data:
            return jsonify({"success": False, "error": "Missing field data"}), 400
        
        field_name = data['field_name']
        field_value = data['field_value']
        
        try:
            # Initialize resume_data if it doesn't exist
            if resume.resume_data is None:
                resume.resume_data = {}
            
            # Determine the section based on field name
            if field_name in ['name', 'email', 'phone', 'location', 'linkedin', 'website']:
                # Contact fields
                if 'contact' not in resume.resume_data:
                    resume.resume_data['contact'] = {}
                resume.resume_data['contact'][field_name] = field_value
            
            elif field_name == 'skills':
                # Skills field
                resume.resume_data['skills'] = field_value
            
            elif field_name == 'summary':
                # Summary field
                if isinstance(resume.resume_data.get('summary'), dict):
                    resume.resume_data['summary']['content'] = field_value
                else:
                    resume.resume_data['summary'] = {
                        'content': field_value,
                        'last_updated': datetime.now().isoformat()
                    }
            
            # Flag the resume_data field as modified so SQLAlchemy detects the change
            attributes.flag_modified(resume, 'resume_data')
            
            # Save changes
            db.session.commit()
            
            return jsonify({"success": True})
        
        except Exception as e:
            db.session.rollback()
            print(f"Error saving field: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500


    @app.route('/resume/<int:resume_id>/customize', methods=['POST'])
    @login_required
    def customize_template(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        
        # Get customization options from form
        primary_color = request.form.get('primary_color')
        font_family = request.form.get('font_family')
        
        # Store customization options
        if not resume.customization:
            resume.customization = {}
        
        resume.customization['colors'] = {
            'primary': primary_color
        }
        
        resume.customization['fonts'] = {
            'primary': font_family
        }
        
        db.session.commit()
        
        flash('Template customized successfully!', 'success')
        return redirect(url_for('resume_preview', resume_id=resume.id))
