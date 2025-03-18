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
class ModernTwoColumnDocument(ResumeDocumentBase):
    """Document class for modern two-column resume template"""
    
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        
        # Set up frames for the resume
        page_width, page_height = self.pagesize
        
        # Create frames: header, left column, right column
        frame_header = Frame(
            self.leftMargin, 
            page_height - self.topMargin - 1.5*inch,  # Header height: 1.5 inches 
            page_width - self.leftMargin - self.rightMargin, 
            1.5*inch,
            id='header'
        )
        
        # The main content frames: 2-column layout
        left_column_width = (page_width - self.leftMargin - self.rightMargin) * 0.65
        right_column_width = (page_width - self.leftMargin - self.rightMargin) * 0.35
        
        frame_left = Frame(
            self.leftMargin, 
            self.bottomMargin,
            left_column_width,
            page_height - self.topMargin - 1.5*inch - self.bottomMargin,
            id='left'
        )
        
        frame_right = Frame(
            self.leftMargin + left_column_width, 
            self.bottomMargin,
            right_column_width,
            page_height - self.topMargin - 1.5*inch - self.bottomMargin,
            id='right'
        )
        
        # Create page template
        template = PageTemplate(
            id='resume_template',
            frames=[frame_header, frame_left, frame_right],
            pagesize=self.pagesize
        )
        
        self.addPageTemplates(template)