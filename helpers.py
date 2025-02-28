import requests

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