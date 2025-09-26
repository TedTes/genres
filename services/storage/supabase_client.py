import os
from supabase import create_client

class SupabaseStorage:
    """Simple Supabase Storage client"""
    
    def __init__(self):
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY') 
        self.client = create_client(url, key)
        self.bucket_name = os.getenv('SUPABASE_BUCKET_NAME', 'resume-templates')
    
    def download_file(self, file_path: str):
        """Download file content from storage"""
        try:
            response = self.client.storage.from_(self.bucket_name).download(file_path)
            return response.decode('utf-8')
        except Exception as e:
            print(f"Error downloading {file_path}: {e}")
            return None
    
    def get_public_url(self, file_path: str):
        """Get public URL for file (for CSS assets)"""
        try:
            response = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
            return response
        except Exception as e:
            print(f"Error getting URL for {file_path}: {e}")
            return None