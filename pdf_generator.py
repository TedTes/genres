from flask import make_response, render_template, send_file, request
from io import BytesIO
import base64
import os
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage

class ResumePDFGenerator:
    """Enhanced resume PDF generator with support for custom templates and profile images."""
    
    def __init__(self, resume, template_info):
        """Initialize the PDF generator.
        
        Args:
            resume: The Resume model object containing resume data
            template_info: Dictionary with template styling information
        """
        self.resume = resume
        self.template_info = template_info
        self.buffer = BytesIO()
        self.styles = getSampleStyleSheet()
        self.template_class = template_info.get('css_class', 'template-standard')
        self.primary_color = self._get_template_color()
        self.page_size = A4  # Default to A4, can be customized
        self.doc = None  # Will be set up in _setup_document
        
    def _get_template_color(self):
        """Get the primary color for the template."""
        color_map = {
            'template-standard': colors.blue,
            'template-modern': colors.HexColor('#10B981'),  # Green
            'template-minimal': colors.HexColor('#4B5563'),  # Gray
            'template-executive': colors.HexColor('#1E40AF'),  # Dark Blue
            'template-creative': colors.HexColor('#EC4899'),  # Pink
            'template-technical': colors.HexColor('#6366F1')  # Indigo
        }
        return color_map.get(self.template_class, colors.blue)
    
    def _setup_document(self):
        """Set up the PDF document with appropriate margins based on template."""
        # If we already have a document created, return it
        if self.doc is not None:
            return self.doc
            
        # Adjust margins based on template
        if self.template_class == 'template-minimal':
            margins = (0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch)
        elif self.template_class == 'template-executive':
            margins = (1*inch, 1*inch, 1*inch, 1*inch)
        else:
            margins = (0.75*inch, 0.75*inch, 0.75*inch, 0.75*inch)
            
        # Create a new document
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=self.page_size,
            rightMargin=margins[0],
            leftMargin=margins[1],
            topMargin=margins[2],
            bottomMargin=margins[3],
            title=self._get_resume_title()
        )
        
        return self.doc
    
    def _get_resume_title(self):
        """Generate a title for the PDF document."""
        contact = self.resume.resume_data.get('contact', {})
        name = contact.get('name', 'Resume')
        if self.resume.job:
            job_title = self.resume.job.title
            return f"{name} - {job_title}"
        return f"{name}'s Resume"
    
    def _create_styles(self):
        """Create custom paragraph styles based on the template."""
        # Common style attributes
        font_family = 'Helvetica'
        if self.template_class == 'template-executive':
            font_family = 'Times-Roman'
        
        # Create title style
        title_style = ParagraphStyle(
            name='ResumeTitle',
            parent=self.styles['Heading1'],
            fontName=f'{font_family}-Bold',
            fontSize=16,
            alignment=1 if self.template_class in ['template-standard', 'template-executive'] else 0,
            textColor=self.primary_color if self.template_class in ['template-modern', 'template-creative'] else colors.black,
            spaceAfter=12
        )
        
        # Section heading style
        section_style = ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontName=f'{font_family}-Bold',
            fontSize=12,
            textColor=self.primary_color,
            spaceAfter=8,
            spaceBefore=16,
            borderWidth=1 if self.template_class == 'template-executive' else 0,
            borderColor=colors.black,
            borderPadding=(0, 0, 1, 0) if self.template_class == 'template-executive' else 0
        )
        
        # Contact info style
        contact_style = ParagraphStyle(
            name='ContactInfo',
            parent=self.styles['Normal'],
            fontName=font_family,
            fontSize=9,
            alignment=1 if self.template_class in ['template-standard', 'template-executive'] else 0,
            textColor=colors.gray if self.template_class == 'template-minimal' else colors.black,
            spaceAfter=12
        )
        
        # Normal text style
        normal_style = ParagraphStyle(
            name='NormalText',
            parent=self.styles['Normal'],
            fontName=font_family,
            fontSize=10,
            leading=14  # Line height
        )
        
        # Bold text style
        bold_style = ParagraphStyle(
            name='BoldText',
            parent=normal_style,
            fontName=f'{font_family}-Bold'
        )
        
        # Italic text style
        italic_style = ParagraphStyle(
            name='ItalicText',
            parent=normal_style,
            fontName=f'{font_family}-Oblique'
        )
        
        # Bullet style
        bullet_style = ParagraphStyle(
            name='BulletText',
            parent=normal_style,
            leftIndent=20,
            spaceBefore=2,
            spaceAfter=2
        )
        
        return {
            'title': title_style,
            'section': section_style,
            'contact': contact_style,
            'normal': normal_style,
            'bold': bold_style,
            'italic': italic_style,
            'bullet': bullet_style
        }
    
    def _add_profile_image(self, elements, profile_image_path):
        """Add a profile image to the resume if available."""
        if not profile_image_path or not os.path.exists(profile_image_path):
            return
        
        try:
            # Create a circular/square profile image based on template
            img = Image.open(profile_image_path)
            
            # Resize to appropriate dimensions
            size = 100  # Default size in pixels
            img = img.resize((size, size))
            
            # Save to a temporary BytesIO
            temp_img = BytesIO()
            img.save(temp_img, format='PNG')
            temp_img.seek(0)
            
            # Create ReportLab image
            image = RLImage(temp_img, width=1*inch, height=1*inch)
            
            # Add the image based on template style
            if self.template_class in ['template-standard', 'template-executive']:
                # Center the image for these templates
                elements.append(image)
            else:
                # For other templates, we'll position it differently
                # This would ideally be handled with a Table or other positioning
                elements.append(image)
            
            elements.append(Spacer(1, 0.25*inch))
            
        except Exception as e:
            print(f"Error processing profile image: {e}")
    
    def _add_contact_info(self, elements, styles):
        """Add contact information section."""
        contact = self.resume.resume_data.get('contact', {})
        
        # Add name as title
        elements.append(Paragraph(contact.get('name', 'Your Name'), styles['title']))
        
        # Add contact details
        contact_text = []
        if contact.get('email'):
            contact_text.append(contact.get('email'))
        if contact.get('phone'):
            contact_text.append(contact.get('phone'))
        if contact.get('location'):
            contact_text.append(contact.get('location'))
        
        elements.append(Paragraph(' | '.join(contact_text), styles['contact']))
        
        # Add website/LinkedIn
        if contact.get('linkedin') or contact.get('website'):
            website_text = []
            if contact.get('linkedin'):
                website_text.append(contact.get('linkedin'))
            if contact.get('website'):
                website_text.append(contact.get('website'))
            elements.append(Paragraph(' | '.join(website_text), styles['contact']))
        
        elements.append(Spacer(1, 0.2*inch))
    
    def _add_summary(self, elements, styles):
        """Add professional summary section."""
        if not self.resume.resume_data.get('summary'):
            return
        
        elements.append(Paragraph('Professional Summary', styles['section']))
        
        summary_text = self.resume.resume_data.get('summary')
        if not isinstance(summary_text, str):
            summary_text = summary_text.get('content', '')
        
        elements.append(Paragraph(summary_text, styles['normal']))
        elements.append(Spacer(1, 0.2*inch))
    
    def _add_experience(self, elements, styles):
        """Add work experience section."""
        experience = self.resume.resume_data.get('experience')
        if not experience:
            return
        
        elements.append(Paragraph('Work Experience', styles['section']))
        
        for exp in experience:
            # Job title and company
            title_company = f"{exp.get('title')} - {exp.get('company')}"
            elements.append(Paragraph(title_company, styles['bold']))
            
            # Date range
            date_range = f"{exp.get('startDate')} - {'Present' if exp.get('current') else exp.get('endDate')}"
            elements.append(Paragraph(date_range, styles['italic']))
            
            # Description bullets
            if exp.get('description'):
                for line in exp.get('description').split('\n'):
                    if line.strip():
                        elements.append(Paragraph(f"• {line.strip()}", styles['bullet']))
            
            elements.append(Spacer(1, 0.15*inch))
    
    def _add_education(self, elements, styles):
        """Add education section."""
        education = self.resume.resume_data.get('education')
        if not education:
            return
        
        elements.append(Paragraph('Education', styles['section']))
        
        if isinstance(education, dict):
            # Single education entry
            elements.append(Paragraph(education.get('degree', ''), styles['bold']))
            elements.append(Paragraph(education.get('school', ''), styles['normal']))
            elements.append(Paragraph(education.get('year', ''), styles['italic']))
        
        elif isinstance(education, list):
            # Multiple education entries
            for edu in education:
                elements.append(Paragraph(edu.get('degree', ''), styles['bold']))
                elements.append(Paragraph(edu.get('school', ''), styles['normal']))
                
                date_range = f"{edu.get('startYear', '')} - {'Present' if edu.get('current') else edu.get('endYear', '')}"
                elements.append(Paragraph(date_range, styles['italic']))
                
                if edu.get('description'):
                    elements.append(Paragraph(edu.get('description'), styles['normal']))
                
                elements.append(Spacer(1, 0.15*inch))
    
    def _add_skills(self, elements, styles):
        """Add skills section."""
        skills = self.resume.resume_data.get('skills')
        if not skills:
            return
        
        elements.append(Paragraph('Skills', styles['section']))
        
        # Process skills into list
        if isinstance(skills, str):
            skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        else:
            skills_list = skills
        
        # Create a table for skills (3 columns)
        if skills_list:
            # Organize skills into rows of 3
            skill_rows = []
            row = []
            for skill in skills_list:
                row.append(skill)
                if len(row) == 3:
                    skill_rows.append(row)
                    row = []
            
            if row:  # Add any remaining skills
                while len(row) < 3:
                    row.append('')
                skill_rows.append(row)
            
            # Style the skills table based on template
            table_style = TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
            ])
            
            if self.template_class == 'template-modern':
                # Add background color to skill cells
                for i in range(len(skill_rows)):
                    for j in range(len(skill_rows[i])):
                        if skill_rows[i][j]:  # Only add style if cell has content
                            table_style.add('BACKGROUND', (j, i), (j, i), colors.Color(0.9, 0.9, 0.9))
                            table_style.add('TEXTCOLOR', (j, i), (j, i), self.primary_color)
            
            # Create table with appropriate width distribution
            # Get document margins from our document object
            doc = self._setup_document()
            available_width = self.page_size[0] - doc.leftMargin - doc.rightMargin
            col_width = available_width / 3
            
            skills_table = Table(skill_rows, colWidths=[col_width] * 3)
            skills_table.setStyle(table_style)
            
            elements.append(skills_table)
    
    def generate(self, profile_image_path=None):
        """Generate the PDF document.
        
        Args:
            profile_image_path: Optional path to profile image
            
        Returns:
            BytesIO: Buffer containing the generated PDF
        """
        # Setup document first to initialize self.doc
        self._setup_document()
        
        # Create styles
        styles = self._create_styles()
        
        # Build resume content
        elements = []
        
        # Add profile image if provided
        if profile_image_path:
            self._add_profile_image(elements, profile_image_path)
        
        # Add sections
        self._add_contact_info(elements, styles)
        self._add_summary(elements, styles)
        self._add_experience(elements, styles)
        self._add_education(elements, styles)
        self._add_skills(elements, styles)
        
        # Build document
        self.doc.build(elements)
        
        # Reset buffer position to beginning
        self.buffer.seek(0)
        return self.buffer

def generate_resume_pdf(resume_id, current_user, db, Resume):
    """Function to handle PDF generation request."""
    resume = Resume.query.get_or_404(resume_id)
    
    # Check if the resume belongs to the current user
    if resume.user_id != current_user.id:
        return None, "Unauthorized"
    
    # Prepare the resume filename
    if resume.job:
        filename = f"resume_{current_user.username}_{resume.job.title}.pdf"
    else:
        filename = f"resume_{current_user.username}.pdf"
    filename = filename.replace(' ', '_')
    
    try:
        from resume_templates import RESUME_TEMPLATES
        
        # Get template info
        template_info = RESUME_TEMPLATES.get(resume.template, RESUME_TEMPLATES['standard'])
        
        # Check for profile image if provided in the request
        profile_image_path = None
        if 'profile_image' in request.files:
            # Handle image upload and temporary storage
            image_file = request.files['profile_image']
            if image_file.filename:
                temp_dir = os.path.join(os.getcwd(), 'temp')
                os.makedirs(temp_dir, exist_ok=True)
                temp_path = os.path.join(temp_dir, f"profile_{resume_id}.png")
                image_file.save(temp_path)
                profile_image_path = temp_path
        
        # Create PDF generator and generate PDF
        generator = ResumePDFGenerator(resume, template_info)
        pdf_buffer = generator.generate(profile_image_path)
        
        # Clean up temporary image if it was created
        if profile_image_path and os.path.exists(profile_image_path):
            os.remove(profile_image_path)
        
        return pdf_buffer, filename
    
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        import traceback
        traceback.print_exc()  # Print full traceback for debugging
        return None, str(e)