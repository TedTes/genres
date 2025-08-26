"""
Main orchestration pipeline for resume optimization.
Coordinates all steps of the AI-powered resume optimization process.
"""

import asyncio
import time
from typing import Dict, Any, Optional

from .schemas import (
    ResumeInput, JDInput, OptimizationOptions, OptimizationResult,
    OptimizedResume, Rationale
)
from .ingest import ingest_resume_sync
from .embedding import perform_gap_analysis_sync
from .rewrite import optimize_resume_sync
from .explain import generate_explanations_sync
from .policy import apply_guardrails_sync, score_resume_match
from .formatting import create_docx_sync, create_pdf_sync
from .storage import store_resume_files_sync, generate_resume_hash_sync
from .cache import get_enhanced_cache


class ResumeOptimizer:
    """
    Main orchestration class for resume optimization pipeline.
    Coordinates all steps from input processing to final artifact generation.
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.cache = get_enhanced_cache()
        self.request_id = None
        self.performance_metrics = {}
    
    async def optimize_resume(
        self,
        resume_input: ResumeInput,
        jd_input: JDInput,
        options: OptimizationOptions = None
    ) -> OptimizationResult:
        """
        Execute complete resume optimization pipeline.
        
        Args:
            resume_input: Resume data (text, DOCX, or PDF)
            jd_input: Job description data
            options: Optimization preferences
            
        Returns:
            Complete optimization result with artifacts
        """
        
        if options is None:
            options = OptimizationOptions()
        
        start_time = time.time()
        
        # Generate request hash for caching and tracking
        resume_text = resume_input.text or "file_input"
        self.request_id = generate_resume_hash_sync(
            resume_text, jd_input.text, options.dict()
        )
        
        print(f"🚀 Starting optimization pipeline | Request: {self.request_id}")
        
        try:
            # Check cache first
            cached_result = await self._check_cache(resume_input, jd_input, options)
            if cached_result:
                print(f"⚡ Cache hit - returning cached result")
                return OptimizationResult(**cached_result)
            
            # Execute pipeline steps
            result = await self._execute_pipeline(resume_input, jd_input, options)
            
            # Cache the result
            await self._cache_result(result, resume_input, jd_input, options)
            
            # Add final metadata
            total_time = (time.time() - start_time) * 1000
            result.processing_time_ms = round(total_time, 2)
            result.cache_hit = False
            
            print(f"✅ Pipeline complete | {total_time:.0f}ms | Score: {result.match_score:.2f}")
            
            return result
            
        except Exception as e:
            error_time = (time.time() - start_time) * 1000
            print(f"❌ Pipeline failed after {error_time:.0f}ms: {str(e)}")
            raise
    
    async def _check_cache(
        self,
        resume_input: ResumeInput,
        jd_input: JDInput, 
        options: OptimizationOptions
    ) -> Optional[Dict[str, Any]]:
        """Check if optimization result is cached."""
        
        return await self.cache.get_cached_result(
            resume_text=resume_input.text or "file_input",
            jd_text=jd_input.text,
            options=options.dict(),
            model_info=self._get_model_info()
        )
    
    async def _execute_pipeline(
        self,
        resume_input: ResumeInput,
        jd_input: JDInput,
        options: OptimizationOptions
    ) -> OptimizationResult:
        """Execute the complete optimization pipeline."""
        
        # Step 1: Document Ingestion & Parsing
        step_start = time.time()
        print("📄 Step 1: Ingesting and parsing resume...")
        
        parsed_resume = ingest_resume_sync(
            text=resume_input.text,
            docx_url=resume_input.docx_url,
            pdf_url=resume_input.pdf_url
        )
        
        self.performance_metrics['ingestion_ms'] = (time.time() - step_start) * 1000
        
        # Step 2: Gap Analysis
        step_start = time.time()
        print("🔍 Step 2: Analyzing skill and content gaps...")
        
        gap_analysis = perform_gap_analysis_sync(
            resume_chunks=parsed_resume.chunks,
            jd_text=jd_input.text,
            jd_title=jd_input.title
        )
        
        self.performance_metrics['gap_analysis_ms'] = (time.time() - step_start) * 1000
        
        # Step 3: LLM-Powered Optimization
        step_start = time.time()
        print("🤖 Step 3: AI-powered content optimization...")
        
        optimized_resume = optimize_resume_sync(
            resume_sections=parsed_resume.sections,
            experience_items=parsed_resume.experience_items,
            jd_text=jd_input.text,
            missing_keywords=gap_analysis['missing_keywords'],
            weak_keywords=gap_analysis['weak_keywords'],
            optimization_focus=options.tone
        )
        
        self.performance_metrics['llm_optimization_ms'] = (time.time() - step_start) * 1000
        
        # Step 4: Generate Explanations
        step_start = time.time()
        print("📋 Step 4: Generating change explanations...")
        
        explanations = generate_explanations_sync(
            original_resume={'sections': parsed_resume.sections, 'experience_items': parsed_resume.experience_items},
            optimized_resume=optimized_resume,
            missing_keywords=gap_analysis['missing_keywords'],
            gap_analysis=gap_analysis
        )
        
        self.performance_metrics['explanations_ms'] = (time.time() - step_start) * 1000
        
        # Step 5: Apply Policy Guardrails
        step_start = time.time()
        print("🛡️  Step 5: Applying compliance guardrails...")
        
        clean_resume, policy_violations = apply_guardrails_sync(optimized_resume)
        
        # Calculate match scores
        score_breakdown = score_resume_match(
            keyword_analysis=gap_analysis.get('keyword_analysis', {}),
            semantic_analysis=gap_analysis.get('semantic_analysis', {}),
            gap_analysis=gap_analysis,
            resume_sections=parsed_resume.sections
        )
        
        self.performance_metrics['guardrails_ms'] = (time.time() - step_start) * 1000
        
        # Step 6: Document Generation
        step_start = time.time()
        print("📄 Step 6: Generating optimized documents...")
        
        contact_info = self._extract_contact_info(parsed_resume.sections)
        
        # Generate DOCX (always)
        docx_bytes = create_docx_sync(clean_resume, contact_info, options.tone)
        
        # Generate PDF (optional)
        pdf_bytes = None
        if getattr(options, 'include_pdf', True):
            pdf_bytes = create_pdf_sync(clean_resume, contact_info, options.tone)
        
        self.performance_metrics['document_generation_ms'] = (time.time() - step_start) * 1000
        
        # Step 7: File Storage
        step_start = time.time()
        print("💾 Step 7: Storing optimized files...")
        
        file_urls = store_resume_files_sync(
            docx_bytes=docx_bytes,
            pdf_bytes=pdf_bytes,
            user_id=str(self.user_id),
            resume_hash=self.request_id,
            contact_info=contact_info
        )
        
        self.performance_metrics['storage_ms'] = (time.time() - step_start) * 1000
        
        # Compile final result
        result = OptimizationResult(
            match_score=score_breakdown['overall_score'],
            missing_keywords=gap_analysis['missing_keywords'],
            weak_keywords=gap_analysis['weak_keywords'],
            optimized_resume=clean_resume,
            explanations=explanations,
            artifacts=file_urls,
            model_info=self._get_model_info(),
            processing_time_ms=sum(self.performance_metrics.values()),
            input_type=resume_input.input_type
        )
        
        return result
    
    async def _cache_result(
        self,
        result: OptimizationResult,
        resume_input: ResumeInput,
        jd_input: JDInput,
        options: OptimizationOptions
    ):
        """Cache the optimization result."""
        
        await self.cache.cache_result(
            resume_text=resume_input.text or "file_input",
            jd_text=jd_input.text,
            result=result.dict(),
            options=options.dict(),
            model_info=self._get_model_info(),
            ttl=24*60*60  # 24 hours
        )
    
    def _extract_contact_info(self, sections: Dict[str, str]) -> Dict[str, str]:
        """Extract contact information from resume sections."""
        
        import re
        
        # Check header section first, then summary
        header_text = sections.get('header', '') or sections.get('summary', '')
        contact_info = {}
        
        # Extract email
        email_match = re.search(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', header_text)
        if email_match:
            contact_info['email'] = email_match.group()
        
        # Extract phone
        phone_match = re.search(r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', header_text)
        if phone_match:
            contact_info['phone'] = phone_match.group()
        
        # Extract name (first non-email, non-phone line)
        lines = header_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if (len(line.split()) <= 4 and 
                '@' not in line and 
                not any(char.isdigit() for char in line) and
                len(line) > 3):
                contact_info['name'] = line
                break
        
        return contact_info
    
    def _get_model_info(self) -> Dict[str, str]:
        """Get current model configuration."""
        
        from flask import current_app
        
        return {
            'provider': current_app.config.get('MODEL_PROVIDER', 'unknown'),
            'llm_model': current_app.config.get('LLM_MODEL', 'unknown'),  
            'embed_model': current_app.config.get('EMBED_MODEL', 'unknown'),
            'version': 'v1.0-mvp'
        }
    
    # Sync wrapper methods
    def optimize_resume_sync(
        self,
        resume_input: ResumeInput,
        jd_input: JDInput,
        options: OptimizationOptions = None
    ) -> OptimizationResult:
        """Synchronous wrapper for optimize_resume."""
        return asyncio.run(self.optimize_resume(resume_input, jd_input, options))


# Convenience functions for direct usage
async def optimize_resume_pipeline(
    resume_input: ResumeInput,
    jd_input: JDInput,
    user_id: int,
    options: OptimizationOptions = None
) -> OptimizationResult:
    """
    Convenience function to run the complete optimization pipeline.
    
    Args:
        resume_input: Resume input data
        jd_input: Job description input
        user_id: User identifier
        options: Optimization options
        
    Returns:
        Complete optimization result
    """
    
    optimizer = ResumeOptimizer(user_id)
    return await optimizer.optimize_resume(resume_input, jd_input, options)


def optimize_resume_pipeline_sync(
    resume_input: ResumeInput,
    jd_input: JDInput,
    user_id: int,
    options: OptimizationOptions = None
) -> OptimizationResult:
    """Synchronous wrapper for optimize_resume_pipeline."""
    return asyncio.run(optimize_resume_pipeline(resume_input, jd_input, user_id, options))


# Quick test function for development
def test_pipeline_with_sample_data(user_id: int = 1) -> OptimizationResult:
    """Test the pipeline with sample data - useful for development."""
    
    sample_resume = ResumeInput(text="""John Smith
Software Engineer
john.smith@email.com | (555) 123-4567

EXPERIENCE
Software Developer | TechCorp | 2020-2023
- Built web applications using Python and Flask
- Worked with databases and APIs
- Collaborated with team members

SKILLS
Python, HTML, CSS, JavaScript""")

    sample_jd = JDInput(
        text="""We are seeking a Senior Python Developer with experience in:
- Flask and Django frameworks
- PostgreSQL and database design
- Docker containerization
- CI/CD pipelines
- AWS cloud services

Requirements:
- 3+ years Python experience
- Experience with REST APIs
- Knowledge of containerization""",
        title="Senior Python Developer",
        company="TestCorp"
    )
    
    return optimize_resume_pipeline_sync(sample_resume, sample_jd, user_id)