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
        self._document_instance = None
    
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
        """Generate the resume PDF with improved error handling"""
        try:
            # Create the document
            doc = self._create_document(output_path)
            
            # Store document instance for reference in other methods
            self._document_instance = doc
            
            # Store buffer for return
            self.buffer = doc.buffer if hasattr(doc, 'buffer') else None
            
            # Build content
            self._build_header()
            self._build_body()
            
            # Build document
            doc.build(self.story)
            
            # Return buffer if path is None
            if output_path is None and self.buffer:
                self.buffer.seek(0)
                return self.buffer
                
        except Exception as e:
            print(f"Error in template generation: {e}")
            import traceback
            traceback.print_exc()
            
            # If we encountered an error but have a buffer, try to return it
            if self.buffer:
                try:
                    self.buffer.seek(0)
                    return self.buffer
                except:
                    pass
            
            # If all else fails, return a simple error PDF
            return self._generate_error_pdf(output_path, str(e))
    
    def _generate_error_pdf(self, output_path, error_message):
        """Generate a simple error PDF if regular generation fails"""
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        buffer = BytesIO() if output_path is None else output_path
        doc = SimpleDocTemplate(buffer)
        styles = getSampleStyleSheet()
        
        # Create a simple error report
        story = []
        story.append(Paragraph("Resume Generation Error", styles['Title']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("There was an error generating your resume:", styles['Heading2']))
        story.append(Paragraph(error_message, styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("Please check your resume data and try again.", styles['Normal']))
        
        # Build document
        doc.build(story)
        
        # Return if path is None
        if output_path is None:
            buffer.seek(0)
            return buffer