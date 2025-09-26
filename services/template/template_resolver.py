from .template_loader import TemplateLoader
from ..storage.file_fetcher import FileFetcher

class TemplateResolver:
    """Unified template resolution system"""
    
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
    
    def resolve_all_partials(self, template_id: str, section_names: list):
        """Resolve all partials for a template with fallback"""
        partials = {}
        
        for section in section_names:
            partial_content = self.fetcher.fetch_partial(template_id, section)
            if partial_content:
                partials[section] = partial_content
        
        return partials
    
    def get_template_gallery_data(self):
        """Get all templates for frontend gallery"""
        return self.loader.get_all_active_templates()