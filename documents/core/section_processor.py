
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, NextPageTemplate, FrameBreak, PageBreak, BaseDocTemplate, Image
from reportlab.lib.units import inch, mm
from io import BytesIO
import json
import os
import copy

class SectionProcessor:
    """Process different resume sections into flowables"""
    
    @staticmethod
    def process_experience(experience_data, styles):
        """Process experience section into flowables"""
        result = []
        # Add section title
        result.append(Paragraph("EXPERIENCE", styles['SectionHeading']))
        
        # Process each experience item
        for exp in experience_data:
            job_title = exp.get('title', '')
            company = exp.get('company', '')
            start_date = exp.get('startDate', '')
            end_date = exp.get('endDate', 'Present') if not exp.get('current', False) else 'Present'
            description = exp.get('description', '')
            
            job_heading = f"{job_title}, {company}"
            result.append(Paragraph(job_heading, styles['JobTitle']))
            result.append(Paragraph(f"{start_date} - {end_date}", styles['JobInfo']))
            
            # Add description as bullet points
            if description:
                for line in description.split('\n'):
                    if line.strip():
                        result.append(Paragraph(f"• {line.strip()}", styles['BulletPoint']))
                
                # Add a small space after each job
                result.append(Spacer(1, 10))
        
        return result
    
    @staticmethod
    def process_education(education_data, styles):
        """Process education section into flowables"""
        result = []
        # Add section title
        result.append(Paragraph("EDUCATION", styles['SectionHeading']))
        
        if isinstance(education_data, list):
            for edu in education_data:
                degree = edu.get('degree', '')
                school = edu.get('school', '')
                year = edu.get('year', '')
                
                result.append(Paragraph(degree, styles['JobTitle']))
                result.append(Paragraph(f"{school}, {year}", styles['JobInfo']))
                result.append(Spacer(1, 8))
        else:
            # Handle single education entry as dictionary
            degree = education_data.get('degree', '')
            school = education_data.get('school', '')
            year = education_data.get('year', '')
            
            result.append(Paragraph(degree, styles['JobTitle']))
            result.append(Paragraph(f"{school}, {year}", styles['JobInfo']))
        
        return result
    
    @staticmethod
    def process_skills(skills_data, styles):
        """Process skills section into flowables"""
        result = []
        # Add section title
        result.append(Paragraph("SKILLS", styles['SectionHeading']))
        
        # Process skills into list format
        if isinstance(skills_data, str):
            skills_list = [skill.strip() for skill in skills_data.split(',') if skill.strip()]
        else:
            skills_list = skills_data
        
        # Add each skill as a bullet point
        for skill in skills_list:
            result.append(Paragraph(f"• {skill}", styles['BulletPoint']))
        
        return result