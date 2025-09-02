"""
LLM-powered resume rewriting logic.
Handles prompt engineering and resume optimization using language models.
"""

from typing import List, Dict, Any, Optional
import json


from .schemas import OptimizedResume, ExperienceItem, validate_json_with_retry
from .keywords import TechnicalSkills
from providers import get_models


class ResumePrompts:
    """Prompt templates for resume optimization."""
    
    SYSTEM_PROMPT = """You are an expert resume writer and ATS optimization specialist. Your goal is to rewrite resume content to better match job requirements while maintaining truthfulness.

CRITICAL RULES:
1. NEVER invent employers, dates, degrees, or accomplishments
2. ONLY enhance and reframe existing experience 
3. Return ONLY valid JSON - no explanations or markdown
4. Focus on ATS keyword optimization
5. Use action verbs and quantify achievements when possible
6. Keep bullets between 10-24 words
7. Avoid age signals (no graduation years >15 years ago, no "25+ years experience")

ATS OPTIMIZATION PRIORITIES:
- Include relevant keywords naturally
- Use industry-standard terminology
- Emphasize measurable achievements
- Match job description language patterns
- Ensure keyword density without stuffing"""

    @staticmethod
    def create_optimization_prompt(
        resume_sections: Dict[str, str],
        experience_items: List[Dict[str, Any]],
        jd_text: str,
        missing_keywords: List[str],
        weak_keywords: List[str],
        optimization_focus: str = "balanced"
    ) -> str:
        """
        Create the main optimization prompt for LLM.
        
        Args:
            resume_sections: Parsed resume sections
            experience_items: Structured experience data
            jd_text: Job description text
            missing_keywords: Keywords to add
            weak_keywords: Keywords to strengthen
            optimization_focus: 'aggressive', 'balanced', or 'conservative'
            
        Returns:
            Formatted prompt string
        """
        
        # Sample of experience bullets for context
        sample_bullets = []
        for item in experience_items[:3]:  # Show first 3 jobs
            bullets = item.get('bullets', [])
            sample_bullets.extend(bullets[:2])  # 2 bullets per job
        
        focus_instructions = {
            'aggressive': "Maximize keyword inclusion and rewrite extensively for strong ATS optimization",
            'balanced': "Balance keyword inclusion with natural language and readability", 
            'conservative': "Make minimal changes while adding essential missing keywords"
        }
        
        prompt = f"""RESUME OPTIMIZATION TASK:

JOB DESCRIPTION:
{jd_text[:1000]}...

CURRENT RESUME SUMMARY:
{resume_sections.get('summary', 'No summary provided')[:300]}

SAMPLE EXPERIENCE BULLETS:
{chr(10).join([f"- {bullet}" for bullet in sample_bullets[:6]])}

GAP ANALYSIS:
Missing Critical Keywords: {', '.join(missing_keywords[:8])}
Weak Keywords to Strengthen: {', '.join(weak_keywords[:6])}

OPTIMIZATION APPROACH: {focus_instructions.get(optimization_focus, focus_instructions['balanced'])}

REQUIRED OUTPUT FORMAT:
{{
    "summary": "2-3 sentence professional summary with relevant keywords",
    "experience": [
        {{
            "company": "Exact company name from original",
            "role": "Exact role from original or slight enhancement",
            "dates": "Exact dates from original",
            "bullets": [
                "Enhanced bullet 1 with relevant keywords",
                "Enhanced bullet 2 with quantified achievements",
                "Enhanced bullet 3 with action verbs"
            ]
        }}
    ],
    "skills_to_add": ["keyword1", "keyword2", "keyword3"],
    "skills": ["updated", "technical", "skills", "list"]
}}

ENHANCEMENT GUIDELINES:
- Start bullets with strong action verbs: "Developed", "Implemented", "Led", "Optimized"
- Include metrics when possible: "Improved performance by 40%", "Managed team of 8"
- Add missing keywords naturally: "Developed Python applications using Flask and PostgreSQL"
- Strengthen weak keywords: "Built scalable microservices" → "Architected scalable microservices using Docker and Kubernetes"
- Remove age signals: "10+ years" → "extensive", graduation years → remove if >15 years ago

Generate optimized resume JSON:"""

        return prompt
    
    @staticmethod
    def create_explanation_prompt(
        original_bullets: List[str],
        optimized_bullets: List[str],
        missing_keywords: List[str]
    ) -> str:
        """
        Create prompt for explaining resume changes.
        
        Args:
            original_bullets: Original experience bullets
            optimized_bullets: Optimized experience bullets
            missing_keywords: Keywords that were missing
            
        Returns:
            Explanation prompt string
        """
        
        changes_preview = []
        for i, (orig, opt) in enumerate(zip(original_bullets[:3], optimized_bullets[:3])):
            if orig != opt:
                changes_preview.append(f"Original: {orig}")
                changes_preview.append(f"Optimized: {opt}")
                changes_preview.append("---")
        
        prompt = f"""EXPLAIN RESUME CHANGES:

You made changes to optimize this resume. Explain the key changes and rationale.

SAMPLE CHANGES:
{chr(10).join(changes_preview)}

MISSING KEYWORDS ADDRESSED: {', '.join(missing_keywords[:5])}

Return explanations in this JSON format:
{{
    "rationale": [
        {{
            "change": "Specific change made",
            "reason": "Why this change improves the resume"
        }}
    ]
}}

Focus on:
- Keyword additions and why they're important
- Quantification improvements
- Action verb enhancements
- ATS optimization benefits
- Age signal removals

Generate explanation JSON:"""

        return prompt


class ResumeRewriter:
    """Handles LLM-powered resume rewriting and optimization."""
    
    def __init__(self):
        _, self.chat_model = get_models()
    
    async def optimize_resume(
        self,
        resume_sections: Dict[str, str],
        experience_items: List[Dict[str, Any]],
        jd_text: str,
        missing_keywords: List[str],
        weak_keywords: List[str],
        optimization_focus: str = "balanced"
    ) -> OptimizedResume:
        """
        Optimize resume using LLM rewriting.
        
        Args:
            resume_sections: Parsed resume sections
            experience_items: Structured experience data
            jd_text: Job description text
            missing_keywords: Keywords to incorporate
            weak_keywords: Keywords to strengthen
            optimization_focus: Optimization strategy
            
        Returns:
            OptimizedResume object
        """
        
        print(f"🤖 Optimizing resume with {len(missing_keywords)} missing keywords...")
        
        # Create optimization prompt
        prompt = ResumePrompts.create_optimization_prompt(
            resume_sections=resume_sections,
            experience_items=experience_items,
            jd_text=jd_text,
            missing_keywords=missing_keywords,
            weak_keywords=weak_keywords,
            optimization_focus=optimization_focus
        )
        
        # Generate optimized resume
        messages = [
            {"role": "system", "content": ResumePrompts.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # LLM generation with specific parameters for JSON output
            response = await self.chat_model.chat(
                messages=messages,
                temperature=0.2,  # Low temperature for consistent output
                max_tokens=2048,
                top_p=0.9
            )
            
            print(f"📝 Generated optimization response ({len(response)} chars)")
            
            # Validate and parse JSON response
            optimized = await validate_json_with_retry(
                json_str=response,
                schema_class=OptimizedResume,
                chat_model=self.chat_model,
                max_retries=2
            )
            
            # Post-process the optimized resume
            optimized = self._post_process_resume(optimized, experience_items)
            
            print(f"✅ Resume optimization complete")
            return optimized
            
        except Exception as e:
            print(f"❌ Resume optimization failed: {str(e)}")
            raise ValueError(f"Failed to optimize resume: {str(e)}")
    
    def _post_process_resume(
        self,
        optimized: OptimizedResume,
        original_experience: List[Dict[str, Any]]
    ) -> OptimizedResume:
        """
        Post-process optimized resume to ensure constraints.
        
        Args:
            optimized: LLM-generated OptimizedResume
            original_experience: Original experience for validation
            
        Returns:
            Post-processed OptimizedResume
        """
        
        # Enforce bullet length constraints (10-24 words)
        for exp_item in optimized.experience:
            processed_bullets = []
            for bullet in exp_item.bullets:
                word_count = len(bullet.split())
                
                if word_count < 10:
                    # Too short - could be enhanced but keep as-is for MVP
                    processed_bullets.append(bullet)
                elif word_count > 24:
                    # Too long - truncate at sentence boundary
                    words = bullet.split()
                    truncated = ' '.join(words[:24])
                    if not truncated.endswith('.'):
                        truncated += '...'
                    processed_bullets.append(truncated)
                else:
                    processed_bullets.append(bullet)
            
            exp_item.bullets = processed_bullets
        
        # Ensure action verb starts
        action_verbs = {
            'achieved', 'analyzed', 'architected', 'automated', 'built', 'collaborated',
            'created', 'delivered', 'designed', 'developed', 'enhanced', 'established',
            'executed', 'implemented', 'improved', 'increased', 'led', 'managed',
            'optimized', 'organized', 'reduced', 'streamlined', 'transformed'
        }
        
        for exp_item in optimized.experience:
            for i, bullet in enumerate(exp_item.bullets):
                first_word = bullet.split()[0].lower() if bullet.split() else ''
                if first_word not in action_verbs:
                    # Try to add an action verb
                    if 'develop' in bullet.lower() or 'build' in bullet.lower():
                        exp_item.bullets[i] = f"Developed {bullet}"
                    elif 'manage' in bullet.lower() or 'lead' in bullet.lower():
                        exp_item.bullets[i] = f"Led {bullet}"
                    else:
                        exp_item.bullets[i] = f"Implemented {bullet}"
        
        # Deduplicate skills
        if optimized.skills_to_add:
            optimized.skills_to_add = list(dict.fromkeys(optimized.skills_to_add))  # Remove duplicates
        
        return optimized


# Sync wrapper
def optimize_resume_sync(*args, **kwargs) -> OptimizedResume:
    """Synchronous wrapper for optimize_resume."""
    import asyncio
    async def _optimize_with_cleanup():
        rewriter = ResumeRewriter()
        try:
            return await rewriter.optimize_resume(*args, **kwargs)
        finally:
            # Force cleanup of any remaining async resources
            await asyncio.sleep(0.1)  # Allow cleanup tasks to complete
    
    return asyncio.run(_optimize_with_cleanup())