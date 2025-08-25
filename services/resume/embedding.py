"""
Embedding generation and similarity calculations.
Handles text vectorization and semantic matching between resumes and job descriptions.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import asyncio

from ..resume.schemas import DocumentChunk
from ..resume.keywords import KeywordMatch, extract_keywords_from_text
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
        
        print(f"🎯 Generating job description embedding...")
        
        try:
            embeddings = await self.embedder.embed([jd_text])
            
            result = EmbeddingResult(
                text=jd_text,
                embedding=embeddings[0],
                token_count=len(jd_text.split())
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
) -> Dict[str, any]:
    """
    Analyze semantic gaps between resume and job description.
    
    Args:
        resume_chunks: Resume text chunks
        jd_text: Job description text
        similarity_threshold: Minimum similarity for matches
        
    Returns:
        Gap analysis with similarity metrics
    """
    
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
) -> Dict[str, any]:
    """Synchronous wrapper for analyze_semantic_gaps."""
    return asyncio.run(analyze_semantic_gaps(resume_chunks, jd_text, similarity_threshold))