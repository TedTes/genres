from .template_loader import TemplateLoader
from ..storage.file_fetcher import FileFetcher

class TemplateResolver:
    """Unified template resolution system with data-driven partial fetching"""
    
    def __init__(self):
        self.loader = TemplateLoader()
        self.fetcher = FileFetcher()
    
    def resolve_template(self, template_id: str):
        """Get complete template: metadata + skeleton + asset URLs"""
        # Get template metadata from database
        template_meta = self.loader.load_template_metadata(template_id)
        if not template_meta:
            return None
        
        # Get skeleton HTML from storage
        skeleton_html = self.fetcher.fetch_template_skeleton(template_meta['skeleton_handle'])
        if not skeleton_html:
            return None
        
        # Get asset URLs
        asset_urls = self.fetcher.get_asset_urls(template_id)
        
        return {
            'metadata': template_meta,
            'skeleton': skeleton_html,
            'assets': asset_urls
        }
    
    def resolve_partials(self, template_id: str, section_names: list):
        """Resolve specific partials for a template with fallback"""
        partials = {}
        
        for section in section_names:
            partial_content = self.fetcher.fetch_partial(template_id, section)
            if partial_content:
                partials[section] = partial_content
        
        return partials
    
    def _detect_sections(self, resume_data: dict):
        """Detect which sections have content in resume data"""
        if not resume_data:
            return []
        
        sections_with_data = []
        
        for section_key, section_value in resume_data.items():
            # Check if section has meaningful content
            has_content = False
            
            if section_value is None:
                has_content = False
            elif isinstance(section_value, list):
                # Array: check if not empty
                has_content = len(section_value) > 0
            elif isinstance(section_value, dict):
                # Object: check if has any content
                has_content = bool(section_value)
            elif isinstance(section_value, str):
                # String: check if not empty/whitespace
                has_content = bool(section_value.strip())
            else:
                # Other types: check truthiness
                has_content = bool(section_value)
            
            if has_content:
                sections_with_data.append(section_key)
        
        return sections_with_data
    
    def resolve_template_with_data(self, template_id: str, resume_data: dict):
        """
        Complete data-driven template resolution.
        Detects sections from resume data and fetches only relevant partials.
        """
        # Step 1: Detect which sections user has data for
        sections_in_data = self._detect_sections(resume_data)
        
        if not sections_in_data:
            return None
        
        # Step 2: Get template metadata from database
        template_meta = self.loader.load_template_metadata(template_id)
        if not template_meta:
            return None
        
        # Step 3: Get skeleton HTML from storage
        skeleton_html = self.fetcher.fetch_template_skeleton(template_meta['skeleton_handle'])
        if not skeleton_html:
            return None
        
        # Step 4: Fetch ONLY partials for sections user has data for
        partials = self.resolve_partials(template_id, sections_in_data)
        
        # Step 5: Get asset URLs
        asset_urls = self.fetcher.get_asset_urls(template_id)
        
        # Return complete context ready for rendering
        return {
            'metadata': template_meta,
            'skeleton': skeleton_html,
            'assets': asset_urls,
            'partials': partials,
            'sections': sections_in_data,  # List of sections user has data for
            'resume_data': resume_data
        }
    
    def get_template_gallery_data(self):
        """Get all templates for frontend gallery"""
        return self.loader.get_all_active_templates()