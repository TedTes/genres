from flask import Blueprint, current_app,request,Response, abort,jsonify,render_template,flash,request,redirect,url_for,send_file,session,make_response
from flask_login import login_user,  current_user, login_required
from weasyprint import HTML, CSS
from template_registry import TemplateRegistry
import os
from io import BytesIO
import json
from models import Job, Resume,Application
from sqlalchemy.orm import attributes
from datetime import datetime
from helpers.job_helper import analyze_job_description
from helpers.resume_helper import extract_skills_from_text,generate_resume
from forms import ContactForm,SummaryForm,ExperienceForm,EducationForm,SkillsForm
from db import db

resume_bp = Blueprint("resume", __name__)
template_registry = TemplateRegistry('pages/templates')

@resume_bp.route('/resume/start/<int:job_id>')
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
    return redirect(url_for('resume.resume_contact', resume_id=last_resume.id))

@resume_bp.route('/resume/<int:resume_id>/contact', methods=['GET', 'POST'])
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
            return redirect(url_for('resume.resume_skills', resume_id=resume.id))
        except Exception as e:
            db.session.rollback()
            print(f"Error saving contact info: {str(e)}")
            flash(f"Error saving contact information: {str(e)}", 'danger')

    if resume.resume_data and 'contact' in resume.resume_data:
        form.name.data = resume.resume_data['contact'].get('name', '')
        form.email.data = resume.resume_data['contact'].get('email', '')
        form.phone.data = resume.resume_data['contact'].get('phone', '')
    return render_template('resume_contact.html', form=form, resume=resume)

@resume_bp.route('/resume/<int:resume_id>/summary', methods=['GET', 'POST'])
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
            return redirect(url_for('resume.resume_preview', resume_id=resume.id))
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

@resume_bp.route('/resume/<int:resume_id>/experience', methods=['GET', 'POST'])
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
                    return redirect(url_for('resume.resume_education', resume_id=resume.id))
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

    return render_template('resume_experience.html', form=form, resume=resume, 
                        experiences=experiences, skills=session.get('skills', []))

@resume_bp.route('/resume/<int:resume_id>/education', methods=['GET', 'POST'])
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
            return redirect(url_for('resume.resume_summary', resume_id=resume.id))
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

@resume_bp.route('/resume/<int:resume_id>/skills', methods=['GET', 'POST'])
@login_required
def resume_skills(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        abort(403)
    form = SkillsForm()
    if form.validate_on_submit() and form.skills.data :
        if resume.resume_data is None:
            resume.resume_data = {}
        resume.resume_data['skills'] = [skill.strip() for skill in form.skills.data.split(',')] if form.skills.data else []
        attributes.flag_modified(resume, 'resume_data')
        try:
            db.session.commit()
            flash('Skills saved successfully!', 'success')
            return redirect(url_for('resume.resume_experience', resume_id=resume.id))
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
        form.skills.data = ', '.join(resume.resume_data['skills'])
    return render_template('resume_skills.html', form=form, resume=resume, suggested_skills=suggested_skills)

@resume_bp.route('/resume/<int:resume_id>/preview')
@login_required
def resume_preview(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        abort(403)
    
    # Get all available templates
    templates = template_registry.get_all_templates()

    return render_template(
        'resume_preview.html', 
        resume=resume,
        templates=templates,
        selected_template=resume.template or 'professional_classic'  # Default to professional_classic if none selected
    )
@resume_bp.route('/resume/<int:resume_id>/download')
@login_required
def download_resume(resume_id):
    
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        abort(403)
    
    try:
        
        template_id = resume.template or 'professional_classic'
        template = template_registry.get_template(template_id)

        html_string  = generate_resume(template['theme']['id'],template['layout']['id'],resume.resume_data)
        # Render the resume template
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
        return redirect(url_for('resume.resume_preview', resume_id=resume_id))

@resume_bp.route('/resume/<int:resume_id>/update-template', methods=['POST'])
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
    
    return redirect(url_for('resume.resume_preview', resume_id=resume_id))

@resume_bp.route('/resume/<int:resume_id>/render')
@login_required
def resume_render(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        abort(403)

    # Default to standard template if none specified
    template_id = resume.template or 'professional_classic'
    template = template_registry.get_template(template_id)

    html_output  = generate_resume(template['theme']['id'],template['layout']['id'],resume.resume_data)
    # Render the resume template
    return Response(html_output, mimetype="text/html")


@resume_bp.route('/resume/<int:resume_id>/delete', methods=['POST'])
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
    
    
    # Placeholder for applications count
    applications_count = Application.query.filter_by(user_id=current_user.id).count()
    
    return render_template(
        'dashboard.html', 
        resumes=resumes,
        job_matches=len(job_matches_list),
        job_matches_list=job_matches_list,
        applications=applications_count
    )

    # Placeholder for applications count
    applications_count = Application.query.filter_by(user_id=current_user.id).count()
    
    return render_template(
        'dashboard.html', 
        resumes=resumes,
        job_matches=len(job_matches_list),
        job_matches_list=job_matches_list,
        applications=applications_count
    )



@resume_bp.route('/resume/<int:resume_id>/view')
@login_required
def view_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    # Check if the resume belongs to the current user
    if resume.user_id != current_user.id:
        flash('You do not have permission to view this resume.', 'danger')
        return redirect(url_for('root.dashboard'))
    
    # return render_template('view_resume.html', resume=resume)
    # Temp
    return render_template('resume_template.html', resume=resume)


@resume_bp.route('/resume/<int:resume_id>/pdf', methods=['GET', 'POST'])
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
        return redirect(url_for('root.dashboard'))
    
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
        return redirect(url_for('resume.resume_preview', resume_id=resume_id))
    
    # Create response with PDF
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=result
    )


@resume_bp.route('/resume/create/general')
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
        return redirect(url_for('resume.resume_contact', resume_id=resume.id))
    
    except Exception as e:
        print(f"Error creating general resume: {e}")
        flash(f"Error creating resume: {str(e)}", 'danger')
        return redirect(url_for('root.dashboard'))

@resume_bp.route('/resume/<int:resume_id>/preview-pdf')
@login_required
def preview_pdf(resume_id):
    """Preview the PDF in the browser instead of downloading it."""
    resume = Resume.query.get_or_404(resume_id)
    
    # Check if the resume belongs to the current user
    if resume.user_id != current_user.id:
        flash('You do not have permission to access this resume.', 'danger')
        return redirect(url_for('root.dashboard'))
    
    # Import the PDF generator
    from pdf_generator import generate_resume_pdf
    
    # Generate the PDF
    pdf_buffer, result = generate_resume_pdf(resume_id, current_user, db, Resume)
    
    if pdf_buffer is None:
        # Error occurred
        flash(f"Error generating PDF preview: {result}", 'danger')
        return redirect(url_for('resume.resume_preview', resume_id=resume_id))
    
    # Create response with PDF for display in browser
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline'
    
    return response



@resume_bp.route('/resume/<int:resume_id>/save-field', methods=['POST'])
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


@resume_bp.route('/resume/<int:resume_id>/customize', methods=['POST'])
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
    return redirect(url_for('resume.resume_preview', resume_id=resume.id))