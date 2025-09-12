"""
Resume policy compliance and guardrails.
Handles age discrimination prevention and content quality controls.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass

from schemas import OptimizedResume, ExperienceItem


@dataclass
class PolicyViolation:
    """Represents a policy violation found in resume content."""
    type: str  # 'age_signal', 'contact_placement', 'inappropriate_content'
    severity: str  # 'error', 'warning', 'info'
    location: str  # Where the violation was found
    original_text: str
    suggested_fix: str
    reason: str


class AgeSignalScrubber:
    """Detects and removes age-related signals from resumes."""
    
    # Patterns that might indicate age
    AGE_PATTERNS = [
        # Graduation years
        r'\b(graduated|graduation|degree|bachelor|master|phd|ba|bs|ma|ms)\s+.*?(19\d{2}|20[0-1]\d)\b',
        r'\b(19\d{2}|20[0-1]\d)\s*[-–—]\s*(bachelor|master|degree|graduation|ba|bs|ma|ms)\b',
        
        # Experience duration signals
        r'\b(\d{2,})\s*\+?\s*(years?)\s+(of\s+)?(experience|exp)\b',
        r'\b(over|more than|above)\s+(\d{2,})\s*(years?)\b',
        r'\b(\d{2,})\s*(years?)\s+(in|of|with)\s+(industry|field|experience)\b',
        
        # Career milestone years
        r'\bstarted\s+(career|working)\s+in\s+(19\d{2}|20[0-1]\d)\b',
        r'\bsince\s+(19\d{2}|20[0-1]\d)\b',
        
        # Technology vintage signals
        r'\b(early|original|initial)\s+(adopter|user|implementer)\s+of\b',
        r'\bpioneer(ed)?\s+(in|with)\b',
        r'\bwhen\s+\w+\s+(was\s+)?(new|emerging|first\s+introduced)\b'
    ]
    
    # Years experience thresholds
    CURRENT_YEAR = datetime.now().year
    MAX_GRADUATION_AGE = 15  # Don't show graduation years older than 15 years
    MAX_EXPERIENCE_YEARS = 20  # Cap experience descriptions at 20 years
    
    @classmethod
    def detect_age_signals(cls, text: str) -> List[PolicyViolation]:
        """
        Detect age-related signals in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of PolicyViolation objects
        """
        
        violations = []
        
        for pattern in cls.AGE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                matched_text = match.group(0)
                
                # Check if it's a problematic graduation year
                if any(year_word in matched_text.lower() for year_word in ['graduated', 'degree', 'bachelor', 'master']):
                    # Extract year
                    year_match = re.search(r'(19\d{2}|20[0-1]\d)', matched_text)
                    if year_match:
                        year = int(year_match.group(1))
                        years_ago = cls.CURRENT_YEAR - year
                        
                        if years_ago > cls.MAX_GRADUATION_AGE:
                            violations.append(PolicyViolation(
                                type='age_signal',
                                severity='warning',
                                location=f"Character {match.start()}-{match.end()}",
                                original_text=matched_text,
                                suggested_fix=re.sub(r'\b(19\d{2}|20[0-1]\d)\b', '', matched_text).strip(),
                                reason=f"Graduation year {year} indicates age ({years_ago} years ago)"
                            ))
                
                # Check for excessive experience years
                exp_match = re.search(r'(\d{2,})\s*\+?\s*(years?)', matched_text, re.IGNORECASE)
                if exp_match:
                    years = int(exp_match.group(1))
                    if years > cls.MAX_EXPERIENCE_YEARS:
                        violations.append(PolicyViolation(
                            type='age_signal',
                            severity='warning',
                            location=f"Character {match.start()}-{match.end()}",
                            original_text=matched_text,
                            suggested_fix=matched_text.replace(f"{years}+", "extensive").replace(f"{years}", "extensive"),
                            reason=f"{years}+ years of experience may indicate age"
                        ))
        
        return violations
    
    @classmethod
    def scrub_age_signals(cls, text: str, strict_mode: bool = False) -> Tuple[str, List[str]]:
        """
        Remove age signals from text.
        
        Args:
            text: Text to scrub
            strict_mode: If True, removes more aggressively
            
        Returns:
            Tuple of (scrubbed_text, list_of_changes_made)
        """
        
        scrubbed = text
        changes_made = []
        
        # Remove graduation years older than threshold
        def replace_old_graduation(match):
            year_match = re.search(r'(19\d{2}|20[0-1]\d)', match.group(0))
            if year_match:
                year = int(year_match.group(1))
                years_ago = cls.CURRENT_YEAR - year
                if years_ago > cls.MAX_GRADUATION_AGE:
                    changes_made.append(f"Removed graduation year {year}")
                    return re.sub(r'\b(19\d{2}|20[0-1]\d)\b', '', match.group(0)).strip()
            return match.group(0)
        
        for pattern in cls.AGE_PATTERNS[:2]:  # Just graduation patterns
            scrubbed = re.sub(pattern, replace_old_graduation, scrubbed, flags=re.IGNORECASE)
        
        # Replace excessive years of experience
        def replace_excessive_experience(match):
            exp_match = re.search(r'(\d{2,})\s*\+?\s*(years?)', match.group(0), re.IGNORECASE)
            if exp_match:
                years = int(exp_match.group(1))
                if years > cls.MAX_EXPERIENCE_YEARS:
                    changes_made.append(f"Replaced '{years}+ years' with 'extensive'")
                    return match.group(0).replace(f"{years}+", "extensive").replace(f"{years}", "extensive")
            return match.group(0)
        
        # Apply experience scrubbing
        for pattern in cls.AGE_PATTERNS[2:5]:  # Experience patterns
            scrubbed = re.sub(pattern, replace_excessive_experience, scrubbed, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        scrubbed = re.sub(r'\s+', ' ', scrubbed).strip()
        
        return scrubbed, changes_made


class ContactInfoValidator:
    """Validates proper placement of contact information."""
    
    CONTACT_PATTERNS = [
        r'\b[\w\.-]+@[\w\.-]+\.\w+\b',  # Email
        r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',  # Phone
        r'\b\d{3}[-.\s]\d{2}[-.\s]\d{4}\b',  # SSN-like patterns (should be removed)
        r'\b\d{4}\s+\w+\s+(street|st|avenue|ave|road|rd|drive|dr|lane|ln)\b'  # Address
    ]
    
    @classmethod
    def validate_contact_placement(cls, resume_sections: Dict[str, str]) -> List[PolicyViolation]:
        """
        Ensure contact info only appears in header/contact section.
        
        Args:
            resume_sections: Parsed resume sections
            
        Returns:
            List of contact placement violations
        """
        
        violations = []
        
        # Contact info should only be in header/summary, not in experience/skills
        prohibited_sections = ['experience', 'skills', 'education']
        
        for section_name, section_text in resume_sections.items():
            if section_name in prohibited_sections:
                
                for pattern in cls.CONTACT_PATTERNS:
                    matches = re.finditer(pattern, section_text, re.IGNORECASE)
                    
                    for match in matches:
                        matched_text = match.group(0)
                        
                        # Skip if it's clearly not contact info (e.g., technical terms)
                        if '@' in matched_text and any(domain in matched_text.lower() for domain in ['github', 'linkedin', 'stackoverflow']):
                            continue  # Professional profiles are OK
                        
                        violations.append(PolicyViolation(
                            type='contact_placement',
                            severity='warning',
                            location=f"{section_name} section",
                            original_text=matched_text,
                            suggested_fix=f"Move to header section",
                            reason=f"Contact information should not appear in {section_name} section"
                        ))
        
        return violations


class ResumeGuardrails:
    """Complete resume policy compliance system."""
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.scrubber = AgeSignalScrubber()
        self.contact_validator = ContactInfoValidator()
    
    def apply_guardrails(self, optimized_resume: OptimizedResume) -> Tuple[OptimizedResume, List[PolicyViolation]]:
        """
        Apply all policy guardrails to optimized resume.
        
        Args:
            optimized_resume: LLM-generated resume
            
        Returns:
            Tuple of (cleaned_resume, violations_found)
        """
        
        print("🛡️  Applying policy guardrails...")
        
        violations = []
        
        # 1. Scrub age signals from summary
        if optimized_resume.summary:
            scrubbed_summary, summary_changes = self.scrubber.scrub_age_signals(
                optimized_resume.summary, self.strict_mode
            )
            optimized_resume.summary = scrubbed_summary
            
            for change in summary_changes:
                violations.append(PolicyViolation(
                    type='age_signal',
                    severity='info',
                    location='summary',
                    original_text=change,
                    suggested_fix='Removed',
                    reason='Age signal removal for legal compliance'
                ))
        
        # 2. Scrub age signals from experience bullets
        for exp_item in optimized_resume.experience:
            cleaned_bullets = []
            for bullet in exp_item.bullets:
                scrubbed_bullet, bullet_changes = self.scrubber.scrub_age_signals(
                    bullet, self.strict_mode
                )
                cleaned_bullets.append(scrubbed_bullet)
                
                for change in bullet_changes:
                    violations.append(PolicyViolation(
                        type='age_signal',
                        severity='info',
                        location=f"{exp_item.company} - {exp_item.role}",
                        original_text=change,
                        suggested_fix='Sanitized',
                        reason='Age signal removal for legal compliance'
                    ))
            
            exp_item.bullets = cleaned_bullets
        
        print(f"✅ Guardrails applied. {len(violations)} violations addressed.")
        
        return optimized_resume, violations


# Sync wrapper
def apply_guardrails_sync(optimized_resume: OptimizedResume) -> Tuple[OptimizedResume, List[PolicyViolation]]:
    """Synchronous wrapper for apply_guardrails."""
    guardrails = ResumeGuardrails()
    return guardrails.apply_guardrails(optimized_resume)




class TransparentScoring:
    """Transparent match scoring system with detailed breakdown."""
    
    # Scoring weights for different factors
    SCORING_WEIGHTS = {
        'keyword_coverage': 0.35,      # Most important for ATS
        'semantic_similarity': 0.25,   # Important for human reviewers
        'experience_relevance': 0.20,  # Job-specific experience
        'skills_alignment': 0.15,      # Technical skills match
        'resume_completeness': 0.05    # Structure and completeness
    }
    
    @classmethod
    def calculate_match_score(
        cls,
        keyword_analysis: Dict[str, Any],
        semantic_analysis: Dict[str, Any],
        gap_analysis: Dict[str, Any],
        resume_sections: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive match score with detailed breakdown.
        
        Args:
            keyword_analysis: Keyword gap analysis results
            semantic_analysis: Semantic similarity results  
            gap_analysis: Complete gap analysis
            resume_sections: Parsed resume sections
            
        Returns:
            Detailed scoring breakdown
        """
        
        print("📊 Calculating transparent match score...")
        
        # 1. Keyword Coverage Score (0.0 - 1.0)
        keyword_score = keyword_analysis.get('coverage_score', 0.0)
        
        # 2. Semantic Similarity Score (0.0 - 1.0)
        semantic_score = semantic_analysis.get('semantic_similarity', 0.0)
        
        # 3. Experience Relevance Score
        experience_score = cls._calculate_experience_relevance(
            semantic_analysis.get('strong_matches', []),
            semantic_analysis.get('weak_matches', []),
            semantic_analysis.get('total_chunks_analyzed', 1)
        )
        
        # 4. Skills Alignment Score
        skills_score = cls._calculate_skills_alignment(
            keyword_analysis.get('matched_keywords', []),
            keyword_analysis.get('missing_keywords', []),
            keyword_analysis.get('importance_map', {})
        )
        
        # 5. Resume Completeness Score
        completeness_score = cls._calculate_completeness(resume_sections)
        
        # Calculate weighted overall score
        weighted_scores = {
            'keyword_coverage': keyword_score * cls.SCORING_WEIGHTS['keyword_coverage'],
            'semantic_similarity': semantic_score * cls.SCORING_WEIGHTS['semantic_similarity'],
            'experience_relevance': experience_score * cls.SCORING_WEIGHTS['experience_relevance'],
            'skills_alignment': skills_score * cls.SCORING_WEIGHTS['skills_alignment'],
            'resume_completeness': completeness_score * cls.SCORING_WEIGHTS['resume_completeness']
        }
        
        overall_score = sum(weighted_scores.values())
        
        # Generate score interpretation
        interpretation = cls._interpret_score(overall_score)
        
        # Create detailed breakdown
        score_breakdown = {
            'overall_score': round(overall_score, 3),
            'score_letter_grade': cls._score_to_letter_grade(overall_score),
            'interpretation': interpretation,
            'component_scores': {
                'keyword_coverage': {
                    'raw_score': round(keyword_score, 3),
                    'weighted_score': round(weighted_scores['keyword_coverage'], 3),
                    'weight': cls.SCORING_WEIGHTS['keyword_coverage'],
                    'description': 'How well your resume matches required keywords'
                },
                'semantic_similarity': {
                    'raw_score': round(semantic_score, 3),
                    'weighted_score': round(weighted_scores['semantic_similarity'], 3),
                    'weight': cls.SCORING_WEIGHTS['semantic_similarity'],
                    'description': 'How conceptually similar your experience is to the job'
                },
                'experience_relevance': {
                    'raw_score': round(experience_score, 3),
                    'weighted_score': round(weighted_scores['experience_relevance'], 3),
                    'weight': cls.SCORING_WEIGHTS['experience_relevance'],
                    'description': 'How relevant your specific work experience is'
                },
                'skills_alignment': {
                    'raw_score': round(skills_score, 3),
                    'weighted_score': round(weighted_scores['skills_alignment'], 3),
                    'weight': cls.SCORING_WEIGHTS['skills_alignment'],
                    'description': 'How well your technical skills match requirements'
                },
                'resume_completeness': {
                    'raw_score': round(completeness_score, 3),
                    'weighted_score': round(weighted_scores['resume_completeness'], 3),
                    'weight': cls.SCORING_WEIGHTS['resume_completeness'],
                    'description': 'How complete and well-structured your resume is'
                }
            },
            'improvement_potential': {
                'max_possible_score': 1.0,
                'current_score': round(overall_score, 3),
                'improvement_points': round(1.0 - overall_score, 3),
                'biggest_opportunity': max(weighted_scores.keys(), key=lambda k: cls.SCORING_WEIGHTS[k] - weighted_scores[k])
            }
        }
        
        print(f"✅ Match score calculated: {overall_score:.2f} ({cls._score_to_letter_grade(overall_score)})")
        
        return score_breakdown
    
    @classmethod
    def _calculate_experience_relevance(
        cls, 
        strong_matches: List[Any], 
        weak_matches: List[Any], 
        total_chunks: int
    ) -> float:
        """Calculate how relevant work experience is to the job."""
        
        if total_chunks == 0:
            return 0.0
        
        # Strong matches count more than weak matches
        strong_weight = 1.0
        weak_weight = 0.3
        
        relevance_score = (
            (len(strong_matches) * strong_weight + len(weak_matches) * weak_weight) / 
            total_chunks
        )
        
        return min(1.0, relevance_score)
    
    @classmethod
    def _calculate_skills_alignment(
        cls,
        matched_keywords: List[str],
        missing_keywords: List[str], 
        importance_map: Dict[str, str]
    ) -> float:
        """Calculate how well technical skills align with requirements."""
        
        total_keywords = len(matched_keywords) + len(missing_keywords)
        if total_keywords == 0:
            return 1.0
        
        # Weight by importance
        matched_weight = 0
        total_weight = 0
        
        weights = {'critical': 3, 'important': 2, 'nice-to-have': 1}
        
        for keyword in matched_keywords:
            importance = importance_map.get(keyword.lower(), 'nice-to-have')
            weight = weights[importance]
            matched_weight += weight
            total_weight += weight
        
        for keyword in missing_keywords:
            importance = importance_map.get(keyword.lower(), 'nice-to-have')
            weight = weights[importance]
            total_weight += weight
        
        return matched_weight / total_weight if total_weight > 0 else 0.0
    
    @classmethod
    def _calculate_completeness(cls, resume_sections: Dict[str, str]) -> float:
        """Calculate how complete the resume structure is."""
        
        expected_sections = ['summary', 'experience', 'skills']
        optional_sections = ['education', 'projects', 'certifications']
        
        # Required sections
        required_score = sum(1 for section in expected_sections if section in resume_sections) / len(expected_sections)
        
        # Optional sections bonus
        optional_score = sum(1 for section in optional_sections if section in resume_sections) / len(optional_sections)
        
        # Weight: 80% required, 20% optional
        completeness = (required_score * 0.8) + (optional_score * 0.2)
        
        return min(1.0, completeness)
    
    @classmethod
    def _interpret_score(cls, score: float) -> Dict[str, str]:
        """Provide human-readable interpretation of score."""
        
        if score >= 0.9:
            return {
                'level': 'Excellent Match',
                'description': 'Your resume is an excellent match for this position',
                'advice': 'This resume should perform very well with ATS systems and hiring managers',
                'color': 'green'
            }
        elif score >= 0.75:
            return {
                'level': 'Good Match', 
                'description': 'Your resume is a good match with room for improvement',
                'advice': 'Consider adding a few more relevant keywords to strengthen your match',
                'color': 'blue'
            }
        elif score >= 0.6:
            return {
                'level': 'Fair Match',
                'description': 'Your resume shows some alignment but needs enhancement',
                'advice': 'Focus on adding missing skills and strengthening relevant experience',
                'color': 'yellow'
            }
        elif score >= 0.4:
            return {
                'level': 'Weak Match',
                'description': 'Your resume has limited alignment with this position',
                'advice': 'Significant optimization needed to improve chances with ATS systems',
                'color': 'orange'
            }
        else:
            return {
                'level': 'Poor Match',
                'description': 'Your resume does not align well with this position',
                'advice': 'Consider whether this role matches your background, or create a specialized resume',
                'color': 'red'
            }
    
    @classmethod
    def _score_to_letter_grade(cls, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 0.9:
            return 'A'
        elif score >= 0.8:
            return 'B+'
        elif score >= 0.7:
            return 'B'
        elif score >= 0.6:
            return 'C+'
        elif score >= 0.5:
            return 'C'
        elif score >= 0.4:
            return 'D'
        else:
            return 'F'


# Convenience function
def score_resume_match(
    keyword_analysis: Dict[str, Any],
    semantic_analysis: Dict[str, Any],
    gap_analysis: Dict[str, Any],
    resume_sections: Dict[str, str]
) -> Dict[str, Any]:
    """
    Score resume match with transparent breakdown.
    
    Returns:
        Complete scoring analysis
    """
    return TransparentScoring.calculate_match_score(
        keyword_analysis, semantic_analysis, gap_analysis, resume_sections
    )