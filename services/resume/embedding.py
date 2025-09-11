"""
Embedding generation and similarity calculations.
Handles text vectorization and semantic matching between resumes and job descriptions.
"""

import numpy as np
from typing import Any,List, Dict, Tuple, Optional
from dataclasses import dataclass
import asyncio

from .document_processor import DocumentChunk
from .keywords import KeywordMatch, extract_keywords_from_text
from providers import get_models


@dataclass
class EmbeddingResult:
    """Result of embedding generation with metadata."""
    text: str
    embedding: List[float]
    token_count: int
    chunk_index: Optional[int] = None
    section: Optional[str] = None


@dataclass
class SimilarityMatch:
    """Similarity match between resume chunk and JD."""
    chunk: DocumentChunk
    similarity_score: float
    jd_section: str
    matching_keywords: List[str]


class ResumeEmbedder:
    """Handles embedding generation and similarity analysis for resumes."""
    
    def __init__(self):
        self.embedder, _ = get_models()
    
    async def embed_resume_chunks(self, chunks: List[DocumentChunk]) -> List[EmbeddingResult]:
        """
        Generate embeddings for resume chunks.
        
        Args:
            chunks: List of DocumentChunk objects
            
        Returns:
            List of EmbeddingResult objects
        """
        
        if not chunks:
            return []
        
        print(f"🔢 Generating embeddings for {len(chunks)} resume chunks...")
        
        # Extract texts from chunks
        texts = [chunk.text for chunk in chunks]
        
        try:
            # Generate embeddings
            embeddings = await self.embedder.embed(texts)
            
            # Create results with metadata
            results = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                result = EmbeddingResult(
                    text=chunk.text,
                    embedding=embedding,
                    token_count=chunk.token_count or len(chunk.text.split()),
                    chunk_index=chunk.chunk_index,
                    section=chunk.section
                )
                results.append(result)
            
            print(f"✅ Generated {len(results)} embeddings (dim: {len(embeddings[0])})")
            return results
            
        except Exception as e:
            print(f"❌ Embedding generation failed: {str(e)}")
            raise ValueError(f"Failed to generate resume embeddings: {str(e)}")
    
    async def embed_job_description(self, jd_text: str) -> EmbeddingResult:
        """
        Generate embedding for job description.
        
        Args:
            jd_text: Job description text
            
        Returns:
            EmbeddingResult for the job description
        """
        if not jd_text or not jd_text.strip():
          raise ValueError("Job description text cannot be empty for embedding generation")

        clean_text = jd_text.strip()

        if len(clean_text) < 10:  # Minimum meaningful content
          raise ValueError("Job description too short for meaningful embedding generation")
        print(f"🎯 Generating job description embedding...")
        
        try:
            embeddings = await self.embedder.embed([clean_text])
            
            result = EmbeddingResult(
                text=clean_text,
                embedding=embeddings[0],
                token_count=len(clean_text.split())
            )
            
            print(f"✅ Generated JD embedding (dim: {len(embeddings[0])})")
            return result
            
        except Exception as e:
            print(f"❌ JD embedding generation failed: {str(e)}")
            raise ValueError(f"Failed to generate JD embedding: {str(e)}")


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score (0.0 to 1.0)
    """
    
    if len(vec1) != len(vec2):
        raise ValueError(f"Vector dimensions don't match: {len(vec1)} vs {len(vec2)}")
    
    # Convert to numpy arrays for efficient computation
    a = np.array(vec1)
    b = np.array(vec2)
    
    # Calculate cosine similarity
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    similarity = dot_product / (norm_a * norm_b)
    
    # Ensure result is between 0 and 1
    return max(0.0, min(1.0, float(similarity)))


def find_similar_chunks(
    resume_embeddings: List[EmbeddingResult],
    jd_embedding: EmbeddingResult,
    similarity_threshold: float = 0.3
) -> List[SimilarityMatch]:
    """
    Find resume chunks that are similar to the job description.
    
    Args:
        resume_embeddings: Resume chunk embeddings
        jd_embedding: Job description embedding
        similarity_threshold: Minimum similarity score to include
        
    Returns:
        List of SimilarityMatch objects
    """
    
    matches = []
    
    for resume_emb in resume_embeddings:
        # Calculate similarity
        similarity = cosine_similarity(resume_emb.embedding, jd_embedding.embedding)
        
        if similarity >= similarity_threshold:
            # Find matching keywords between chunk and JD
            resume_keywords = extract_keywords_from_text(resume_emb.text)
            jd_keywords = extract_keywords_from_text(jd_embedding.text)
            
            resume_kw_set = {kw.keyword.lower() for kw in resume_keywords}
            jd_kw_set = {kw.keyword.lower() for kw in jd_keywords}
            matching_keywords = list(resume_kw_set & jd_kw_set)
            
            # Create chunk object for compatibility
            chunk = DocumentChunk(
                text=resume_emb.text,
                section=resume_emb.section or 'unknown',
                chunk_index=resume_emb.chunk_index or 0,
                token_count=resume_emb.token_count
            )
            
            match = SimilarityMatch(
                chunk=chunk,
                similarity_score=round(similarity, 3),
                jd_section='overall',  # Could be enhanced to match specific JD sections
                matching_keywords=matching_keywords
            )
            matches.append(match)
    
    # Sort by similarity score (highest first)
    matches.sort(key=lambda x: x.similarity_score, reverse=True)
    
    return matches


async def analyze_semantic_gaps(
    resume_chunks: List[DocumentChunk],
    jd_text: str,
    similarity_threshold: float = 0.3
) -> Dict[str, Any]:
    """
    Analyze semantic gaps between resume and job description.
    
    Args:
        resume_chunks: Resume text chunks
        jd_text: Job description text
        similarity_threshold: Minimum similarity for matches
        
    Returns:
        Gap analysis with similarity metrics
    """
    # Validate inputs
    if not resume_chunks:
        raise ValueError("No resume chunks provided for gap analysis")
    if not jd_text or not jd_text.strip():
        print("⚠️ No job description provided - skipping semantic gap analysis")
        return {
            'semantic_similarity': 0.0,
            'strong_matches': [],
            'weak_matches': [],
            'section_similarities': {},
            'total_chunks_analyzed': len(resume_chunks),
            'embedding_dimension': 0,
            'skipped_reason': 'No job description provided'
        }
    embedder = ResumeEmbedder()
    
    # Generate embeddings
    resume_embeddings = await embedder.embed_resume_chunks(resume_chunks)
    jd_embedding = await embedder.embed_job_description(jd_text)
    
    # Find similar chunks
    similar_chunks = find_similar_chunks(resume_embeddings, jd_embedding, similarity_threshold)
    
    # Calculate section-level similarities
    section_similarities = {}
    for emb in resume_embeddings:
        if emb.section:
            sim = cosine_similarity(emb.embedding, jd_embedding.embedding)
            if emb.section not in section_similarities or sim > section_similarities[emb.section]:
                section_similarities[emb.section] = round(sim, 3)
    
    # Calculate overall semantic match
    if resume_embeddings:
        avg_similarity = np.mean([
            cosine_similarity(emb.embedding, jd_embedding.embedding) 
            for emb in resume_embeddings
        ])
    else:
        avg_similarity = 0.0
    
    return {
        'semantic_similarity': round(avg_similarity, 3),
        'strong_matches': [m for m in similar_chunks if m.similarity_score >= 0.7],
        'weak_matches': [m for m in similar_chunks if 0.3 <= m.similarity_score < 0.7],
        'section_similarities': section_similarities,
        'total_chunks_analyzed': len(resume_embeddings),
        'embedding_dimension': len(jd_embedding.embedding)
    }


# Sync wrappers for non-async code
def embed_resume_chunks_sync(chunks: List[DocumentChunk]) -> List[EmbeddingResult]:
    """Synchronous wrapper for embed_resume_chunks."""
    embedder = ResumeEmbedder()
    return asyncio.run(embedder.embed_resume_chunks(chunks))


def analyze_semantic_gaps_sync(
    resume_chunks: List[DocumentChunk],
    jd_text: str,
    similarity_threshold: float = 0.3
) -> Dict[str, Any]:
    """Synchronous wrapper for analyze_semantic_gaps."""
    return asyncio.run(analyze_semantic_gaps(resume_chunks, jd_text, similarity_threshold))


class GapAnalyzer:
    """Comprehensive gap analysis combining keywords and semantic similarity."""
    
    def __init__(self):
        self.embedder = ResumeEmbedder()
    
    async def analyze_resume_gaps(
        self,
        resume_chunks: List[DocumentChunk],
        jd_text: str,
        jd_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive gap analysis between resume and job description.
        
        Args:
            resume_chunks: Parsed resume chunks
            jd_text: Job description text
            jd_title: Optional job title for context
            
        Returns:
            Complete gap analysis with recommendations
        """
        
        print(f"🔍 Analyzing gaps for {len(resume_chunks)} resume chunks...")
        
        # 1. Keyword-based analysis
        keyword_gaps = await self._analyze_keyword_gaps(resume_chunks, jd_text)
        
        # 2. Semantic similarity analysis  
        semantic_gaps = await analyze_semantic_gaps(resume_chunks, jd_text)
        
        # 3. Section-specific analysis
        section_gaps = self._analyze_section_gaps(resume_chunks, jd_text)
        
        # 4. Generate recommendations
        recommendations = self._generate_recommendations(keyword_gaps, semantic_gaps, section_gaps)
        
        # 5. Calculate overall score
        overall_score = self._calculate_overall_score(keyword_gaps, semantic_gaps)
        
        result = {
            'overall_match_score': overall_score,
            'keyword_analysis': keyword_gaps,
            'semantic_analysis': semantic_gaps,
            'section_analysis': section_gaps,
            'recommendations': recommendations,
            'missing_keywords': keyword_gaps.get('missing_keywords', []),
            'weak_keywords': keyword_gaps.get('weak_keywords', []),
            'strong_sections': [s for s, score in semantic_gaps.get('section_similarities', {}).items() if score >= 0.6],
            'weak_sections': [s for s, score in semantic_gaps.get('section_similarities', {}).items() if score < 0.4]
        }
        
        print(f"✅ Gap analysis complete. Overall score: {overall_score:.2f}")
        return result
    
    async def _analyze_keyword_gaps(
        self, 
        resume_chunks: List[DocumentChunk], 
        jd_text: str
    ) -> Dict[str, Any]:
        """Analyze keyword-based gaps between resume and JD."""
        
        from ..resume.keywords import extract_jd_requirements, calculate_skill_coverage
        
        # Extract resume keywords from all chunks
        resume_text = '\n'.join([chunk.text for chunk in resume_chunks])
        resume_keywords = extract_keywords_from_text(resume_text)
        resume_kw_list = [kw.keyword for kw in resume_keywords]
        
        # Extract JD requirements
        jd_keywords, importance_map = extract_jd_requirements(jd_text)
        
        # Calculate coverage
        coverage = calculate_skill_coverage(resume_kw_list, jd_keywords, importance_map)
        
        # Identify weak keywords (present but low similarity)
        weak_keywords = []
        for chunk in resume_chunks:
            chunk_keywords = extract_keywords_from_text(chunk.text)
            chunk_kw_set = {kw.keyword.lower() for kw in chunk_keywords}
            
            for kw in chunk_kw_set:
                if kw in [k.lower() for k in jd_keywords]:
                    # Check if this keyword appears weakly in this chunk
                    kw_match = next((k for k in chunk_keywords if k.keyword.lower() == kw), None)
                    if kw_match and kw_match.frequency < 2:
                        weak_keywords.append(kw_match.keyword)
        
        return {
            'coverage_score': coverage['coverage_score'],
            'matched_keywords': coverage['matched_keywords'],
            'missing_keywords': coverage['missing_keywords'],
            'weak_keywords': list(set(weak_keywords)),
            'critical_missing': coverage['critical_missing'],
            'keyword_frequency': {kw.keyword: kw.frequency for kw in resume_keywords},
            'importance_map': importance_map
        }
    
    def _analyze_section_gaps(
        self, 
        resume_chunks: List[DocumentChunk], 
        jd_text: str
    ) -> Dict[str, Any]:
        """Analyze gaps at the section level."""
        
        # Group chunks by section
        sections = {}
        for chunk in resume_chunks:
            if chunk.section not in sections:
                sections[chunk.section] = []
            sections[chunk.section].append(chunk)
        
        section_analysis = {}
        
        # Expected sections for a complete resume
        expected_sections = ['summary', 'experience', 'skills', 'education']
        missing_sections = []
        
        for expected in expected_sections:
            if expected not in sections:
                missing_sections.append(expected)
            else:
                chunk_count = len(sections[expected])
                total_text = '\n'.join([c.text for c in sections[expected]])
                word_count = len(total_text.split())
                
                section_analysis[expected] = {
                    'present': True,
                    'chunk_count': chunk_count,
                    'word_count': word_count,
                    'completeness': min(1.0, word_count / 50)  # Rough completeness metric
                }
        
        return {
            'section_completeness': section_analysis,
            'missing_sections': missing_sections,
            'total_sections': len(sections),
            'section_distribution': {k: len(v) for k, v in sections.items()}
        }
    
    def _generate_recommendations(
        self,
        keyword_gaps: Dict[str, Any],
        semantic_gaps: Dict[str, Any], 
        section_gaps: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on gap analysis."""
        
        recommendations = []
        
        # Keyword recommendations
        critical_missing = keyword_gaps.get('critical_missing', [])
        if critical_missing:
            recommendations.append({
                'type': 'critical',
                'action': f"Add critical missing skills: {', '.join(critical_missing[:3])}",
                'reason': 'These skills are marked as required in the job description',
                'priority': 'high'
            })
        
        missing_keywords = keyword_gaps.get('missing_keywords', [])
        if len(missing_keywords) > len(critical_missing):
            other_missing = [kw for kw in missing_keywords if kw not in critical_missing]
            recommendations.append({
                'type': 'enhancement',
                'action': f"Consider adding: {', '.join(other_missing[:5])}",
                'reason': 'These skills appear in the job description but not in your resume',
                'priority': 'medium'
            })
        
        # Semantic recommendations
        weak_matches = semantic_gaps.get('weak_matches', [])
        if weak_matches:
            recommendations.append({
                'type': 'strengthening',
                'action': f"Strengthen {len(weak_matches)} experience sections with more specific details",
                'reason': 'These sections relate to the job but could be more detailed',
                'priority': 'medium'
            })
        
        # Section recommendations
        missing_sections = section_gaps.get('missing_sections', [])
        if missing_sections:
            recommendations.append({
                'type': 'structure',
                'action': f"Add missing sections: {', '.join(missing_sections)}",
                'reason': 'Complete resumes typically include these sections',
                'priority': 'low'
            })
        
        # Low overall similarity
        if semantic_gaps.get('semantic_similarity', 0) < 0.4:
            recommendations.append({
                'type': 'major_revision',
                'action': 'Consider significant resume revision for this role',
                'reason': 'Low semantic similarity suggests major skill/experience gaps',
                'priority': 'high'
            })
        
        return recommendations
    
    def _calculate_overall_score(
        self,
        keyword_gaps: Dict[str, Any],
        semantic_gaps: Dict[str, Any]
    ) -> float:
        """Calculate weighted overall match score."""
        
        # Weights for different factors
        keyword_weight = 0.6  # Keyword matching is very important for ATS
        semantic_weight = 0.4  # Semantic similarity for human reviewers
        
        keyword_score = keyword_gaps.get('coverage_score', 0.0)
        semantic_score = semantic_gaps.get('semantic_similarity', 0.0)
        
        overall = (keyword_score * keyword_weight) + (semantic_score * semantic_weight)
        
        return round(overall, 3)


# Convenience function for the complete analysis
async def perform_gap_analysis(
    resume_chunks: List[DocumentChunk],
    jd_text: str,
    jd_title: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform complete gap analysis between resume and job description.
    
    Args:
        resume_chunks: Parsed resume chunks
        jd_text: Job description text  
        jd_title: Optional job title
        
    Returns:
        Complete gap analysis results
    """
    
    analyzer = GapAnalyzer()
    return await analyzer.analyze_resume_gaps(resume_chunks, jd_text, jd_title)


# Sync wrapper
def perform_gap_analysis_sync(
    resume_chunks: List[DocumentChunk],
    jd_text: str,
    jd_title: Optional[str] = None
) -> Dict[str, Any]:
    """Synchronous wrapper for perform_gap_analysis."""
    return asyncio.run(perform_gap_analysis(resume_chunks, jd_text, jd_title))