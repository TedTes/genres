import requests
from datetime import datetime
from utils.date import format_job_posted_date

def analyze_job_description(description):
    """
    Analyze job description to extract important skills and keywords
    This is a simplified version -  TODO: use more 
     NLP techniques with spaCy
    """
    # List of common technology skills to look for
    tech_skills = [
        "Python", "JavaScript", "React", "Angular", "Vue", "Node.js", "Django", 
        "Flask", "SQL", "NoSQL", "MongoDB", "PostgreSQL", "AWS", "Azure", "GCP",
        "Docker", "Kubernetes", "DevOps", "CI/CD", "Git", "Agile", "Scrum",
        "Frontend", "Backend", "Full Stack", "Web", "Mobile", "Android", "iOS",
        "Machine Learning", "AI", "Data Science", "Big Data", "Cloud", "API"
    ]
    
    # List of common soft skills
    soft_skills = [
        "Communication", "Teamwork", "Leadership", "Problem Solving", 
        "Critical Thinking", "Time Management", "Adaptability", 
        "Creativity", "Attention to Detail", "Customer Service",
        "Presentation", "Negotiation", "Conflict Resolution"
    ]
    
    # Combine all skills
    all_skills = tech_skills + soft_skills
    
    # Find matching skills in description (case-insensitive)
    description_lower = description.lower()
    found_skills = []
    
    for skill in all_skills:
        if skill.lower() in description_lower:
            found_skills.append(skill)
    
    return found_skills



def extract_job_tags(title, description):
    """
    Extract relevant tags from job title and description
    """
    # List of common technology keywords to look for
    tech_keywords = [
        "Python", "JavaScript", "React", "Angular", "Vue", "Node.js", "Django", 
        "Flask", "SQL", "NoSQL", "MongoDB", "PostgreSQL", "AWS", "Azure", "GCP",
        "Docker", "Kubernetes", "DevOps", "CI/CD", "Git", "Agile", "Scrum",
        "Frontend", "Backend", "Full Stack", "Web", "Mobile", "Android", "iOS",
        "Machine Learning", "AI", "Data Science", "Big Data", "Cloud", "API"
    ]
    
    # Combine title and description, lowercase for case-insensitive matching
    text = f"{title} {description}".lower()
    
    # Find matching tags
    tags = []
    for keyword in tech_keywords:
        if keyword.lower() in text:
            tags.append(keyword)
    
    # Check for remote work
    if "remote" in text or "work from home" in text:
        tags.append("Remote")
    
    # Check for job types
    job_types = ["Full-time", "Part-time", "Contract", "Freelance", "Internship"]
    for job_type in job_types:
        if job_type.lower() in text:
            tags.append(job_type)
    
    return tags

def find_similar_jobs(current_slug, job_skills, limit=3):
    """
    Find similar jobs based on skills overlap
    """
    from models import Job
    
    try:
        # Get all jobs except the current one
        all_jobs = Job.query.filter(Job.slug != current_slug).all()
        job_scores = []
        
        for job in all_jobs:
            # Extract skills from this job
            other_job_skills = extract_skills_from_text(job.description)
            
            # Calculate similarity score based on skills overlap
            similarity_score = 0
            
            for skill, importance in job_skills.items():
                if skill in other_job_skills:
                    # Add to similarity score, weighted by both jobs' importance for this skill
                    other_importance = other_job_skills.get(skill, 0)
                    similarity_score += (importance + other_importance) / 2
            
            # Add location score if locations match
            current_job = Job.query.filter_by(slug=current_slug).first()
            if current_job and job.location == current_job.location:
                similarity_score += 20
            
            # Add to scores list
            job_scores.append((similarity_score, job))
        
        # Sort by score (highest first) and take top X
        job_scores.sort(reverse=True, key=lambda x: x[0])
        similar_jobs = [job for _, job in job_scores[:limit]]
        
        # Process similar jobs for display (add any needed attributes)
        for job in similar_jobs:
            # Add tags for display
            job.tags = list(extract_skills_from_text(job.description).keys())[:5]
            
            # Format dates
            days_ago = (datetime.now() - job.posted_at).days if job.posted_at else 0
            if days_ago == 0:
                job.posted_at = "Today"
            elif days_ago == 1:
                job.posted_at = "Yesterday"
            else:
                job.posted_at = f"{days_ago} days ago"
        
        return similar_jobs
    
    except Exception as e:
        print(f"Error finding similar jobs: {e}")
        return []



def get_recent_job_matches(user_id, limit=3):
    """
    Fetch recent job matches from the database for a specific user.
    
    Args:
        user_id: The ID of the user to fetch matches for
        limit: Maximum number of matches to return
        
    Returns:
        A list of job match dictionaries
    """
    from models import Job, Resume
    from sqlalchemy import desc
    
    try:
        # Get the user's skills from their most recent resume
        user_resume = Resume.query.filter_by(user_id=user_id).order_by(desc(Resume.updated_at)).first()
        if not user_resume or not user_resume.resume_data or 'skills' not in user_resume.resume_data:
            # If no skills found, return the most recent jobs posted
            recent_jobs = Job.query.order_by(desc(Job.posted_at)).limit(limit).all()
            return [{
                'slug': job.slug,
                'title': job.title,
                'company_name': job.company,
                'location': job.location,
                'remote': 'remote' in job.location.lower() if job.location else False,
                'posted_at': (datetime.now() - job.posted_at).days if job.posted_at else 0,
                'match': 50  # Default match score of 50% for users without skills
            } for job in recent_jobs]
        
        # Extract user skills
        user_skills_data = user_resume.resume_data['skills']
        user_skills = []
        
        if isinstance(user_skills_data, str):
            user_skills = [skill.strip() for skill in user_skills_data.split(',')]
        elif isinstance(user_skills_data, list):
            user_skills = user_skills_data
        
        # Get all jobs to match against
        all_jobs = Job.query.order_by(desc(Job.posted_at)).limit(50).all()
        # Calculate match score for each job
        job_matches = []
        
        for job in all_jobs:
            # Extract skills from job description
            job_skills = extract_skills_from_text(job.description)
            
            # Calculate match score
            match_percentage, _ = calculate_skill_match(user_skills, job_skills)
            
            # Create job match dictionary with score
            job_match = {
                'id': job.id,
                'slug': job.slug,
                'title': job.title,
                'company_name': job.company,
                'location': job.location,
                'remote': 'remote' in job.location.lower() if job.location else False,
                'match': match_percentage,
                'posted_at': (datetime.now() - job.posted_at).days if job.posted_at else 0
            }
            
            job_matches.append(job_match)
        
        # Sort by match score (highest first) and take top matches
        job_matches.sort(key=lambda x: x['match'], reverse=True)
        
        return job_matches[:limit]
    
    except Exception as e:
        print(f"Error getting job matches: {e}")
        import traceback
        traceback.print_exc()
        return []

def process_jobs_for_display(jobs):
        """
        Process job data to add tags and format dates
        
        Args:
            jobs: List of Job objects
            
        Returns:
            list: List of processed job dictionaries
        """
        processed_jobs = []
        
        for job in jobs:
            # Convert SQLAlchemy object to dictionary
            job_dict = {
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'description': job.description,
                'remote': job.remote,
                'salary': job.salary,
                'url': job.url,
                'slug': job.slug,
                'created_at': job.created_at
            }
            
            # Extract tags from job title and description
            tags = extract_job_tags(job.title, job.description)
            
            # Format the date
            formatted_date = format_job_posted_date(job.posted_at)
            
            # Create processed job object
            processed_job = {
                **job_dict,
                'tags': tags[:3],  # Limit to top 3 tags
                'posted_at': formatted_date
            }
            
            processed_jobs.append(processed_job)
        
        return processed_jobs