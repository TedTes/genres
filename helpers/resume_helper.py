
from flask import Response
import spacy
from jinja2 import  FileSystemLoader
from flask import Flask,request,render_template,jsonify,current_app
from io import BytesIO
from weasyprint import HTML, CSS
import os
from db import db
from typing import Dict, Any,Optional,Tuple,List
from services.resume.schemas import (
    ResumeInput, JDInput, OptimizationOptions, OptimizationResult,
    validate_json_with_retry_sync
)
import asyncio
from models import Resume , ResumeOptimization,User
from datetime import datetime
from services.resume.cache import get_enhanced_cache
def calculate_resume_completeness(resume_data):
    """
    Calculate completeness percentage of a resume based on filled sections
    """
    if not resume_data:
        return 0
        
    # Define key sections for a complete resume
    key_sections = ['contact', 'summary', 'experience', 'education', 'skills']
    
    # Count completed sections
    completed = sum(1 for section in key_sections if section in resume_data and resume_data[section])
    
    # Calculate percentage
    return int((completed / len(key_sections)) * 100)


def extract_skills_from_text(text):
    """
    Extract skills from text using NLP techniques.
    Returns a dictionary of skills with their importance score.
    """
    # Load the spaCy model
    nlp = spacy.load('en_core_web_sm')
    # Common technical skills to look for
    tech_skills = [
        "Python", "JavaScript", "React", "Angular", "Vue", "Node.js", "Django", 
        "Flask", "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "AWS", "Azure", 
        "GCP", "Docker", "Kubernetes", "DevOps", "CI/CD", "Git", "GitHub", "GitLab",
        "Agile", "Scrum", "Kanban", "REST", "GraphQL", "API", "Microservices",
        "HTML", "CSS", "SASS", "LESS", "Bootstrap", "Tailwind", "TypeScript",
        "Java", "C#", "C++", "Ruby", "PHP", "Go", "Rust", "Swift", "Kotlin",
        "Redux", "jQuery", "Express", "Spring", "Laravel", "Rails", "ASP.NET",
        "TDD", "BDD", "Machine Learning", "AI", "Data Science", "Big Data", 
        "Hadoop", "Spark", "Kafka", "ElasticSearch", "Tableau", "Power BI",
        "Linux", "Unix", "Windows", "MacOS", "Mobile", "Android", "iOS",
        "Responsive Design", "Webpack", "Babel", "Gulp", "Grunt", "npm", "yarn",
        "SEO", "Accessibility", "WCAG", "Performance Optimization", "Security",
        "Frontend", "Backend", "Full Stack", "UI/UX", "Figma", "Sketch", "Adobe XD"
    ]
    
    # Common soft skills
    soft_skills = [
        "Communication", "Teamwork", "Leadership", "Problem Solving", 
        "Critical Thinking", "Time Management", "Project Management", 
        "Adaptability", "Creativity", "Attention to Detail", "Analytical",
        "Interpersonal", "Presentation", "Negotiation", "Conflict Resolution",
        "Decision Making", "Emotional Intelligence", "Customer Service", 
        "Multitasking", "Flexibility", "Initiative", "Self-Motivation"
    ]
    
    # Combine all skills
    all_skills = tech_skills + soft_skills
    skill_patterns = {skill.lower(): skill for skill in all_skills}
    
    # Process the text
    doc = nlp(text)
    
    # Extract skills using multiple approaches
    found_skills = {}
    
    # 1. Direct matching of skill keywords
    for token in doc:
        token_lower = token.text.lower()
        if token_lower in skill_patterns:
            actual_skill = skill_patterns[token_lower]
            found_skills[actual_skill] = found_skills.get(actual_skill, 0) + 1
    
    # 2. Look for compound skills (e.g., "machine learning")
    for i in range(len(doc) - 1):
        bigram = (doc[i].text + " " + doc[i+1].text).lower()
        if bigram in skill_patterns:
            actual_skill = skill_patterns[bigram]
            found_skills[actual_skill] = found_skills.get(actual_skill, 0) + 2  # Higher score for compounds
    
    # 3. Analyze using noun chunks (might find things like "data analysis")
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.lower()
        if chunk_text in skill_patterns:
            actual_skill = skill_patterns[chunk_text]
            found_skills[actual_skill] = found_skills.get(actual_skill, 0) + 2
    
    # 4. Look for skills near requirement words
    requirement_indicators = ["required", "requirements", "qualifications", "skills", "proficiency", "knowledge", "experience with"]
    requirement_section = False
    skill_context_bonus = {}
    
    for sent in doc.sents:
        sent_text = sent.text.lower()
        
        # Check if this is a requirements section
        if any(indicator in sent_text for indicator in requirement_indicators):
            requirement_section = True
        
        if requirement_section:
            # Skills mentioned in requirements sections get a bonus
            for skill, original in skill_patterns.items():
                if skill in sent_text:
                    skill_context_bonus[original] = skill_context_bonus.get(original, 0) + 3
    
    # Add the context bonuses to the found skills
    for skill, bonus in skill_context_bonus.items():
        found_skills[skill] = found_skills.get(skill, 0) + bonus
    
    # Convert counts to importance scores (0-100)
    total_mentions = sum(found_skills.values()) if found_skills else 1
    skill_scores = {}
    
    for skill, count in found_skills.items():
        # Calculate normalized score (0-100)
        normalized_score = min(100, int((count / total_mentions) * 100) + 50)
        skill_scores[skill] = normalized_score
    
    return skill_scores




def calculate_skill_match(user_skills, job_skills):
    """
    Calculate the match percentage between user skills and job skills.
    
    Parameters:
    - user_skills: List of strings representing user's skills
    - job_skills: Dictionary of job skills with importance scores
    
    Returns:
    - match_percentage: Overall match percentage (0-100)
    - skill_matches: List of dictionaries with skill match details
    """
    if not user_skills or not job_skills:
        return 0, []
    
    # Normalize user skills (convert to lowercase for matching)
    user_skills_normalized = [skill.lower() for skill in user_skills]
    
    # Initialize match metrics
    total_job_importance = sum(job_skills.values())
    total_match_score = 0
    skill_matches = []
    
    # Calculate match for each job skill
    for job_skill, importance in job_skills.items():
        skill_match = 0
        
        # Exact match
        if job_skill.lower() in user_skills_normalized:
            skill_match = 100
        else:
            # Check for partial matches (e.g., "Python" would partially match "Python Programming")
            for user_skill in user_skills_normalized:
                if job_skill.lower() in user_skill or user_skill in job_skill.lower():
                    # Partial match - score based on similarity
                    skill_match = 70
                    break
        
        # Add to skill matches list
        if skill_match > 0:
            skill_matches.append({
                "name": job_skill,
                "match": skill_match,
                "importance": importance
            })
            
            # Add to total match score, weighted by importance
            total_match_score += (skill_match / 100) * importance
    
    # Calculate overall match percentage
    if total_job_importance > 0:
        overall_match = int((total_match_score / total_job_importance) * 100)
    else:
        overall_match = 0
    
    # Sort skills by importance
    skill_matches.sort(key=lambda x: x["importance"], reverse=True)
    
    # Limit to top skills
    skill_matches = skill_matches[:10]
    
    return overall_match, skill_matches


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


