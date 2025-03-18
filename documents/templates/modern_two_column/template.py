from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, NextPageTemplate, FrameBreak, PageBreak, BaseDocTemplate, Image
from reportlab.lib.units import inch, mm
from io import BytesIO
import json
import os
import copy

from base_resume_template import BaseResumeTemplate
from modern_two_column_document import ModernTwoColumnDocument
class ModernTwoColumnTemplate(BaseResumeTemplate):
    """Modern two-column resume template with header"""
    
    def _create_styles(self):
        styles = super()._create_styles()
        
        # Get colors from metadata
        colors_data = self.metadata.get('colors', {})
        primary_color = colors.Color(*colors_data.get('primary', [0.1, 0.4, 0.7]))
        secondary_color = colors.Color(*colors_data.get('secondary', [0.2, 0.2, 0.2]))
        
        # Get fonts from metadata
        fonts_data = self.metadata.get('fonts', {})
        name_font = fonts_data.get('name', {'family': 'Helvetica-Bold', 'size': 26})
        heading_font = fonts_data.get('heading', {'family': 'Helvetica-Bold', 'size': 14})
        normal_font = fonts_data.get('normal', {'family': 'Helvetica', 'size': 10})
        
        # Add custom styles
        styles.add(ParagraphStyle(
            'ResumeName',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=28,
            letterSpacing=1,  # Add letter spacing
            leading=34,  # Improve line height
            textColor=primary_color,
            spaceAfter=8
        ))
        
        styles.add(ParagraphStyle(
            'ResumeTitle',
            parent=styles['Heading2'],
            fontName='Helvetica',
            fontSize=18,
            textColor=primary_color,
            spaceAfter=12,
            alignment=0
        ))
        
        styles.add(ParagraphStyle(
            'ContactInfo',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            textColor=secondary_color,
            spaceAfter=20
        ))
        
        styles.add(ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading3'],
            fontName=heading_font['family'],
            fontSize=heading_font['size'],
            textColor=primary_color,
            spaceBefore=15,
            spaceAfter=10,
            alignment=0,
            borderWidth=0,
            borderColor=None,
            borderPadding=0
        ))
        
        styles.add(ParagraphStyle(
            'JobTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=secondary_color,
            spaceBefore=6,
            spaceAfter=2
        ))
        
        styles.add(ParagraphStyle(
            'JobInfo',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=secondary_color,
            spaceAfter=6
        ))
        
        styles.add(ParagraphStyle(
            'BulletPoint',
            parent=styles['Normal'],
            fontName=normal_font['family'],
            fontSize=normal_font['size'],
            leftIndent=12,
            firstLineIndent=-12,  # Negative for bullet indent
            spaceBefore=2,
            spaceAfter=2
        ))
        
        return styles
    def _add_design_elements(self, canvas, doc):
        """Add design elements to the page"""
        # Get page dimensions
        page_width, page_height = doc.pagesize
        
        # Get colors from metadata
        colors_data = self.metadata.get('colors', {})
        primary_color = colors.Color(*colors_data.get('primary', [0.1, 0.4, 0.7]))
        
        # Add subtle header background
        canvas.setFillColor(colors.Color(0.97, 0.97, 0.97))
        canvas.rect(0, page_height-2*inch, page_width, 2*inch, fill=1, stroke=0)
        
        # Add thin accent line
        canvas.setStrokeColor(primary_color)
        canvas.setLineWidth(3)
        canvas.line(inch, page_height-2.1*inch, page_width-inch, page_height-2.1*inch)
        
        # Add subtle footer
        canvas.setFillColor(colors.Color(0.9, 0.9, 0.9))
        canvas.rect(0, 0, page_width, 0.5*inch, fill=1, stroke=0)
    
    def _create_document(self, output_path):
        """Create the document with frames and page callbacks"""
        buffer = BytesIO() if output_path is None else output_path
        
        # Create document with custom margins
        margins = self.metadata.get('margins', {})
        left_margin = margins.get('left', 0.5) * inch
        right_margin = margins.get('right', 0.5) * inch
        top_margin = margins.get('top', 0.5) * inch
        bottom_margin = margins.get('bottom', 0.5) * inch
        
        doc = ModernTwoColumnDocument(
            buffer,
            pagesize=A4,
            leftMargin=left_margin,
            rightMargin=right_margin,
            topMargin=top_margin,
            bottomMargin=bottom_margin
        )
        
        # Add page callback for design elements
        doc.build_callback = self._add_design_elements
        
        return doc
    
    def _build_header(self):
        """Build header content"""
        # Create header with contact info
        contact_info = self.user_data.get('contact', {})
        name = contact_info.get('name', 'Full Name')
        title = contact_info.get('title', 'Professional Title')
        
        self.story.append(Paragraph(name, self.styles['ResumeName']))
        self.story.append(Paragraph(title, self.styles['ResumeTitle']))
        
        # Create contact info line
        contact_line = []
        if contact_info.get('email'):
            contact_line.append(contact_info['email'])
        if contact_info.get('phone'):
            contact_line.append(contact_info['phone'])
        if contact_info.get('location'):
            contact_line.append(contact_info['location'])
        
        if contact_line:
            self.story.append(Paragraph(" | ".join(contact_line), self.styles['ContactInfo']))
        
        # Add frame break to move to the next frame (left column)
        self.story.append(FrameBreak())
    
    def _build_experience_section(self):
        """Build experience section"""
        experiences = self.user_data.get('experience', [])
        if experiences:
            self.story.append(Paragraph("EXPERIENCE", self.styles['SectionHeading']))
            
            for exp in experiences:
                job_title = exp.get('title', '')
                company = exp.get('company', '')
                start_date = exp.get('startDate', '')
                end_date = exp.get('endDate', 'Present') if not exp.get('current', False) else 'Present'
                description = exp.get('description', '')
                
                job_heading = f"{job_title}, {company}"
                self.story.append(Paragraph(job_heading, self.styles['JobTitle']))
                self.story.append(Paragraph(f"{start_date} - {end_date}", self.styles['JobInfo']))
                
                # Add description as bullet points
                if description:
                    for line in description.split('\n'):
                        if line.strip():
                            self.story.append(Paragraph(f"• {line.strip()}", self.styles['BulletPoint']))
                    
                    # Add a small space after each job
                    self.story.append(Spacer(1, 10))
    
    def _build_education_section(self):
        """Build education section"""
        education = self.user_data.get('education', [])
        if education:
            self.story.append(Paragraph("EDUCATION", self.styles['SectionHeading']))
            
            if isinstance(education, list):
                for edu in education:
                    degree = edu.get('degree', '')
                    school = edu.get('school', '')
                    year = edu.get('year', '')
                    
                    self.story.append(Paragraph(degree, self.styles['JobTitle']))
                    self.story.append(Paragraph(f"{school}, {year}", self.styles['JobInfo']))
                    self.story.append(Spacer(1, 8))
            else:
                # Handle single education entry as dictionary
                degree = education.get('degree', '')
                school = education.get('school', '')
                year = education.get('year', '')
                
                self.story.append(Paragraph(degree, self.styles['JobTitle']))
                self.story.append(Paragraph(f"{school}, {year}", self.styles['JobInfo']))
    
    def _build_skills_section(self):
        """Build skills section"""
        skills = self.user_data.get('skills', [])
        if skills:
            self.story.append(Paragraph("SKILLS", self.styles['SectionHeading']))
            
            # Process skills into list format
            if isinstance(skills, str):
                skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
            else:
                skills_list = skills
            
            # Add each skill as a bullet point
            for skill in skills_list:
                self.story.append(Paragraph(f"• {skill}", self.styles['BulletPoint']))
    
    def _build_additional_sections(self):
        """Build additional sections like languages, certifications, etc."""
        # Languages section
        if self.user_data.get('languages'):
            languages = self.user_data.get('languages', [])
            self.story.append(Spacer(1, 15))
            self.story.append(Paragraph("LANGUAGES", self.styles['SectionHeading']))
            
            if isinstance(languages, list):
                for lang in languages:
                    self.story.append(Paragraph(f"• {lang}", self.styles['BulletPoint']))
            elif isinstance(languages, str):
                for lang in languages.split(','):
                    self.story.append(Paragraph(f"• {lang.strip()}", self.styles['BulletPoint']))
        
        # Certifications section
        if self.user_data.get('certifications'):
            certifications = self.user_data.get('certifications', [])
            self.story.append(Spacer(1, 15))
            self.story.append(Paragraph("CERTIFICATIONS", self.styles['SectionHeading']))
            
            if isinstance(certifications, list):
                for cert in certifications:
                    self.story.append(Paragraph(f"• {cert}", self.styles['BulletPoint']))
            elif isinstance(certifications, str):
                for cert in certifications.split(','):
                    self.story.append(Paragraph(f"• {cert.strip()}", self.styles['BulletPoint']))
    
    def _build_body(self):
        """Build body content"""
        # Left column
        self._build_experience_section()
        self._build_education_section()
        
        # Add frame break to move to the right column
        self.story.append(FrameBreak())
        
        # Right column
        self._build_skills_section()
        self._build_additional_sections()