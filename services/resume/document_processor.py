"""
Document ingestion and parsing utilities.
Handles DOCX, PDF, and text input for resume processing.
"""

import os
import tempfile
from typing import Any,Dict, List, Optional, Tuple
import mammoth
from pydantic import BaseModel
from providers import get_models
from .schemas import create_json_prompt
import requests
# For PDF support
try:
    import pypdf
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("Warning: pypdf not installed. PDF support disabled.")


class DocumentChunk(BaseModel):
    """Represents a chunk of resume text with metadata."""
    
    text: str
    section: str  # 'summary', 'experience', 'education', 'skills'
    chunk_index: int
    token_count: Optional[int] = None
    metadata: Dict[str, Any] = {}


class ParsedResume(BaseModel):
    """Structured representation of a parsed resume."""
    
    raw_text: str
    sections: Dict[str, str] = {}
    experience_items: List[Dict[str, Any]] = []
    education_items: List[Dict[str, str]] = []
    skills: List[str] = []
    contact_info: Dict[str, str] = {}
    chunks: List[DocumentChunk] = []


class DocumentProcessor:
      """Main document processing class that handles parsing and LLM normalization."""

      def __init__(self):
         self.embedder, self.chat_model = get_models()    

      async def process_document(
            self,
            text: Optional[str] = None,
            docx_url: Optional[str] = None, 
            pdf_url: Optional[str] = None
        ) -> ParsedResume :
            """
                Main docuemnt processor function that handles all resume input types.
                
                Args:
                    text: Raw text input
                    docx_url: Path or URL to DOCX file
                    pdf_url: Path or URL to PDF file
                    
                Returns:
                    ParsedResume object with structured data
                    
                Raises:
                    ValueError: If no input provided or processing fails
            """
            if text:
                raw_text = text
                input_type = "text"
            elif docx_url:
                raw_text = await self.extract_text_from_docx(docx_url)
                input_type = "docx"
            elif pdf_url:
                raw_text = await self.extract_text_from_pdf(pdf_url)
                input_type = "pdf"
            else:
                raise ValueError("No input provided")

            print(f"📄 Processing resume from {input_type} ({len(raw_text)} characters)")


            # Parse the text into structured format
            parsed = await self._normalize_with_llm(raw_text,input_type)
            return parsed
      def process_document_sync(self, *args, **kwargs):
            # Sync wrappers for non-async code
            """Synchronous wrapper for ingest_resume."""
            import asyncio
            return asyncio.run(self.process_document(*args, **kwargs))
      async def extract_text_from_docx(self, docx_path: str) -> str:
            """
            Extract text from DOCX file using mammoth.
            
            Args:
                docx_path: Path or URL to DOCX file
                
            Returns:
                Extracted text content
            """
            
            try:
                # Handle URL vs local path
                if docx_path.startswith(('http://', 'https://')):
                    # Download file
                        response = requests.get(docx_path, timeout=30)
                        response.raise_for_status()
                        
                        # Save to temporary file
                        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
                            temp_file.write(response.content)
                            temp_path = temp_file.name
                else:
                    temp_path = docx_path
                
                # Extract text with mammoth
                with open(temp_path, "rb") as docx_file:
                    result = mammoth.extract_raw_text(docx_file)
                    text = result.value
                
                # Clean up temporary file if downloaded
                if docx_path.startswith(('http://', 'https://')):
                    os.unlink(temp_path)
                
                if not text.strip():
                    raise ValueError("DOCX file appears to be empty")
                    
                return text.strip()
                
            except Exception as e:
                raise ValueError(f"Failed to extract text from DOCX: {str(e)}")


      async def extract_text_from_pdf(self, pdf_path: str) -> str:
            """
            Extract text from PDF file using pypdf.
            
            Args:
                pdf_path: Path or URL to PDF file
                
            Returns:
                Extracted text content
            """
            
            if not PDF_SUPPORT:
                raise ValueError("PDF support not available. Install pypdf: pip install pypdf")
            
            try:
                # Handle URL vs local path
                if pdf_path.startswith(('http://', 'https://')):
                    # Download file
                
                    response = requests.get(pdf_path, timeout=30)
                    response.raise_for_status()
                    
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                        temp_file.write(response.content)
                        temp_path = temp_file.name
                else:
                    temp_path = pdf_path
                
                # Extract text with pypdf
                text_parts = []
                with open(temp_path, 'rb') as pdf_file:
                    pdf_reader = pypdf.PdfReader(pdf_file)
                    
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_parts.append(page_text)
                
                # Clean up temporary file if downloaded
                if pdf_path.startswith(('http://', 'https://')):
                    os.unlink(temp_path)
                
                full_text = '\n'.join(text_parts)
                
                if not full_text.strip():
                    raise ValueError("PDF file appears to be empty or text could not be extracted")
                    
                return full_text.strip()
                
            except Exception as e:
                raise ValueError(f"Failed to extract text from PDF: {str(e)}")
      async def _normalize_with_llm(self, raw_text: str, file_type: str):
            """
            Use LLM to normalize and structure resume text.
            
            Args:
                raw_text: Raw extracted text from document
                file_type: Source file type for context
                
            Returns:
                Structured and normalized resume data
            """
            
            
            system_message, user_message = self.create_normalization_prompt(raw_text, file_type)
            messages = create_json_prompt(system_message, user_message)
            
            response = await self.chat_model.chat(
                messages,
                temperature=0.1,  # Low temperature for accuracy
                max_tokens=8000
            )
            # Validate against schema with auto-retry
            validated_resume = await validate_json_with_retry(
                response, 
                NormalizedResume, 
                self.chat_model,
                max_retries=2
            )
            validated_resume.parsed_date = datetime.now().isoformat()
            validated_resume.source_format = file_type
            return validated_resume.dict()



      def create_normalization_prompt(raw_text: str, file_type: str) -> tuple[str, str]:
        """
        Create system and user messages for resume normalization with explicit schema.
        
        Args:
            raw_text: Raw extracted text from document
            file_type: Source file type for context
            
        Returns:
            Tuple of (system_message, user_message)
        """
        
        # Get the schema example from NormalizedResume
        schema_example = NormalizedResume.Config.schema_extra["example"]
        
        system_message = f"""You are an expert resume parser and data extraction specialist. Your task is to extract and normalize resume information from raw text that may contain formatting issues or OCR errors.

        CRITICAL INSTRUCTIONS:
        1. Extract ALL available information accurately
        2. Normalize dates to consistent format (YYYY-YYYY or MM/YYYY-MM/YYYY)
        3. Clean up garbled text and fix obvious OCR errors
        4. Structure work experience chronologically (most recent first)
        5. Separate and categorize all skills appropriately
        6. Extract contact information comprehensively
        7. Preserve all quantifiable achievements and metrics
        8. If information is unclear or missing, use null or empty arrays
        9. Return ONLY valid JSON matching the EXACT schema below

        REQUIRED JSON SCHEMA - You MUST follow this structure exactly:

        {json.dumps(schema_example, indent=2)}

        SCHEMA RULES:
        - contact_information: REQUIRED - extract name, email, phone, location, social profiles
        - work_experience: Array of jobs, most recent first, with detailed responsibilities
        - education: Array of educational background with degrees, institutions, dates
        - skills: Categorize into technical_skills, programming_languages, frameworks, tools, etc.
        - professional_summary: Extract or infer from objective/summary sections
        - certifications: Professional certifications with issuing organizations
        - projects: Personal/side projects mentioned
        - additional_sections: For non-standard sections like Patents, Publications, Awards, Volunteer Work

        FIELD MAPPING GUIDANCE:
        - Put programming languages in "programming_languages", not "technical_skills"
        - Separate frameworks/libraries from core programming languages  
        - Cloud platforms (AWS, GCP, Azure) go in "cloud_platforms"
        - Databases get their own "databases" category
        - Soft skills like "communication" go in "soft_skills"
        - Put unusual sections (Patents, Publications, Speaking, Military, etc.) in "additional_sections"

        ADDITIONAL SECTIONS FORMAT:
        For any non-standard sections, use this structure:
        {{
        "section_title": "exact title from resume",
        "section_type": "category like 'publications', 'awards', 'volunteer'", 
        "content": {{ flexible structure preserving all information }}
        }}

        Return ONLY the JSON object, no explanations or markdown formatting."""

        user_message = f"""Parse and normalize this resume text extracted from a {file_type} file:

        RAW TEXT:
        {raw_text}

        SPECIFIC EXTRACTION REQUIREMENTS:
        - Fix obvious formatting and OCR errors
        - Extract complete contact information (name, email, phone, location, all social profiles)
        - Structure work experience with normalized date formats and detailed responsibilities
        - Categorize skills into appropriate technical subcategories
        - Capture education with degrees, institutions, graduation dates, honors
        - Extract certifications with issuing organizations and dates
        - Identify projects with technologies and descriptions
        - Preserve ALL quantifiable metrics and achievements exactly as stated
        - Map unusual sections (Patents, Publications, Awards, etc.) to additional_sections

        Return the complete structured JSON following the exact schema provided:"""

        return system_message, user_message


