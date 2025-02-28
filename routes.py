from flask import render_template, request, redirect, url_for, flash, session, abort, send_file
from helpers import fetch_jobs
from flask import render_template, request, redirect, url_for, flash, session, abort, send_file
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import io
import requests

from forms import RegistrationForm, LoginForm, JobSearchForm, ContactForm, SummaryForm, ExperienceForm, EducationForm, SkillsForm
from db import db
from models import  User, Job, Resume


# Import NLP analyzer 
import spacy
nlp = spacy.load('en_core_web_sm')

app = None

def init_routes(flask_app):
    global app
    app = flask_app
    @app.route('/')
    def home():
        try:
            print("home being accessed")
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
        if form.validate_on_submit():
            jobs_data = fetch_jobs(form.search.data, form.location.data, form.remote.data)
        else:
            jobs_data = fetch_jobs()  # Default fetch
        return render_template('jobs.html', jobs=jobs_data, form=form)

    @app.route('/job/<slug>')
    def job_detail(slug):
        job = Job.query.filter_by(slug=slug).first()
        if not job:
            url = "https://job-board.arbeitnow.com/api/jobs"  # Fetch all and find, or use specific endpoint if available
            jobs_data = fetch_jobs()
            job_data = next((j for j in jobs_data if j['slug'] == slug), None)
            if job_data:
                job = Job(
                    slug=job_data['slug'],
                    title=job_data['title'],
                    company=job_data['company_name'],
                    location=job_data['location'],
                    description=job_data['description'],
                    posted_at=datetime.fromisoformat(job_data['created_at'].replace('Z', '+00:00'))
                )
                db.session.add(job)
                db.session.commit()
            else:
                flash('Job not found.', 'danger')
                return redirect(url_for('jobs'))
        return render_template('job_detail.html', job=job)
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
                    password_hash=hashed_password
                )
                
                # Add and commit to database
                db.session.add(new_user)
                db.session.commit()
                
                flash('Account created successfully! Please log in.', 'success')
                return redirect(url_for('login'))
                
            except Exception as e:
                db.session.rollback()  # Roll back the session on error
                print(f"Registration error: {e}")
                flash('An error occurred during registration. Please try again.', 'danger')
        
        return render_template('register.html', form=form)

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



    @app.route('/resume/start/<int:job_id>')
    @login_required
    def start_resume(job_id):
        job = Job.query.get_or_404(job_id)
        resume = Resume(user_id=current_user.id, job_id=job.id, resume_data={})
        db.session.add(resume)
        db.session.commit()
        skills = analyze_job_description(job.description)
        session['skills'] = skills
        return redirect(url_for('resume_contact', resume_id=resume.id))

    @app.route('/resume/<int:resume_id>/contact', methods=['GET', 'POST'])
    @login_required
    def resume_contact(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        form = ContactForm()
        if form.validate_on_submit():
            resume.resume_data['contact'] = {
                'name': form.name.data,
                'email': form.email.data,
                'phone': form.phone.data
            }
            db.session.commit()
            return redirect(url_for('resume_summary', resume_id=resume.id))
        if 'contact' in resume.resume_data:
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
        form = SummaryForm()
        if form.validate_on_submit():
            resume.resume_data['summary'] = form.summary.data
            db.session.commit()
            return redirect(url_for('resume_experience', resume_id=resume.id))
        if 'summary' in resume.resume_data:
            form.summary.data = resume.resume_data['summary']
        return render_template('resume_summary.html', form=form, resume=resume, skills=session.get('skills', []))

    @app.route('/resume/<int:resume_id>/experience', methods=['GET', 'POST'])
    @login_required
    def resume_experience(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        form = ExperienceForm()
        if form.validate_on_submit():
            resume.resume_data['experience'] = {
                'title': form.title.data,
                'company': form.company.data,
                'start_date': form.start_date.data,
                'end_date': form.end_date.data,
                'bullets': form.bullets.data
            }
            db.session.commit()
            return redirect(url_for('resume_education', resume_id=resume.id))
        if 'experience' in resume.resume_data:
            exp = resume.resume_data['experience']
            form.title.data = exp.get('title', '')
            form.company.data = exp.get('company', '')
            form.start_date.data = exp.get('start_date', '')
            form.end_date.data = exp.get('end_date', '')
            form.bullets.data = exp.get('bullets', '')
        return render_template('resume_experience.html', form=form, resume=resume, skills=session.get('skills', []))

    @app.route('/resume/<int:resume_id>/education', methods=['GET', 'POST'])
    @login_required
    def resume_education(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        form = EducationForm()
        if form.validate_on_submit():
            resume.resume_data['education'] = {
                'degree': form.degree.data,
                'school': form.school.data,
                'year': form.year.data
            }
            db.session.commit()
            return redirect(url_for('resume_skills', resume_id=resume.id))
        if 'education' in resume.resume_data:
            edu = resume.resume_data['education']
            form.degree.data = edu.get('degree', '')
            form.school.data = edu.get('school', '')
            form.year.data = edu.get('year', '')
        return render_template('resume_education.html', form=form, resume=resume)

    @app.route('/resume/<int:resume_id>/skills', methods=['GET', 'POST'])
    @login_required
    def resume_skills(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        form = SkillsForm()
        if form.validate_on_submit():
            resume.resume_data['skills'] = form.skills.data
            db.session.commit()
            return redirect(url_for('resume_preview', resume_id=resume.id))
        if 'skills' in resume.resume_data:
            form.skills.data = resume.resume_data['skills']
        return render_template('resume_skills.html', form=form, resume=resume, suggested_skills=session.get('skills', []))

    @app.route('/resume/<int:resume_id>/preview')
    @login_required
    def resume_preview(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        return render_template('resume_template.html', **resume.resume_data, job=resume.job)

    @app.route('/resume/<int:resume_id>/download')
    @login_required
    def resume_download(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        html = render_template('resume_template.html', **resume.resume_data, job=resume.job)
        pdf = generate_pdf(html)
        return send_file(
            io.BytesIO(pdf),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'resume_for_{resume.job.slug}.pdf'
        )


    @app.route('/dashboard')
    @login_required
    def dashboard():
        resumes = Resume.query.filter_by(user_id=current_user.id).all()
        return render_template('dashboard.html', resumes=resumes)

    @app.route('/pricing')
    def pricing():
        return render_template('pricing.html')
