from typing import Dict, List, Optional
import re

def enhance_resume_content(content: str, section: str, job_description: Optional[str] = None, enhancement_type: str = 'rewrite') -> str:
    """
    Enhance resume content with AI-powered suggestions and improvements.
    
    Args:
        content: The content to enhance
        section: The resume section being enhanced
        job_description: Optional job description for targeting
        enhancement_type: Type of enhancement to apply
        
    Returns:
        Enhanced content
    """
    if section == 'summary':
        if enhancement_type == 'rewrite':
            return improve_writing(content)
        elif enhancement_type == 'tailor':
            return tailor_to_job(content, job_description)
        elif enhancement_type == 'keywords':
            return add_keywords(content, job_description)
    elif section == 'experience':
        return enhance_experience(content, job_description)
    
    return content

def improve_writing(content: str) -> str:
    """
    Improve the writing style and clarity of the content.
    """
    # Remove redundant phrases
    content = re.sub(r'\b(I|me|my)\b', '', content, flags=re.IGNORECASE)
    
    # Add action verbs if missing
    action_verbs = [
        'developed', 'implemented', 'managed', 'led', 'created',
        'designed', 'built', 'improved', 'optimized', 'achieved'
    ]
    
    # Ensure sentences start with action verbs
    sentences = content.split('. ')
    enhanced_sentences = []
    
    for sentence in sentences:
        if sentence.strip():
            # Check if sentence starts with an action verb
            starts_with_action = any(
                sentence.lower().startswith(verb)
                for verb in action_verbs
            )
            
            if not starts_with_action:
                # Add an appropriate action verb
                sentence = f"Developed {sentence.lower()}"
            
            enhanced_sentences.append(sentence)
    
    return '. '.join(enhanced_sentences)

def tailor_to_job(content: str, job_description: Optional[str]) -> str:
    """
    Tailor the content to match job requirements.
    """
    if not job_description:
        return content
    
    # Extract key requirements from job description
    requirements = extract_keywords(job_description)
    
    # Ensure content includes key requirements
    enhanced_content = content
    for req in requirements:
        if req.lower() not in enhanced_content.lower():
            enhanced_content += f" Proficient in {req} with demonstrated experience."
    
    return enhanced_content

def add_keywords(content: str, job_description: Optional[str]) -> str:
    """
    Add relevant keywords from job description to the content.
    """
    if not job_description:
        return content
    
    # Extract keywords from job description
    keywords = extract_keywords(job_description)
    
    # Add missing keywords
    enhanced_content = content
    for keyword in keywords:
        if keyword.lower() not in enhanced_content.lower():
            enhanced_content += f" Experienced in {keyword}."
    
    return enhanced_content

def enhance_experience(content: str, job_description: Optional[str]) -> str:
    """
    Enhance work experience descriptions.
    """
    # Add metrics if missing
    if not re.search(r'\d+%|\d+\s*(million|thousand)', content):
        content += " Improved efficiency by 25% through process optimization."
    
    # Add impact statements if missing
    if not re.search(r'\b(increased|decreased|reduced|improved)\b', content, re.IGNORECASE):
        content += " Successfully delivered projects on time and within budget."
    
    return content

def extract_keywords(text: str) -> List[str]:
    """
    Extract important keywords from text.
    """
    # Common technical skills and keywords
    common_keywords = [
        'python', 'javascript', 'java', 'react', 'angular', 'vue',
        'node.js', 'django', 'flask', 'aws', 'azure', 'gcp',
        'docker', 'kubernetes', 'ci/cd', 'agile', 'scrum',
        'machine learning', 'ai', 'data science', 'sql', 'nosql',
        'rest api', 'graphql', 'microservices', 'devops'
    ]
    
    # Find keywords in text
    found_keywords = []
    text_lower = text.lower()
    
    for keyword in common_keywords:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    return found_keywords