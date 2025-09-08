from flask import Blueprint, request, jsonify,current_app,send_file, make_response,Response,render_template,flash,redirect,url_for
from flask_login import login_required,current_user
from werkzeug.exceptions import BadRequest
import asyncio
import time
from typing import Dict, Any,Optional,Dict,Tuple,List
import io
import tempfile
import os
from services.resume.schemas import (
    ResumeInput, JDInput, OptimizationOptions, OptimizationResult,
    validate_json_with_retry_sync
)
from services.resume.ingest import ingest_resume_sync
from services.resume.embedding import perform_gap_analysis_sync
from services.resume.rewrite import optimize_resume_sync
from services.resume.explain import generate_explanations_sync
from services.resume.policy import apply_guardrails_sync, score_resume_match
from services.resume.formatting import create_docx_sync, create_pdf_sync
from services.resume.storage import store_resume_files_sync, generate_resume_hash_sync
from services.resume.cache import get_enhanced_cache
from providers import get_models, test_provider_connection
from models import Resume,ResumeOptimization,User
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
                        # Handle as text
                        content = resume_file.read().decode('utf-8')
                        resume_input = ResumeInput(text=content)

                else:
                    # Text input
                    resume_text = request.form.get('resume_text', '')
                    resume_input = ResumeInput(text=resume_text)

        # Create schema objects
        jd_input = JDInput(**job_data)
        options = OptimizationOptions(**options_data)

        # Generate request hash for caching and tracking
        request_hash = generate_resume_hash_sync(
            resume_text=resume_input.text if resume_input.text else "file_input",
            jd_text=jd_input.text,
            options=options.dict()
        )

            
        # Check cache first (optional for MVP)
        cache = get_enhanced_cache()
    
      
        # Process optimization pipeline
        try:
            print("🔄 Running optimization pipeline...")
            result = _run_optimization_pipeline(
                resume_input, jd_input, options, request_hash, user_id
            )
            
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
            result['request_hash'] = request_hash
            
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


def _run_optimization_pipeline(
    resume_input: ResumeInput,
    jd_input: JDInput, 
    options: OptimizationOptions,
    request_hash: str,
    user_id:str
) -> Dict[str, Any]:
    """
    Execute the complete optimization pipeline - simplified without user tracking.
    
    Args:
        resume_input: Resume input data
        jd_input: Job description input
        options: Optimization options
        request_hash: Unique request identifier
        
    Returns:
        Complete optimization result
    """
    
    # Step 1: Ingest and parse resume
    print("📄 Step 1: Ingesting resume...")
    parsed_resume = ingest_resume_sync(
        text=resume_input.text,
        docx_url=resume_input.docx_url,
        pdf_url=resume_input.pdf_url
    )
    
    # Step 2: Perform gap analysis
    print("🔍 Step 2: Analyzing gaps...")
    gap_analysis = perform_gap_analysis_sync(
        resume_chunks=parsed_resume.chunks,
        jd_text=jd_input.text,
        jd_title=jd_input.title
    )
    
    # Step 3: Optimize resume with LLM
    print("🤖 Step 3: Optimizing with LLM...")
    optimized_resume = optimize_resume_sync(
        resume_sections=parsed_resume.sections,
        experience_items=parsed_resume.experience_items,
        jd_text=jd_input.text,
        missing_keywords=gap_analysis['missing_keywords'],
        weak_keywords=gap_analysis['weak_keywords'],
        optimization_focus=options.tone
    )
    
    # Step 4: Generate explanations
    print("📋 Step 4: Generating explanations...")
    explanations = generate_explanations_sync(
        original_resume=parsed_resume.dict(),
        optimized_resume=optimized_resume,
        missing_keywords=gap_analysis['missing_keywords'],
        gap_analysis=gap_analysis
    )
    
    # Step 5: Apply guardrails
    print("🛡️  Step 5: Applying guardrails...")
    clean_resume, policy_violations = apply_guardrails_sync(optimized_resume)
    
    # Step 6: Calculate final score
    print("📊 Step 6: Calculating scores...")
    score_breakdown = score_resume_match(
        keyword_analysis=gap_analysis['keyword_analysis'],
        semantic_analysis=gap_analysis['semantic_analysis'],
        gap_analysis=gap_analysis,
        resume_sections=parsed_resume.sections
    )
    
    # Step 7: Generate documents (simplified - no user storage)
    print("📄 Step 7: Generating documents...")
    contact_info = _extract_contact_info(parsed_resume.sections.get('header', ''))
    
    docx_bytes = create_docx_sync(clean_resume, contact_info)
    pdf_bytes = create_pdf_sync(clean_resume, contact_info) if options.include_pdf else None
    
    # Step 8: Store files temporarily (simplified)
    print("💾 Step 8: Storing files...")
    file_urls = store_resume_files_sync(
        docx_bytes=docx_bytes,
        pdf_bytes=pdf_bytes,
        user_id="anonymous",  # Simplified - no user tracking
        resume_hash=request_hash,
        contact_info=contact_info
    )
    
    # Compile final result
    result = {
        'match_score': score_breakdown['overall_score'],
        'score_breakdown': score_breakdown,
        'missing_keywords': gap_analysis['missing_keywords'],
        'weak_keywords': gap_analysis['weak_keywords'],
        'optimized_resume': clean_resume.dict(),
        'explanations': explanations.dict(),
        'artifacts': file_urls,
        'model_info': _get_model_info(),
        'policy_violations': [v.__dict__ for v in policy_violations],
        'input_type': resume_input.input_type,
        'processing_steps': 8
    }
    
    return result


def _extract_contact_info(header_text: str) -> Dict[str, str]:
    """Extract contact information from resume header."""
    
    import re
    
    contact_info = {}
    
    # Extract email
    email_match = re.search(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', header_text)
    if email_match:
        contact_info['email'] = email_match.group()
    
    # Extract phone  
    phone_match = re.search(r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', header_text)
    if phone_match:
        contact_info['phone'] = phone_match.group()
    
    # Extract name (first line typically)
    lines = header_text.strip().split('\n')
    if lines:
        potential_name = lines[0].strip()
        if len(potential_name.split()) <= 4 and not '@' in potential_name:
            contact_info['name'] = potential_name
    
    return contact_info


def _get_model_info() -> Dict[str, str]:
    """Get current model configuration info."""
    
    return {
        'provider': current_app.config.get('MODEL_PROVIDER', 'unknown'),
        'llm_model': current_app.config.get('LLM_MODEL', 'unknown'),
        'embed_model': current_app.config.get('EMBED_MODEL', 'unknown'),
        'optimization_version': 'v1.0'
    }


def _check_rate_limit(user_id: int, limit_per_hour: int) -> bool:
    """
    Basic rate limiting check.
    
    Args:
        user_id: User ID
        limit_per_hour: Maximum requests per hour
        
    Returns:
        True if within limit, False if exceeded
    """
    
    # For MVP, simple implementation
    # In production, use Redis for distributed rate limiting
    
    cache_key = f"rate_limit:user:{user_id}:{int(time.time() // 3600)}"  # Hour bucket
    
    try:
        cache = get_enhanced_cache()
        current_count = asyncio.run(cache.cache.get(cache_key)) or 0
        
        if current_count >= limit_per_hour:
            return False
        
        # Increment counter
        asyncio.run(cache.cache.set(cache_key, current_count + 1, ttl=3600))
        return True
        
    except:
        # If rate limiting fails, allow the request (fail open)
        return True


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




# Add CSRF token endpoint for frontend
@optimizer_bp.route('/csrf-token', methods=['GET'])
def get_csrf_token():
    """Get CSRF token for form submissions."""
    try:
        # Generate or get CSRF token
        from flask_wtf.csrf import generate_csrf
        token = generate_csrf()
        return jsonify({'csrf_token': token}), 200
    except:
        # Fallback if CSRF is not configured
        return jsonify({'csrf_token': 'not-required'}), 200


@optimizer_bp.errorhandler(400)
def handle_bad_request(error):
    """Handle bad request errors."""
    return jsonify({
        'error': 'Bad Request',
        'message': 'Invalid request format or missing required fields',
        'status_code': 400
    }), 400


@optimizer_bp.errorhandler(429)
def handle_rate_limit(error):
    """Handle rate limit errors."""
    return jsonify({
        'error': 'Rate Limit Exceeded',
        'message': 'Too many requests. Please try again later.',
        'status_code': 429,
        'retry_after': 3600  # 1 hour
    }), 429


@optimizer_bp.errorhandler(500)
def handle_internal_error(error):
    """Handle internal server errors."""
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'Resume optimization service encountered an error',
        'status_code': 500
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



def _get_cached_optimization_result(result_id: str) -> Optional[Dict]:
    """
    Get cached optimization result by ID.
    For MVP, this uses a simple approach.
    """
    try:
        cache = get_enhanced_cache()
        # Simple cache key based on result_id
        cache_key = f"result:{result_id}"
        
        # Try to get from cache
        result = asyncio.run(cache.cache.get(cache_key))
        return result
        
    except:
        return None


def _serve_local_file(filename: str, file_type: str) -> Response:
    """
    Serve file from local storage.
    
    Args:
        filename: Local filename
        file_type: pdf or docx
        
    Returns:
        File response
    """
    
    # Construct local file path (adjust based on your storage setup)
    local_storage_path = current_app.config.get('LOCAL_STORAGE_PATH', 'temp_files')
    file_path = os.path.join(local_storage_path, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    # Determine MIME type and filename
    if file_type == 'pdf':
        mimetype = 'application/pdf'
        download_name = f"optimized_resume.pdf"
    else:  # docx
        mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        download_name = f"optimized_resume.docx"
    
    return send_file(
        file_path,
        mimetype=mimetype,
        as_attachment=True,
        download_name=download_name
    )

def _proxy_remote_file(file_url: str, file_type: str, result_data: Dict) -> Response:
    """
    Proxy download from remote storage (S3, etc.).
    
    Args:
        file_url: Remote file URL
        file_type: pdf or docx
        result_data: Optimization result data
        
    Returns:
        File response
    """
    
    try:
        import requests
        
        # Download file from remote storage
        response = requests.get(file_url, timeout=30)
        response.raise_for_status()
        
        # Create in-memory file
        file_data = io.BytesIO(response.content)
        file_data.seek(0)
        
        # Determine MIME type and filename
        if file_type == 'pdf':
            mimetype = 'application/pdf'
            download_name = f"optimized_resume.pdf"
        else:  # docx
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            download_name = f"optimized_resume.docx"
        
        return send_file(
            file_data,
            mimetype=mimetype,
            as_attachment=True,
            download_name=download_name
        )
        
    except Exception as e:
        print(f"❌ Remote file download error: {str(e)}")
        return jsonify({'error': 'Failed to download file from storage'}), 500


def _store_temp_files(docx_bytes: bytes, pdf_bytes: bytes, result_id: str) -> Dict[str, str]:
    """
    Store files temporarily for download.
    
    Args:
        docx_bytes: DOCX file content
        pdf_bytes: PDF file content  
        result_id: Result identifier
        
    Returns:
        Storage information
    """
    
    try:
        # Create temp directory if needed
        temp_dir = current_app.config.get('TEMP_DOWNLOAD_PATH', 'temp_downloads')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generate temporary filenames
        docx_filename = f"resume_{result_id}.docx"
        pdf_filename = f"resume_{result_id}.pdf"
        
        docx_path = os.path.join(temp_dir, docx_filename)
        pdf_path = os.path.join(temp_dir, pdf_filename)
        
        # Write files
        with open(docx_path, 'wb') as f:
            f.write(docx_bytes)
            
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        
        # Store in cache for lookup
        cache = get_enhanced_cache()
        file_info = {
            'docx_path': docx_path,
            'pdf_path': pdf_path,
            'created_at': time.time(),
            'result_id': result_id
        }
        
        # Cache for 24 hours
        cache_key = f"temp_files:{result_id}"
        asyncio.run(cache.cache.set(cache_key, file_info, ttl=86400))
        
        return {
            'storage_type': 'local_temp',
            'docx_path': docx_path,
            'pdf_path': pdf_path,
            'expires_in': 86400
        }
        
    except Exception as e:
        print(f"❌ Temp storage error: {str(e)}")
        return {'error': str(e)}



def validate_optimization_input(data: Dict) -> Tuple[bool, List[str]]:
    """
    Comprehensive input validation for optimization requests.
    
    Args:
        data: Request JSON data
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    
    errors = []
    
    # Check required top-level structure
    required_fields = ['resume_input', 'job_description', 'options']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")
    
    if errors:
        return False, errors
    
    # Validate resume input
    resume_input = data.get('resume_input', {})
    if not any([
        resume_input.get('text'),
        resume_input.get('docx_url'),
        resume_input.get('pdf_url')
    ]):
        errors.append("Resume input must contain 'text', 'docx_url', or 'pdf_url'")
    
    # Validate text length if provided
    if resume_input.get('text'):
        text_len = len(resume_input['text'].strip())
        if text_len < 100:
            errors.append(f"Resume text too short ({text_len} characters). Minimum 100 characters required.")
        elif text_len > 50000:
            errors.append(f"Resume text too long ({text_len} characters). Maximum 50,000 characters allowed.")
    
    # Validate job description
    job_desc = data.get('job_description', {})
    if job_desc.get('text') and len(job_desc['text']) > 20000:
        errors.append("Job description too long. Maximum 20,000 characters allowed.")
    
    # Validate options
    options = data.get('options', {})
    valid_tones = ['professional-concise', 'creative', 'technical', 'executive']
    if options.get('tone') and options['tone'] not in valid_tones:
        errors.append(f"Invalid tone '{options['tone']}'. Must be one of: {', '.join(valid_tones)}")
    
    return len(errors) == 0, errors


def handle_optimization_error(error: Exception, context: str = "optimization") -> Tuple[Dict[str, Any], int]:
    """
    Handle optimization errors with appropriate user messages and status codes.
    
    Args:
        error: The exception that occurred
        context: Context where error occurred
        
    Returns:
        Tuple of (error_response_dict, http_status_code)
    """
    
    error_id = f"err_{int(time.time())}_{hash(str(error)) % 10000}"
    
    # Log full error details for debugging
    print(f"🔥 Error {error_id} in {context}: {str(error)}")
    print(f"🔍 Traceback: {traceback.format_exc()}")
    
    # Categorize error types
    if isinstance(error, ValueError):
        return _handle_validation_error(error, error_id)
    elif isinstance(error, ConnectionError):
        return _handle_connection_error(error, error_id)
    elif isinstance(error, TimeoutError):
        return _handle_timeout_error(error, error_id)
    elif "rate limit" in str(error).lower():
        return _handle_rate_limit_error(error, error_id)
    elif "api" in str(error).lower() and ("key" in str(error).lower() or "auth" in str(error).lower()):
        return _handle_api_auth_error(error, error_id)
    else:
        return _handle_generic_error(error, error_id)


def _handle_validation_error(error: Exception, error_id: str) -> Tuple[Dict[str, Any], int]:
    """Handle validation errors (400 status)."""
    
    return {
        'error': 'Input Validation Error',
        'message': str(error),
        'error_id': error_id,
        'category': 'validation',
        'suggested_actions': [
            'Check that your resume contains standard sections (experience, skills, etc.)',
            'Ensure file is not corrupted or empty',
            'Try using plain text instead of file upload'
        ]
    }, 400


def _handle_connection_error(error: Exception, error_id: str) -> Tuple[Dict[str, Any], int]:
    """Handle connection errors (503 status)."""
    
    return {
        'error': 'Service Connection Error',
        'message': 'Unable to connect to AI optimization service. Please try again in a moment.',
        'error_id': error_id,
        'category': 'connection',
        'retry_recommended': True,
        'retry_delay_seconds': 30
    }, 503


def _handle_timeout_error(error: Exception, error_id: str) -> Tuple[Dict[str, Any], int]:
    """Handle timeout errors (408 status)."""
    
    return {
        'error': 'Request Timeout',
        'message': 'Optimization is taking longer than expected. Please try again with a shorter resume.',
        'error_id': error_id,
        'category': 'timeout',
        'retry_recommended': True,
        'suggested_actions': [
            'Try shortening your resume content',
            'Use simpler job description',
            'Check your internet connection stability'
        ]
    }, 408


def _handle_rate_limit_error(error: Exception, error_id: str) -> Tuple[Dict[str, Any], int]:
    """Handle rate limiting errors (429 status)."""
    
    return {
        'error': 'Rate Limit Exceeded',
        'message': 'You\'ve reached the optimization limit. Please try again later.',
        'error_id': error_id,
        'category': 'rate_limit',
        'retry_recommended': True,
        'retry_after_seconds': 3600,
        'suggested_actions': [
            'Wait an hour before trying again',
            'Consider upgrading to premium for higher limits'
        ]
    }, 429


def _handle_api_auth_error(error: Exception, error_id: str) -> Tuple[Dict[str, Any], int]:
    """Handle API authentication errors (502 status)."""
    
    return {
        'error': 'AI Service Unavailable',
        'message': 'AI optimization service is temporarily unavailable. Please try again later.',
        'error_id': error_id,
        'category': 'service_unavailable',
        'retry_recommended': True,
        'retry_delay_seconds': 300  # 5 minutes
    }, 502


def _handle_generic_error(error: Exception, error_id: str) -> Tuple[Dict[str, Any], int]:
    """Handle generic errors (500 status)."""
    
    return {
        'error': 'Internal Processing Error',
        'message': 'An unexpected error occurred during optimization. Please try again.',
        'error_id': error_id,
        'category': 'internal',
        'retry_recommended': True,
        'suggested_actions': [
            'Try again with the same input',
            'If problem persists, try with a different resume format',
            'Contact support if errors continue'
        ]
    }, 500


def log_optimization_attempt(
    user_id: int,
    resume_input: 'ResumeInput',
    jd_input: 'JDInput',
    success: bool,
    error_details: Optional[str] = None,
    processing_time_ms: Optional[float] = None
):
    """
    Log optimization attempts for monitoring and debugging.
    
    Args:
        user_id: User ID
        resume_input: Resume input data
        jd_input: Job description input
        success: Whether optimization succeeded
        error_details: Error details if failed
        processing_time_ms: Processing time if successful
    """
    
    try:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'success': success,
            'resume_input_type': resume_input.input_type,
            'resume_length': len(resume_input.text) if resume_input.text else 0,
            'jd_length': len(jd_input.text) if jd_input.text else 0,
            'has_job_title': bool(jd_input.title),
            'processing_time_ms': processing_time_ms,
            'error_details': error_details,
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'ip_address': request.remote_addr
        }
        
        # In production, send to logging service
        print(f"📊 Optimization Log: {json.dumps(log_entry)}")
        
    except Exception as e:
        print(f"❌ Logging failed: {str(e)}")


# Enhanced error handling wrapper for the main optimization function
def safe_optimization_pipeline(
    resume_input: 'ResumeInput',
    jd_input: 'JDInput',
    options: 'OptimizationOptions',
    request_hash: str,
    user_id: int
) -> Dict[str, Any]:
    """
    Execute optimization pipeline with comprehensive error handling.
    
    This is a wrapper around _run_optimization_pipeline with enhanced error handling.
    """
    
    start_time = time.time()
    
    try:
        # Log the attempt
        log_optimization_attempt(user_id, resume_input, jd_input, False)
        
        # Execute pipeline
        result = _run_optimization_pipeline(
            resume_input, jd_input, options, request_hash, user_id
        )
        
        # Log success
        processing_time = (time.time() - start_time) * 1000
        log_optimization_attempt(
            user_id, resume_input, jd_input, True,
            processing_time_ms=processing_time
        )
        
        return result
        
    except Exception as e:
        # Log failure
        processing_time = (time.time() - start_time) * 1000
        log_optimization_attempt(
            user_id, resume_input, jd_input, False,
            error_details=str(e),
            processing_time_ms=processing_time
        )
        
        # Re-raise for handling by route
        raise



def save_temp_file(uploaded_file):
    """Save uploaded file temporarily for processing."""
    import tempfile
    import os
    
    # Create temp file with proper extension
    file_ext = '.pdf' if 'pdf' in uploaded_file.content_type else '.docx'
    fd, temp_path = tempfile.mkstemp(suffix=file_ext)
    
    try:
        with os.fdopen(fd, 'wb') as tmp_file:
            uploaded_file.seek(0)  # Reset file pointer
            tmp_file.write(uploaded_file.read())
        
        return temp_path
    except Exception as e:
        os.unlink(temp_path)  # Clean up on error
        raise e





# #######################################
###utils
####################

def save_optimization_to_db(
    user_id: int,
    resume_input: ResumeInput,
    jd_input: JDInput,
    optimization_result: dict,
    processing_time_ms: float,
    model_provider: str
) -> str:
    """Save optimization results to database and return the ID."""
    
    try:
        # Create resume record
        resume_record = Resume(
            user_id=user_id,
            title=f"Optimized Resume - {jd_input.title or 'Untitled Job'}",
            resume_data={
                'original_text': resume_input.text[:5000] if resume_input.text else None,
                'file_type': 'pdf' if resume_input.pdf_url else 'docx' if resume_input.docx_url else 'text',
                'optimization_date': datetime.utcnow().isoformat()
            },
            template="optimized_standard",
            is_optimized=True,
            last_optimized_at=datetime.utcnow()
        )
        
        db.session.add(resume_record)
        db.session.flush()  # Get ID without committing
        explanations = optimization_result.get('explanations', [])
        if hasattr(explanations, 'dict'):  # Pydantic model
            explanations_list = [explanations.dict()]
        else:
            explanations_list = list(explanations) if explanations else []
        # Create optimization record
        optimization = ResumeOptimization(
            user_id=user_id,
            resume_id=resume_record.id,
            
            # Input data
            original_resume_data={
                'text_preview': resume_input.text[:1000] if resume_input.text else None,
                'input_type': getattr(resume_input, 'input_type', 'unknown'),
                'file_info': {
                    'has_pdf': bool(resume_input.pdf_url),
                    'has_docx': bool(resume_input.docx_url),
                    'has_text': bool(resume_input.text)
                }
            },
            job_description=jd_input.text[:5000] if jd_input.text else None,
            job_title=jd_input.title[:200] if jd_input.title else None,
            company_name=jd_input.company[:200] if jd_input.company else None,
            
            # Optimization settings
            optimization_style=optimization_result.get('optimization_focus', 'professional-concise'),
            

            
            # Results
            optimized_resume_data={
                'sections': optimization_result.get('sections', {}),
                'experience': optimization_result.get('experience', []),
                'skills_added': optimization_result.get('skills_to_add', []),
                'explanations': explanations_list[:10],
                'gap_analysis': optimization_result.get('gap_analysis', {})
            },
            match_score_before=float(optimization_result.get('original_match_score', 0.0)),
            match_score_after=float(optimization_result.get('match_score', 0.0)),
            missing_keywords=list(optimization_result.get('missing_keywords', [])[:50]),
            added_keywords=list(optimization_result.get('added_keywords', [])[:50]),
            
            # Files
            docx_url=optimization_result.get('artifacts', {}).get('docx_url'),
            pdf_url=optimization_result.get('artifacts', {}).get('pdf_url'),
            
            # Processing info
            processing_time_ms=processing_time_ms,
            model_provider=model_provider,
            created_at=datetime.utcnow()
        )
        
        db.session.add(optimization)
        db.session.commit()
        
        # Update user stats
        user = User.query.get(user_id)
        if user:
            user.optimization_count = (user.optimization_count or 0) + 1
            user.last_optimization_at = datetime.utcnow()
            db.session.commit()
        
        print(f"✅ Optimization saved to DB with ID: {optimization.id}")
        return str(optimization.id)
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Failed to save optimization to DB: {str(e)}")
        raise