from typing import Dict, Any, Type, Optional
import json
import os
from pathlib import Path

class TemplateRegistry:
    """
    Enhanced registry for managing multiple resume template designs with better organization,
    versioning, and configuration options.
    """
    
    def __init__(self):
        self.templates = {}
        self.default_template_id = None
    
    def register_template(self, 
                         template_id: str, 
                         template_class: Type, 
                         document_class: Type,
                         metadata: Dict[str, Any],
                         is_default: bool = False) -> None:
        """
        Register a new template design with improved metadata structure.
        
        Args:
            template_id: Unique identifier for the template
            template_class: The template implementation class
            document_class: The document class that defines the layout
            metadata: Template configuration metadata
            is_default: Whether this should be the default template
        """
        self.templates[template_id] = {
            'class': template_class,
            'document_class': document_class,
            'metadata': self._process_metadata(metadata),
            'version': metadata.get('version', '1.0.0')
        }
        
        # Set as default if specified or if it's the first template
        if is_default or not self.default_template_id:
            self.default_template_id = template_id
    
    def _process_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate metadata to ensure all required fields are present."""
        # Ensure required sections exist
        required_sections = ['colors', 'fonts', 'margins', 'layout']
        for section in required_sections:
            if section not in metadata:
                metadata[section] = {}
        
        # Set default colors if not provided
        if not metadata['colors']:
            metadata['colors'] = {
                'primary': [0.1, 0.4, 0.7],  # Blue
                'secondary': [0.2, 0.2, 0.2]  # Dark gray
            }
        
        # Set default fonts if not provided
        if not metadata['fonts']:
            metadata['fonts'] = {
                'name': {"family": "Helvetica-Bold", "size": 24},
                'heading': {"family": "Helvetica-Bold", "size": 14},
                'normal': {"family": "Helvetica", "size": 10}
            }
        
        # Set default margins if not provided
        if not metadata['margins']:
            metadata['margins'] = {
                'left': 0.75,
                'right': 0.75,
                'top': 0.75,
                'bottom': 0.75
            }
        
        # Add UI-specific metadata if not present
        if 'ui' not in metadata:
            metadata['ui'] = {
                'name': metadata.get('name', 'Unnamed Template'),
                'description': metadata.get('description', 'No description provided'),
                'thumbnail': metadata.get('thumbnail', 'default_thumbnail.png'),
                'category': metadata.get('category', 'General'),
                'tags': metadata.get('tags', []),
                'preview_image': metadata.get('preview_image', None)
            }
        
        return metadata
    
    def get_template(self, template_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a template by ID or the default template if no ID is provided.
        
        Args:
            template_id: Identifier for the template
            
        Returns:
            Template configuration dictionary
            
        Raises:
            ValueError: If the template ID doesn't exist
        """
        if not template_id:
            template_id = self.default_template_id
        
        if template_id not in self.templates:
            raise ValueError(f"Template '{template_id}' not found")
        
        return self.templates[template_id]
    
    def get_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get all available templates."""
        return self.templates
    
    def get_template_options(self) -> Dict[str, Dict[str, Any]]:
        """
        Get template options suitable for UI display with just the metadata
        needed for selection and preview.
        """
        options = {}
        for template_id, template in self.templates.items():
            options[template_id] = {
                'name': template['metadata']['ui']['name'],
                'description': template['metadata']['ui']['description'],
                'thumbnail': template['metadata']['ui']['thumbnail'],
                'category': template['metadata']['ui']['category'],
                'tags': template['metadata']['ui']['tags'],
                'preview_image': template['metadata']['ui']['preview_image'],
                'version': template['version']
            }
        return options
    
    def load_from_config(self, config_dir: str, template_module) -> None:
        """
        Load all templates from configuration files in a directory.
        
        Args:
            config_dir: Path to directory containing template configurations
            template_module: Module containing template implementation classes
        """
        try:
            config_path = Path(config_dir)
            if not config_path.exists():
                raise FileNotFoundError(f"Template config directory not found: {config_dir}")
            
            # Load each JSON config file
            for file_path in config_path.glob("*.json"):
                with open(file_path, 'r') as f:
                    try:
                        config = json.load(f)
                        template_id = config.get('template_id')
                        template_class_name = config.get('template_class')
                        document_class_name = config.get('document_class')
                        
                        if not all([template_id, template_class_name, document_class_name]):
                            print(f"Skipping incomplete template config: {file_path}")
                            continue
                        
                        # Get the actual class references
                        template_class = getattr(template_module, template_class_name)
                        document_class = getattr(template_module, document_class_name)
                        
                        # Register the template
                        self.register_template(
                            template_id=template_id,
                            template_class=template_class,
                            document_class=document_class,
                            metadata=config,
                            is_default=config.get('default', False)
                        )
                        
                        print(f"Loaded template: {template_id}")
                    except (json.JSONDecodeError, AttributeError) as e:
                        print(f"Error loading template config {file_path}: {e}")
        except Exception as e:
            print(f"Error loading template configurations: {e}")
    
    def customize_template(self, template_id: str, options: Dict[str, Any]) -> str:
        """
        Create a customized version of a template with the specified options.
        
        Args:
            template_id: Base template ID to customize
            options: Customization options
            
        Returns:
            New template ID for the customized template
        """
        base_template = self.get_template(template_id)
        new_template = base_template.copy()
        
        # Create a new ID for the customized template
        custom_id = f"{template_id}-custom-{len(self.templates)}"
        
        # Update metadata with custom options
        metadata = new_template['metadata'].copy()
        
        # Apply customizations
        for key, value in options.items():
            if key in metadata:
                if isinstance(metadata[key], dict) and isinstance(value, dict):
                    # Deep update for nested dicts
                    for sub_key, sub_value in value.items():
                        metadata[key][sub_key] = sub_value
                else:
                    metadata[key] = value
        
        # Register the customized template
        self.register_template(
            template_id=custom_id,
            template_class=new_template['class'],
            document_class=new_template['document_class'],
            metadata=metadata
        )
        
        return custom_id