from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, NextPageTemplate, FrameBreak, PageBreak, BaseDocTemplate, Image
from reportlab.lib.units import inch, mm
from io import BytesIO
import json
import os
import copy
class ResumeTemplateRegistry:
    """Registry for managing multiple resume template designs"""
    
    def __init__(self):
        self.templates = {}
    
    def register_template(self, template_id, template_class, metadata=None):
        """Register a new template design"""
        self.templates[template_id] = {
            'class': template_class,
            'metadata': metadata or {}
        }
    
    def get_template(self, template_id):
        """Get a template by ID"""
        if template_id not in self.templates:
            raise ValueError(f"Template '{template_id}' not found")
        return self.templates[template_id]
    
    def get_all_templates(self):
        """Get all available templates"""
        return self.templates