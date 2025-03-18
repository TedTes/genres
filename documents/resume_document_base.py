from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, NextPageTemplate, FrameBreak, PageBreak, BaseDocTemplate, Image
from reportlab.lib.units import inch, mm
from io import BytesIO
import json
import os
import copy
class ResumeDocumentBase(BaseDocTemplate):
    """Base document class for all resume templates"""
    
    def __init__(self, filename, pagesize=A4, **kwargs):
        self.allowSplitting = 0
        self.buffer = filename if hasattr(filename, 'write') else None
        self.build_callback = None
        self.primary_color = kwargs.get('primary_color', colors.blue)
        BaseDocTemplate.__init__(self, filename, pagesize=pagesize, **kwargs)
    
    def build(self, flowables,canvasmaker=None):
        """Override build to use our callback"""
        if self.build_callback:
            # Create a custom canvasmaker function that applies our callback
            from reportlab.pdfgen.canvas import Canvas
            
            _old_canvasmaker = canvasmaker or Canvas
            callback = self.build_callback
            doc = self
            # Define a custom canvasmaker function
            def _custom_canvasmaker(*args, **kwargs):
                canvas = _old_canvasmaker(*args, **kwargs)
                # Set up a showPage method that applies our callback
                old_showPage = canvas.showPage
                
                def _custom_showPage():
                    # Apply callback before calling the original showPage
                    self.build_callback(canvas, self)
                    old_showPage()
                
                canvas.showPage = _custom_showPage
                return canvas
            
            # Use our custom canvasmaker
            canvasmaker = _custom_canvasmaker
        
        # Call parent build method
        BaseDocTemplate.build(self, flowables, canvasmaker=canvasmaker)
    # Add professional design elements
    def _add_design_elements(self, canvas, doc):
        """Add design elements to the page"""
        # Get page dimensions
        page_width, page_height = doc.pagesize
        
        # Add subtle header background
        canvas.setFillColor(colors.Color(0.97, 0.97, 0.97))
        canvas.rect(0, page_height-2*inch, page_width, 2*inch, fill=1, stroke=0)
        
        # Add thin accent line
        canvas.setStrokeColor(self.primary_color)
        canvas.setLineWidth(3)
        canvas.line(inch, page_height-2.1*inch, page_width-inch, page_height-2.1*inch)
    
        # Add subtle footer
        canvas.setFillColor(colors.Color(0.9, 0.9, 0.9))
        canvas.rect(0, 0, page_width, 0.5*inch, fill=1, stroke=0)
