
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, NextPageTemplate, FrameBreak, PageBreak, BaseDocTemplate, Image
from reportlab.lib.units import inch, mm
from io import BytesIO
import json
import os
import copy

class MinimalTemplate(BaseResumeTemplate):
    """Minimal resume template with sidebar"""
    
    def _create_styles(self):
        styles = super()._create_styles()
        
        # Get colors from metadata
        colors_data = self.metadata.get('colors', {})
        primary_color = colors.Color(*colors_data.get('primary', [0.5, 0.5, 0.5]))  # Gray by default
        secondary_color = colors.Color(*colors_data.get('secondary', [0.2, 0.2, 0.2]))  # Dark gray by default
        background_color = colors.Color(*colors_data.get('background', [0.95, 0.95, 0.95]))  # Light gray for sidebar
        
        # Get fonts from metadata
        fonts_data = self.metadata.get('fonts', {})
        name_font = fonts_data.get('name', {'family': 'Helvetica-Bold', 'size': 20})
        heading_font = fonts_data.get('heading', {'family': 'Helvetica-Bold', 'size': 12})
        normal_font = fonts_data.get('normal', {'family': 'Helvetica', 'size': 9})
        
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
            fontSize=14,
            textColor=primary_color,
            spaceAfter=20,
            alignment=0
        ))
        
        styles.add(ParagraphStyle(
            'SidebarHeading',
            parent=styles['Heading3'],
            fontName=heading_font['family'],
            fontSize=heading_font['size'],
            textColor=secondary_color,
            spaceBefore=15,
            spaceAfter=10,
            alignment=0,
            textTransform='uppercase'
        ))
        
        styles.add(ParagraphStyle(
            'SidebarContent',
            parent=styles['Normal'],
            fontName=normal_font['family'],
            fontSize=normal_font['size'],
            textColor=secondary_color,
            spaceAfter=5
        ))
        
        styles.add(ParagraphStyle(
            'MainHeading',
            parent=styles['Heading3'],
            fontName=heading_font['family'],
            fontSize=heading_font['size'] + 2,  # Slightly larger
            textColor=primary_color,
            spaceBefore=15,
            spaceAfter=10,
            alignment=0,
            textTransform='uppercase'
        ))
        
        styles.add(ParagraphStyle(
            'JobTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=secondary_color,
            spaceBefore=6,
            spaceAfter=2
        ))
        
        styles.add(ParagraphStyle(
            'JobInfo',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=primary_color,
            spaceAfter=6
        ))
        
        styles.add(ParagraphStyle(
            'BulletPoint',
            parent=styles['Normal'],
            fontName=normal_font['family'],
            fontSize=normal_font['size'],
            leftIndent=10,
            firstLineIndent=-6,  # Minimal bullet indent
            spaceBefore=1,
            spaceAfter=1,
            leading=12  # Tighter line spacing
        ))
        
        return styles
    
    def _create_document(self, output_path):
        """Create the document with frames"""
        buffer = BytesIO() if output_path is None else output_path
        
        # Create document with custom margins
        margins = self.metadata.get('margins', {})
        left_margin = margins.get('left', 0.4) * inch  # Narrower margins for minimal style
        right_margin = margins.get('right', 0.4) * inch
        top_margin = margins.get('top', 0.5) * inch
        bottom_margin = margins.get('bottom', 0.5) * inch
        
        doc = MinimalResumeDocument(
            buffer,
            pagesize=A4,
            leftMargin=left_margin,
            rightMargin=right_margin,
            topMargin=top_margin,
            bottomMargin=bottom_margin
        )
        doc.build_callback = self._add_design_elements
        return doc
    
    def _build_sidebar(self):
        """Build sidebar content"""
        # Contact section
        contact_info = self.user_data.get('contact', {})
        name = contact_info.get('name', 'Full Name')
        title = contact_info.get('title', 'Professional Title')
        
        self.story.append(Paragraph(name, self.styles['ResumeName']))
        self.story.append(Paragraph(title, self.styles['ResumeTitle']))
        
        # Contact details
        self.story.append(Paragraph("CONTACT", self.styles['SidebarHeading']))
        
        if contact_info.get('email'):
            self.story.append(Paragraph(f"Email: {contact_info['email']}", self.styles['SidebarContent']))
        
        if contact_info.get('phone'):
            self.story.append(Paragraph(f"Phone: {contact_info['phone']}", self.styles['SidebarContent']))
        
        if contact_info.get('location'):
            self.story.append(Paragraph(f"Location: {contact_info['location']}", self.styles['SidebarContent']))
        
        # Skills section
        skills = self.user_data.get('skills', [])
        if skills:
            self.story.append(Paragraph("SKILLS", self.styles['SidebarHeading']))
            
            # Process skills into list format
            if isinstance(skills, str):
                skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
            else:
                skills_list = skills
            
            # Add each skill
            for skill in skills_list:
                self.story.append(Paragraph(f"• {skill}", self.styles['SidebarContent']))
        
        # Languages section
        languages = self.user_data.get('languages', [])
        if languages:
            self.story.append(Paragraph("LANGUAGES", self.styles['SidebarHeading']))
            
            if isinstance(languages, list):
                for lang in languages:
                    self.story.append(Paragraph(f"• {lang}", self.styles['SidebarContent']))
            elif isinstance(languages, str):
                for lang in languages.split(','):
                    self.story.append(Paragraph(f"• {lang.strip()}", self.styles['SidebarContent']))
        
        # Education section (in sidebar for minimal template)
        education = self.user_data.get('education', [])
        if education:
            self.story.append(Paragraph("EDUCATION", self.styles['SidebarHeading']))
            
            if isinstance(education, list):
                for edu in education:
                    degree = edu.get('degree', '')
                    school = edu.get('school', '')
                    year = edu.get('year', '')
                    
                    education_text = f"{degree}<br/>{school}, {year}"
                    self.story.append(Paragraph(education_text, self.styles['SidebarContent']))
                    self.story.append(Spacer(1, 5))
            else:
                # Handle single education entry as dictionary
                degree = education.get('degree', '')
                school = education.get('school', '')
                year = education.get('year', '')
                
                education_text = f"{degree}<br/>{school}, {year}"
                self.story.append(Paragraph(education_text, self.styles['SidebarContent']))
        
        # Move to main content area
        self.story.append(FrameBreak())
    
    def _build_main_content(self):
        """Build main content area"""
        # Summary section
        summary = self.user_data.get('summary', '')
        if summary:
            self.story.append(Paragraph("PROFILE", self.styles['MainHeading']))
            if isinstance(summary, str):
                self.story.append(Paragraph(summary, self.styles['SidebarContent']))
            elif isinstance(summary, dict) and 'content' in summary:
                self.story.append(Paragraph(summary['content'], self.styles['SidebarContent']))
            self.story.append(Spacer(1, 10))
        
        # Experience section
        experiences = self.user_data.get('experience', [])
        if experiences:
            self.story.append(Paragraph("EXPERIENCE", self.styles['MainHeading']))
            
            for exp in experiences:
                job_title = exp.get('title', '')
                company = exp.get('company', '')
                start_date = exp.get('startDate', '')
                end_date = exp.get('endDate', 'Present') if not exp.get('current', False) else 'Present'
                description = exp.get('description', '')
                
                self.story.append(Paragraph(job_title, self.styles['JobTitle']))
                self.story.append(Paragraph(f"{company} | {start_date} - {end_date}", self.styles['JobInfo']))
                
                # Add description as bullet points
                if description:
                    for line in description.split('\n'):
                        if line.strip():
                            self.story.append(Paragraph(f"• {line.strip()}", self.styles['BulletPoint']))
                    
                    # Add a small space after each job
                    self.story.append(Spacer(1, 10))
        
        # Certifications section
        certifications = self.user_data.get('certifications', [])
        if certifications:
            self.story.append(Paragraph("CERTIFICATIONS", self.styles['MainHeading']))
            
            if isinstance(certifications, list):
                for cert in certifications:
                    self.story.append(Paragraph(f"• {cert}", self.styles['BulletPoint']))
            elif isinstance(certifications, str):
                for cert in certifications.split(','):
                    self.story.append(Paragraph(f"• {cert.strip()}", self.styles['BulletPoint']))
    
    def _build_header(self):
        """Build header - not used in minimal template"""
        # This template doesn't have a separate header
        pass
    
    def _build_body(self):
        """Build body content"""
        self._build_sidebar()
        self._build_main_content()