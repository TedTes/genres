from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, NextPageTemplate, FrameBreak, PageBreak
from reportlab.lib.units import inch, mm
from io import BytesIO
import json
import os
import copy

from documents.core.resume_document_base import ResumeDocumentBase

class ClassicOneColumnDocument(ResumeDocumentBase):
    """Enhanced document class for classic one-column resume template with professional layout"""
    
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        
        # Set up frames for the resume
        page_width, page_height = self.pagesize
        
        # Create frames: header and main content with proportional spacing
        header_height = 1.8 * inch  # Slightly reduced header height for more content space
        
        # Header frame for name and contact info
        frame_header = Frame(
            self.leftMargin, 
            page_height - self.topMargin - header_height,
            page_width - self.leftMargin - self.rightMargin, 
            header_height,
            id='header',
            showBoundary=0  # No visible frame boundaries
        )
        
        # Main content frame
        frame_content = Frame(
            self.leftMargin, 
            self.bottomMargin,
            page_width - self.leftMargin - self.rightMargin,
            page_height - self.topMargin - header_height - self.bottomMargin,
            id='content',
            showBoundary=0  # No visible frame boundaries
        )
        
        # Create page template
        template = PageTemplate(
            id='resume_template',
            frames=[frame_header, frame_content],
            pagesize=self.pagesize,
            onPage=self._on_page  # Add callback for page decoration
        )
        
        self.addPageTemplates(template)
        
        # Set document properties
        self.title = "Professional Resume"
        self.author = "ResumeMatch"
        self.subject = "Professional Resume"
        self.keywords = ["resume", "curriculum vitae", "professional"]
        
    def _on_page(self, canvas, doc):
        """Optional page decoration callback for more professional look"""
        # This can be used to add header/footer elements, page numbers, etc.
        # We'll leave it empty for now as the main design elements will be added through the template's callback
        pass