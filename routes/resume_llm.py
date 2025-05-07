from flask import Blueprint, request, jsonify
from services.llm_service import LLMService
from flask_login import login_required
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