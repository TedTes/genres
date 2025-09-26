from models import ResumeTemplate
from db import db

class TemplateLoader:
    """Simple template metadata loader from database"""
    
    def load_template_metadata(self, template_id: str):
        """Load template metadata from resume_templates table"""
        template = ResumeTemplate.query.filter_by(id=template_id).first()
        
        if not template:
            return None
            
        return {
            'id': template.id,
            'name': template.name,
            'tier': template.tier,
            'layout': template.layout,
            'supported_sections': template.supported_sections,
            'design_tokens': template.design_tokens,
            'skeleton_handle': template.skeleton_handle
        }
    
    def get_all_active_templates(self):
        """Get list of all active templates for gallery"""
        templates = ResumeTemplate.query.filter_by(active_version=1).all()
        
        return [{
            'id': t.id,
            'name': t.name,
            'tier': t.tier.value,  # Convert enum to string
            'capabilities': t.capabilities
        } for t in templates]