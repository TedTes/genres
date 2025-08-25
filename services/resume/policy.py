"""
Resume policy compliance and guardrails.
Handles age discrimination prevention and content quality controls.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass

from .schemas import OptimizedResume, ExperienceItem


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