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
from helpers import validate_json_with_retry
from schemas import NormalizedResumeSchema
import requests
import json
from datetime import datetime
from utils import get_optimization_prompt,extract_json_from_response,get_normalization_prompt,get_json_prompt
# For PDF support
try:
    import pypdf
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("Warning: pypdf not installed. PDF support disabled.")



class DocumentProcessor:
      """Main document processing class that handles parsing and LLM normalization."""

      def __init__(self):
         self.embedder, self.chat_model = get_models()    

      async def process_document(
            self,
            text: Optional[str] = None,
            docx_url: Optional[str] = None, 
            pdf_url: Optional[str] = None
        ) :
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


            print("normalized raw text.....")
            # Parse the text into structured format
            parsed = await self._normalize_with_llm(raw_text,input_type)
            print("normalizing raw text done")
            
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
            
            
            system_message, user_message = get_normalization_prompt(raw_text, file_type)
            messages = get_json_prompt(system_message, user_message)
            response = await self.chat_model.chat(
                messages,
                temperature=0.1,  # Low temperature for accuracy
                max_tokens=8000
            )
            # Validate against schema with auto-retry
            validated_resume = await validate_json_with_retry(
                response, 
                NormalizedResumeSchema, 
                self.chat_model,
                max_retries=2
            )
            validated_resume.parsed_date = datetime.now().isoformat()
            validated_resume.source_format = file_type
            return validated_resume.dict()

      async def analyze_and_optimize(
            self,
            normalized_resume: Dict[str, Any],
            jd_text: str,
            jd_title: Optional[str] = None,
            optimization_focus: str = "professional-concise"
      ):
        """
        Perform comprehensive gap analysis and resume optimization in one LLM call.
        
        Args:
            normalized_resume: MultiNicheResume dictionary structure
            jd_text: Job description text
            jd_title: Optional job title
            optimization_focus: Optimization tone/style
            
        Returns:
            ComprehensiveOptimizationResult with gap analysis and optimized resume
        """
        
        print(f"🔍🤖 Starting comprehensive gap analysis + optimization...")
        print(f"📊 Resume industry context: {normalized_resume.get('industry_context', {}).get('primary_industry', 'Unknown')}")
        
        try:
            # Create the comprehensive prompt
            system_message, user_message = get_optimization_prompt(
                normalized_resume, jd_text, jd_title, optimization_focus
            )
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
            
            # Execute LLM call with optimized parameters
            response = await self.chat_model.chat(
                messages=messages,
                temperature=0.2,  # Low temperature for consistency and accuracy
                max_tokens=8000,  # Large response needed for comprehensive output
                top_p=0.9
            )
            
            print(f"📝 Generated comprehensive analysis ({len(response)} chars)")
            
            # Extract and validate JSON response
            json_response = extract_json_from_response(response)
            
            # Validate against schema with retry capability
            validated_result = await validate_json_with_retry(
                json_str=json_response,
                schema_class=ComprehensiveOptimizationResult,
                chat_model=self.chat_model,
                max_retries=2
            )
            
            print(f"✅ Gap analysis + optimization complete")
            print(f"📈 Match score: {validated_result.gap_analysis.get('overall_match_score', 'N/A')}")
            print(f"🔧 Total changes: {validated_result.optimization_metadata.get('total_changes', 'N/A')}")
            
            return validated_result
            
        except Exception as e:
            print(f"❌ LLM gap analysis + optimization failed: {str(e)}")
            raise ValueError(f"Failed to analyze and optimize resume: {str(e)}")





