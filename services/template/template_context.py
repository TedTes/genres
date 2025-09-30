class TemplateContext:
    """Prepare rendering context for templates with data-driven approach"""
    
    def __init__(self, template_resolver):
        self.resolver = template_resolver
    
    def build_context(self, template_id: str, resume_data: dict = None, user_overrides: dict = None):
        """
        Build complete context for template rendering.
        Data-driven: analyzes resume data first, then fetches only relevant partials.
        """
        if not resume_data:
            return None
        
        # Step 1: Use resolver's data-driven method to get everything we need
        resolved = self.resolver.resolve_template_with_data(template_id, resume_data)
        if not resolved:
            return None
        
        # Step 2: Map user's sections to template's layout structure
        layout = resolved['metadata']['layout']
        sections_in_data = resolved['sections']
        section_placement = self._map_sections_to_layout(sections_in_data, layout)
        
        # Step 3: Merge design tokens with user overrides
        design_tokens = resolved['metadata']['design_tokens'].copy()
        if user_overrides:
            design_tokens.update(user_overrides)
        
        # Step 4: Build final rendering context
        context = {
            'template_id': template_id,
            'skeleton': resolved['skeleton'],
            'partials': resolved['partials'],
            'layout': layout,
            'sections': sections_in_data,
            'section_placement': section_placement,
            'design_tokens': design_tokens,
            'assets': resolved['assets'],
            'resume_data': resume_data
        }
        
        return context
    
    def _map_sections_to_layout(self, sections: list, layout: dict):
        """
        Map user's available sections to template's layout positions.
        Determines which sections go in sidebar vs main area.
        """
        layout_type = layout.get('type', 'one_column')
        
        # Get layout preferences for section placement
        sidebar_preference = layout.get('sidebar', [])
        main_preference = layout.get('main', [])
        
        # Map sections based on layout preferences
        sidebar_sections = []
        main_sections = []
        
        for section in sections:
            # Check if section is preferred in sidebar
            if section in sidebar_preference:
                sidebar_sections.append(section)
            # Check if section is preferred in main
            elif section in main_preference:
                main_sections.append(section)
            else:
                # Default: put in main if not specified
                main_sections.append(section)
        
        # Maintain order from layout preferences
        sidebar_sections = self._order_by_preference(sidebar_sections, sidebar_preference)
        main_sections = self._order_by_preference(main_sections, main_preference)
        
        return {
            'sidebar': sidebar_sections,
            'main': main_sections
        }
    
    def _order_by_preference(self, sections: list, preference_order: list):
        """
        Order sections according to template's preference order.
        Sections not in preference list are appended at the end.
        """
        ordered = []
        
        # First, add sections in preference order
        for preferred in preference_order:
            if preferred in sections:
                ordered.append(preferred)
        
        # Then add any remaining sections not in preference
        for section in sections:
            if section not in ordered:
                ordered.append(section)
        
        return ordered