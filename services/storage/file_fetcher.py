from .supabase_client import SupabaseStorage

class FileFetcher:
    """Simple file fetcher for template files"""
    
    def __init__(self):
        self.storage = SupabaseStorage()
    
    def fetch_template_skeleton(self, skeleton_handle: str):
        """Fetch main template HTML file"""
        if not skeleton_handle:
            return None
        return self.storage.download_file(skeleton_handle)
    
    def fetch_partial(self, template_id: str, section_name: str):
        """Fetch a partial file with fallback to global library"""
        # Try template-specific partial first
        template_path = f"templates/{template_id}/v1/partials/{section_name}.html"
        content = self.storage.download_file(template_path)
        
        if content:
            return content
        
        # Fallback to global library
        library_path = f"templates/_library/v1/partials/{section_name}.html"
        return self.storage.download_file(library_path)
    
    def get_asset_urls(self, template_id: str):
        """Get URLs for CSS assets"""
        library_css = self.storage.get_public_url("templates/_library/v1/assets/shared.css")
        theme_css = self.storage.get_public_url(f"templates/{template_id}/v1/assets/theme.css")
        
        return {
            'library_css': library_css,
            'theme_css': theme_css
        }