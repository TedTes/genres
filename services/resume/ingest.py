"""
Document ingestion and parsing utilities.
Handles DOCX, PDF, and text input for resume processing.
"""

import os
import tempfile
from typing import Any,Dict, List, Optional, Tuple
import httpx
import mammoth
from pydantic import BaseModel

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


async def ingest_resume(
    text: Optional[str] = None,
    docx_url: Optional[str] = None, 
    pdf_url: Optional[str] = None
) -> ParsedResume:
    """
    Main ingestion function that handles all resume input types.
    
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
        raw_text = await extract_text_from_docx(docx_url)
        input_type = "docx"
    elif pdf_url:
        raw_text = await extract_text_from_pdf(pdf_url)
        input_type = "pdf"
    else:
        raise ValueError("No input provided")
    
    print(f"📄 Processing resume from {input_type} ({len(raw_text)} characters)")
    
    # Parse the text into structured format
    parsed = parse_resume_sections(raw_text)
    parsed.raw_text = raw_text
    
    # Create text chunks for embedding
    parsed.chunks = create_resume_chunks(parsed)
    
    print(f"✅ Parsed resume: {len(parsed.experience_items)} jobs, {len(parsed.chunks)} chunks")
    
    return parsed


async def extract_text_from_docx(docx_path: str) -> str:
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
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(docx_path)
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


async def extract_text_from_pdf(pdf_path: str) -> str:
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
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(pdf_path)
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


def parse_resume_sections(text: str) -> ParsedResume:
    """
    Parse resume text into structured sections using heuristics.
    
    Args:
        text: Raw resume text
        
    Returns:
        ParsedResume with parsed sections
    """
    
    lines = text.split('\n')
    parsed = ParsedResume(raw_text=text)
    
    # Common section headers (case insensitive)
    section_patterns = {
        'summary': ['summary', 'profile', 'objective', 'about'],
        'experience': ['experience', 'work', 'employment', 'career', 'professional'],
        'education': ['education', 'academic', 'degree', 'university', 'school'],
        'skills': ['skills', 'technical', 'technologies', 'competencies', 'expertise']
    }
    
    current_section = 'header'
    section_content = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line is a section header
        is_section_header = False
        for section_name, patterns in section_patterns.items():
            if any(pattern in line.lower() for pattern in patterns):
                # Save previous section
                if current_section and section_content:
                    parsed.sections[current_section] = '\n'.join(section_content)
                
                # Start new section
                current_section = section_name
                section_content = []
                is_section_header = True
                break
        
        if not is_section_header:
            section_content.append(line)
    
    # Save final section
    if current_section and section_content:
        parsed.sections[current_section] = '\n'.join(section_content)
    
    # Parse experience items from experience section
    if 'experience' in parsed.sections:
        parsed.experience_items = parse_experience_items(parsed.sections['experience'])
    
    # Extract skills from skills section
    if 'skills' in parsed.sections:
        parsed.skills = extract_skills_list(parsed.sections['skills'])
    
    return parsed


def parse_experience_items(experience_text: str) -> List[Dict[str, Any]]:
    """
    Parse experience section into individual job items.
    
    Args:
        experience_text: Experience section text
        
    Returns:
        List of experience dictionaries
    """
    
    items = []
    current_item = {}
    bullets = []
    
    lines = experience_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if line looks like a job title/company (heuristic)
        if (len(line.split()) <= 6 and 
            not line.startswith(('-', '•', '*')) and
            not line[0].islower()):
            
            # Save previous item
            if current_item and bullets:
                current_item['bullets'] = bullets
                items.append(current_item)
            
            # Start new item
            current_item = {'raw_line': line}
            bullets = []
            
            # Try to parse company/role
            parts = line.split(' | ')
            if len(parts) == 2:
                current_item['role'] = parts[0].strip()
                current_item['company'] = parts[1].strip()
            else:
                current_item['role'] = line
        
        # Check if line is a bullet point
        elif line.startswith(('-', '•', '*', '▪')):
            bullets.append(line[1:].strip())  # Remove bullet character
        
        # Other lines might be dates or continued descriptions
        else:
            if 'dates' not in current_item and any(char.isdigit() for char in line):
                current_item['dates'] = line
    
    # Save final item
    if current_item and bullets:
        current_item['bullets'] = bullets
        items.append(current_item)
    
    return items


def extract_skills_list(skills_text: str) -> List[str]:
    """
    Extract individual skills from skills section.
    
    Args:
        skills_text: Skills section text
        
    Returns:
        List of individual skills
    """
    
    skills = []
    
    # Split by common delimiters
    delimiters = [',', '|', '•', '-', '\n']
    text = skills_text
    
    for delimiter in delimiters:
        text = text.replace(delimiter, ',')
    
    # Extract skills
    for skill in text.split(','):
        skill = skill.strip()
        if skill and len(skill) > 1:
            skills.append(skill)
    
    return skills


def create_resume_chunks(parsed: ParsedResume) -> List[DocumentChunk]:
    """
    Create chunks of resume text for embedding and analysis.
    
    Args:
        parsed: ParsedResume object
        
    Returns:
        List of DocumentChunk objects
    """
    
    chunks = []
    chunk_index = 0
    
    # Chunk summary
    if 'summary' in parsed.sections:
        chunks.append(DocumentChunk(
            text=parsed.sections['summary'],
            section='summary',
            chunk_index=chunk_index,
            token_count=len(parsed.sections['summary'].split())
        ))
        chunk_index += 1
    
    # Chunk experience items (group bullets for context)
    for i, exp_item in enumerate(parsed.experience_items):
        if 'bullets' in exp_item:
            # Create chunks of 3-4 bullets each
            bullets = exp_item['bullets']
            chunk_size = 4
            
            for j in range(0, len(bullets), chunk_size):
                chunk_bullets = bullets[j:j + chunk_size]
                chunk_text = '\n'.join([f"- {bullet}" for bullet in chunk_bullets])
                
                # Add context
                context = f"Job: {exp_item.get('role', 'Unknown')} at {exp_item.get('company', 'Unknown')}\n{chunk_text}"
                
                chunks.append(DocumentChunk(
                    text=context,
                    section='experience',
                    chunk_index=chunk_index,
                    token_count=len(context.split()),
                    metadata={
                        'job_index': i,
                        'company': exp_item.get('company'),
                        'role': exp_item.get('role'),
                        'bullet_range': f"{j}-{min(j + chunk_size - 1, len(bullets) - 1)}"
                    }
                ))
                chunk_index += 1
    
    # Chunk skills
    if parsed.skills:
        skills_text = ', '.join(parsed.skills)
        chunks.append(DocumentChunk(
            text=f"Technical Skills: {skills_text}",
            section='skills',
            chunk_index=chunk_index,
            token_count=len(skills_text.split())
        ))
    
    return chunks


# Sync wrappers for non-async code
def ingest_resume_sync(*args, **kwargs) -> ParsedResume:
    """Synchronous wrapper for ingest_resume."""
    import asyncio
    return asyncio.run(ingest_resume(*args, **kwargs))