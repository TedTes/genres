from flask import Blueprint, request, jsonify,current_app,send_file, make_response,Response,render_template,flash,redirect,url_for
from flask_login import login_required,current_user
from werkzeug.exceptions import BadRequest
import asyncio
import time
from typing import Dict,Any,Optional,Tuple,List
import io
import tempfile
import os
from services.resume.schemas import (
    ResumeInput, JDInput, OptimizationOptions, OptimizationResult,
    validate_json_with_retry_sync
)

from services.resume.formatting import create_docx_sync, create_pdf_sync
from services.resume.cache import get_enhanced_cache
from helpers.resume_helper import save_optimization_to_db,save_temp_file,_get_cached_optimization_result,_serve_local_file,_proxy_remote_file,_run_optimization_pipeline
from providers import  test_provider_connection
from models import ResumeOptimization
from db import db
import traceback
from datetime import datetime



optimizer_bp = Blueprint('optimizer', __name__)

# Resume AI enhancement endpoints
"""
Resume LLM optimization routes.
Handles AI-powered resume optimization API endpoints.
"""
@optimizer_bp.route('/optimize', methods=['GET'])
@login_required 
def optimize_page():
    return render_template('optimize.html')

    
# Update the optimize_resume endpoint decorator
@optimizer_bp.route('/optimize', methods=['POST'])
@login_required 
def optimize_resume():
    """
    Main resume optimization endpoint.
    
    Request body:
    {
        "resume_input": {"text": "..." or "docx_url": "..." or "pdf_url": "..."},
        "job_description": {"text": "...", "title": "...", "company": "..."},
        "options": {"tone": "professional-concise", "locale": "en-US", ...}
    }
    
    Returns:
        OptimizationResult with optimized resume and analytics
    """
    request_start_time = time.time()
    try:
        # Authentication temporarily disabled for MVP testing
        user_id = current_user.id
        
        # Validate request
        resume_input = None
        # Handle FormData instead of JSON
        if request.content_type.startswith('multipart/form-data'):
               
               
                # Extract form fields
                job_data = {
                    'text': request.form.get('job_description', ''),
                    'title': request.form.get('job_title', ''),
                    'company': request.form.get('job_company', '')
                }
                
                options_data = {
                    'tone': request.form.get('tone', 'professional-concise'),
                    'locale': request.form.get('locale', 'en-US'),
                    'include_pdf': request.form.get('include_pdf', 'true') == 'true'
                }
                
                # Handle resume input
                resume_type = request.form.get('resume_type')
              
                if resume_type == 'file':
                    # Get uploaded file
                    resume_file = request.files.get('resume_file')
                    if not resume_file:
                        return jsonify({'error': 'No file uploaded'}), 400
                    
                    # Save file temporarily and create file URL
                    temp_path = save_temp_file(resume_file)
                    

                    if resume_file.content_type == 'application/pdf':
                        resume_input = ResumeInput(pdf_url=temp_path)
    
                    elif resume_file.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                        resume_input = ResumeInput(docx_url=temp_path)
                    else:
                        content = resume_file.read().decode('utf-8')
                        resume_input = ResumeInput(text=content)

                else:
                    # Text input
                    resume_input = ResumeInput(text=request.form.get('resume_text', ''))

        # Create schema objects
        jd_input = JDInput(**job_data)
        options = OptimizationOptions(**options_data) 
        # Process optimization pipeline
        try:
            print("🔄 Running optimization pipeline...")
            result = _run_optimization_pipeline(
                resume_input, jd_input, options,  user_id
            )
            
          

            # Check cache first (optional for MVP)
            cache = get_enhanced_cache()
            # Cache the result (temporarily disabled for testing)
            # asyncio.run(cache.cache_result(
            #     resume_text=resume_text,
            #     jd_text=jd_input.text,
            #     result=result,
            #     options=options.dict(),
            #     model_info=_get_model_info(),
            #     ttl=24*60*60  # 24 hours
            # ))
            total_time = (time.time() - request_start_time) * 1000
            # Save to database
            model_provider = current_app.config.get('MODEL_PROVIDER', 'unknown')
            
            result_id = save_optimization_to_db(
                user_id=user_id,
                resume_input=resume_input,
                jd_input=jd_input,
                optimization_result=result,
                processing_time_ms=total_time,
                model_provider=model_provider
            )
            # Add processing metadata
            
            result['processing_time_ms'] = round(total_time, 2)
            result['cache_hit'] = False
            
            
            print(f"✅ Optimization complete in {total_time:.0f}ms")
            print(f"📊 Match score: {result.get('match_score', 'N/A')}%")
            print(f"🔧 Missing keywords: {len(result.get('missing_keywords', []))}")
            
            # SERVER-SIDE REDIRECT to results page
            return redirect(url_for('optimizer.show_results', result_id=result_id))
            
        except Exception as e:
            print(f"❌ Optimization pipeline failed: {str(e)}")
            flash(f'Optimization failed: {str(e)}', 'error')
            return redirect(url_for('root.dashboard'))
    
    except Exception as e:
        print(f"❌ Request processing failed: {str(e)}")
        flash(f'Request processing failed: {str(e)}', 'error')
        return redirect(url_for('root.dashboard'))



@optimizer_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for resume optimization service.
    
    Returns:
        Service health status and configuration
    """
    
    try:
        # Test provider connection
        provider_test = test_provider_connection()
        
        # Get cache stats
        cache = get_enhanced_cache()
        cache_stats = asyncio.run(cache.get_performance_report())
        
        # System info
        health_data = {
            'status': 'healthy' if provider_test['status'] == 'success' else 'degraded',
            'timestamp': time.time(),
            'service': 'resume-optimizer',
            'version': 'v1.0-mvp',
            'provider_status': provider_test,
            'cache_performance': cache_stats,
            'configuration': {
                'provider': current_app.config.get('MODEL_PROVIDER'),
                'llm_model': current_app.config.get('LLM_MODEL'),
                'embed_model': current_app.config.get('EMBED_MODEL'),
                'rate_limit': current_app.config.get('RATE_LIMIT_PER_HOUR'),
                'max_file_size': current_app.config.get('MAX_RESUME_SIZE_MB')
            }
        }
        
        status_code = 200 if health_data['status'] == 'healthy' else 503
        return jsonify(health_data), status_code
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }), 503


@optimizer_bp.route('/test', methods=['POST'])
@login_required  
def test_optimization():
    """
    Test endpoint for resume optimization with sample data.
    Useful for debugging and development.
    """
    
    sample_resume = """John Smith
Software Engineer
john.smith@email.com | (555) 123-4567

EXPERIENCE
Software Developer | TechCorp | 2020-2023
- Built web applications using Python and Flask
- Worked with databases and APIs
- Collaborated with team members

SKILLS
Python, HTML, CSS, JavaScript"""

    sample_jd = """We are seeking a Senior Python Developer with experience in:
- Flask and Django frameworks
- PostgreSQL and database design
- Docker containerization
- CI/CD pipelines
- AWS cloud services
- Agile development methodologies

Requirements:
- 3+ years Python experience
- Experience with REST APIs
- Knowledge of containerization
- Strong problem-solving skills"""

    try:
        # Use sample data
        resume_input = ResumeInput(text=sample_resume)
        jd_input = JDInput(text=sample_jd, title="Senior Python Developer", company="TestCorp")
        options = OptimizationOptions()
        
        # Run optimization
        result = _run_optimization_pipeline(
            resume_input, jd_input, options, 
            "test_" + str(int(time.time())), 
            current_user.id
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Test optimization completed',
            'result': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Test optimization failed: {str(e)}'
        }), 500


@optimizer_bp.route('/status', methods=['GET']) 
def optimization_status():
    """
    Get current optimization service status.
    Useful for frontend to check if service is available.
    """
    
    try:
        # Test provider connection
        provider_test = test_provider_connection()
        
        # Basic system info
        status_data = {
            'status': 'available' if provider_test['status'] == 'success' else 'degraded',
            'timestamp': time.time(),
            'provider_status': provider_test,
            'rate_limit_per_hour': current_app.config.get('RATE_LIMIT_PER_HOUR', 10),
            'max_file_size_mb': current_app.config.get('MAX_RESUME_SIZE_MB', 5)
        }
        
        return jsonify(status_data), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }), 500


@optimizer_bp.route('/results/<result_id>', methods=['GET'])
@login_required
def show_results(result_id):
    """
    Display optimization results page with data from database.
    """
    try:
        # Get optimization from database
        optimization = ResumeOptimization.query.filter_by(
            id=int(result_id),
            user_id=current_user.id
        ).first()
        
        if not optimization:
            flash('Optimization results not found or you do not have permission to view them.', 'error')
            return redirect(url_for('root.dashboard'))
        
        # Prepare data for template
        optimization_data = {
            'id': optimization.id,
            'match_score': optimization.match_score_after,
            'original_match_score': optimization.match_score_before,
            'missing_keywords': optimization.missing_keywords or [],
            'added_keywords': optimization.added_keywords or [],
            'processing_time_ms': optimization.processing_time_ms,
            'model_provider': optimization.model_provider,
            'created_at': optimization.created_at,
            
            # Job info
            'job_title': optimization.job_title,
            'job_description': optimization.job_description,
            'company_name': optimization.company_name,
            
            # Optimized content
            'sections': optimization.optimized_resume_data.get('sections', {}),
            'experience': optimization.optimized_resume_data.get('experience', []),
            'skills_to_add': optimization.optimized_resume_data.get('skills_added', []),
            'explanations': optimization.optimized_resume_data.get('explanations', []),
            'gap_analysis': optimization.optimized_resume_data.get('gap_analysis', {}),
            
            # Files
            'docx_url': optimization.docx_url,
            'pdf_url': optimization.pdf_url,
            
            # Metadata
            'optimization_style': optimization.optimization_style,
        }
        
        # Render results template with data
        return render_template('results.html', 
                             result_id=result_id,
                             optimization_data=optimization_data)
        
    except Exception as e:
        print(f"Error displaying results: {e}")
        flash('Error loading optimization results.', 'error')
        return redirect(url_for('root.dashboard'))

@optimizer_bp.route('/results', methods=['GET'])  
def show_results_direct():
    """Direct results page access."""
    return render_template('results.html')



@optimizer_bp.route('/download/<file_type>/<result_id>', methods=['GET'])
def download_resume(file_type, result_id):
    """
    Download optimized resume in specified format.
    
    Args:
        file_type: 'pdf' or 'docx'
        result_id: Unique identifier for the optimization result
        
    Returns:
        File download response
    """
    
    try:
        # Validate file type
        if file_type not in ['pdf', 'docx']:
            return jsonify({'error': 'Invalid file type. Use pdf or docx'}), 400
        
        # For MVP: Get results from session/temp storage
        # Later: Fetch from database using result_id and user authentication
        
        # Try to get results from a temporary storage mechanism
        # This is a simplified approach for MVP
        result_data = _get_cached_optimization_result(result_id)
        
        if not result_data:
            return jsonify({'error': 'Optimization result not found or expired'}), 404
        
        # Get file URL from artifacts
        artifacts = result_data.get('artifacts', {})
        file_url = artifacts.get(f'{file_type}_url')
        
        if not file_url:
            return jsonify({'error': f'{file_type.upper()} file not available'}), 404
        
        # For local files, serve directly
        if file_url.startswith('/download/resume/'):
            filename = file_url.split('/')[-1]
            return _serve_local_file(filename, file_type)
        
        # For S3/remote files, proxy the download
        return _proxy_remote_file(file_url, file_type, result_data)
        
    except Exception as e:
        print(f"❌ Download error: {str(e)}")
        return jsonify({'error': 'Download failed'}), 500


@optimizer_bp.route('/generate-download/<result_id>', methods=['POST'])
def generate_download_files(result_id):
    """
    Generate fresh download files for a given optimization result.
    Useful if original files are expired or unavailable.
    
    Args:
        result_id: Optimization result identifier
        
    Returns:
        New download URLs
    """
    
    try:
        # Get the optimization result
        result_data = _get_cached_optimization_result(result_id)
        
        if not result_data:
            return jsonify({'error': 'Optimization result not found'}), 404
        
        # Extract optimized resume data
        optimized_resume_data = result_data.get('optimized_resume', {})
        
        # Convert dict back to OptimizedResume object
        from services.resume.schemas import OptimizedResume
        optimized_resume = OptimizedResume(**optimized_resume_data)
        
        # Get contact info (stored in result or extract from original)
        contact_info = result_data.get('contact_info', {})
        
        # Generate fresh files
        docx_bytes = create_docx_sync(optimized_resume, contact_info, 'professional')
        pdf_bytes = create_pdf_sync(optimized_resume, contact_info)
        
        # Store files temporarily for download
        temp_storage = _store_temp_files(docx_bytes, pdf_bytes, result_id)
        
        return jsonify({
            'status': 'success',
            'downloads': {
                'pdf_url': f"/optimizer/download/pdf/{result_id}",
                'docx_url': f"/optimizer/download/docx/{result_id}"
            },
            'temp_storage': temp_storage
        }), 200
        
    except Exception as e:
        print(f"❌ Generate download error: {str(e)}")
        return jsonify({'error': 'Failed to generate download files'}), 500

# Add file cleanup route for maintenance
@optimizer_bp.route('/cleanup-temp-files', methods=['POST'])
def cleanup_temp_files():
    """
    Clean up expired temporary download files.
    Should be called periodically by a maintenance job.
    """
    
    try:
        temp_dir = current_app.config.get('TEMP_DOWNLOAD_PATH', 'temp_downloads')
        if not os.path.exists(temp_dir):
            return jsonify({'message': 'No temp directory found'}), 200
        
        cleaned_count = 0
        current_time = time.time()
        
        # Clean files older than 24 hours
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            file_age = current_time - os.path.getctime(file_path)
            
            if file_age > 86400:  # 24 hours
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                except:
                    pass
        
        return jsonify({
            'status': 'success',
            'files_cleaned': cleaned_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

