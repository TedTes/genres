from flask import Response
import spacy
from jinja2 import  FileSystemLoader
from flask import Flask,request,render_template,jsonify,current_app
from io import BytesIO
from weasyprint import HTML, CSS
import os
import time
from db import db
from typing import Dict, Any,Optional,Tuple,List
from schemas import (
    ResumeInput, JDInput, OptimizationOptions, OptimizationResult
)
import asyncio
from models import Resume , ResumeOptimization,User
from datetime import datetime
from services.resume.cache import get_enhanced_cache
from services.resume.document_processor import DocumentProcessor
from services.resume.storage import store_resume_files_sync, generate_resume_hash_sync
from services.resume.embedding import perform_gap_analysis_sync
from services.resume.rewrite import optimize_resume_sync
from services.resume.explain import generate_explanations_sync
from services.resume.policy import apply_guardrails_sync, score_resume_match
from services.resume.formatting import create_docx_sync, create_pdf_sync

class ResumeOptimizationPipeline:

    def __init__(self):
       self._document_processor = None

    @property
    def document_processor(self):
        if self._document_processor is None:
            self._document_processor = DocumentProcessor()
        return self._document_processor
    async def _run_optimization_pipeline(
        self,
        resume_input: ResumeInput,
        jd_input: JDInput, 
        options: OptimizationOptions,
        user_id:str
    ) -> Dict[str, Any]:
        """
        Execute the complete optimization pipeline - simplified without user tracking.
        
        Args:
            resume_input: Resume input data
            jd_input: Job description input
            options: Optimization options
            request_hash: Unique request identifier
            
        Returns:
            Complete optimization result
        """
        try:
            request_start_time = time.time()
            # Step 1: Ingest and parse resume
            print("📄 Step 1: Ingesting resume...")
            document_processor_instance = self.document_processor
    
            parsed_resume = await document_processor_instance.process_document(
                text=resume_input.text,
                docx_url=resume_input.docx_url,
                pdf_url=resume_input.pdf_url
            )
            # print("parsed _resuem")
            # print(parsed_resume)
            # Generate request hash for caching and tracking
            print("🔍 Step 2: Generating request hash...")
            request_hash = generate_resume_hash_sync(
                resume_text=resume_input.text ,
                jd_text=jd_input.text,
                options=options.dict()
            )
        
            print("🔍 Step 3: Analyzing gaps and optimizing...")
            comprehensive_result = await self._document_processor.analyze_and_optimize(
                normalized_resume=parsed_resume,  # NormalizedResumeSchema structure
                jd_text=jd_input.text,
                jd_title=jd_input.title,
                optimization_focus=options.tone
            )
            
            model_provider = current_app.config.get('MODEL_PROVIDER', 'unknown')
            
            total_time = (time.time() - request_start_time) * 1000
            # Save to database
            print("saving to database....")
            result_id = self.save_optimization_to_db(
                user_id=user_id,
                resume_input_metadata=resume_input,
                processed_resume=parsed_resume,
                jd_input=jd_input,
                optimization_result=comprehensive_result,
                processing_time_ms=total_time,
                model_provider=model_provider
            )
            print("saving to database done.")

            
            comprehensive_result['processing_time_ms'] = round(total_time, 2)
            print(f"✅ Optimization complete in {total_time:.0f}ms")
            # gap_analysis = extract_gap_analysis(comprehensive_result)
            # optimized_resume = extract_optimized_resume(comprehensive_result)
            # explanations = extract_explanations(comprehensive_result)
            
        
            # print("🛡️  Step 6: Applying guardrails...")
            # clean_resume, policy_violations = apply_guardrails_sync(optimized_resume)
            
        
            # print("📊 Step 7: Calculating scores...")
            # score_breakdown = score_resume_match(
            #     keyword_analysis=gap_analysis['keyword_analysis'],
            #     semantic_analysis=gap_analysis['semantic_analysis'],
            #     gap_analysis=gap_analysis,
            #     resume_sections=parsed_resume.sections
            # )
            
            # print("📄 Step 8: Generating documents...")
            # contact_info = parsed_resume.contact_information
        
            # docx_bytes = create_docx_sync(optimized_resume, contact_info)
            # pdf_bytes = create_pdf_sync(optimized_resume, contact_info) if options.include_pdf else None
            
            # print("💾 Step 9: Storing files...")
            # file_urls = store_resume_files_sync(
            #     docx_bytes=docx_bytes,
            #     pdf_bytes=pdf_bytes,
            #     user_id="anonymous",  # Simplified - no user tracking
            #     resume_hash=request_hash,
            #     contact_info=contact_info
            # )
        
            result = {
                'result_id':result_id,
                # 'match_score': score_breakdown['overall_score'],
                # 'score_breakdown': score_breakdown,
                'request_hash' : request_hash,
                # 'missing_keywords': gap_analysis['missing_keywords'],
                # 'weak_keywords': gap_analysis['weak_keywords'],
                'optimized_resume': comprehensive_result,
                # 'explanations': explanations.dict(),
                # 'artifacts': file_urls,
                # 'model_info': _get_model_info(),
                # 'policy_violations': [v.__dict__ for v in policy_violations],
                'input_type': resume_input.input_type,
             
            }
        

            return result
        finally:
            # Clean up temp files
            for url in [resume_input.pdf_url, resume_input.docx_url]:
                if url and os.path.exists(url):
                    os.unlink(url)


    def _run_optimization_pipeline_sync(self, *args, **kwargs):
       import asyncio
       return  asyncio.run(self._run_optimization_pipeline(*args, **kwargs))

    def calculate_resume_completeness(self,resume_data):
        """
        Calculate completeness percentage of a resume based on filled sections
        """
        if not resume_data:
            return 0
            
        # Define key sections for a complete resume
        key_sections = ['contact', 'summary', 'experience', 'education', 'skills']
        
        # Count completed sections
        completed = sum(1 for section in key_sections if section in resume_data and resume_data[section])
        
        # Calculate percentage
        return int((completed / len(key_sections)) * 100)





    def calculate_skill_match(self,user_skills, job_skills):
        """
        Calculate the match percentage between user skills and job skills.
        
        Parameters:
        - user_skills: List of strings representing user's skills
        - job_skills: Dictionary of job skills with importance scores
        
        Returns:
        - match_percentage: Overall match percentage (0-100)
        - skill_matches: List of dictionaries with skill match details
        """
        if not user_skills or not job_skills:
            return 0, []
        
        # Normalize user skills (convert to lowercase for matching)
        user_skills_normalized = [skill.lower() for skill in user_skills]
        
        # Initialize match metrics
        total_job_importance = sum(job_skills.values())
        total_match_score = 0
        skill_matches = []
        
        # Calculate match for each job skill
        for job_skill, importance in job_skills.items():
            skill_match = 0
            
            # Exact match
            if job_skill.lower() in user_skills_normalized:
                skill_match = 100
            else:
                # Check for partial matches (e.g., "Python" would partially match "Python Programming")
                for user_skill in user_skills_normalized:
                    if job_skill.lower() in user_skill or user_skill in job_skill.lower():
                        # Partial match - score based on similarity
                        skill_match = 70
                        break
            
            # Add to skill matches list
            if skill_match > 0:
                skill_matches.append({
                    "name": job_skill,
                    "match": skill_match,
                    "importance": importance
                })
                
                # Add to total match score, weighted by importance
                total_match_score += (skill_match / 100) * importance
        
        # Calculate overall match percentage
        if total_job_importance > 0:
            overall_match = int((total_match_score / total_job_importance) * 100)
        else:
            overall_match = 0
        
        # Sort skills by importance
        skill_matches.sort(key=lambda x: x["importance"], reverse=True)
        
        # Limit to top skills
        skill_matches = skill_matches[:10]
        
        return overall_match, skill_matches


    def save_optimization_to_db(
        self,
        user_id: int,
        resume_input_metadata: ResumeInput,
        processed_resume: dict,
        jd_input: JDInput,
        optimization_result: dict,
        processing_time_ms: float,
        model_provider: str
    ) -> str:
        """Save optimization results to database and return the ID."""

        try:
            # Create resume record using processed resume data
            resume_record = Resume(
                user_id=user_id,
                title=f"Optimized Resume - {jd_input.title or 'Untitled Job'}",
                resume_data={
                    'processed_resume': processed_resume,  # Store the full normalized resume
                    'original_input_type': resume_input_metadata.input_type,
                    'file_type': resume_input_metadata.input_type,
                    'optimization_date': datetime.utcnow().isoformat()
                },
                template="optimized_standard",
                is_optimized=True,
                last_optimized_at=datetime.utcnow()
            )
            
            db.session.add(resume_record)
            db.session.flush()  # Get ID without committing
            
            # Extract data for optimization record
            gap_analysis = optimization_result.get('gap_analysis', {})
            optimized_resume = optimization_result.get('optimized_resume', {})
            optimization_changes = optimization_result.get('optimization_changes', {})
            optimization_metadata = optimization_result.get('optimization_metadata', {})
            # Create optimization record
            optimization = ResumeOptimization(
                user_id=user_id,
                resume_id=resume_record.id,
                
                # Input data - use processed resume for meaningful preview
                original_resume_data={
                    'processed_resume_preview': {
                        'professional_summary': processed_resume.get('professional_summary', '')[:500],
                        'contact_name': processed_resume.get('contact_information', {}).get('name', ''),
                        'experience_count': len(processed_resume.get('work_experience', [])),
                        'skills_count': len(processed_resume.get('skills', {}).get('specialized_skills', []))
                    },
                    'input_metadata': {
                        'input_type': resume_input_metadata.input_type,
                        'has_pdf': bool(resume_input_metadata.pdf_url),
                        'has_docx': bool(resume_input_metadata.docx_url),
                        'has_text': bool(resume_input_metadata.text)
                    }
                },
                job_description=jd_input.text[:5000] if jd_input.text else None,
                job_title=jd_input.title[:200] if jd_input.title else None,
                company_name=jd_input.company[:200] if jd_input.company else None,
                
                # Optimization settings
                optimization_style=optimization_metadata.get('optimization_focus', 'professional-concise'),
                
                # Results - store the actual optimized resume
                optimized_resume_data={
                    'optimized_resume': optimized_resume,
                    'gap_analysis': gap_analysis,
                    'optimization_changes': optimization_changes,
                    'optimization_metadata': optimization_metadata
                },
                match_score_before=0.0,  # You don't have original score
                match_score_after=float(gap_analysis.get('overall_match_score', 0.0)),
                missing_keywords=gap_analysis.get('keyword_analysis', {}).get('missing_critical', [])[:50],
                added_keywords=optimization_changes.get('skills_changes', {}).get('additions', [])[:50],
                
                # Files - these would be generated later in your pipeline
                docx_url=None,  # To be updated after file generation
                pdf_url=None,   # To be updated after file generation
                
                # Processing info
                processing_time_ms=processing_time_ms,
                model_provider=model_provider,
                created_at=datetime.utcnow()
            )
            
            db.session.add(optimization)
            db.session.commit()
            
            # Update user stats
            user = User.query.get(user_id)
            if user:
                user.optimization_count = (user.optimization_count or 0) + 1
                user.last_optimization_at = datetime.utcnow()
                db.session.commit()
            
            print(f"✅ Optimization saved to DB with ID: {optimization.id}")
            return str(optimization.id)
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Failed to save optimization to DB: {str(e)}")
            raise



    def save_temp_file(self,uploaded_file):
        """Save uploaded file temporarily for processing."""
        import tempfile
        import os
        
        # Create temp file with proper extension
        file_ext = '.pdf' if 'pdf' in uploaded_file.content_type else '.docx'
        fd, temp_path = tempfile.mkstemp(suffix=file_ext)
        
        try:
            with os.fdopen(fd, 'wb') as tmp_file:
                uploaded_file.seek(0)  # Reset file pointer
                tmp_file.write(uploaded_file.read())
            
            return temp_path
        except Exception as e:
            os.unlink(temp_path)  # Clean up on error
            raise e


    def safe_optimization_pipeline(
        self,
        resume_input: 'ResumeInput',
        jd_input: 'JDInput',
        options: 'OptimizationOptions',
        request_hash: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Execute optimization pipeline with comprehensive error handling.
        
        This is a wrapper around _run_optimization_pipeline with enhanced error handling.
        """
        
        start_time = time.time()
        
        try:
            # Log the attempt
            log_optimization_attempt(user_id, resume_input, jd_input, False)
            
            # Execute pipeline
            result = _run_optimization_pipeline(
                resume_input, jd_input, options, request_hash, user_id
            )
            
            # Log success
            processing_time = (time.time() - start_time) * 1000
            log_optimization_attempt(
                user_id, resume_input, jd_input, True,
                processing_time_ms=processing_time
            )
            
            return result
            
        except Exception as e:
            # Log failure
            processing_time = (time.time() - start_time) * 1000
            log_optimization_attempt(
                user_id, resume_input, jd_input, False,
                error_details=str(e),
                processing_time_ms=processing_time
            )
            
            # Re-raise for handling by route
            raise





    def log_optimization_attempt(
        self,
        user_id: int,
        resume_input: 'ResumeInput',
        jd_input: 'JDInput',
        success: bool,
        error_details: Optional[str] = None,
        processing_time_ms: Optional[float] = None
    ):
        """
        Log optimization attempts for monitoring and debugging.
        
        Args:
            user_id: User ID
            resume_input: Resume input data
            jd_input: Job description input
            success: Whether optimization succeeded
            error_details: Error details if failed
            processing_time_ms: Processing time if successful
        """
        
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'success': success,
                'resume_input_type': resume_input.input_type,
                'resume_length': len(resume_input.text) if resume_input.text else 0,
                'jd_length': len(jd_input.text) if jd_input.text else 0,
                'has_job_title': bool(jd_input.title),
                'processing_time_ms': processing_time_ms,
                'error_details': error_details,
                'user_agent': request.headers.get('User-Agent', 'unknown'),
                'ip_address': request.remote_addr
            }
            
            # In production, send to logging service
            print(f"📊 Optimization Log: {json.dumps(log_entry)}")
            
        except Exception as e:
            print(f"❌ Logging failed: {str(e)}")


    def _extract_contact_info(self,header_text: str) -> Dict[str, str]:
        """Extract contact information from resume header."""
        
        import re
        
        contact_info = {}
        
        # Extract email
        email_match = re.search(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', header_text)
        if email_match:
            contact_info['email'] = email_match.group()
        
        # Extract phone  
        phone_match = re.search(r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', header_text)
        if phone_match:
            contact_info['phone'] = phone_match.group()
        
        # Extract name (first line typically)
        lines = header_text.strip().split('\n')
        if lines:
            potential_name = lines[0].strip()
            if len(potential_name.split()) <= 4 and not '@' in potential_name:
                contact_info['name'] = potential_name
        
        return contact_info


    def _get_model_info(self) -> Dict[str, str]:
        """Get current model configuration info."""
        
        return {
            'provider': current_app.config.get('MODEL_PROVIDER', 'unknown'),
            'llm_model': current_app.config.get('LLM_MODEL', 'unknown'),
            'embed_model': current_app.config.get('EMBED_MODEL', 'unknown'),
            'optimization_version': 'v1.0'
        }


    
    

    def _get_cached_optimization_result(self,result_id: str) -> Optional[Dict]:
        """
        Get cached optimization result by ID.
        For MVP, this uses a simple approach.
        """
        try:
            cache = get_enhanced_cache()
            # Simple cache key based on result_id
            cache_key = f"result:{result_id}"
            
            # Try to get from cache
            result = asyncio.run(cache.cache.get(cache_key))
            return result
            
        except:
            return None


    def _serve_local_file(self,filename: str, file_type: str) -> Response:
        """
        Serve file from local storage.
        
        Args:
            filename: Local filename
            file_type: pdf or docx
            
        Returns:
            File response
        """
        
        # Construct local file path (adjust based on your storage setup)
        local_storage_path = current_app.config.get('LOCAL_STORAGE_PATH', 'temp_files')
        file_path = os.path.join(local_storage_path, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Determine MIME type and filename
        if file_type == 'pdf':
            mimetype = 'application/pdf'
            download_name = f"optimized_resume.pdf"
        else:  # docx
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            download_name = f"optimized_resume.docx"
        
        return send_file(
            file_path,
            mimetype=mimetype,
            as_attachment=True,
            download_name=download_name
        )



    def _proxy_remote_file(self, file_url: str, file_type: str, result_data: Dict) -> Response:
        """
        Proxy download from remote storage (S3, etc.).
        
        Args:
            file_url: Remote file URL
            file_type: pdf or docx
            result_data: Optimization result data
            
        Returns:
            File response
        """
        
        try:
            import requests
            
            # Download file from remote storage
            response = requests.get(file_url, timeout=30)
            response.raise_for_status()
            
            # Create in-memory file
            file_data = io.BytesIO(response.content)
            file_data.seek(0)
            
            # Determine MIME type and filename
            if file_type == 'pdf':
                mimetype = 'application/pdf'
                download_name = f"optimized_resume.pdf"
            else:  # docx
                mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                download_name = f"optimized_resume.docx"
            
            return send_file(
                file_data,
                mimetype=mimetype,
                as_attachment=True,
                download_name=download_name
            )
            
        except Exception as e:
            print(f"❌ Remote file download error: {str(e)}")
            return jsonify({'error': 'Failed to download file from storage'}), 500



    def _store_temp_files(self, docx_bytes: bytes, pdf_bytes: bytes, result_id: str) -> Dict[str, str]:
        """
        Store files temporarily for download.
        
        Args:
            docx_bytes: DOCX file content
            pdf_bytes: PDF file content  
            result_id: Result identifier
            
        Returns:
            Storage information
        """
        
        try:
            # Create temp directory if needed
            temp_dir = current_app.config.get('TEMP_DOWNLOAD_PATH', 'temp_downloads')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate temporary filenames
            docx_filename = f"resume_{result_id}.docx"
            pdf_filename = f"resume_{result_id}.pdf"
            
            docx_path = os.path.join(temp_dir, docx_filename)
            pdf_path = os.path.join(temp_dir, pdf_filename)
            
            # Write files
            with open(docx_path, 'wb') as f:
                f.write(docx_bytes)
                
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)
            
            # Store in cache for lookup
            cache = get_enhanced_cache()
            file_info = {
                'docx_path': docx_path,
                'pdf_path': pdf_path,
                'created_at': time.time(),
                'result_id': result_id
            }
            
            # Cache for 24 hours
            cache_key = f"temp_files:{result_id}"
            asyncio.run(cache.cache.set(cache_key, file_info, ttl=86400))
            
            return {
                'storage_type': 'local_temp',
                'docx_path': docx_path,
                'pdf_path': pdf_path,
                'expires_in': 86400
            }
            
        except Exception as e:
            print(f"❌ Temp storage error: {str(e)}")
            return {'error': str(e)}