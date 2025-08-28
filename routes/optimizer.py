from flask import Blueprint, request, jsonify,current_app,send_file, make_response
from services.llm_service import LLMService
from flask_login import login_required,current_user
from werkzeug.exceptions import BadRequest
import asyncio
import time
from typing import Dict, Any
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



optimizer_bp = Blueprint('optimizer_bp', __name__)
llm_service = LLMService()

# Resume AI enhancement endpoints


"""
Resume LLM optimization routes.
Handles AI-powered resume optimization API endpoints.
"""

# Update the optimize_resume endpoint decorator
@optimizer_bp.route('/optimize', methods=['POST'])
# @login_required  # Temporarily commented for MVP testing
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
    
    start_time = time.time()
    
    try:
        # Authentication temporarily disabled for MVP testing
        # if not current_user.is_authenticated:
        #     return jsonify({'error': 'Authentication required'}), 401
        # user_id = current_user.id
        
        # Use temporary user ID for MVP testing
        user_id = 999999
        
        # Validate request
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        print(f"📥 Received optimization request: {len(str(data))} characters")
        
        # Validate input schemas
        try:
            resume_input = ResumeInput(**data.get('resume_input', {}))
            jd_input = JDInput(**data.get('job_description', {}))
            options = OptimizationOptions(**data.get('options', {}))
            
            # Debug logging for MVP
            print(f"📄 Resume input type: {resume_input.input_type}")
            print(f"📋 Job description length: {len(jd_input.text) if jd_input.text else 0} chars")
            print(f"⚙️  Options: {options.tone}, PDF: {options.include_pdf}")
            
        except Exception as e:
            print(f"❌ Input validation error: {str(e)}")
            return jsonify({'error': f'Invalid input: {str(e)}'}), 400
        
        # Check if optimization is enabled
        if not current_app.config.get('RESUME_OPTIMIZER_ENABLED', True):
            return jsonify({'error': 'Resume optimization is currently disabled'}), 503
        
        # Rate limiting check (temporarily disabled for testing)
        # rate_limit = current_app.config.get('RATE_LIMIT_PER_HOUR', 10)
        # if not _check_rate_limit(user_id, rate_limit):
        #     return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
        
        print(f"🚀 Starting resume optimization for user {user_id}")
        
        # Generate request hash for caching
        resume_text = resume_input.text or "file_input"
        request_hash = generate_resume_hash_sync(resume_text, jd_input.text, options.dict())
        
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
            
            # Add processing metadata
            total_time = (time.time() - start_time) * 1000
            result['processing_time_ms'] = round(total_time, 2)
            result['cache_hit'] = False
            result['request_hash'] = request_hash
            
            print(f"✅ Optimization complete in {total_time:.0f}ms")
            print(f"📊 Match score: {result.get('match_score', 'N/A')}%")
            print(f"🔧 Missing keywords: {len(result.get('missing_keywords', []))}")
            
            return jsonify(result), 200
            
        except ValueError as e:
            print(f"❌ Validation error: {str(e)}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            print(f"❌ Optimization pipeline failed: {str(e)}")
            return jsonify({
                'error': 'Internal processing error',
                'details': str(e)  # Show details for debugging
            }), 500
    
    except Exception as e:
        print(f"❌ Request processing failed: {str(e)}")
        return jsonify({
            'error': 'Request processing failed',
            'details': str(e)  # Show details for debugging
        }), 500



def _run_optimization_pipeline(
    resume_input: ResumeInput,
    jd_input: JDInput, 
    options: OptimizationOptions,
    request_hash: str
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
            'mvp_testing_mode': MVP_TESTING_MODE,
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
def show_results(result_id):
    """
    Display optimization results page.
    
    Args:
        result_id: The optimization result identifier
    """
    try:
        # For MVP, we'll pass result_id through URL and handle in frontend
        # Later this can load from database when auth is re-enabled
        return render_template('results.html', result_id=result_id)
        
    except Exception as e:
        print(f"Error displaying results: {e}")
        return redirect(url_for('root.optimize_page'))

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


