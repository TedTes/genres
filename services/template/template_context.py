class TemplateContext:
    """Prepare rendering context for templates"""
    
    def __init__(self, template_resolver):
        self.resolver = template_resolver
    
    def build_context(self, template_id: str, resume_data: dict = None, user_overrides: dict = None):
        """Build complete context for template rendering"""
        # Resolve template
        template = self.resolver.resolve_template(template_id)
        if not template:
            return None
        
        # Get required sections from template metadata
        supported_sections = template['metadata']['supported_sections']
        required_sections = supported_sections.get('required', [])
        optional_sections = supported_sections.get('optional', [])
        all_sections = required_sections + optional_sections
        
        # Resolve all partials
        partials = self.resolver.resolve_all_partials(template_id, all_sections)
        
        # Merge design tokens with user overrides
        design_tokens = template['metadata']['design_tokens'].copy()
        if user_overrides:
            design_tokens.update(user_overrides)
        
        # Build rendering context
        context = {
            'template_id': template_id,
            'skeleton': template['skeleton'],
            'partials': partials,
            'layout': template['metadata']['layout'],
            'supported_sections': supported_sections,
            'design_tokens': design_tokens,
            'assets': template['assets'],
            'resume_data': resume_data or {}
        }
        
        return context