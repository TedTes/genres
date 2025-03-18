from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, NextPageTemplate, FrameBreak, PageBreak, BaseDocTemplate, Image
from reportlab.lib.units import inch, mm
from io import BytesIO
import json
import os
import copy
class BaseResumeTemplate:
    """Base class for resume templates"""
    
    def __init__(self, user_data, metadata=None):
        self.user_data = user_data
        self.metadata = metadata or {}
        self.story = []
        self.styles = self._create_styles()
        self.buffer = None
    
    def _create_styles(self):
        """Create and return styles for the template"""
        styles = getSampleStyleSheet()
        return styles
    
    def _build_header(self):
        """Build header content"""
        raise NotImplementedError("Subclasses must implement this method")
    
    def _build_body(self):
        """Build body content"""
        raise NotImplementedError("Subclasses must implement this method")
    
    def _create_document(self, output_path):
        """Create document instance"""
        raise NotImplementedError("Subclasses must implement this method")
    
    def generate(self, output_path=None):
        """Generate the resume PDF"""
        # Create the document
        doc = self._create_document(output_path)
        
        self.buffer = doc.buffer if hasattr(doc, 'buffer') else None
        
        # Build content
        self._build_header()
        self._build_body()
        
        # Build document
        doc.build(self.story)
        
        # Return if path is None
        if output_path is None and self.buffer:
            self.buffer.seek(0)
            return self.buffer