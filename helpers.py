import requests
import spacy
import re
from collections import Counter

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