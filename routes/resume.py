from flask import Blueprint, current_app,request,Response, abort,jsonify,render_template,flash,request,redirect,url_for,send_file,session,make_response,g
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
def generate_job_resume(job_id):
    """
    Create a resume for a specific job, pre-populating with user contact information.
    """
    # Fetch the job
    job = Job.query.get_or_404(job_id)
    
    # Get user's previous resume data for pre-population
    last_resume = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.updated_at.desc()).first()
    
    # Initialize resume_data
    resume_data = {}
    
    # Pre-populate contact information from the User table
    contact_data = {
        "name": current_user.name or "",
        "email": current_user.email,
        "phone": current_user.phone or "",
        "location": current_user.location or "",
        "linkedin": current_user.linkedin or "",
        "github": current_user.github or "",
        "website": current_user.website or ""
    }
    
    if last_resume and last_resume.resume_data:
        # Copy the previous resume data
        resume_data = last_resume.resume_data.copy()
        # Ensure the contact section is updated with the latest user data
        resume_data["contact"] = contact_data
    else:
        # Initialize new resume_data with contact and empty sections
        resume_data = {
            "contact": contact_data,
            "sections": []
        }
    
    # Create a new resume for the specific job
    new_resume = Resume(
        user_id=current_user.id,
        job_id=job.id,
        resume_data=resume_data,
        title=job.title
    )
    
    # Add to database
    db.session.add(new_resume)
    db.session.commit()
    
    # Extract relevant skills from job description
    skills = analyze_job_description(job.description)
    session['skills'] = skills
    
    flash('Resume created with your information! Customize it for this job posting.', 'success')
    return redirect(url_for('resume.resume_builder', resume_id=new_resume.id)) 
@resume_bp.route('/resume/<int:resume_id>/download')
@login_required
def download_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    print("its coming ")
    if resume.user_id != current_user.id:
        abort(403)
    
    try:
        
        template_id = resume.template or 'professional_classic'
        template = template_registry.get_template(template_id)

        html_string  = generate_resume(g.app,resume)

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
        return redirect(url_for('resume.resume_builder', resume_id=resume_id))

@resume_bp.route('/resume/<int:resume_id>/update-template', methods=['POST'])
@login_required
def update_resume_template(resume_id):
    """Update the resume template without reloading the page."""
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
         abort(403)
    
    # Get the selected template
    template = request.form.get('template')
    
    try:
      if template:
        resume.template = template
        db.session.commit()

        return redirect(url_for('resume.resume_builder', resume_id=resume_id))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating template: {str(e)}")
        
        # Fallback
        flash(f"Error updating template: {str(e)}", "error")
        return redirect(url_for('resume.resume_builder', resume_id=resume_id))

@resume_bp.route('/resume/<int:resume_id>/render')
@login_required
def resume_render(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        abort(403)
    # Default to standard template if none specified
    template_id = resume.template or 'professional_classic'
    template = template_registry.get_template(template_id)
   
    html_output  = generate_resume(g.app,resume)
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



@resume_bp.route('/resume/create/general')
@login_required
def generate_general_resume():
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
        return redirect(url_for('resume.resume_builder', resume_id=resume.id))
    
    except Exception as e:
        print(f"Error creating general resume: {e}")
        flash(f"Error creating resume: {str(e)}", 'danger')
        return redirect(url_for('root.dashboard'))




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


@resume_bp.route('/resume/<int:resume_id>/builder', methods=['GET', 'POST'])
@login_required
def resume_builder(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        abort(403)
    # Initialize forms
    contact_form = ContactForm()
    skills_form = SkillsForm()
    experience_form = ExperienceForm()
    education_form = EducationForm()
    summary_form = SummaryForm()

    # Pre-populate forms with existing data
    if resume.resume_data:
        if 'contact' in resume.resume_data:
            contact_form.name.data = resume.resume_data['contact'].get('name', '')
            contact_form.email.data = resume.resume_data['contact'].get('email', '')
            contact_form.phone.data = resume.resume_data['contact'].get('phone', '')
        
        if 'skills' in resume.resume_data:
            skills_form.skills.data = resume.resume_data['skills']
        
        if 'summary' in resume.resume_data:
            if isinstance(resume.resume_data['summary'], dict):
                summary_form.summary.data = resume.resume_data['summary'].get('content', '')
            else:
                summary_form.summary.data = resume.resume_data['summary']
    
    # Get skills from job description if available
    skills = []
    if resume.job_id:
        job = Job.query.get(resume.job_id)
        if job:
            skills = analyze_job_description(job.description)
    
    # Get all available templates
    templates = template_registry.get_all_templates()

    return render_template('resume_builder.html',
                         resume=resume,
                         initial_resume_data=resume.resume_data,
                         contact_form=contact_form,
                         skills_form=skills_form,
                         experience_form=experience_form,
                         education_form=education_form,
                         summary_form=summary_form,
                         skills=skills,
                         templates=templates,
                         selected_template=(resume.template if resume and resume.template else  'professional_classic') )

@resume_bp.route('/resume/<int:resume_id>/save-field', methods=['POST'])
@login_required
def save_resume_field(resume_id):
    """Save a single field from a resume form via AJAX."""
    resume = Resume.query.get_or_404(resume_id)
    
    if resume.user_id != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    data = request.get_json()
    if not data or 'section' not in data or 'data' not in data:
        return jsonify({"success": False, "error": "Missing data"}), 400
    
    section = data['section']
    field_data = data['data']
    
    try:
        if resume.resume_data is None:
            resume.resume_data = {}
        
        # Update the specific section
        resume.resume_data[section] = field_data
        
        # Flag the resume_data field as modified
        attributes.flag_modified(resume, 'resume_data')
        
        # Save changes
        db.session.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@resume_bp.route('/resume/<int:resume_id>/enhance-summary', methods=['POST'])
@login_required
def enhance_summary(resume_id):
    """Enhance resume summary using AI."""
    resume = Resume.query.get_or_404(resume_id)
    
    if resume.user_id != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    data = request.get_json()
    if not data or 'summary' not in data or 'type' not in data:
        return jsonify({"success": False, "error": "Missing data"}), 400
    
    summary = data['summary']
    enhancement_type = data['type']
    
    try:
        # Get job description if available
        job_description = None
        if resume.job_id:
            job = Job.query.get(resume.job_id)
            if job:
                job_description = job.description
        
        # Enhance summary based on type
        enhanced_summary = enhance_resume_content(
            summary,
            'summary',
            job_description,
            enhancement_type
        )
        
        return jsonify({
            "success": True,
            "enhanced_summary": enhanced_summary
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500