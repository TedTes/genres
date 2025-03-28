
from flask import Blueprint, request,flash,url_for,redirect,render_template,abort
from flask_login import login_user,  current_user, login_required
from models import  Job, Resume,Application

application_bp = Blueprint("application",__name__)

@application_bp.route('/applications')
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

@application_bp.route('/jobs/<slug>/apply', methods=['GET', 'POST'])
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
        return redirect(url_for('application.application_details', application_id=existing_application.id))
    
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


@application_bp.route('/applications/<int:application_id>', methods=['GET', 'POST'])
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