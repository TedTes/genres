from jinja2 import Environment, DictLoader, select_autoescape
from datetime import datetime

class RenderHandler:
    """
    Library-independent template rendering handler.
    Uses Jinja2 (already part of Flask) to render resume templates.
    """
    
    def __init__(self):
        """Initialize Jinja2 environment with custom configuration"""
        self.env = None
    
    def render(self, context: dict):
        """
        Render template with provided context.
        
        Args:
            context: Dictionary containing:
                - skeleton: Main template HTML
                - partials: Dict of {section_name: partial_html}
                - resume_data: User's resume data
                - design_tokens: Colors, fonts, etc.
                - assets: CSS URLs
                - section_placement: {'sidebar': [...], 'main': [...]}
                
        Returns:
            Rendered HTML string
        """
        if not context:
            return None
        
        try:
            # Step 1: Setup Jinja2 environment with partials
            self._setup_environment(context)
            
            # Step 2: Prepare template variables
            template_vars = self._prepare_template_variables(context)
            
            # Step 3: Render skeleton with variables
            skeleton_template = self.env.from_string(context['skeleton'])
            rendered_html = skeleton_template.render(**template_vars)
            
            return rendered_html
            
        except Exception as e:
            print(f"Rendering error: {e}")
            return None
    
    def _setup_environment(self, context: dict):
        """Setup Jinja2 environment with partials and custom filters"""
        # Create DictLoader with all partials
        partials = context.get('partials', {})
        loader = DictLoader(partials)
        
        # Create Jinja2 environment
        self.env = Environment(
            loader=loader,
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['date_format'] = self._filter_date_format
        self.env.filters['list_join'] = self._filter_list_join
        self.env.filters['default_if_empty'] = self._filter_default_if_empty
    
    def _prepare_template_variables(self, context: dict):
        """
        Prepare all variables that will be available in Jinja2 templates.
        Dynamically extracts ALL resume data sections without hardcoding.
        """
        resume_data = context.get('resume_data', {})
        
        # Start with template configuration
        template_vars = {
            # Template configuration
            'layout': context.get('layout', {}),
            'sections': context.get('sections', []),
            'section_placement': context.get('section_placement', {}),
            
            # Design tokens (colors, fonts)
            'tokens': context.get('design_tokens', {}),
            
            # Asset URLs
            'assets': context.get('assets', {}),
            
            # Partials dictionary (for dynamic includes)
            'partials': context.get('partials', {}),
            
            # Helper functions
            'now': datetime.now(),
            'current_year': datetime.now().year
        }
        
        # Dynamically add ALL sections from resume_data
        # This allows any section to be added without changing code
        if resume_data:
            for section_key, section_value in resume_data.items():
                template_vars[section_key] = section_value
        
        return template_vars
    
    # Custom Jinja2 Filters
    
    def _filter_date_format(self, date_value, format_string='%B %Y'):
        """
        Format date strings consistently.
        
        Usage in template: {{ experience.startDate | date_format }}
        """
        if not date_value:
            return ''
        
        try:
            # Handle various date formats
            if isinstance(date_value, datetime):
                return date_value.strftime(format_string)
            elif isinstance(date_value, str):
                # Try to parse common date formats
                for fmt in ['%Y-%m-%d', '%Y-%m', '%Y']:
                    try:
                        dt = datetime.strptime(date_value, fmt)
                        return dt.strftime(format_string)
                    except ValueError:
                        continue
                # If parsing fails, return original
                return date_value
            else:
                return str(date_value)
        except Exception:
            return str(date_value)
    
    def _filter_list_join(self, value, separator=', '):
        """
        Join list items with separator.
        
        Usage in template: {{ skills | list_join(', ') }}
        """
        if not value:
            return ''
        
        if isinstance(value, list):
            # Handle list of strings
            if all(isinstance(item, str) for item in value):
                return separator.join(value)
            # Handle list of dicts (extract name field)
            elif all(isinstance(item, dict) for item in value):
                names = [item.get('name', '') for item in value if item.get('name')]
                return separator.join(names)
        
        return str(value)
    
    def _filter_default_if_empty(self, value, default=''):
        """
        Return default value if empty.
        
        Usage in template: {{ basics.location | default_if_empty('Remote') }}
        """
        if not value:
            return default
        
        if isinstance(value, str) and not value.strip():
            return default
        
        if isinstance(value, (list, dict)) and not value:
            return default
        
        return value