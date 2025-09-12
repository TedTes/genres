"""
File storage utilities for generated resume documents.
Supports local storage and S3 cloud storage.
"""

import os
import boto3
import hashlib
import asyncio
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from flask import current_app
from botocore.exceptions import ClientError, NoCredentialsError
import re
from schemas import OptimizedResume


class FileStorageError(Exception):
    """Custom exception for file storage operations."""
    pass


class S3StorageManager:
    """Handles S3 storage operations for resume files."""
    
    def __init__(self):
        self.aws_access_key = current_app.config.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = current_app.config.get('AWS_SECRET_ACCESS_KEY')
        self.aws_region = current_app.config.get('AWS_REGION', 'us-east-1')
        self.bucket_name = current_app.config.get('AWS_S3_BUCKET')
        
        if not all([self.aws_access_key, self.aws_secret_key, self.bucket_name]):
            self.s3_enabled = False
            print("⚠️  S3 not configured. Using local storage fallback.")
        else:
            self.s3_enabled = True
            self._init_s3_client()
    
    def _init_s3_client(self):
        """Initialize S3 client with credentials."""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            
            # Test connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✅ S3 connection established: {self.bucket_name}")
            
        except (ClientError, NoCredentialsError) as e:
            print(f"❌ S3 initialization failed: {str(e)}")
            self.s3_enabled = False
    
    async def upload_file(
        self,
        file_bytes: bytes,
        file_key: str,
        content_type: str,
        metadata: Dict[str, str] = None
    ) -> str:
        """
        Upload file to S3 and return public URL.
        
        Args:
            file_bytes: File content as bytes
            file_key: S3 object key (path)
            content_type: MIME type
            metadata: Optional file metadata
            
        Returns:
            Public S3 URL
            
        Raises:
            FileStorageError: If upload fails
        """
        
        if not self.s3_enabled:
            raise FileStorageError("S3 not configured")
        
        try:
            # Upload with metadata
            upload_args = {
                'Bucket': self.bucket_name,
                'Key': file_key,
                'Body': file_bytes,
                'ContentType': content_type,
                'ACL': 'private'  # Private by default
            }
            
            if metadata:
                upload_args['Metadata'] = metadata
            
            # Perform upload
            self.s3_client.put_object(**upload_args)
            
            # Generate public URL (you might want presigned URLs instead)
            url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{file_key}"
            
            print(f"✅ File uploaded to S3: {file_key}")
            return url
            
        except ClientError as e:
            error_msg = f"S3 upload failed: {str(e)}"
            print(f"❌ {error_msg}")
            raise FileStorageError(error_msg)
    
    async def generate_presigned_url(
        self,
        file_key: str,
        expiration: int = 3600
    ) -> str:
        """
        Generate presigned URL for secure file access.
        
        Args:
            file_key: S3 object key
            expiration: URL expiration in seconds (default 1 hour)
            
        Returns:
            Presigned URL
        """
        
        if not self.s3_enabled:
            raise FileStorageError("S3 not configured")
        
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_key},
                ExpiresIn=expiration
            )
            
            return presigned_url
            
        except ClientError as e:
            error_msg = f"Presigned URL generation failed: {str(e)}"
            print(f"❌ {error_msg}")
            raise FileStorageError(error_msg)
    
    def delete_file(self, file_key: str) -> bool:
        """
        Delete file from S3.
        
        Args:
            file_key: S3 object key to delete
            
        Returns:
            True if successful, False otherwise
        """
        
        if not self.s3_enabled:
            return False
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
            print(f"🗑️  Deleted S3 file: {file_key}")
            return True
            
        except ClientError as e:
            print(f"❌ S3 delete failed: {str(e)}")
            return False


class LocalStorageManager:
    """Handles local file storage as fallback."""
    
    def __init__(self):
        self.storage_dir = os.path.join(os.getcwd(), 'generated_resumes', 'optimized')
        os.makedirs(self.storage_dir, exist_ok=True)
    
    async def save_file(
        self,
        file_bytes: bytes,
        filename: str,
        metadata: Dict[str, str] = None
    ) -> str:
        """
        Save file locally and return file path.
        
        Args:
            file_bytes: File content
            filename: Local filename
            metadata: Optional metadata (saved as .meta file)
            
        Returns:
            Local file path
        """
        
        file_path = os.path.join(self.storage_dir, filename)
        
        try:
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            
            # Save metadata if provided
            if metadata:
                meta_path = file_path + '.meta'
                with open(meta_path, 'w') as f:
                    import json
                    json.dump(metadata, f, indent=2)
            
            print(f"💾 File saved locally: {filename}")
            return file_path
            
        except Exception as e:
            error_msg = f"Local storage failed: {str(e)}"
            print(f"❌ {error_msg}")
            raise FileStorageError(error_msg)


class ResumeStorageService:
    """Main storage service that handles both S3 and local storage."""
    
    def __init__(self):
        self.s3_manager = S3StorageManager()
        self.local_manager = LocalStorageManager()
    
    async def store_resume_files(
        self,
        docx_bytes: bytes,
        pdf_bytes: Optional[bytes],
        user_id: str,
        resume_hash: str,
        contact_info: Dict[str, str] = None
    ) -> Dict[str, Optional[str]]:
        """
        Store resume files using best available storage method.
        
        Args:
            docx_bytes: DOCX file content
            pdf_bytes: PDF file content (optional)
            user_id: User identifier
            resume_hash: Unique resume hash
            contact_info: Contact info for filename generation
            
        Returns:
            Dictionary with file URLs/paths
        """
        
        print(f"💾 Storing resume files for user {user_id}...")
        
        # Generate filenames
        contact_name = contact_info.get('name', 'Resume') if contact_info else 'Resume'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        docx_filename = f"{contact_name}_{timestamp}_optimized.docx"
        pdf_filename = f"{contact_name}_{timestamp}_optimized.pdf" if pdf_bytes else None
        
        # Clean filenames
        docx_filename = self._sanitize_filename(docx_filename)
        if pdf_filename:
            pdf_filename = self._sanitize_filename(pdf_filename)
        
        # Metadata
        metadata = {
            'user_id': user_id,
            'resume_hash': resume_hash,
            'generated_at': datetime.now().isoformat(),
            'file_type': 'optimized_resume'
        }
        
        urls = {}
        
        try:
            # Try S3 first
            if self.s3_manager.s3_enabled:
                urls = await self._store_to_s3(
                    docx_bytes, pdf_bytes, user_id, resume_hash,
                    docx_filename, pdf_filename, metadata
                )
            else:
                # Fallback to local storage
                urls = await self._store_locally(
                    docx_bytes, pdf_bytes,
                    docx_filename, pdf_filename, metadata
                )
            
            print(f"✅ Resume files stored successfully")
            return urls
            
        except Exception as e:
            print(f"❌ Storage failed: {str(e)}")
            # Try local storage as final fallback
            try:
                urls = await self._store_locally(
                    docx_bytes, pdf_bytes,
                    docx_filename, pdf_filename, metadata
                )
                print("✅ Fallback to local storage successful")
                return urls
            except Exception as fallback_error:
                raise FileStorageError(f"All storage methods failed: {str(fallback_error)}")
    
    async def _store_to_s3(
        self,
        docx_bytes: bytes,
        pdf_bytes: Optional[bytes],
        user_id: str,
        resume_hash: str,
        docx_filename: str,
        pdf_filename: Optional[str],
        metadata: Dict[str, str]
    ) -> Dict[str, Optional[str]]:
        """Store files to S3."""
        
        # S3 key structure: resumes/{user_id}/{resume_hash}/filename
        docx_key = f"resumes/{user_id}/{resume_hash}/{docx_filename}"
        
        # Upload DOCX
        docx_url = await self.s3_manager.upload_file(
            docx_bytes, docx_key, 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            metadata
        )
        
        # Upload PDF if provided
        pdf_url = None
        if pdf_bytes and pdf_filename:
            pdf_key = f"resumes/{user_id}/{resume_hash}/{pdf_filename}"
            pdf_url = await self.s3_manager.upload_file(
                pdf_bytes, pdf_key, 'application/pdf', metadata
            )
        
        return {
            'docx_url': await self.s3_manager.generate_presigned_url(docx_key),
            'pdf_url': await self.s3_manager.generate_presigned_url(pdf_key) if pdf_url else None
        }
    
    async def _store_locally(
        self,
        docx_bytes: bytes,
        pdf_bytes: Optional[bytes],
        docx_filename: str,
        pdf_filename: Optional[str],
        metadata: Dict[str, str]
    ) -> Dict[str, Optional[str]]:
        """Store files locally."""
        
        # Save DOCX
        docx_path = await self.local_manager.save_file(docx_bytes, docx_filename, metadata)
        
        # Save PDF if provided
        pdf_path = None
        if pdf_bytes and pdf_filename:
            pdf_path = await self.local_manager.save_file(pdf_bytes, pdf_filename, metadata)
        
        return {
            'docx_url': f"/download/resume/{docx_filename}",  # Will need route for this
            'pdf_url': f"/download/resume/{pdf_filename}" if pdf_path else None
        }
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove or replace unsafe characters
        safe_filename = re.sub(r'[^\w\s.-]', '', filename)
        safe_filename = re.sub(r'\s+', '_', safe_filename)
        return safe_filename
    
    @staticmethod
    def generate_resume_hash(
        resume_text: str,
        jd_text: str,
        options: Dict[str, Any] = None
    ) -> str:
        """
        Generate unique hash for resume+JD combination.
        
        Args:
            resume_text: Original resume text
            jd_text: Job description text
            options: Optimization options
            
        Returns:
            SHA256 hash string
        """
        
        # Create hash input
        hash_input = f"{resume_text}|{jd_text}"
        if options:
            hash_input += f"|{str(sorted(options.items()))}"
        
        # Generate SHA256 hash
        hash_bytes = hash_input.encode('utf-8')
        hash_object = hashlib.sha256(hash_bytes)
        
        return hash_object.hexdigest()[:16]  # Use first 16 characters


# Sync wrappers
def store_resume_files_sync(
    docx_bytes: bytes,
    pdf_bytes: Optional[bytes],
    user_id: str,
    resume_hash: str,
    contact_info: Dict[str, str] = None
) -> Dict[str, Optional[str]]:
    """Synchronous wrapper for store_resume_files."""
    storage = ResumeStorageService()
    return asyncio.run(storage.store_resume_files(
        docx_bytes, pdf_bytes, user_id, resume_hash, contact_info
    ))


def generate_resume_hash_sync(
    resume_text: str,
    jd_text: str,
    options: Dict[str, Any] = None
) -> str:
    """Synchronous wrapper for generate_resume_hash."""
    return ResumeStorageService.generate_resume_hash(resume_text, jd_text, options)