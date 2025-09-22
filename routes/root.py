from flask import Blueprint,abort,render_template,url_for,redirect
from flask_login import  current_user, login_required
from models import  User,Resume,ResumeOptimization
from services.subscription_service import SubscriptionService
from utils.date import format_job_posted_date
root_bp = Blueprint("root",__name__)


@root_bp.route('/')
def home():

    try:
        if current_user.is_authenticated:
            return redirect(url_for('root.dashboard'))
            
        else:
            return render_template('home.html')
    except Exception as e:
        print(f"Error rendering home page: {e}")  # Debug print
        abort(500)

@root_bp.route('/dashboard')
@login_required
def dashboard():
    # Get user's resumes
    resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.updated_at.desc()).limit(5).all()
    
    # Get user's recent optimizations
    optimizations = ResumeOptimization.query.filter_by(user_id=current_user.id).order_by(ResumeOptimization.created_at.desc()).limit(5).all()
    
    # Calculate average match score
    match_scores = [opt.match_score_after for opt in optimizations if opt.match_score_after]
    avg_match_score = (sum(match_scores) / len(match_scores) * 100) if match_scores else 0
    
    # Mock data for stats not yet implemented
    export_count = len([opt for opt in optimizations if opt.pdf_url or opt.docx_url])
    time_saved = current_user.optimization_count * 2 if current_user.optimization_count else 0
    
    # For saved jobs - you'll need to create this model/table later
    saved_jobs = []  # TODO: Implement SavedJob model
    
    # return render_template('dashboard.html', 
    #                      resumes=resumes,
    #                      user_stats={total_optimization: 20},
    #                      optimizations=optimizations,
    #                      saved_jobs=saved_jobs,
    #                      avg_match_score=avg_match_score,
    #                      export_count=export_count,
    #                      time_saved=time_saved)
    return render_template('dashboard.html', 
                    user_stats={
                        'total_optimizations': 5,
                        'remaining_free_optimizations': 1,
                        'recent_optimizations': []
                    })

    

@root_bp.route('/my-resumes')
@login_required
def my_resumes():
    """Display all user's resumes with management options."""
    try:
        # Get all user's resumes ordered by most recent
        resumes = Resume.query.filter_by(
            user_id=current_user.id
        ).order_by(Resume.updated_at.desc()).all()
        
        # Get user's optimizations for resume status
        optimizations = ResumeOptimization.query.filter_by(
            user_id=current_user.id
        ).all()
        
        # Create optimization lookup for resume status
        optimization_lookup = {}
        for opt in optimizations:
            if opt.resume_id:  # If linked to a resume
                optimization_lookup[opt.resume_id] = opt
        
        # Add optimization status to each resume
        for resume in resumes:
            resume.is_optimized = resume.id in optimization_lookup
            resume.last_optimization = optimization_lookup.get(resume.id)
            
            # Calculate completeness score (TODO: refine this logic)
            # resume.completeness_score = calculate_resume_completeness(resume)
        for resume in resumes:
            # Create display title from available data
            resume.display_title = getattr(resume, 'title', 'Untitled Resume')
            
            # Extract company from work experience if available
            resume.display_company = 'Various Companies'  # Placeholder
            
            # Mock completeness score for now
            resume.completeness_score = 85  # You can implement actual calculation later
            
            # Check if this resume has been optimized
            resume.is_optimized = ResumeOptimization.query.filter_by(
                user_id=current_user.id,
                # TODO: might need to add original_resume_id to link optimizations to resumes
            ).first() is not None
        
        return render_template('resumes.html', resumes=resumes)
        
    except Exception as e:
        print(f"Error loading resumes: {e}")
        abort(500)


@root_bp.route('/templates')
def templates():
    """Display available resume templates."""
    try:
        # TODO: Mock template data - replace with actual template system later
        templates = [
            {
                'id': 1,
                'name': 'Professional',
                'description': 'Clean, ATS-friendly design perfect for corporate roles',
                'preview_image': '/static/images/templates/professional.png',
                'category': 'Business',
                'is_premium': False
            },
            {
                'id': 2,
                'name': 'Modern',
                'description': 'Contemporary layout with subtle design elements',
                'preview_image': '/static/images/templates/modern.png',
                'category': 'Technology',
                'is_premium': False
            },
            {
                'id': 3,
                'name': 'Executive',
                'description': 'Sophisticated template for senior-level positions',
                'preview_image': '/static/images/templates/executive.png',
                'category': 'Executive',
                'is_premium': True
            },
            {
                'id': 4,
                'name': 'Creative',
                'description': 'Stylish design for creative professionals',
                'preview_image': '/static/images/templates/creative.png',
                'category': 'Creative',
                'is_premium': True
            }
        ]
        
        return render_template('templates.html', templates=templates)
        
    except Exception as e:
        print(f"Error loading templates: {e}")
        abort(500)