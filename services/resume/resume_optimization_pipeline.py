from flask import Response
import spacy
from jinja2 import  FileSystemLoader
from flask import Flask,request,render_template,jsonify,current_app
from io import BytesIO
from weasyprint import HTML, CSS
import os
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
    
    def _run_optimization_pipeline(
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
            # Step 1: Ingest and parse resume
            print("📄 Step 1: Ingesting resume...")
            parsed_resume = DocumentProcessor().process_document_sync(
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
        
            print("🔍 Step 3: Analyzing gaps...")
            gap_analysis = perform_gap_analysis_sync(
                resume_chunks=parsed_resume.chunks,
                jd_text=jd_input.text,
                jd_title=jd_input.title
            )
            
        
            # print("🤖 Step 4: Optimizing with LLM...")
            # optimized_resume = optimize_resume_sync(
            #     resume_sections=parsed_resume.sections,
            #     experience_items=parsed_resume.experience_items,
            #     jd_text=jd_input.text,
            #     missing_keywords=gap_analysis['missing_keywords'],
            #     weak_keywords=gap_analysis['weak_keywords'],
            #     optimization_focus=options.tone
            # )
            
        
            # print("📋 Step 5: Generating explanations...")
            # explanations = generate_explanations_sync(
            #     original_resume=parsed_resume.dict(),
            #     optimized_resume=optimized_resume,
            #     missing_keywords=gap_analysis['missing_keywords'],
            #     gap_analysis=gap_analysis
            # )
            
        
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
        
            # result = {
            #     'match_score': score_breakdown['overall_score'],
            #     'score_breakdown': score_breakdown,
            #     'request_hash' : request_hash,
            #     'missing_keywords': gap_analysis['missing_keywords'],
            #     'weak_keywords': gap_analysis['weak_keywords'],
            #     'optimized_resume': clean_resume.dict(),
            #     'explanations': explanations.dict(),
            #     'artifacts': file_urls,
            #     'model_info': _get_model_info(),
            #     # 'policy_violations': [v.__dict__ for v in policy_violations],
            #     'input_type': resume_input.input_type,
            #     'processing_steps': 8
            # }
            result = {
                    'match_score': 87.3,
                    'score_breakdown': {
                        'overall_score': 87.3,
                        'keyword_match': 82.5,
                        'semantic_similarity': 91.2,
                        'experience_relevance': 89.1,
                        'skills_alignment': 85.7,
                        'education_match': 88.0,
                        'format_quality': 92.3
                    },
                    'missing_keywords': [
                        {
                            'keyword': 'machine learning',
                            'importance': 'high',
                            'frequency_in_jd': 3,
                            'context': 'Experience with machine learning algorithms and frameworks'
                        },
                        {
                            'keyword': 'kubernetes',
                            'importance': 'medium', 
                            'frequency_in_jd': 2,
                            'context': 'Container orchestration with Kubernetes'
                        },
                        {
                            'keyword': 'microservices',
                            'importance': 'high',
                            'frequency_in_jd': 4,
                            'context': 'Design and implement microservices architecture'
                        },
                        {
                            'keyword': 'terraform',
                            'importance': 'low',
                            'frequency_in_jd': 1,
                            'context': 'Infrastructure as code using Terraform'
                        }
                    ],
                    'weak_keywords': [
                        {
                            'keyword': 'python',
                            'current_strength': 'weak',
                            'suggested_improvement': 'Add specific Python frameworks and libraries used',
                            'examples': ['Django', 'FastAPI', 'pandas', 'scikit-learn']
                        },
                        {
                            'keyword': 'cloud computing',
                            'current_strength': 'moderate',
                            'suggested_improvement': 'Specify cloud platforms and services',
                            'examples': ['AWS EC2', 'Lambda', 'S3', 'RDS']
                        }
                    ],
                    'optimized_resume': {
                        'header': {
                            'name': 'John Doe',
                            'email': 'john.doe@email.com',
                            'phone': '(555) 123-4567',
                            'location': 'San Francisco, CA',
                            'linkedin': 'linkedin.com/in/johndoe'
                        },
                        'summary': 'Senior Software Engineer with 8+ years of experience building scalable microservices and machine learning solutions. Expert in Python, cloud computing (AWS), and container orchestration with Kubernetes. Proven track record of designing and implementing high-performance systems serving millions of users.',
                        'experience': [
                            {
                                'title': 'Senior Software Engineer',
                                'company': 'Tech Solutions Inc.',
                                'duration': '2021 - Present',
                                'achievements': [
                                    'Led development of microservices architecture serving 10M+ daily users',
                                    'Implemented machine learning pipeline using Python and scikit-learn, improving recommendation accuracy by 25%',
                                    'Designed and deployed Kubernetes clusters on AWS, reducing infrastructure costs by 30%',
                                    'Built CI/CD pipelines using Terraform for infrastructure as code'
                                ]
                            },
                            {
                                'title': 'Software Engineer',
                                'company': 'StartupCorp',
                                'duration': '2019 - 2021', 
                                'achievements': [
                                    'Developed Python-based web applications using Django and FastAPI',
                                    'Optimized cloud computing infrastructure on AWS (EC2, Lambda, S3, RDS)',
                                    'Collaborated with data science team on machine learning model deployment',
                                    'Implemented automated testing and monitoring for microservices'
                                ]
                            }
                        ],
                        'skills': {
                            'programming': ['Python', 'JavaScript', 'Java', 'Go'],
                            'frameworks': ['Django', 'FastAPI', 'React', 'Spring Boot'],
                            'cloud_platforms': ['AWS', 'Google Cloud Platform'],
                            'tools': ['Kubernetes', 'Docker', 'Terraform', 'Jenkins'],
                            'databases': ['PostgreSQL', 'MongoDB', 'Redis'],
                            'machine_learning': ['scikit-learn', 'TensorFlow', 'pandas', 'numpy']
                        },
                        'education': [
                            {
                                'degree': 'Bachelor of Science in Computer Science',
                                'school': 'University of California, Berkeley',
                                'year': '2016',
                                'gpa': '3.7/4.0'
                            }
                        ]
                    },
                    'explanations': {
                        'summary_changes': 'Enhanced summary to emphasize microservices, machine learning, and Kubernetes experience to better align with job requirements.',
                        'experience_improvements': [
                            'Added specific metrics and quantifiable achievements',
                            'Incorporated missing keywords: microservices, machine learning, Kubernetes',
                            'Emphasized cloud computing and Python expertise',
                            'Added Terraform experience to match infrastructure requirements'
                        ],
                        'skills_additions': [
                            'Added machine learning frameworks (scikit-learn, TensorFlow)',
                            'Specified Python frameworks (Django, FastAPI)',
                            'Included container orchestration tools (Kubernetes, Docker)',
                            'Added infrastructure as code tools (Terraform)'
                        ],
                        'keyword_integration': {
                            'machine_learning': 'Integrated throughout experience section with specific examples and frameworks',
                            'microservices': 'Emphasized in current role with user scale metrics',
                            'kubernetes': 'Added as key infrastructure skill with cost savings metric',
                            'python': 'Strengthened with specific frameworks and use cases'
                        }
                    },
                    'artifacts': {
                        'docx_url': 'https://storage.example.com/resumes/optimized_resume_abc123.docx',
                        'pdf_url': 'https://storage.example.com/resumes/optimized_resume_abc123.pdf',
                        'download_expires': '2025-09-15T10:30:00Z'
                    },
                    'model_info': {
                        'provider': 'openai',
                        'llm_model': 'gpt-4-turbo',
                        'embed_model': 'text-embedding-ada-002', 
                        'optimization_version': 'v1.0'
                    },
                    'policy_violations': [
                        {
                            'type': 'potential_hallucination',
                            'severity': 'low',
                            'description': 'Added specific metric (25% improvement) - verify accuracy',
                            'location': 'experience.achievements[1]',
                            'suggestion': 'Replace with actual metric if available'
                        }
                    ],
                    'input_type': 'text',
                    'processing_steps': 8,
                    'processing_time_ms': 15420,
                    'tokens_used': {
                        'input_tokens': 2847,
                        'output_tokens': 1923,
                        'total_tokens': 4770
                    },
                    'metadata': {
                        'request_hash': 'abc123def456',
                        'optimization_timestamp': '2025-09-08T14:30:00Z',
                        'user_id': 'user_12345',
                        'job_title': 'Senior Software Engineer',
                        'company': 'Google',
                        'optimization_focus': 'professional-concise'
                    }
            }

            return result
        finally:
            # Clean up temp files
            for url in [resume_input.pdf_url, resume_input.docx_url]:
                if url and os.path.exists(url):
                    os.unlink(url)



    def calculate_resume_completeness(resume_data):
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





    def calculate_skill_match(user_skills, job_skills):
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
        user_id: int,
        resume_input: ResumeInput,
        jd_input: JDInput,
        optimization_result: dict,
        processing_time_ms: float,
        model_provider: str
    ) -> str:
        """Save optimization results to database and return the ID."""
        
        try:
            # Create resume record
            resume_record = Resume(
                user_id=user_id,
                title=f"Optimized Resume - {jd_input.title or 'Untitled Job'}",
                resume_data={
                    'original_text': resume_input.text[:5000] if resume_input.text else None,
                    'file_type': 'pdf' if resume_input.pdf_url else 'docx' if resume_input.docx_url else 'text',
                    'optimization_date': datetime.utcnow().isoformat()
                },
                template="optimized_standard",
                is_optimized=True,
                last_optimized_at=datetime.utcnow()
            )
            
            db.session.add(resume_record)
            db.session.flush()  # Get ID without committing
            explanations = optimization_result.get('explanations', [])
            if hasattr(explanations, 'dict'):  # Pydantic model
                explanations_list = [explanations.dict()]
            else:
                explanations_list = list(explanations) if explanations else []
            # Create optimization record
            optimization = ResumeOptimization(
                user_id=user_id,
                resume_id=resume_record.id,
                
                # Input data
                original_resume_data={
                    'text_preview': resume_input.text[:1000] if resume_input.text else None,
                    'input_type': getattr(resume_input, 'input_type', 'unknown'),
                    'file_info': {
                        'has_pdf': bool(resume_input.pdf_url),
                        'has_docx': bool(resume_input.docx_url),
                        'has_text': bool(resume_input.text)
                    }
                },
                job_description=jd_input.text[:5000] if jd_input.text else None,
                job_title=jd_input.title[:200] if jd_input.title else None,
                company_name=jd_input.company[:200] if jd_input.company else None,
                
                # Optimization settings
                optimization_style=optimization_result.get('optimization_focus', 'professional-concise'),
                

                
                # Results
                optimized_resume_data={
                    'sections': optimization_result.get('sections', {}),
                    'experience': optimization_result.get('experience', []),
                    'skills_added': optimization_result.get('skills_to_add', []),
                    'explanations': explanations_list[:10],
                    'gap_analysis': optimization_result.get('gap_analysis', {})
                },
                match_score_before=float(optimization_result.get('original_match_score', 0.0)),
                match_score_after=float(optimization_result.get('match_score', 0.0)),
                missing_keywords=list(optimization_result.get('missing_keywords', [])[:50]),
                added_keywords=list(optimization_result.get('added_keywords', [])[:50]),
                
                # Files
                docx_url=optimization_result.get('artifacts', {}).get('docx_url'),
                pdf_url=optimization_result.get('artifacts', {}).get('pdf_url'),
                
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



    def save_temp_file(uploaded_file):
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


    def _extract_contact_info(header_text: str) -> Dict[str, str]:
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


    def _get_model_info() -> Dict[str, str]:
        """Get current model configuration info."""
        
        return {
            'provider': current_app.config.get('MODEL_PROVIDER', 'unknown'),
            'llm_model': current_app.config.get('LLM_MODEL', 'unknown'),
            'embed_model': current_app.config.get('EMBED_MODEL', 'unknown'),
            'optimization_version': 'v1.0'
        }


    def _check_rate_limit(user_id: int, limit_per_hour: int) -> bool:
        """
        Basic rate limiting check.
        
        Args:
            user_id: User ID
            limit_per_hour: Maximum requests per hour
            
        Returns:
            True if within limit, False if exceeded
        """
        
        # For MVP, simple implementation
        # In production, use Redis for distributed rate limiting
        
        cache_key = f"rate_limit:user:{user_id}:{int(time.time() // 3600)}"  # Hour bucket
        
        try:
            cache = get_enhanced_cache()
            current_count = asyncio.run(cache.cache.get(cache_key)) or 0
            
            if current_count >= limit_per_hour:
                return False
            
            # Increment counter
            asyncio.run(cache.cache.set(cache_key, current_count + 1, ttl=3600))
            return True
            
        except:
            # If rate limiting fails, allow the request (fail open)
            return True
    

    def _get_cached_optimization_result(result_id: str) -> Optional[Dict]:
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


    def _serve_local_file(filename: str, file_type: str) -> Response:
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



    def _proxy_remote_file(file_url: str, file_type: str, result_data: Dict) -> Response:
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



    def _store_temp_files(docx_bytes: bytes, pdf_bytes: bytes, result_id: str) -> Dict[str, str]:
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