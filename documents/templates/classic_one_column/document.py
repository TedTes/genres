from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, NextPageTemplate, FrameBreak, PageBreak, BaseDocTemplate, Image
from reportlab.lib.units import inch, mm
from io import BytesIO
import json
import os
import copy

from documents.core.resume_document_base import ResumeDocumentBase

class ClassicOneColumnDocument(ResumeDocumentBase):
    """Document class for classic one-column resume template"""
    
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        
        # Set up frames for the resume
        page_width, page_height = self.pagesize
        
        # Create frames: header and main content
        frame_header = Frame(
            self.leftMargin, 
            page_height - self.topMargin - 2*inch,  # Header height: 2 inches 
            page_width - self.leftMargin - self.rightMargin, 
            2*inch,
            id='header'
        )
        
        frame_content = Frame(
            self.leftMargin, 
            self.bottomMargin,
            page_width - self.leftMargin - self.rightMargin,
            page_height - self.topMargin - 2*inch - self.bottomMargin,
            id='content'
        )
        
        # Create page template
        template = PageTemplate(
            id='resume_template',
            frames=[frame_header, frame_content],
            pagesize=self.pagesize
        )
        
        self.addPageTemplates(template)