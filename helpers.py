import requests
import spacy
import re
from collections import Counter
from datetime import datetime
from jinja2 import Template, Environment, FileSystemLoader
def fetch_jobs(search_term=None, location=None, remote=None):
    """
    Fetch jobs from the Arbeitnow API with optional filters
    """
    url = "https://www.arbeitnow.com/api/job-board-api"
    params = {}
    
    if search_term:
        params['search'] = search_term
    if location:
        params['location'] = location
    if remote is not None:
        params['remote'] = 'true' if remote else 'false'
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.RequestException as e:
        print(f"API request error: {e}")
        return []

def fetch_job_by_slug(slug):
    """
    Fetch a specific job from the Arbeitnow API using its slug
    """
    url = "https://www.arbeitnow.com/api/job-board-api"
    
   
    params = {'slug': slug}
    
    try:
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json().get('data', [])
        
        matching_job = next((job for job in data if job.get('slug') == slug), None)
        if matching_job:
            return matching_job
        # If the API doesn't support slug filtering, we need to fetch all and filter
        if not data or len(data) > 1:
            print("API doesn't support direct slug lookup, fetching all jobs")
            all_jobs = fetch_jobs()
            return next((job for job in all_jobs if job.get('slug') == slug), None)
            
        return None
    except requests.RequestException as e:
        print(f"API request error when fetching job by slug: {e}")
        return None


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
# from weasyprint import HTML
def generate_pdf(html_string):
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    return pdf


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
                job.created_at = "Today"
            elif days_ago == 1:
                job.created_at = "Yesterday"
            else:
                job.created_at = f"{days_ago} days ago"
        
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
                'created_at': (datetime.now() - job.posted_at).days if job.posted_at else 0,
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
                'created_at': (datetime.now() - job.posted_at).days if job.posted_at else 0
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


THEMES = {
    "professional": {
        "name": "Professional",
        "colors": {
            "primary": "#2c3e50",
            "secondary": "#3498db",
            "text": "#333333",
            "text_light": "#666666",
            "background": "#ffffff",
            "accent": "#e74c3c",
            "border": "#dddddd"
        },
        "typography": {
            "font_family": "'Open Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif",
            "heading_family": "'Open Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif",
            "base_size": "14px",
            "line_height": "1.6",
            "heading_weight": "600"
        }
    },
    "modern": {
        "name": "Modern",
        "colors": {
            "primary": "#3b82f6",
            "secondary": "#10b981",
            "text": "#1f2937",
            "text_light": "#6b7280",
            "background": "#ffffff",
            "accent": "#f59e0b",
            "border": "#e5e7eb"
        },
        "typography": {
            "font_family": "'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif",
            "heading_family": "'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif",
            "base_size": "15px",
            "line_height": "1.7",
            "heading_weight": "700"
        }
    },
    "minimalist": {
        "name": "Minimalist",
        "colors": {
            "primary": "#000000",
            "secondary": "#555555",
            "text": "#333333",
            "text_light": "#777777",
            "background": "#ffffff",
            "accent": "#000000",
            "border": "#eeeeee"
        },
        "typography": {
            "font_family": "'Helvetica Neue', Helvetica, Arial, sans-serif",
            "heading_family": "'Helvetica Neue', Helvetica, Arial, sans-serif",
            "base_size": "14px",
            "line_height": "1.5",
            "heading_weight": "500"
        }
    },
    "elegant": {
        "name": "Elegant",
        "colors": {
            "primary": "#1e293b",
            "secondary": "#64748b",
            "text": "#334155",
            "text_light": "#64748b",
            "background": "#ffffff",
            "accent": "#0369a1",
            "border": "#e2e8f0"
        },
        "typography": {
            "font_family": "'Playfair Display', 'Georgia', serif",
            "heading_family": "'Playfair Display', 'Georgia', serif",
            "base_size": "15px",
            "line_height": "1.7",
            "heading_weight": "700"
        }
    },
    "corporate": {
        "name": "Corporate",
        "colors": {
            "primary": "#0f172a",
            "secondary": "#475569",
            "text": "#1e293b",
            "text_light": "#64748b",
            "background": "#ffffff",
            "accent": "#0284c7",
            "border": "#e2e8f0"
        },
        "typography": {
            "font_family": "'Roboto', 'Segoe UI', 'Helvetica Neue', sans-serif",
            "heading_family": "'Roboto', 'Segoe UI', 'Helvetica Neue', sans-serif",
            "base_size": "14px",
            "line_height": "1.6",
            "heading_weight": "500"
        }
    },
     "tech": {
        "name": "Tech",
        "colors": {
            "primary": "#6b21a8",  # Deep purple
            "secondary": "#6d28d9",
            "text": "#18181b",
            "text_light": "#71717a",
            "background": "#ffffff",
            "accent": "#2dd4bf",  # Teal
            "border": "#e4e4e7"
        },
        "typography": {
            "font_family": "'Fira Code', 'Source Code Pro', monospace",
            "heading_family": "'Montserrat', 'SF Pro Display', sans-serif",
            "base_size": "14px",
            "line_height": "1.6",
            "heading_weight": "700"
        }
    },
    "creative": {
        "name": "Creative",
        "colors": {
            "primary": "#ec4899",  # Pink
            "secondary": "#8b5cf6",  # Purple
            "text": "#18181b",
            "text_light": "#71717a",
            "background": "#ffffff",
            "accent": "#fcd34d",  # Yellow
            "border": "#f3f4f6"
        },
        "typography": {
            "font_family": "'Poppins', 'Helvetica Neue', sans-serif",
            "heading_family": "'Poppins', 'Helvetica Neue', sans-serif",
            "base_size": "15px",
            "line_height": "1.7",
            "heading_weight": "600"
        }
    },
    "dark": {
        "name": "Dark Mode",
        "colors": {
            "primary": "#60a5fa",  # Blue
            "secondary": "#93c5fd",  # Light blue
            "text": "#e5e7eb",
            "text_light": "#9ca3af",
            "background": "#1f2937",
            "accent": "#f472b6",  # Pink
            "border": "#374151"
        },
        "typography": {
            "font_family": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
            "heading_family": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
            "base_size": "15px",
            "line_height": "1.7",
            "heading_weight": "600"
        }
    },
    "vintage": {
        "name": "Vintage",
        "colors": {
            "primary": "#854d0e",  # Brown
            "secondary": "#a16207",  # Amber
            "text": "#44403c",
            "text_light": "#78716c",
            "background": "#faf7f5",
            "accent": "#b45309",  # Darker amber
            "border": "#e7e5e4"
        },
        "typography": {
            "font_family": "'Libre Baskerville', 'Georgia', serif",
            "heading_family": "'Libre Baskerville', 'Georgia', serif",
            "base_size": "15px",
            "line_height": "1.7",
            "heading_weight": "700"
        }
    },
    "gradient": {
        "name": "Gradient",
        "colors": {
            "primary": "#4f46e5",  # Indigo
            "secondary": "#7c3aed",  # Violet
            "text": "#111827", 
            "text_light": "#6b7280",
            "background": "#ffffff",
            "accent": "#3b82f6",  # Blue 
            "border": "#e5e7eb"
        },
        "typography": {
            "font_family": "'Raleway', 'Helvetica Neue', sans-serif",
            "heading_family": "'Raleway', 'Helvetica Neue', sans-serif",
            "base_size": "15px",
            "line_height": "1.7",
            "heading_weight": "600"
        }
    }
}


LAYOUTS = {
    "classic": {
        "name": "Classic",
        "description": "Traditional single-column layout",
        "template": "classic.html",
        "css": """
            .resume-container {
                max-width: 800px;
                margin: 0 auto;
                padding: 25px;
                font-family: var(--font-family);
                color: var(--text);
                line-height: var(--line-height);
            }
            
            .resume-header {
                margin-bottom: 25px;
                border-bottom: 2px solid var(--primary);
                padding-bottom: 15px;
            }
            
            .name {
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 5px;
                color: var(--primary);
            }
            
            .title {
                font-size: 18px;
                color: var(--text-light);
                margin-bottom: 15px;
            }
            
            .contact-grid {
                display: flex;
                flex-wrap: wrap;
                gap: 10px 20px;
            }
            
            .contact-item {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .contact-icon {
                color: var(--primary);
                width: 16px;
                text-align: center;
            }
            
            .resume-section {
                margin-bottom: 25px;
            }
            
            .section-title {
                font-size: 18px;
                font-weight: 600;
                color: var(--primary);
                margin-bottom: 15px;
                padding-bottom: 5px;
                border-bottom: 1px solid var(--border);
            }
            
            .experience-item, .education-item {
                margin-bottom: 15px;
            }
            
            .job-title, .degree {
                font-weight: 600;
                font-size: 16px;
                margin-bottom: 5px;
            }
            
            .company-name, .school {
                font-weight: 500;
            }
            
            .job-duration, .education-date {
                color: var(--text-light);
                font-size: 14px;
                margin-bottom: 8px;
            }
            
            .job-duties {
                margin-top: 8px;
                padding-left: 20px;
            }
            
            .job-duties li {
                margin-bottom: 5px;
            }
            
            .skills-container {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }
            
            .skill-tag {
                background-color: #f0f4f8;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 14px;
            }
        """
    },
    "modern": {
        "name": "Modern",
        "description": "Two-column modern layout",
        "template": "modern.html",
        "css": """
            .resume-container {
                max-width: 800px;
                margin: 0 auto;
                padding: 30px;
                font-family: var(--font-family);
                color: var(--text);
                line-height: var(--line-height);
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
            }
            
            .resume-header {
                grid-column: 1 / -1;
                display: flex;
                flex-direction: column;
                margin-bottom: 25px;
            }
            
            .name {
                font-size: 32px;
                font-weight: 700;
                margin-bottom: 5px;
                color: var(--primary);
            }
            
            .title {
                font-size: 18px;
                color: var(--text-light);
                margin-bottom: 15px;
            }
            
            .contact-grid {
                display: flex;
                flex-wrap: wrap;
                gap: 10px 20px;
            }
            
            .contact-item {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .contact-icon {
                color: var(--primary);
                width: 16px;
                text-align: center;
            }
            
            .main-column {
                grid-column: 1 / 2;
            }
            
            .side-column {
                grid-column: 2 / 3;
            }
            
            .resume-section {
                margin-bottom: 25px;
            }
            
            .section-title {
                font-size: 18px;
                font-weight: 600;
                color: var(--primary);
                margin-bottom: 15px;
                padding-bottom: 5px;
                border-bottom: 2px solid var(--primary);
            }
            
            .experience-item, .education-item {
                margin-bottom: 20px;
            }
            
            .job-title, .degree {
                font-weight: 600;
                font-size: 16px;
                margin-bottom: 5px;
            }
            
            .company-name, .school {
                font-weight: 500;
            }
            
            .job-duration, .education-date {
                color: var(--text-light);
                font-size: 14px;
                margin-bottom: 8px;
            }
            
            .job-duties {
                margin-top: 8px;
                padding-left: 20px;
            }
            
            .job-duties li {
                margin-bottom: 5px;
            }
            
            .skills-container {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }
            
            .skill-tag {
                background-color: rgba(59, 130, 246, 0.1);
                color: var(--primary);
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 14px;
            }
            
            @media print, (max-width: 768px) {
                .resume-container {
                    grid-template-columns: 1fr;
                    gap: 20px;
                }
                
                .main-column, .side-column {
                    grid-column: 1 / -1;
                }
            }
        """
    },
    "sidebar": {
        "name": "Sidebar",
        "description": "Two-column layout with left sidebar",
        "template": "sidebar.html",
        "css": """
            .resume-container {
                max-width: 800px;
                margin: 0 auto;
                font-family: var(--font-family);
                color: var(--text);
                line-height: var(--line-height);
                display: grid;
                grid-template-columns: 250px 1fr;
            }
            
            .sidebar {
                background-color: var(--primary);
                color: white;
                padding: 30px 20px;
                height: 100%;
            }
            
            .main-content {
                padding: 30px;
            }
            
            .avatar {
                width: 120px;
                height: 120px;
                border-radius: 50%;
                background-color: rgba(255, 255, 255, 0.2);
                margin: 0 auto 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 36px;
                font-weight: 700;
            }
            
            .name {
                font-size: 24px;
                font-weight: 700;
                text-align: center;
                margin-bottom: 5px;
            }
            
            .title {
                font-size: 16px;
                text-align: center;
                margin-bottom: 25px;
                opacity: 0.9;
            }
            
            .sidebar-section {
                margin-bottom: 25px;
            }
            
            .sidebar-title {
                text-transform: uppercase;
                font-size: 14px;
                letter-spacing: 1px;
                margin-bottom: 15px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
                padding-bottom: 5px;
            }
            
            .contact-item {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 10px;
            }
            
            .contact-icon {
                width: 16px;
                text-align: center;
            }
            
            .skill-tag {
                background-color: rgba(255, 255, 255, 0.1);
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 14px;
                margin-bottom: 8px;
                display: inline-block;
                margin-right: 8px;
            }
            
            .main-section {
                margin-bottom: 25px;
            }
            
            .main-title {
                font-size: 20px;
                font-weight: 600;
                color: var(--primary);
                margin-bottom: 15px;
                padding-bottom: 5px;
                border-bottom: 2px solid var(--primary);
            }
            
            .experience-item, .education-item {
                margin-bottom: a20px;
            }
            
            .job-title, .degree {
                font-weight: 600;
                font-size: 16px;
                margin-bottom: 5px;
            }
            
            .company-name, .school {
                font-weight: 500;
            }
            
            .job-duration, .education-date {
                color: var(--text-light);
                font-size: 14px;
                margin-bottom: 8px;
            }
            
            .job-duties {
                margin-top: 8px;
                padding-left: 20px;
            }
            
            .job-duties li {
                margin-bottom: 5px;
            }
            
            @media print, (max-width: 768px) {
                .resume-container {
                    grid-template-columns: 1fr;
                }
                
                .sidebar {
                    padding-bottom: 20px;
                }
            }
        """
    },
    "minimalist": {
        "name": "Minimalist",
        "description": "Clean and minimal single-column layout",
        "template": "minimalist.html",
        "css": """
            .resume-container {
                max-width: 800px;
                margin: 0 auto;
                padding: 40px;
                font-family: var(--font-family);
                color: var(--text);
                line-height: var(--line-height);
            }
            
            .resume-header {
                text-align: center;
                margin-bottom: 40px;
            }
            
            .name {
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 5px;
                color: var(--primary);
                letter-spacing: 1px;
            }
            
            .title {
                font-size: 16px;
                color: var(--text-light);
                margin-bottom: 20px;
                font-weight: 400;
            }
            
            .contact-grid {
                display: flex;
                justify-content: center;
                flex-wrap: wrap;
                gap: 15px 30px;
            }
            
            .contact-item {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 14px;
            }
            
            .contact-icon {
                color: var(--primary);
                width: 16px;
                text-align: center;
            }
            
            .resume-section {
                margin-bottom: 30px;
            }
            
            .section-title {
                font-size: 16px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: var(--primary);
                margin-bottom: 15px;
            }
            
            .experience-item, .education-item {
                margin-bottom: 25px;
                display: grid;
                grid-template-columns: 150px 1fr;
                gap: 20px;
            }
            
            .job-header, .education-header {
                grid-column: 1 / -1;
                margin-bottom: 10px;
            }
            
            .job-title, .degree {
                font-weight: 600;
                font-size: 16px;
            }
            
            .company-name, .school {
                color: var(--text-light);
            }
            
            .job-duration, .education-date {
                font-size: 14px;
                color: var(--text-light);
            }
            
            .job-duties {
                margin: 0;
                padding-left: 20px;
            }
            
            .job-duties li {
                margin-bottom: 5px;
            }
            
            .skills-container {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }
            
            .skill-tag {
                background: none;
                border: 1px solid var(--border);
                padding: 4px 10px;
                border-radius: 3px;
                font-size: 14px;
            }
            
            @media (max-width: 600px) {
                .experience-item, .education-item {
                    grid-template-columns: 1fr;
                    gap: 10px;
                }
            }
        """
    },
    "professional": {
        "name": "Professional",
        "description": "Professional two-column layout with header",
        "template": "professional.html",
        "css": """
            .resume-container {
                max-width: 800px;
                margin: 0 auto;
                font-family: var(--font-family);
                color: var(--text);
                line-height: var(--line-height);
            }
            
            .resume-header {
                padding: 25px 30px;
                background-color: var(--primary);
                color: white;
            }
            
            .name-title-container {
                margin-bottom: 15px;
            }
            
            .name {
                font-size: 26px;
                font-weight: 700;
                margin-bottom: 5px;
            }
            
            .title {
                font-size: 16px;
                opacity: 0.9;
            }
            
            .contact-grid {
                display: flex;
                flex-wrap: wrap;
                gap: 10px 30px;
            }
            
            .contact-item {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 14px;
            }
            
            .contact-icon {
                width: 16px;
                text-align: center;
            }
            
            .resume-body {
                display: grid;
                grid-template-columns: 2fr 1fr;
            }
            
            .main-column {
                padding: 25px;
                border-right: 1px solid var(--border);
            }
            
            .side-column {
                padding: 25px;
            }
            
            .resume-section {
                margin-bottom: 25px;
            }
            
            .section-title {
                font-size: 18px;
                font-weight: 600;
                color: var(--primary);
                margin-bottom: 15px;
                padding-bottom: 5px;
                border-bottom: 1px solid var(--border);
            }
            
            .experience-item, .education-item {
                margin-bottom: 20px;
            }
            
            .job-title, .degree {
                font-weight: 600;
                font-size: 16px;
                margin-bottom: 2px;
            }
            
            .company-name, .school {
                font-weight: 500;
                margin-bottom: 2px;
            }
            
            .job-duration, .education-date {
                color: var(--text-light);
                font-size: 14px;
                margin-bottom: 8px;
            }
            
            .job-duties {
                margin-top: 8px;
                padding-left: 20px;
            }
            
            .job-duties li {
                margin-bottom: 5px;
            }
            
            .skills-container {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }
            
            .skill-tag {
                background-color: #f0f4f8;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 14px;
            }
            
            @media print, (max-width: 768px) {
                .resume-body {
                    grid-template-columns: 1fr;
                }
                
                .main-column {
                    border-right: none;
                    border-bottom: 1px solid var(--border);
                }
            }
        """
    },
    "timeline": {
        "name": "Timeline",
        "description": "Experience presented as a visual timeline",
        "template": "timeline.html",
        "css": """
            .resume-container {
                max-width: 800px;
                margin: 0 auto;
                padding: 25px;
                font-family: var(--font-family);
                color: var(--text);
            }
            
            .resume-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 2px solid var(--primary);
            }
            
            .header-main {
                flex: 1;
            }
            
            .name {
                font-size: 28px;
                font-weight: 700;
                color: var(--primary);
                margin-bottom: 5px;
            }
            
            .title {
                font-size: 16px;
                color: var(--text-light);
            }
            
            .contact-grid {
                display: flex;
                flex-wrap: wrap;
                gap: 10px 20px;
                flex: 1;
                justify-content: flex-end;
                text-align: right;
            }
            
            .contact-item {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 14px;
            }
            
            .contact-icon {
                color: var(--primary);
                width: 16px;
                text-align: center;
            }
            
            .content-container {
                display: grid;
                grid-template-columns: 7fr 3fr;
                gap: 30px;
            }
            
            .main-column {
                grid-column: 1;
            }
            
            .side-column {
                grid-column: 2;
            }
            
            .resume-section {
                margin-bottom: 25px;
            }
            
            .section-title {
                font-family: var(--heading-family);
                font-size: 18px;
                font-weight: var(--heading-weight);
                color: var(--primary);
                margin-bottom: 15px;
                padding-bottom: 5px;
                border-bottom: 1px solid var(--primary);
            }
            
            .summary {
                margin-bottom: 20px;
                line-height: var(--line-height);
            }
            
            /* Timeline specific styles */
            .timeline {
                position: relative;
                padding-left: 30px;
                margin-left: 10px;
            }
            
            .timeline::before {
                content: '';
                position: absolute;
                left: 0;
                top: 10px;
                bottom: 0;
                width: 2px;
                background-color: var(--primary);
                opacity: 0.3;
            }
            
            .timeline-item {
                position: relative;
                margin-bottom: 30px;
            }
            
            .timeline-dot {
                position: absolute;
                left: -39px;
                top: 5px;
                width: 16px;
                height: 16px;
                border-radius: 50%;
                background-color: var(--primary);
                z-index: 1;
            }
            
            .timeline-date {
                position: absolute;
                left: -205px;
                top: 3px;
                width: 150px;
                text-align: right;
                font-size: 14px;
                color: var(--text-light);
            }
            
            .timeline-content {
                background-color: #f8f9fa;
                border-radius: 5px;
                padding: 15px;
                border-left: 3px solid var(--primary);
            }
            
            .job-title {
                font-size: 16px;
                font-weight: 600;
                color: var(--primary);
                margin-bottom: 5px;
            }
            
            .company-name {
                font-size: 15px;
                color: var(--text-light);
                margin-bottom: 10px;
            }
            
            .job-duties {
                margin-top: 10px;
                padding-left: 20px;
            }
            
            .job-duties li {
                margin-bottom: 5px;
            }
            
            /* Education & Skills */
            .education-item {
                margin-bottom: 20px;
            }
            
            .degree {
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 2px;
            }
            
            .school {
                font-size: 15px;
                color: var(--text-light);
                margin-bottom: 2px;
            }
            
            .education-date {
                font-size: 14px;
                color: var(--text-light);
                margin-bottom: 5px;
            }
            
            .education-description {
                font-size: 14px;
                margin-top: 5px;
            }
            
            .skills-container {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }
            
            .skill-tag {
                background-color: var(--primary);
                color: white;
                padding: 4px 10px;
                border-radius: 4px;
                font-size: 13px;
                opacity: 0.8;
                transition: opacity 0.2s;
            }
            
            .skill-tag:hover {
                opacity: 1;
            }
            
            .certs-list {
                padding-left: 20px;
            }
            
            .certs-list li {
                margin-bottom: 5px;
            }
            
            /* Project styles */
            .project-item {
                background-color: #f8f9fa;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 15px;
                border-left: 3px solid var(--secondary);
            }
            
            .project-title {
                font-size: 16px;
                font-weight: 600;
                color: var(--secondary);
                margin-bottom: 5px;
            }
            
            .project-description {
                margin-bottom: 10px;
            }
            
            .project-tech {
                display: flex;
                flex-wrap: wrap;
                gap: 5px;
                margin-top: 10px;
            }
            
            .tech-tag {
                background-color: rgba(0, 0, 0, 0.05);
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 12px;
            }
            
            @media (max-width: 768px) {
                .content-container {
                    grid-template-columns: 1fr;
                }
                
                .main-column, .side-column {
                    grid-column: 1;
                }
                
                .timeline-date {
                    position: static;
                    text-align: left;
                    margin-bottom: 5px;
                    width: auto;
                }
                
                .timeline {
                    padding-left: 20px;
                }
                
                .timeline-dot {
                    left: -29px;
                }
            }
        """
    },
    "cards": {
        "name": "Cards",
        "description": "Card-based components for each section",
        "template": "cards.html",
        "css": """
            .resume-container {
                max-width: 800px;
                margin: 0 auto;
                padding: 25px;
                font-family: var(--font-family);
                color: var(--text);
                background-color: #f9fafb;
            }
            
            /* Card styles */
            .resume-card {
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
                margin-bottom: 20px;
                overflow: hidden;
            }
            
            .header-card {
                display: flex;
                padding: 20px;
                background: linear-gradient(to right, var(--primary), var(--secondary));
                color: white;
            }
            
            .card-content {
                padding: 20px;
            }
            
            .card-header {
                padding: 15px 20px;
                background-color: #f8fafc;
                border-bottom: 1px solid var(--border);
            }
            
            .card-title {
                font-size: 16px;
                font-weight: 600;
                color: var(--primary);
                margin: 0;
            }
            
            .avatar {
                width: 64px;
                height: 64px;
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                font-weight: 700;
                margin-right: 20px;
                flex-shrink: 0;
            }
            
            .header-info {
                flex: 1;
            }
            
            .name {
                font-size: 24px;
                font-weight: 700;
                margin-bottom: 5px;
            }
            
            .title {
                font-size: 16px;
                opacity: 0.9;
                margin-bottom: 15px;
            }
            
            .contact-grid {
                display: flex;
                flex-wrap: wrap;
                gap: 10px 20px;
            }
            
            .contact-item {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 14px;
            }
            
            .contact-icon {
                width: 16px;
                text-align: center;
            }
            
            /* Cards grid layout */
            .cards-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 20px;
            }
            
            /* Item styles */
            .experience-item, .education-item, .project-item {
                margin-bottom: 20px;
            }
            
            .experience-item:last-child, .education-item:last-child, .project-item:last-child {
                margin-bottom: 0;
            }
            
            .job-title, .degree, .project-title {
                font-size: 16px;
                font-weight: 600;
                color: var(--text);
                margin-bottom: 2px;
            }
            
            .company-name, .school {
                font-size: 15px;
                color: var(--text-light);
                margin-bottom: 2px;
            }
            
            .job-duration, .education-date {
                font-size: 14px;
                color: var(--text-light);
                margin-bottom: 10px;
            }
            
            .job-duties {
                margin-top: 10px;
                padding-left: 20px;
            }
            
            .job-duties li {
                margin-bottom: 5px;
            }
            
            .certs-list {
                padding-left: 20px;
            }
            
            .certs-list li {
                margin-bottom: 5px;
            }
            
            .skills-container {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }
            
            .skill-tag {
                background-color: #f1f5f9;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 13px;
                color: var(--primary);
            }
            
            .summary {
                line-height: var(--line-height);
            }
            
          /* Project styles */
            .project-description {
                margin-top: 8px;
                font-size: 14px;
            }
            
            .project-tech {
                display: flex;
                flex-wrap: wrap;
                gap: 5px;
                margin-top: 8px;
            }
            
            .tech-tag {
                background-color: #f1f5f9;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 12px;
                color: var(--text-light);
            }
            
            .card-divider {
                border: none;
                height: 1px;
                background-color: var(--border);
                margin: 15px 0;
            }
            
            @media (max-width: 768px) {
                .cards-grid {
                    grid-template-columns: 1fr;
                }
            }
        """
    },
    "grid": {
        "name": "Modern Grid",
        "description": "A responsive grid layout with modern styling",
        "template": "grid.html",
        "css": """
            .resume-container {
                max-width: 800px;
                margin: 0 auto;
                font-family: var(--font-family);
                color: var(--text);
                background-color: var(--background);
            }
            
            /* Header styles */
            .resume-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 25px 30px;
                background-color: var(--primary);
                color: white;
            }
            
            .header-left {
                flex: 1;
            }
            
            .name {
                font-size: 24px;
                font-weight: 700;
                margin-bottom: 5px;
            }
            
            .title {
                font-size: 16px;
                opacity: 0.9;
            }
            
            .header-right {
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                gap: 8px;
            }
            
            .contact-item {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 14px;
            }
            
            .contact-icon {
                width: 16px;
                text-align: center;
            }
            
            /* Grid layout */
            .resume-grid {
                display: grid;
                grid-template-columns: repeat(12, 1fr);
                grid-gap: 20px;
                padding: 30px;
            }
            
            .grid-section {
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
                padding: 20px;
                margin-bottom: 10px;
            }
            
            /* Section sizing */
            .summary-section {
                grid-column: span 12;
            }
            
            .skills-section {
                grid-column: span 6;
            }
            
            .languages-section {
                grid-column: span 6;
            }
            
            .experience-section {
                grid-column: span 12;
            }
            
            .education-section {
                grid-column: span 6;
            }
            
            .certifications-section {
                grid-column: span 6;
            }
            
            .projects-section, .awards-section {
                grid-column: span 12;
            }
            
            /* Section styles */
            .section-title {
                font-size: 16px;
                font-weight: 600;
                color: var(--primary);
                margin-bottom: 15px;
                padding-bottom: 5px;
                border-bottom: 2px solid var(--primary);
            }
            
            .section-content {
                padding-top: 5px;
            }
            
            /* Item styles */
            .experience-item, .education-item {
                margin-bottom: 20px;
            }
            
            .exp-header, .edu-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 5px;
            }
            
            .job-title-company, .degree-school {
                flex: 1;
            }
            
            .job-title, .degree {
                font-size: 16px;
                font-weight: 600;
                color: var(--text);
                margin-bottom: 2px;
            }
            
            .company-name, .school {
                font-size: 15px;
                color: var(--text-light);
            }
            
            .job-duration, .education-date {
                font-size: 14px;
                color: var(--text-light);
                text-align: right;
            }
            
            .job-duties {
                margin-top: 10px;
                padding-left: 20px;
            }
            
            .job-duties li {
                margin-bottom: 5px;
            }
            
            .education-description {
                font-size: 14px;
                margin-top: 5px;
            }
            
            /* Skills and languages */
            .skills-container {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }
            
            .skill-tag {
                background-color: rgba(59, 130, 246, 0.1);
                color: var(--primary);
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 13px;
            }
            
            .certs-list {
                padding-left: 20px;
            }
            
            .certs-list li {
                margin-bottom: 5px;
            }
            
            /* Projects grid */
            .projects-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 15px;
            }
            
            .project-item {
                background-color: #f8fafc;
                border-radius: 8px;
                padding: 15px;
                border-top: 3px solid var(--accent);
            }
            
            .project-title {
                font-size: 16px;
                font-weight: 600;
                color: var(--text);
                margin-bottom: 8px;
            }
            
            .project-description {
                font-size: 14px;
                margin-bottom: 10px;
            }
            
            .project-tech {
                display: flex;
                flex-wrap: wrap;
                gap: 5px;
                margin-top: 10px;
            }
            
            .tech-tag {
                background-color: rgba(0, 0, 0, 0.05);
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 12px;
                color: var(--text-light);
            }
            
            .project-link {
                display: block;
                margin-top: 10px;
                font-size: 13px;
                color: var(--primary);
                text-decoration: none;
            }
            
            /* Award styles */
            .award-item {
                margin-bottom: 15px;
            }
            
            .award-title-date {
                display: flex;
                justify-content: space-between;
                margin-bottom: 5px;
            }
            
            .award-title {
                font-size: 16px;
                font-weight: 600;
                color: var(--text);
            }
            
            .award-date {
                font-size: 14px;
                color: var(--text-light);
            }
            
            .award-issuer {
                font-size: 15px;
                color: var(--text-light);
                margin-bottom: 5px;
            }
            
            /* Resume footer */
            .resume-footer {
                grid-column: span 12;
                display: flex;
                justify-content: center;
                gap: 20px;
                padding: 10px 0;
                margin-top: 20px;
            }
            
            .social-link {
                color: var(--primary);
                text-decoration: none;
                font-size: 14px;
                display: flex;
                align-items: center;
                gap: 5px;
            }
            
            @media (max-width: 768px) {
                .skills-section, .languages-section, .education-section, .certifications-section {
                    grid-column: span 12;
                }
                
                .resume-header {
                    flex-direction: column;
                    align-items: flex-start;
                }
                
                .header-right {
                    margin-top: 15px;
                    align-items: flex-start;
                }
                
                .projects-grid {
                    grid-template-columns: 1fr;
                }
            }
        """
    },
    "portfolio": {
        "name": "Portfolio",
        "description": "Design that highlights projects for creative professionals",
        "template": "portfolio.html",
        "css": """
            .resume-container {
                max-width: 800px;
                margin: 0 auto;
                font-family: var(--font-family);
                color: var(--text);
                background-color: var(--background);
            }
            
            /* Portfolio header */
            .portfolio-header {
                background: linear-gradient(to right, var(--primary), var(--secondary));
                color: white;
                padding: 30px;
                border-radius: 8px 8px 0 0;
            }
            
            .header-content {
                max-width: 100%;
                margin: 0 auto;
            }
            
            .name-title {
                text-align: center;
                margin-bottom: 20px;
            }
            
            .name {
                font-size: 32px;
                font-weight: 700;
                margin-bottom: 5px;
            }
            
            .title {
                font-size: 18px;
                opacity: 0.9;
            }
            
            .contact-bar {
                display: flex;
                justify-content: center;
                flex-wrap: wrap;
                gap: 20px 30px;
            }
            
            .contact-item {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 14px;
            }
            
            .contact-icon {
                width: 16px;
                text-align: center;
            }
            
            /* Portfolio wrapper */
            .portfolio-wrapper {
                padding: 30px;
                background-color: white;
                border-radius: 0 0 8px 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            }
            
            /* About section */
            .about-section {
                margin-bottom: 40px;
            }
            
            .section-title {
                font-size: 22px;
                font-weight: 600;
                color: var(--primary);
                margin-bottom: 20px;
                text-align: center;
                position: relative;
            }
            
            .section-title::after {
                content: '';
                display: block;
                width: 50px;
                height: 3px;
                background-color: var(--primary);
                margin: 10px auto 0;
            }
            
            .about-content {
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            
            .summary {
                line-height: var(--line-height);
            }
            
            .subsection-title {
                font-size: 18px;
                font-weight: 600;
                color: var(--text);
                margin-bottom: 15px;
            }
            
            /* Skills area */
            .skills-area {
                margin-top: 20px;
            }
            
            .skills-container {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
            }
            
            .skill-tag {
                background-color: var(--primary);
                color: white;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 14px;
                opacity: 0.8;
                transition: all 0.2s;
            }
            
            .skill-tag:hover {
                opacity: 1;
                transform: translateY(-2px);
            }
            
            /* Projects section */
            .projects-section {
                margin-bottom: 40px;
            }
            
            .projects-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
            }
            
            .project-card {
                background-color: #f9fafb;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
                transition: all 0.3s;
            }
            
            .project-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
            }
            
            .project-card-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            
            .project-title {
                font-size: 18px;
                font-weight: 600;
                color: var(--primary);
            }
            
            .project-link {
                color: var(--text-light);
                text-decoration: none;
                font-size: 16px;
            }
            
            .project-tech {
                display: flex;
                flex-wrap: wrap;
                gap: 5px;
                margin-bottom: 15px;
            }
            
            .tech-tag {
                background-color: rgba(0, 0, 0, 0.05);
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 13px;
                color: var(--text-light);
            }
            
            .project-description {
                font-size: 14px;
                line-height: 1.5;
            }
            
            /* Dual column section */
            .dual-column-section {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 30px;
                margin-bottom: 40px;
            }
            
            /* Experience column */
            .experience-item {
                margin-bottom: 25px;
            }
            
            .exp-header {
                margin-bottom: 10px;
            }
            
            .job-title {
                font-size: 18px;
                font-weight: 600;
                color: var(--primary);
                margin-bottom: 2px;
            }
            
            .job-duration {
                font-size: 14px;
                color: var(--text-light);
            }
            
            .company-name {
                font-size: 16px;
                color: var(--text);
                margin-bottom: 10px;
            }
            
            .job-duties {
                padding-left: 20px;
            }
            
            .job-duties li {
                margin-bottom: 5px;
            }
            
            /* Education and Certifications */
            .education-item {
                margin-bottom: 20px;
            }
            
            .edu-header {
                margin-bottom: 5px;
            }
            
            .degree {
                font-size: 18px;
                font-weight: 600;
                color: var(--primary);
                margin-bottom: 2px;
            }
            
            .education-date {
                font-size: 14px;
                color: var(--text-light);
            }
            
            .school {
                font-size: 16px;
                color: var(--text);
                margin-bottom: 5px;
            }
            
            .certifications-title, .languages-title {
                margin-top: 30px;
            }
            
            .certifications-list {
                padding-left: 20px;
            }
            
            .cert-item {
                margin-bottom: 5px;
            }
            
            .languages-container {
                margin-top: 10px;
            }
            
            /* Awards section */
            .awards-section {
                margin-bottom: 30px;
            }
            
            .awards-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
            }
            
            .award-item {
                display: flex;
                background-color: #f9fafb;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }
            
            .award-icon {
                font-size: 24px;
                color: var(--accent);
                margin-right: 15px;
                display: flex;
                align-items: center;
            }
            
            .award-content {
                flex: 1;
            }
            
            .award-title {
                font-size: 16px;
                font-weight: 600;
                color: var(--text);
                margin-bottom: 5px;
            }
            
            .award-meta {
                font-size: 14px;
                color: var(--text-light);
                margin-bottom: 8px;
            }
            
            .award-description {
                font-size: 14px;
            }
            
            @media (max-width: 768px) {
                .dual-column-section {
                    grid-template-columns: 1fr;
                    gap: 20px;
                }
                
                .projects-grid, .awards-grid {
                    grid-template-columns: 1fr;
                }
            }
        """
    },
    "compact": {
        "name": "One-Page Compact",
        "description": "Compact layout designed to fit everything on one page",
        "template": "compact.html",
        "css": """
            .resume-container {
                max-width: 800px;
                margin: 0 auto;
                font-family: var(--font-family);
                color: var(--text);
                background-color: var(--background);
                font-size: 0.9em;
                padding: 20px;
            }
            
            /* Compact header */
            .compact-header {
                border-bottom: 2px solid var(--primary);
                padding-bottom: 10px;
                margin-bottom: 15px;
                display: flex;
                flex-direction: column;
                gap: 5px;
            }
            
            .name-title {
                display: flex;
                justify-content: space-between;
                align-items: baseline;
            }
            
            .name {
                font-size: 24px;
                font-weight: 700;
                color: var(--primary);
            }
            
            .title {
                font-size: 15px;
                color: var(--text-light);
            }
            
            .contact-info {
                display: flex;
                flex-wrap: wrap;
                gap: 10px 15px;
                font-size: 12px;
            }
            
            .contact-item:not(:last-child)::after {
                content: '•';
                margin-left: 15px;
                color: var(--text-light);
            }
            
            /* Compact layout */
            .compact-content {
                display: grid;
                grid-template-columns: 3fr 2fr;
                gap: 15px;
            }
            
            .compact-main {
                grid-column: 1;
            }
            
            .compact-sidebar {
                grid-column: 2;
                font-size: 0.95em;
            }
            
            /* Compact sections */
            .compact-section {
                margin-bottom: 15px;
            }
            
            .compact-title {
                font-size: 16px;
                font-weight: 600;
                color: var(--primary);
                border-bottom: 1px solid var(--border);
                padding-bottom: 5px;
                margin-bottom: 10px;
            }
            
            .compact-summary {
                font-size: 13px;
                line-height: 1.5;
                margin-bottom: 10px;
            }
            
            /* Compact items */
            .compact-item {
                margin-bottom: 12px;
            }
            
            .compact-header {
                display: flex;
                justify-content: space-between;
                align-items: baseline;
                margin-bottom: 3px;
            }
            
            .item-title {
                font-size: 14px;
                font-weight: 600;
                color: var(--text);
            }
            
            .small-title {
                font-size: 13px;
            }
            
            .item-date {
                font-size: 12px;
                color: var(--text-light);
            }
            
            .item-subtitle {
                font-size: 13px;
                color: var(--text-light);
                margin-bottom: 5px;
            }
            
            .compact-description {
                font-size: 12px;
                margin-top: 5px;
            }
            
            /* List styles */
            .compact-list {
                padding-left: 20px;
                margin-top: 5px;
                font-size: 12px;
            }
            
            .compact-list li {
                margin-bottom: 3px;
            }
            
            /* Tag styles */
            .compact-tags {
                display: flex;
                flex-wrap: wrap;
                gap: 5px;
                margin-top: 5px;
            }
            
            .compact-tag {
                background-color: #f1f5f9;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 11px;
                color: var(--text);
            }
            
            .compact-skills {
                margin-bottom: 0;
            }
            
            .project-link {
                font-size: 12px;
                color: var(--primary);
                text-decoration: none;
            }
            
            @media print {
                .resume-container {
                    padding: 0;
                    max-width: 100%;
                }
                
                body {
                    font-size: 11pt;
                }
            }
            
            @media (max-width: 768px) {
                .compact-content {
                    grid-template-columns: 1fr;
                }
                
                .compact-main, .compact-sidebar {
                    grid-column: 1;
                }
            }
        """
    }
}

def generate_resume(theme_id, layout_id,resume_data=None):
    """Generate a resume with specified theme and layout."""

    TEMPLATE_DIR = "./pages/templates"
    # Get theme and layout
    if theme_id not in THEMES:
        raise ValueError(f"Theme '{theme_id}' not found. Available themes: {', '.join(THEMES.keys())}")
    
    if layout_id not in LAYOUTS:
        raise ValueError(f"Layout '{layout_id}' not found. Available layouts: {', '.join(LAYOUTS.keys())}")
    
    theme = THEMES[theme_id]
    layout = LAYOUTS[layout_id]
    
    # Create environment and load template
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(f"{layout_id}.html")
    
    # Render template
    html_content = template.render(
        theme=theme,
        layout_css=layout["css"],
        resume=resume_data
    )
    
    return html_content