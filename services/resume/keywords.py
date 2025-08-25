"""
Keyword extraction and skill matching utilities.
Curated allowlist of technical skills and keyword extraction logic.
"""

import re
from typing import List, Set, Dict, Tuple
from dataclasses import dataclass


@dataclass
class KeywordMatch:
    """Represents a matched keyword with context."""
    keyword: str
    category: str
    frequency: int
    contexts: List[str]  # Sentences where keyword appears
    importance: str  # 'critical', 'important', 'nice-to-have'


class TechnicalSkills:
    """Curated allowlist of technical skills organized by category."""
    
    # Programming Languages
    LANGUAGES = {
        'python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'go', 'rust', 
        'php', 'ruby', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql', 'html', 
        'css', 'sass', 'less', 'jsx', 'tsx'
    }
    
    # Frameworks & Libraries
    FRAMEWORKS = {
        'react', 'angular', 'vue', 'svelte', 'nextjs', 'nuxt', 'gatsby',
        'flask', 'django', 'fastapi', 'express', 'nest', 'spring', 'laravel',
        'rails', 'asp.net', 'blazor', 'xamarin', 'flutter', 'react native',
        'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy', 'matplotlib'
    }
    
    # Cloud & Infrastructure
    CLOUD = {
        'aws', 'azure', 'gcp', 'google cloud', 'digitalocean', 'heroku', 'vercel',
        'docker', 'kubernetes', 'k8s', 'terraform', 'ansible', 'jenkins', 'gitlab ci',
        'github actions', 'circleci', 'travis ci', 'helm', 'istio', 'consul'
    }
    
    # Databases
    DATABASES = {
        'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
        'dynamodb', 'sqlite', 'oracle', 'sql server', 'mariadb', 'neo4j',
        'influxdb', 'clickhouse', 'bigquery', 'snowflake', 'redshift'
    }
    
    # DevOps & Tools
    DEVOPS = {
        'git', 'github', 'gitlab', 'bitbucket', 'jira', 'confluence', 'slack',
        'ci/cd', 'cicd', 'automation', 'monitoring', 'logging', 'prometheus',
        'grafana', 'elk stack', 'splunk', 'datadog', 'new relic', 'sentry'
    }
    
    # Data & Analytics
    DATA = {
        'etl', 'data pipeline', 'data warehouse', 'data lake', 'spark', 'hadoop',
        'airflow', 'kafka', 'rabbitmq', 'power bi', 'tableau', 'looker',
        'analytics', 'machine learning', 'ml', 'ai', 'nlp', 'computer vision'
    }
    
    # Security & Compliance
    SECURITY = {
        'oauth', 'jwt', 'ssl', 'tls', 'encryption', 'security', 'penetration testing',
        'vulnerability assessment', 'soc2', 'pci', 'gdpr', 'hipaa', 'iso27001',
        'cybersecurity', 'authentication', 'authorization', 'firewall'
    }
    
    # Methodologies
    METHODOLOGIES = {
        'agile', 'scrum', 'kanban', 'lean', 'devops', 'tdd', 'bdd', 'pair programming',
        'code review', 'design patterns', 'microservices', 'api design', 'rest',
        'graphql', 'grpc', 'websockets', 'serverless', 'event-driven'
    }
    
    @classmethod
    def get_all_skills(cls) -> Set[str]:
        """Get all curated technical skills."""
        return (cls.LANGUAGES | cls.FRAMEWORKS | cls.CLOUD | cls.DATABASES | 
                cls.DEVOPS | cls.DATA | cls.SECURITY | cls.METHODOLOGIES)
    
    @classmethod
    def get_category_skills(cls, category: str) -> Set[str]:
        """Get skills for a specific category."""
        category_map = {
            'languages': cls.LANGUAGES,
            'frameworks': cls.FRAMEWORKS,
            'cloud': cls.CLOUD,
            'databases': cls.DATABASES,
            'devops': cls.DEVOPS,
            'data': cls.DATA,
            'security': cls.SECURITY,
            'methodologies': cls.METHODOLOGIES
        }
        return category_map.get(category.lower(), set())
    
    @classmethod
    def categorize_skill(cls, skill: str) -> str:
        """Get the category for a specific skill."""
        skill_lower = skill.lower()
        
        if skill_lower in cls.LANGUAGES:
            return 'languages'
        elif skill_lower in cls.FRAMEWORKS:
            return 'frameworks'
        elif skill_lower in cls.CLOUD:
            return 'cloud'
        elif skill_lower in cls.DATABASES:
            return 'databases'
        elif skill_lower in cls.DEVOPS:
            return 'devops'
        elif skill_lower in cls.DATA:
            return 'data'
        elif skill_lower in cls.SECURITY:
            return 'security'
        elif skill_lower in cls.METHODOLOGIES:
            return 'methodologies'
        else:
            return 'other'


def extract_keywords_from_text(text: str, importance_weights: Dict[str, str] = None) -> List[KeywordMatch]:
    """
    Extract technical keywords from text using curated allowlist.
    
    Args:
        text: Text to analyze
        importance_weights: Optional mapping of keywords to importance levels
        
    Returns:
        List of KeywordMatch objects
    """
    
    if not text:
        return []
    
    text_lower = text.lower()
    sentences = text.split('.')
    all_skills = TechnicalSkills.get_all_skills()
    matches = []
    
    for skill in all_skills:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        skill_matches = re.finditer(pattern, text_lower)
        
        match_positions = list(skill_matches)
        if match_positions:
            # Find contexts (sentences containing the skill)
            contexts = []
            for sentence in sentences:
                if skill.lower() in sentence.lower():
                    contexts.append(sentence.strip())
            
            # Determine importance
            importance = 'nice-to-have'
            if importance_weights and skill.lower() in importance_weights:
                importance = importance_weights[skill.lower()]
            elif len(match_positions) >= 3:
                importance = 'important'
            elif any(critical_word in text_lower for critical_word in ['required', 'must have', 'essential']):
                importance = 'critical'
            
            match = KeywordMatch(
                keyword=skill,
                category=TechnicalSkills.categorize_skill(skill),
                frequency=len(match_positions),
                contexts=contexts[:3],  # Keep top 3 contexts
                importance=importance
            )
            matches.append(match)
    
    # Sort by frequency (most mentioned first)
    matches.sort(key=lambda x: x.frequency, reverse=True)
    
    return matches


def extract_jd_requirements(jd_text: str) -> Tuple[List[str], Dict[str, str]]:
    """
    Extract requirements from job description with importance classification.
    
    Args:
        jd_text: Job description text
        
    Returns:
        Tuple of (required_skills, importance_map)
    """
    
    # Extract keywords
    keyword_matches = extract_keywords_from_text(jd_text)
    
    # Classify importance based on JD language
    importance_map = {}
    critical_phrases = ['required', 'must have', 'essential', 'mandatory']
    important_phrases = ['preferred', 'desired', 'experience with', 'knowledge of']
    
    jd_lower = jd_text.lower()
    
    for match in keyword_matches:
        skill_lower = match.keyword.lower()
        
        # Check context around skill mentions
        for context in match.contexts:
            context_lower = context.lower()
            
            if any(phrase in context_lower for phrase in critical_phrases):
                importance_map[skill_lower] = 'critical'
                break
            elif any(phrase in context_lower for phrase in important_phrases):
                importance_map[skill_lower] = 'important'
            else:
                importance_map[skill_lower] = 'nice-to-have'
    
    required_skills = [match.keyword for match in keyword_matches]
    
    return required_skills, importance_map


def calculate_skill_coverage(
    resume_keywords: List[str], 
    jd_keywords: List[str],
    importance_map: Dict[str, str] = None
) -> Dict[str, any]:
    """
    Calculate how well resume covers job description requirements.
    
    Args:
        resume_keywords: Keywords found in resume
        jd_keywords: Keywords found in job description  
        importance_map: Importance levels for keywords
        
    Returns:
        Coverage analysis dictionary
    """
    
    if not importance_map:
        importance_map = {}
    
    resume_set = {kw.lower() for kw in resume_keywords}
    jd_set = {kw.lower() for kw in jd_keywords}
    
    # Find matches and gaps
    matched = resume_set & jd_set
    missing = jd_set - resume_set
    
    # Calculate weighted score
    total_weight = 0
    matched_weight = 0
    
    weights = {'critical': 3, 'important': 2, 'nice-to-have': 1}
    
    for keyword in jd_set:
        importance = importance_map.get(keyword, 'nice-to-have')
        weight = weights[importance]
        total_weight += weight
        
        if keyword in matched:
            matched_weight += weight
    
    coverage_score = matched_weight / total_weight if total_weight > 0 else 0.0
    
    return {
        'matched_keywords': list(matched),
        'missing_keywords': list(missing),
        'coverage_score': round(coverage_score, 3),
        'total_jd_keywords': len(jd_set),
        'matched_count': len(matched),
        'critical_missing': [kw for kw in missing if importance_map.get(kw) == 'critical'],
        'weights_used': importance_map
    }