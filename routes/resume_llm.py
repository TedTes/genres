from flask import Blueprint, request, jsonify
from services.llm_service import LLMService

bp = Blueprint('resume_llm', __name__)
llm_service = LLMService()

@bp.route('/optimize', methods=['POST'])
def optimize_resume():
    """
    Optimize resume for a specific job description
    """
    data = request.get_json()
    resume_data = data.get('resume_data')
    job_description = data.get('job_description')
    
    if not resume_data or not job_description:
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        result = llm_service.optimize_for_job(resume_data, job_description)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/generate-summary', methods=['POST'])
def generate_summary():
    """
    Generate a targeted professional summary
    """
    data = request.get_json()
    experience = data.get('experience', [])
    skills = data.get('skills', [])
    target_role = data.get('target_role')
    
    if not target_role:
        return jsonify({'error': 'Missing target role'}), 400
        
    try:
        summary = llm_service.generate_summary(experience, skills, target_role)
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/enhance-experience', methods=['POST'])
def enhance_experience():
    """
    Enhance an experience entry
    """
    data = request.get_json()
    experience_entry = data.get('experience_entry')
    job_context = data.get('job_context')
    
    if not experience_entry or not job_context:
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        result = llm_service.enhance_experience(experience_entry, job_context)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/analyze', methods=['POST'])
def analyze_resume():
    """
    Analyze resume and provide feedback
    """
    data = request.get_json()
    resume_data = data.get('resume_data')
    
    if not resume_data:
        return jsonify({'error': 'Missing resume data'}), 400
        
    try:
        result = llm_service.analyze_resume(resume_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/trends', methods=['POST'])
def trends():
    """
    Analyze resume and provide feedback
    """
    data = request.get_json()
    resume_data = data.get('resume_data')
    
    if not resume_data:
        return jsonify({'error': 'Missing resume data'}), 400
        
    try:
        result = llm_service.analyze_resume(resume_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500