from flask import Blueprint, request, jsonify, Response
from flask_login import login_required, current_user
from datetime import datetime
from models import Resume, ResumeTemplate
from services.template import TemplateResolver, TemplateContext, RenderHandler
from db import db

template_bp = Blueprint('template', __name__)

# Initialize template services
resolver = TemplateResolver()
context_builder = TemplateContext(resolver)
renderer = RenderHandler()


@template_bp.route('/templates', methods=['GET'])
def get_templates():
    """
    Get all available templates for gallery.
    Public endpoint - no authentication required.
    """
    try:
        templates = resolver.get_template_gallery_data()
        return jsonify(templates), 200
    except Exception as e:
        print(f"Error fetching templates: {e}")
        return jsonify({'error': 'Failed to fetch templates'}), 500


@template_bp.route('/resumes/<int:resume_id>/template', methods=['POST'])
@login_required
def select_template(resume_id):
    """
    Save user's template selection and theme overrides.
    Creates or updates user_resume_settings record.
    """
    try:
        # Verify resume exists and user owns it
        resume = Resume.query.get(resume_id)
        if not resume:
            return jsonify({'error': 'Resume not found'}), 404
        
        if resume.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        # Parse request body
        data = request.get_json()
        template_id = data.get('template_id')
        theme_overrides = data.get('theme_overrides', {})
        
        if not template_id:
            return jsonify({'error': 'template_id is required'}), 400
        
        # Verify template exists
        template = ResumeTemplate.query.get(template_id)
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        # Check if UserResumeSettings table exists and update/create record
        # For now, store in Resume model (assuming it has template_id field)
        # TODO: Create UserResumeSettings table if needed ????
        resume.template = template_id
        resume.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'ok': True,
            'template_id': template_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error saving template selection: {e}")
        return jsonify({'error': 'Failed to save template selection'}), 500


@template_bp.route('/resumes/<int:resume_id>/preview', methods=['GET'])
@login_required
def preview_resume(resume_id):
    """
    Render resume with selected template.
    Returns HTML for preview iframe.
    """
    try:
        # Verify resume exists and user owns it
        resume = Resume.query.get(resume_id)
        if not resume:
            return jsonify({'error': 'Resume not found'}), 404
        
        if resume.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        # Get template_id from query param or use saved preference
        template_id = request.args.get('template_id')
        if not template_id:
            # Use saved template preference or default
            template_id = getattr(resume, 'template', 'one_col_classic')
        
        # Verify template exists
        template = ResumeTemplate.query.get(template_id)
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        # Get resume data
        # Assuming resume.data contains the JSON resume data
        resume_data = resume.data if hasattr(resume, 'data') and resume.data else {}
        
        if not resume_data:
            return Response(
                '<html><body><h1>No resume data available</h1><p>Please upload or create resume content first.</p></body></html>',
                mimetype='text/html'
            )
        
        # Get theme overrides (if any)
        theme_overrides = request.args.get('theme_overrides')
        if theme_overrides:
            import json
            try:
                theme_overrides = json.loads(theme_overrides)
            except:
                theme_overrides = {}
        else:
            theme_overrides = {}
        
        # Build rendering context
        context = context_builder.build_context(
            template_id=template_id,
            resume_data=resume_data,
            user_overrides=theme_overrides
        )
        
        if not context:
            return Response(
                '<html><body><h1>Failed to build template context</h1></body></html>',
                mimetype='text/html'
            )
        
        # Render HTML
        html = renderer.render(context)
        
        if not html:
            return Response(
                '<html><body><h1>Failed to render template</h1></body></html>',
                mimetype='text/html'
            )
        
        # Return rendered HTML
        return Response(html, mimetype='text/html')
        
    except Exception as e:
        print(f"Error rendering preview: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            f'<html><body><h1>Rendering Error</h1><pre>{str(e)}</pre></body></html>',
            mimetype='text/html'
        ), 500


@template_bp.route('/resumes/<int:resume_id>/pdf', methods=['GET'])
@login_required
def export_pdf(resume_id):
    """
    Generate PDF export of resume.
    Stub for now - returns 501 Not Implemented.
    """
    try:
        # Verify resume exists and user owns it
        resume = Resume.query.get(resume_id)
        if not resume:
            return jsonify({'error': 'Resume not found'}), 404
        
        if resume.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        # TODO: Implement PDF generation
        # 1. Get HTML from preview endpoint logic
        # 2. Convert HTML to PDF using WeasyPrint (already in project)
        # 3. Return PDF file
        
        return jsonify({
            'error': 'PDF export not yet implemented',
            'message': 'This feature is coming soon'
        }), 501
        
    except Exception as e:
        print(f"Error exporting PDF: {e}")
        return jsonify({'error': 'Failed to export PDF'}), 500