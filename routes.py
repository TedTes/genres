from flask import render_template, request, redirect, url_for, flash, session, abort, send_file
from helpers import fetch_jobs,extract_job_tags,calculate_resume_completeness
from flask import render_template, request, redirect, url_for, flash, session, abort, send_file
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import io

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
                    # Fetch all jobs from API 
                    jobs_data = fetch_jobs()
                    
                    # Find the job with matching slug
                    job_data = next((j for j in jobs_data if j.get('slug') == slug), None)
                    
                    if not job_data:
                        flash('Job not found.', 'danger')
                        return redirect(url_for('jobs'))
                    
                    created_at = job_data.get('created_at')
                    # Create a new Job record in the database
                    job = Job(
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
                    created_at = job_data.get('created_at')
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
                    db.session.add(job)
                    db.session.commit()
                else:
                    # Convert the SQLAlchemy model to a dictionary for template rendering
                    job_data = {
                        'id': job.id,
                        'slug': job.slug,
                        'title': job.title,
                        'company_name': job.company,
                        'location': job.location,
                        'description': job.description,
                        'remote': True if 'remote' in job.location.lower() else False,
                        'created_at': "Today" if (datetime.now() - job.posted_at).days == 0 else 
                                    "Yesterday" if (datetime.now() - job.posted_at).days == 1 else
                                    f"{(datetime.now() - job.posted_at).days} days ago",
                        'tags': extract_job_tags(job.title, job.description),
                        'apply_url': f"https://www.arbeitnow.com/view/{job.slug}" if job.slug else None
                    }
                
                # For authenticated users, calculate skills match
                skills_match = []
                match_percentage = 0
                
                if current_user.is_authenticated:
                    # This would be where TODOoo implement  actual skills matching algorithm
                    
                    
                    # Example mock skills data - TODOoo:  extract these from the user's profile
                    user_skills = [
                        {"name": "Python", "level": 85},
                        {"name": "JavaScript", "level": 70},
                        {"name": "SQL", "level": 75},
                        {"name": "React", "level": 65},
                        {"name": "Flask", "level": 80}
                    ]
                    
                    # Extract skills from job description
                    job_skills = extract_job_tags(job_data.get('title', ''), job_data.get('description', ''))
                    
                    # Calculate match for each user skill (simplified algorithm)
                    for skill in user_skills:
                        skill_name = skill["name"]
                        # Check if the skill is mentioned in the job skills
                        if any(skill_name.lower() in job_skill.lower() for job_skill in job_skills):
                            # High match if directly mentioned
                            match = skill["level"]
                        elif any(skill_name.lower() in job_data.get('description', '').lower() for job_skill in job_skills):
                            # Medium match if mentioned in description
                            match = int(skill["level"] * 0.7)
                        else:
                            # Low match for general skills
                            match = int(skill["level"] * 0.3)
                        
                        skills_match.append({
                            "name": skill_name,
                            "match": match
                        })
                    
                    # Calculate overall match percentage (average of all skills)
                    if skills_match:
                        match_percentage = int(sum(skill["match"] for skill in skills_match) / len(skills_match))
                
                # Find similar jobs
                similar_jobs = []
                
                if job_data.get('tags'):
                    # Get all jobs (TODO: use a more efficient query in a real app)
                    all_jobs = fetch_jobs()
                    
                    # Score each job based on tag similarity
                    job_scores = []
                    for other_job in all_jobs:
                        # Skip the current job
                        if other_job.get('slug') == slug:
                            continue
                        
                        # Extract tags for the other job
                        other_tags = extract_job_tags(other_job.get('title', ''), other_job.get('description', ''))
                        
                        # Calculate score based on tag overlap
                        common_tags = set(job_data.get('tags')).intersection(set(other_tags))
                        score = len(common_tags)
                        
                        # Add location score if locations match
                        if job_data.get('location') == other_job.get('location'):
                            score += 1
                        
                        # Add remote score if both are remote
                        if job_data.get('remote') and other_job.get('remote'):
                            score += 1
                        
                        # Store the job with its score
                        if score > 0:
                            job_scores.append((score, other_job))
                    
                    # Sort by score (highest first) and take top 3
                    job_scores.sort(reverse=True, key=lambda x: x[0])
                    similar_jobs = [job for _, job in job_scores[:3]]
                    
                    # Process similar jobs to add tags and format dates
                    for job in similar_jobs:
                        job['tags'] = extract_job_tags(job.get('title', ''), job.get('description', ''))
                        
                        # Format date
                        created_at = job.get('created_at')
                        if created_at:
                            try:
                                if created_at and isinstance(created_at,str):
                                   date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                else:
                                    date_obj = datetime.now()
                                days_ago = (datetime.now(date_obj.tzinfo) - date_obj).days
                                
                                if days_ago == 0:
                                    job['created_at'] = "Today"
                                elif days_ago == 1:
                                    job['created_at'] = "Yesterday"
                                else:
                                    job['created_at'] = f"{days_ago} days ago"
                            except:
                                job['created_at'] = "Recently"
                        else:
                            job['created_at'] = "Recently"
                
                return render_template(
                    'job_detail.html',
                    job=job_data,
                    skills_match=skills_match,
                    match_percentage=match_percentage,
                    similar_jobs=similar_jobs
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
        flash('Resume creation started! Let\'s add your contact information.', 'success')
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
            return redirect(url_for('resume_skills', resume_id=resume.id))
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
            return redirect(url_for('resume_preview', resume_id=resume.id))
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
            return redirect(url_for('resume_summary', resume_id=resume.id))
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
            return redirect(url_for('resume_experience', resume_id=resume.id))
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
                resume.display_match = 100  # General resumes show 100%
                
                # Add match score for general resumes (could be based on completeness)
            resume.match_score = calculate_resume_completeness(resume.resume_data)
            
        # Get job matches count
        job_matches = 3  # This would be calculated based on  matching algorithm
        
        # Get sample job matches list ( TODO:this would come from  database)
        job_matches_list = [
            {
                'slug': 'software-engineer-xyz-company',
                'title': 'Software Engineer',
                'company_name': 'XYZ Tech',
                'location': 'San Francisco, CA',
                'remote': True,
                'match': 92
            },
            {
                'slug': 'frontend-developer-abc-inc',
                'title': 'Frontend Developer',
                'company_name': 'ABC Inc',
                'location': 'New York, NY',
                'remote': False,
                'match': 87
            },
            {
                'slug': 'fullstack-engineer-startup',
                'title': 'Fullstack Engineer',
                'company_name': 'Startup Co',
                'location': 'Austin, TX',
                'remote': True,
                'match': 84
            }
        ]
        
        # Placeholder for applications count
        applications = 0
        
        return render_template(
            'dashboard.html', 
            resumes=resumes,
            job_matches=job_matches,
            job_matches_list=job_matches_list,
            applications=applications
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
    

    @app.route('/resume/<int:resume_id>/pdf')
    @login_required
    def generate_pdf(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        
        # Check if the resume belongs to the current user
        if resume.user_id != current_user.id:
            flash('You do not have permission to access this resume.', 'danger')
            return redirect(url_for('dashboard'))
        
        # TODO:Generate PDF logic here
        # For now, redirect to the preview page
        flash('PDF generation will be implemented soon.', 'info')
        return redirect(url_for('resume_preview', resume_id=resume.id))


   
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