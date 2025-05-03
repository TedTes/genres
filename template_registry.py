import os
import json
from pathlib import Path
from flask import current_app

class TemplateRegistry:
    """Manages resume templates"""
    
    def __init__(self, templates_dir=None):
        """Initialize the template registry"""
        self.templates_dir = templates_dir or os.path.join(os.getcwd(), 'config')
        print(self.templates_dir)
        self.templates = {}
        self.load_templates()
    
    def load_templates(self):
        """Load all templates from metadata.json"""
        metadata_file = os.path.join(self.templates_dir, 'metadata.json')
        print(f"Checking if metadata file exists: {metadata_file}")

        try:
            with open(metadata_file, 'r') as f:
                self.templates = json.load(f)  
                print("Templates loaded successfully:")
        except FileNotFoundError:
            print(f"Error: metadata.json not found in {self.templates_dir}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in metadata.json: {e}")
        except Exception as e:
            print(f"Unexpected error loading template config {metadata_file}: {e}")
    
    def get_template(self, template_id):
        """Get a template by ID, defaulting to 'standard' if not found"""
        return self.templates.get(template_id) or self.templates.get('professional_classic')
    
    def get_all_templates(self):
        """Get all available templates"""
        return self.templates