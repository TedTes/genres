from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, NextPageTemplate, FrameBreak, PageBreak, BaseDocTemplate, Image
from reportlab.lib.units import inch, mm
from io import BytesIO
import json
import os
import copy
from resume_document_base import ResumeDocumentBase
class MinimalResumeDocument(ResumeDocumentBase):
    """Document class for minimal resume template with sidebar"""
    
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        
        # Set up frames for the resume
        page_width, page_height = self.pagesize
        
        # Create frames: sidebar and main content
        sidebar_width = (page_width - self.leftMargin - self.rightMargin) * 0.3
        main_width = (page_width - self.leftMargin - self.rightMargin) * 0.7
        
        frame_sidebar = Frame(
            self.leftMargin, 
            self.bottomMargin,
            sidebar_width,
            page_height - self.topMargin - self.bottomMargin,
            id='sidebar'
        )
        
        frame_main = Frame(
            self.leftMargin + sidebar_width, 
            self.bottomMargin,
            main_width,
            page_height - self.topMargin - self.bottomMargin,
            id='main'
        )
        
        # Create page template
        template = PageTemplate(
            id='resume_template',
            frames=[frame_sidebar, frame_main],
            pagesize=self.pagesize
        )
        
        self.addPageTemplates(template)