
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, NextPageTemplate, FrameBreak, PageBreak, BaseDocTemplate, Image
from reportlab.lib.units import inch, mm
from io import BytesIO
import json
import os
import copy

class ResumeDataValidator:
    """Validate and normalize resume data"""
    
    @staticmethod
    def validate(data):
        """Validate the resume data structure"""
        # Check required fields
        if 'contact' not in data:
            raise ValueError("Missing required 'contact' section")
        
        contact = data.get('contact', {})
        if not contact.get('name'):
            raise ValueError("Missing required 'name' in contact section")
        
        # Validate experience section if present
        if 'experience' in data:
            experience = data['experience']
            if isinstance(experience, list):
                for idx, exp in enumerate(experience):
                    if not exp.get('title'):
                        raise ValueError(f"Missing required 'title' in experience item {idx+1}")
                    if not exp.get('company'):
                        raise ValueError(f"Missing required 'company' in experience item {idx+1}")
            elif isinstance(experience, dict):
                if not experience.get('title'):
                    raise ValueError("Missing required 'title' in experience item")
                if not experience.get('company'):
                    raise ValueError("Missing required 'company' in experience item")
            else:
                raise ValueError("Experience must be a list or dictionary")
        
        # Validate education section if present
        if 'education' in data:
            education = data['education']
            if isinstance(education, list):
                for idx, edu in enumerate(education):
                    if not edu.get('degree'):
                        raise ValueError(f"Missing required 'degree' in education item {idx+1}")
                    if not edu.get('school'):
                        raise ValueError(f"Missing required 'school' in education item {idx+1}")
            elif isinstance(education, dict):
                if not education.get('degree'):
                    raise ValueError("Missing required 'degree' in education item")
                if not education.get('school'):
                    raise ValueError("Missing required 'school' in education item")
            else:
                raise ValueError("Education must be a list or dictionary")
        
        return True
    
    @staticmethod
    def normalize(data):
        """Normalize data to standard format"""
        normalized = {}
        
        # Normalize contact info
        contact = data.get('contact', {})
        normalized['contact'] = {
            'name': contact.get('name', ''),
            'title': contact.get('title', ''),
            'email': contact.get('email', ''),
            'phone': contact.get('phone', ''),
            'location': contact.get('location', '')
        }
        
        # Normalize experience
        experience = data.get('experience', [])
        if isinstance(experience, dict):
            experience = [experience]
        normalized['experience'] = experience
        
        # Normalize education
        education = data.get('education', [])
        if isinstance(education, dict):
            education = [education]
        normalized['education'] = education
        
        # Normalize skills
        skills = data.get('skills', [])
        if isinstance(skills, str):
            skills = [skill.strip() for skill in skills.split(',') if skill.strip()]
        normalized['skills'] = skills
        
        # Normalize summary
        summary = data.get('summary', '')
        if isinstance(summary, dict) and 'content' in summary:
            normalized['summary'] = summary
        else:
            normalized['summary'] = {'content': summary} if summary else ''
        
        # Copy other sections
        for key in data:
            if key not in normalized:
                normalized[key] = data[key]
        
        return normalized