from flask import Blueprint, request, jsonify,current_app
from services.llm_service import LLMService
from flask_login import login_required,current_user
from werkzeug.exceptions import BadRequest
import asyncio
import time
from typing import Dict, Any

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



resume_llm_bp = Blueprint('resume_llm_bp', __name__)
llm_service = LLMService()

# Resume AI enhancement endpoints
@resume_llm_bp.route('/generate-summary', methods=['POST'])
@login_required
def api_generate_summary():
    """Generate professional summary options for a resume."""
    data = request.get_json()
    resume_id = data.get('resume_id')
    if not resume_id:
        return jsonify({"success": False, "error": "Missing resume ID"}), 400
    
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    try:
        # Get job description if available for context
        job_description = None
        if resume.job_id:
            job = Job.query.get(resume.job_id)
            if job:
                job_description = job.description
        
        # Generate summary options based on resume data and job
        options = []
        
        # TODO: call an AI service
        options = [
            'Dynamic professional with a proven track record in delivering innovative solutions.',
            'Results-oriented expert skilled in driving operational excellence.',
            'Versatile leader with extensive experience in cross-functional team management.'
        ]
        print("options")
        print(options)
        return jsonify({
            "success": True,
            "options": options
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@resume_llm_bp.route('/improve-text', methods=['POST'])
@login_required
def api_improve_text():
    """Improve existing text with better wording and structure."""
    data = request.get_json()
    text = data.get('text')
    text_type = data.get('type', 'generic')
    resume_id = data.get('resume_id')
    
    if not text or not resume_id:
        return jsonify({"success": False, "error": "Missing required data"}), 400
    
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    try:
        # TODO: call an AI service
        improved = enhance_resume_content(
            text,
            text_type,
            None,  # No job description needed for general improvement
            'improve'
        )
        
        return jsonify({
            "success": True,
            "improved": improved
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@resume_llm_bp.route('/ats-optimize', methods=['POST'])
@login_required
def api_ats_optimize():
    """Optimize text for ATS (Applicant Tracking Systems)."""
    data = request.get_json()
    text = data.get('text')
    job_title = data.get('jobTitle')
    text_type = data.get('type', 'generic')
    resume_id = data.get('resume_id')
    
    if not text or not resume_id:
        return jsonify({"success": False, "error": "Missing required data"}), 400
    
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    try:
        # Get job description if available
        job_description = None
        if resume.job_id:
            job = Job.query.get(resume.job_id)
            if job:
                job_description = job.description
        
        # Call enhancement function with ATS optimization type
        optimized = enhance_resume_content(
            text,
            text_type,
            job_description,
            'ats_optimize'
        )
        
        # Extract keywords that were added (in production would come from AI service)
        keywords = ['leadership', 'teamwork']
        if job_description:
            # Extract some keywords from job description
            additional_keywords = analyze_job_description(job_description)[:3]  
            keywords.extend(additional_keywords)
        
        return jsonify({
            "success": True,
            "optimized": optimized,
            "keywords": keywords
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@resume_llm_bp.route('/enhance-bullets', methods=['POST'])
@login_required
def api_enhance_bullets():
    """Enhance bullet points with strong action verbs and clearer language."""
    data = request.get_json()
    bullets = data.get('bullets', [])
    job_title = data.get('jobTitle')
    company = data.get('company')
    resume_id = data.get('resume_id')
    
    if not bullets or not resume_id:
        return jsonify({"success": False, "error": "Missing required data"}), 400
    
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    try:
        # TODO: call an AI service
        enhanced_bullets = []
        for bullet in bullets:
            enhanced = enhance_resume_content(
                bullet,
                'bullet',
                None,
                'enhance_bullets'
            )
            enhanced_bullets.append(enhanced)
        
        return jsonify({
            "success": True,
            "enhanced": enhanced_bullets
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@resume_llm_bp.route('/add-metrics', methods=['POST'])
@login_required
def api_add_metrics():
    """Add quantifiable metrics to experience bullet points."""
    data = request.get_json()
    bullets = data.get('bullets', [])
    job_title = data.get('jobTitle')
    company = data.get('company')
    resume_id = data.get('resume_id')
    
    if not bullets or not resume_id:
        return jsonify({"success": False, "error": "Missing required data"}), 400
    
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    try:
        # TODO: call an AI service
        enhanced_bullets = []
        for bullet in bullets:
            enhanced = enhance_resume_content(
                bullet,
                'bullet',
                None,
                'add_metrics'
            )
            enhanced_bullets.append(enhanced)
        
        return jsonify({
            "success": True,
            "enhanced": enhanced_bullets
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@resume_llm_bp.route('/tailor-experience', methods=['POST'])
@login_required
def api_tailor_experience():
    """Tailor experience bullet points to a specific job description."""
    data = request.get_json()
    bullets = data.get('bullets', [])
    job_title = data.get('jobTitle')
    company = data.get('company')
    job_description = data.get('jobDescription')
    resume_id = data.get('resume_id')
    
    if not bullets or not job_description or not resume_id:
        return jsonify({"success": False, "error": "Missing required data"}), 400
    
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    try:
        # Apply tailoring to each bullet
        tailored_bullets = []
        for bullet in bullets:
            enhanced = enhance_resume_content(
                bullet,
                'bullet',
                job_description,
                'tailor_to_job'
            )
            tailored_bullets.append(enhanced)
        
        # Calculate match percentage based on keyword overlap
        job_keywords = set(analyze_job_description(job_description))
        bullet_text = " ".join(bullets)
        bullet_keywords = set(extract_skills_from_text(bullet_text))
        
        match_count = len(job_keywords.intersection(bullet_keywords))
        total_keywords = len(job_keywords) if job_keywords else 1
        match_percentage = min(round((match_count / total_keywords) * 100), 100)
        
        return jsonify({
            "success": True,
            "tailored": tailored_bullets,
            "matchPercentage": match_percentage
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@resume_llm_bp.route('/suggest-skills', methods=['POST'])
@login_required
def api_suggest_skills():
    """Suggest relevant skills based on resume content and job description."""
    data = request.get_json()
    resume_id = data.get('resume_id')
    resume_content = data.get('resumeContent')
    
    if not resume_id:
        return jsonify({"success": False, "error": "Missing resume ID"}), 400
    
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    try:
        # Get job description if available
        job_description = None
        if resume.job_id:
            job = Job.query.get(resume.job_id)
            if job:
                job_description = job.description
        
        # Extract skills from job description if available
        suggested_skills = []
        relevance = []
        
        if job_description:
            job_skills = analyze_job_description(job_description)
            suggested_skills = job_skills[:10]  # Just take top 10 skills
            
            # Assign relevance levels
            for i, skill in enumerate(suggested_skills):
                if i < 3:
                    relevance.append("Highly relevant")
                elif i < 6:
                    relevance.append("Relevant")
                else:
                    relevance.append("Moderately relevant")
        else:
            # Default skills if no job description
            suggested_skills = ['Python', 'JavaScript', 'Project Management']
            relevance = ['Highly relevant', 'Relevant', 'Moderately relevant']
        
        return jsonify({
            "success": True,
            "suggestedSkills": suggested_skills,
            "relevance": relevance
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@resume_llm_bp.route('/extract-skills', methods=['POST'])
@login_required
def api_extract_skills():
    """Extract skills from the experience and education sections of the resume."""
    data = request.get_json()
    resume_id = data.get('resume_id')
    resume_content = data.get('resumeContent')
    
    if not resume_id:
        return jsonify({"success": False, "error": "Missing resume ID"}), 400
    
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    try:
        # Get experience sections from resume_data
        resume_data = resume.resume_data or {}
        experience_text = ""
        
        if 'experience' in resume_data:
            experience_items = resume_data['experience']
            if isinstance(experience_items, list):
                for item in experience_items:
                    if isinstance(item, dict):
                        # Extract job title, company, and description
                        job_title = item.get('job_title', '')
                        company = item.get('company', '')
                        description = item.get('description', '')
                        experience_text += f"{job_title} {company} {description} "
        
        # Extract skills from experience text
        extracted_skills = []
        if experience_text:
            # Use the extraction function
            extracted_skills = extract_skills_from_text(experience_text)
        
        # If no skills extracted, provide some common ones
        if not extracted_skills:
            extracted_skills = ['Leadership', 'Communication', 'Data Analysis']
        
        return jsonify({
            "success": True,
            "extractedSkills": extracted_skills
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@resume_llm_bp.route('/ats-scan', methods=['POST'])
@login_required
def api_ats_scan():
    """Analyze resume for ATS compatibility and provide recommendations."""
    data = request.get_json()
    resume_id = data.get('resume_id')
    resume_content = data.get('resumeContent')
    
    if not resume_id:
        return jsonify({"success": False, "error": "Missing resume ID"}), 400
    
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    try:
        job_description = None
        job_keywords = []
        
        # Get job keywords if job is linked
        if resume.job_id:
            job = Job.query.get(resume.job_id)
            if job:
                job_description = job.description
                job_keywords = analyze_job_description(job.description)
        
        # If no job keywords, use some common ones
        if not job_keywords:
            job_keywords = ['software', 'development', 'leadership', 'agile', 'cloud']
        
        # Extract text from all resume sections
        resume_data = resume.resume_data or {}
        resume_text = ""
        
        # Contact info
        if 'contact' in resume_data:
            contact = resume_data['contact']
            if isinstance(contact, dict):
                for key, value in contact.items():
                    if key != 'email' and key != 'phone':  # Skip private info
                        resume_text += f"{value} "
        
        # Summary
        if 'summary' in resume_data:
            summary = resume_data['summary']
            if isinstance(summary, dict):
                resume_text += f"{summary.get('content', '')} "
            else:
                resume_text += f"{summary} "
        
        # Skills
        if 'skills' in resume_data:
            skills = resume_data['skills']
            if isinstance(skills, list):
                resume_text += " ".join(skills) + " "
        
        # Experience
        if 'experience' in resume_data:
            experience = resume_data['experience']
            if isinstance(experience, list):
                for item in experience:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            resume_text += f"{value} "
        
        # Education
        if 'education' in resume_data:
            education = resume_data['education']
            if isinstance(education, list):
                for item in education:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            resume_text += f"{value} "
        
        # Check which keywords are matched
        matched_keywords = []
        missing_keywords = []
        resume_text = resume_text.lower()
        
        for keyword in job_keywords:
            if keyword.lower() in resume_text:
                matched_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        # Calculate ATS score
        match_count = len(matched_keywords)
        total_keywords = len(job_keywords)
        ats_score = min(round((match_count / total_keywords) * 100) + 10, 100) if total_keywords > 0 else 0
        
        # Generate recommendations
        recommendations = []
        
        if missing_keywords:
            for keyword in missing_keywords[:3]:  # Limit to top 3 missing keywords
                recommendations.append(f'Add "{keyword}" to your resume.')
        
        if ats_score < 85:
            recommendations.append("Ensure your resume uses a clean, ATS-friendly format with standard section headings.")
        
        if len(recommendations) == 0:
            recommendations.append("Your resume is well-optimized for ATS systems.")
        
        return jsonify({
            "success": True,
            "atsScore": ats_score,
            "matchedKeywords": matched_keywords,
            "missingKeywords": missing_keywords,
            "recommendations": recommendations
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


"""
Resume LLM optimization routes.
Handles AI-powered resume optimization API endpoints.
"""

@resume_llm_bp.route('/optimize', methods=['POST'])
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
    
    start_time = time.time()
    
    try:
        # Validate request
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        
        # Validate input schemas
        try:
            resume_input = ResumeInput(**data.get('resume_input', {}))
            jd_input = JDInput(**data.get('job_description', {}))
            options = OptimizationOptions(**data.get('options', {}))
        except Exception as e:
            return jsonify({'error': f'Invalid input: {str(e)}'}), 400
        
        # Check if optimization is enabled
        if not current_app.config.get('RESUME_OPTIMIZER_ENABLED', True):
            return jsonify({'error': 'Resume optimization is currently disabled'}), 503
        
        # Rate limiting check (basic implementation)
        rate_limit = current_app.config.get('RATE_LIMIT_PER_HOUR', 10)
        if not _check_rate_limit(current_user.id, rate_limit):
            return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
        
        print(f"🚀 Starting resume optimization for user {current_user.id}")
        
        # Generate request hash for caching
        resume_text = resume_input.text or "file_input"
        request_hash = generate_resume_hash_sync(resume_text, jd_input.text, options.dict())
        
        # Check cache first
        cache = get_enhanced_cache()
        cached_result = asyncio.run(cache.get_cached_result(
            resume_text=resume_text,
            jd_text=jd_input.text,
            options=options.dict(),
            model_info=_get_model_info()
        ))
        
        if cached_result:
            print(f"⚡ Returning cached result for request {request_hash}")
            return jsonify(cached_result), 200
        
        # Process optimization pipeline
        try:
            result = _run_optimization_pipeline(
                resume_input, jd_input, options, request_hash, current_user.id
            )
            
            # Cache the result
            asyncio.run(cache.cache_result(
                resume_text=resume_text,
                jd_text=jd_input.text,
                result=result,
                options=options.dict(),
                model_info=_get_model_info(),
                ttl=24*60*60  # 24 hours
            ))
            
            # Add processing metadata
            total_time = (time.time() - start_time) * 1000
            result['processing_time_ms'] = round(total_time, 2)
            result['cache_hit'] = False
            result['request_hash'] = request_hash
            
            print(f"✅ Optimization complete in {total_time:.0f}ms")
            
            return jsonify(result), 200
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            print(f"❌ Optimization pipeline failed: {str(e)}")
            return jsonify({'error': 'Internal processing error'}), 500
    
    except Exception as e:
        print(f"❌ Request processing failed: {str(e)}")
        return jsonify({'error': 'Request processing failed'}), 500


def _run_optimization_pipeline(
    resume_input: ResumeInput,
    jd_input: JDInput, 
    options: OptimizationOptions,
    request_hash: str,
    user_id: int
) -> Dict[str, Any]:
    """
    Execute the complete optimization pipeline.
    
    Args:
        resume_input: Resume input data
        jd_input: Job description input
        options: Optimization options
        request_hash: Unique request identifier
        user_id: Current user ID
        
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
    
    # Step 7: Generate documents
    print("📄 Step 7: Generating documents...")
    contact_info = _extract_contact_info(parsed_resume.sections.get('header', ''))
    
    docx_bytes = create_docx_sync(clean_resume, contact_info)
    pdf_bytes = create_pdf_sync(clean_resume, contact_info) if options.include_pdf else None
    
    # Step 8: Store files
    print("💾 Step 8: Storing files...")
    file_urls = store_resume_files_sync(
        docx_bytes=docx_bytes,
        pdf_bytes=pdf_bytes,
        user_id=str(user_id),
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


@resume_llm_bp.route('/health', methods=['GET'])
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


@resume_llm_bp.route('/test', methods=['POST'])
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


@resume_llm_bp.route('/status', methods=['GET'])
@login_required
def optimization_status():
    """
    Get current optimization service status and user stats.
    
    Returns:
        Service status and user-specific information
    """
    
    try:
        cache = get_enhanced_cache()
        
        # Get user-specific stats (you could track these in database)
        user_stats = {
            'optimizations_today': 0,  # Could implement actual tracking
            'remaining_quota': current_app.config.get('RATE_LIMIT_PER_HOUR', 10),
            'subscription_tier': 'premium'  # From your existing subscription service
        }
        
        # Service status
        status_data = {
            'service_available': current_app.config.get('RESUME_OPTIMIZER_ENABLED', True),
            'provider': current_app.config.get('MODEL_PROVIDER'),
            'cache_type': cache.cache_type,
            'user_stats': user_stats,
            'supported_formats': ['text', 'docx', 'pdf'],
            'max_file_size_mb': current_app.config.get('MAX_RESUME_SIZE_MB', 5),
            'features': {
                'pdf_export': True,
                's3_storage': bool(current_app.config.get('AWS_S3_BUCKET')),
                'cache_enabled': True,
                'explanations': True,
                'gap_analysis': True
            }
        }
        
        return jsonify(status_data), 200
        
    except Exception as e:
        return jsonify({'error': f'Status check failed: {str(e)}'}), 500


@resume_llm_bp.errorhandler(400)
def handle_bad_request(error):
    """Handle bad request errors."""
    return jsonify({
        'error': 'Bad Request',
        'message': 'Invalid request format or missing required fields',
        'status_code': 400
    }), 400


@resume_llm_bp.errorhandler(429)
def handle_rate_limit(error):
    """Handle rate limit errors."""
    return jsonify({
        'error': 'Rate Limit Exceeded',
        'message': 'Too many requests. Please try again later.',
        'status_code': 429,
        'retry_after': 3600  # 1 hour
    }), 429


@resume_llm_bp.errorhandler(500)
def handle_internal_error(error):
    """Handle internal server errors."""
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'Resume optimization service encountered an error',
        'status_code': 500
    }), 500