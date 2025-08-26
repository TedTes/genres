"""
Generate explanations for resume changes.
Creates detailed rationale for all modifications made during optimization.
"""

from typing import List, Dict, Any, Tuple
import difflib
import asyncio

from .schemas import Rationale, ChangeRationale, validate_json_with_retry
from providers import get_models
from .pipeline import OptimizedResume

class ResumeDiffGenerator:
    """Generates detailed diffs between original and optimized resumes."""
    
    @staticmethod
    def generate_section_diff(
        original_section: str, 
        optimized_section: str, 
        section_name: str
    ) -> List[Dict[str, str]]:
        """
        Generate diff for a specific resume section.
        
        Args:
            original_section: Original section text
            optimized_section: Optimized section text
            section_name: Name of the section (summary, experience, etc.)
            
        Returns:
            List of change dictionaries
        """
        
        changes = []
        
        if not original_section and optimized_section:
            changes.append({
                'type': 'addition',
                'section': section_name,
                'change': f"Added {section_name} section",
                'original': '',
                'optimized': optimized_section[:100] + '...' if len(optimized_section) > 100 else optimized_section
            })
        elif original_section and not optimized_section:
            changes.append({
                'type': 'removal',
                'section': section_name,
                'change': f"Removed {section_name} section",
                'original': original_section[:100] + '...' if len(original_section) > 100 else original_section,
                'optimized': ''
            })
        elif original_section != optimized_section:
            # Generate detailed diff using difflib
            diff = difflib.unified_diff(
                original_section.splitlines(keepends=True),
                optimized_section.splitlines(keepends=True),
                fromfile='original',
                tofile='optimized',
                n=0
            )
            
            diff_text = ''.join(diff)
            
            changes.append({
                'type': 'modification',
                'section': section_name,
                'change': f"Modified {section_name} section",
                'original': original_section[:200] + '...' if len(original_section) > 200 else original_section,
                'optimized': optimized_section[:200] + '...' if len(optimized_section) > 200 else optimized_section,
                'diff': diff_text
            })
        
        return changes
    
    @staticmethod
    def generate_bullet_diff(
        original_bullets: List[str], 
        optimized_bullets: List[str],
        job_context: str = ""
    ) -> List[Dict[str, str]]:
        """
        Generate detailed diff for experience bullets.
        
        Args:
            original_bullets: Original bullet points
            optimized_bullets: Optimized bullet points
            job_context: Job/company context
            
        Returns:
            List of bullet-level changes
        """
        
        changes = []
        
        # Handle different lengths
        max_len = max(len(original_bullets), len(optimized_bullets))
        
        for i in range(max_len):
            orig = original_bullets[i] if i < len(original_bullets) else None
            opt = optimized_bullets[i] if i < len(optimized_bullets) else None
            
            if orig and opt and orig != opt:
                # Modified bullet
                changes.append({
                    'type': 'bullet_modification',
                    'context': job_context,
                    'bullet_index': i,
                    'original': orig,
                    'optimized': opt,
                    'change': f"Enhanced bullet {i+1}: {orig[:50]}... → {opt[:50]}..."
                })
            elif not orig and opt:
                # Added bullet
                changes.append({
                    'type': 'bullet_addition',
                    'context': job_context,
                    'bullet_index': i,
                    'original': '',
                    'optimized': opt,
                    'change': f"Added new bullet: {opt}"
                })
            elif orig and not opt:
                # Removed bullet (shouldn't happen in optimization)
                changes.append({
                    'type': 'bullet_removal',
                    'context': job_context,
                    'bullet_index': i,
                    'original': orig,
                    'optimized': '',
                    'change': f"Removed bullet: {orig}"
                })
        
        return changes
    
    @staticmethod
    def analyze_keyword_additions(
        original_text: str,
        optimized_text: str,
        target_keywords: List[str]
    ) -> List[Dict[str, str]]:
        """
        Analyze which keywords were successfully added.
        
        Args:
            original_text: Original resume text
            optimized_text: Optimized resume text
            target_keywords: Keywords that should be added
            
        Returns:
            List of keyword addition analyses
        """
        
        original_lower = original_text.lower()
        optimized_lower = optimized_text.lower()
        
        keyword_changes = []
        
        for keyword in target_keywords:
            kw_lower = keyword.lower()
            was_present = kw_lower in original_lower
            is_present = kw_lower in optimized_lower
            
            if not was_present and is_present:
                # Successfully added
                keyword_changes.append({
                    'type': 'keyword_addition',
                    'keyword': keyword,
                    'status': 'added',
                    'change': f"Added '{keyword}' to resume",
                    'impact': 'Improves ATS keyword matching'
                })
            elif was_present and is_present:
                # Was already present - might have been strengthened
                orig_count = original_lower.count(kw_lower)
                opt_count = optimized_lower.count(kw_lower)
                
                if opt_count > orig_count:
                    keyword_changes.append({
                        'type': 'keyword_strengthening',
                        'keyword': keyword,
                        'status': 'strengthened',
                        'change': f"Increased '{keyword}' mentions from {orig_count} to {opt_count}",
                        'impact': 'Strengthens keyword relevance'
                    })
            elif not was_present and not is_present:
                # Failed to add
                keyword_changes.append({
                    'type': 'keyword_missing',
                    'keyword': keyword,
                    'status': 'not_added',
                    'change': f"Could not naturally incorporate '{keyword}'",
                    'impact': 'May need manual addition'
                })
        
        return keyword_changes


class ExplanationGenerator:
    """Generates explanations for resume optimization changes."""
    
    def __init__(self):
        _, self.chat_model = get_models()
    
    async def generate_explanations(
        self,
        original_resume: Dict[str, Any],
        optimized_resume: OptimizedResume,
        missing_keywords: List[str],
        gap_analysis: Dict[str, Any]
    ) -> Rationale:
        """
        Generate comprehensive explanations for all resume changes.
        
        Args:
            original_resume: Original parsed resume data
            optimized_resume: LLM-optimized resume
            missing_keywords: Keywords that were missing
            gap_analysis: Gap analysis results
            
        Returns:
            Rationale object with detailed explanations
        """
        
        print(f"📋 Generating explanations for resume changes...")
        
        # Generate detailed diff analysis
        diff_analysis = self._create_detailed_diff(original_resume, optimized_resume)
        
        # Create explanation prompt
        prompt = ResumePrompts.create_explanation_prompt(
            original_bullets=diff_analysis['original_bullets'],
            optimized_bullets=diff_analysis['optimized_bullets'],
            missing_keywords=missing_keywords
        )
        
        messages = [
            {"role": "system", "content": "You are an expert at explaining resume optimization changes. Focus on ATS benefits and career impact."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # Generate explanations
            response = await self.chat_model.chat(
                messages=messages,
                temperature=0.3,
                max_tokens=1024
            )
            
            # Validate explanation JSON
            explanations = await validate_json_with_retry(
                json_str=response,
                schema_class=Rationale,
                chat_model=self.chat_model,
                max_retries=1
            )
            
            # Add automatic explanations for keyword additions
            keyword_explanations = self._generate_keyword_explanations(
                diff_analysis['keyword_changes']
            )
            
            # Combine LLM and automatic explanations
            all_explanations = explanations.rationale + keyword_explanations
            
            return Rationale(rationale=all_explanations)
            
        except Exception as e:
            print(f"❌ Explanation generation failed: {str(e)}")
            # Return basic explanations as fallback
            return self._generate_fallback_explanations(missing_keywords)
    
    def _create_detailed_diff(
        self, 
        original: Dict[str, Any], 
        optimized: OptimizedResume
    ) -> Dict[str, Any]:
        """Create comprehensive diff analysis."""
        
        # Extract original bullets for comparison
        original_bullets = []
        for exp in original.get('experience_items', []):
            original_bullets.extend(exp.get('bullets', []))
        
        # Extract optimized bullets
        optimized_bullets = []
        for exp in optimized.experience:
            optimized_bullets.extend(exp.bullets)
        
        # Analyze keyword additions
        original_text = str(original)
        optimized_text = str(optimized.dict())
        
        keyword_changes = ResumeDiffGenerator.analyze_keyword_additions(
            original_text, optimized_text, optimized.skills_to_add
        )
        
        return {
            'original_bullets': original_bullets,
            'optimized_bullets': optimized_bullets,
            'keyword_changes': keyword_changes
        }
    
    def _generate_keyword_explanations(
        self, 
        keyword_changes: List[Dict[str, str]]
    ) -> List[ChangeRationale]:
        """Generate explanations for keyword changes."""
        
        explanations = []
        
        for change in keyword_changes:
            if change['status'] == 'added':
                explanations.append(ChangeRationale(
                    change=change['change'],
                    reason=f"Added '{change['keyword']}' to improve ATS keyword matching and demonstrate relevant technical expertise"
                ))
            elif change['status'] == 'strengthened':
                explanations.append(ChangeRationale(
                    change=change['change'],
                    reason=f"Increased emphasis on '{change['keyword']}' to better align with job requirements"
                ))
        
        return explanations
    
    def _generate_fallback_explanations(self, missing_keywords: List[str]) -> Rationale:
        """Generate basic explanations if LLM fails."""
        
        explanations = []
        
        for keyword in missing_keywords[:5]:
            explanations.append(ChangeRationale(
                change=f"Enhanced resume to include '{keyword}'",
                reason="This keyword appears in the job description and improves ATS matching"
            ))
        
        explanations.append(ChangeRationale(
            change="Optimized bullet points for ATS compatibility",
            reason="Improved action verbs and formatting for better parsing by applicant tracking systems"
        ))
        
        return Rationale(rationale=explanations)


# Sync wrapper
def generate_explanations_sync(*args, **kwargs) -> Rationale:
    """Synchronous wrapper for generate_explanations."""
    generator = ExplanationGenerator()
    return asyncio.run(generator.generate_explanations(*args, **kwargs))