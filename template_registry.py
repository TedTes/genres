import os
import json
from pathlib import Path
from flask import current_app

class TemplateRegistry:
    """Manages resume templates"""
    
    def __init__(self, templates_dir=None):
        """Initialize the template registry"""
        self.templates_dir = templates_dir or os.path.join(os.getcwd(), 'templates')
        self.templates = {}
        self.load_templates()
    
    def load_templates(self):
        """Load all templates from the templates directory"""
      
        # Try to load from config files
        for template_dir in Path(self.templates_dir).iterdir():
            if template_dir.is_dir() and template_dir.name not in ['partials', 'email']:
                config_file = template_dir / "config.json"
                if config_file.exists():
                    try:
                        with open(config_file, 'r') as f:
                            config = json.load(f)
                            template_id = config.get('id') or template_dir.name
                            self.templates[template_id] = config
                    except Exception as e:
                        print(f"Error loading template config {config_file}: {e}")
    
    def get_template(self, template_id):
        """Get a template by ID, defaulting to 'standard' if not found"""
        return self.templates.get(template_id) or self.templates.get('standard')
    
    def get_all_templates(self):
        """Get all available templates"""
        return self.templates