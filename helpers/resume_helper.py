import spacy
from .themes_helper import generate_theme_css,get_theme
from .layouts_helper import get_layout
from jinja2 import  FileSystemLoader
from flask import Flask,request,render_template,jsonify,current_app
from io import BytesIO
from weasyprint import HTML, CSS
import os

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


def generate_resume(app,resume,is_preview=False):
    try:
  
        layout = get_layout(resume.layout_id)
  
        theme = get_theme(resume.theme_id)
        theme_css = generate_theme_css(theme)

        #Get path to the layout-specific CSS
        css_path = os.path.join(app.static_folder, layout['css_file'].replace('static/', ''))
    
        if not os.path.exists(css_path):
                raise FileNotFoundError(f"CSS file not found: {css_path}")
        with open(css_path, 'r') as f:
            layout_css = f.read()

        # Combine layout and theme CSS
        full_css = layout_css + "\n" + theme_css
   
        # Validate resume_data
        if not isinstance(resume.resume_data, dict) or 'sections' not in resume.resume_data:
            raise ValueError("Invalid resume_data: 'sections' key missing")

        # Get template
        template = app.jinja_env.get_template(layout['template'])
  
        # Render template
        html_content = template.render(
            theme=theme,
            css_content=full_css,
            resume=resume.resume_data,
            is_preview=is_preview
        )
        return html_content
    except Exception as e:
        print("from generate resume method")
        print(e)
        app.logger.error(f"Error generating resume: {str(e)}")
        raise


def generate_pdf(data,base_url):
    pdf_bytes = BytesIO()
    html = HTML(string=data,base_url=base_url)
    html.write_pdf(pdf_bytes)
    pdf_bytes.seek(0)
    return pdf_bytes
