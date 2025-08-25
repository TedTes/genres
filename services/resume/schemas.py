"""
Pydantic schemas for resume optimization data structures.
Defines input/output formats and validation for the optimization pipeline.
"""

from typing import List, Dict, Optional, Union, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class ResumeInput(BaseModel):
    """Input for resume optimization - text, DOCX, or PDF file."""
    
    text: Optional[str] = Field(None, description="Raw resume text")
    docx_url: Optional[str] = Field(None, description="URL or path to DOCX file")
    pdf_url: Optional[str] = Field(None, description="URL or path to PDF file")
    
    @validator('*', pre=True)
    def validate_input(cls, v, values):
        """Ensure exactly one input method is provided."""
        inputs = [values.get('text'), values.get('docx_url'), values.get('pdf_url')]
        provided = [inp for inp in inputs if inp is not None]
        
        if len(provided) == 0:
            raise ValueError("One of 'text', 'docx_url', or 'pdf_url' must be provided")
        elif len(provided) > 1:
            raise ValueError("Only one input method should be provided")
        
        return v
    
    @property
    def input_type(self) -> str:
        """Get the type of input provided."""
        if self.text:
            return "text"
        elif self.docx_url:
            return "docx"
        elif self.pdf_url:
            return "pdf"
        return "unknown"
    
    class Config:
        schema_extra = {
            "examples": [
                {
                    "text": "John Smith\nSoftware Engineer\n\nExperience:\n- Built web applications..."
                },
                {
                    "docx_url": "/uploads/resume.docx"
                },
                {
                    "pdf_url": "/uploads/resume.pdf"
                }
            ]
        }

class JDInput(BaseModel):
    """Job description input for matching."""
    
    text: str = Field(..., description="Job description text")
    title: Optional[str] = Field(None, description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    
    class Config:
        schema_extra = {
            "example": {
                "text": "We are seeking a Senior Python Developer with experience in Flask, PostgreSQL...",
                "title": "Senior Python Developer",
                "company": "TechCorp"
            }
        }


class OptimizationOptions(BaseModel):
    """Options for resume optimization."""
    
    locale: str = Field("en-US", description="Locale for optimization")
    tone: str = Field("professional-concise", description="Writing tone")
    max_bullets_per_job: int = Field(4, description="Maximum bullets per job")
    include_skills_section: bool = Field(True, description="Include skills section")
    ats_optimize: bool = Field(True, description="Optimize for ATS systems")
    
    class Config:
        schema_extra = {
            "example": {
                "locale": "en-US",
                "tone": "professional-concise",
                "max_bullets_per_job": 4,
                "include_skills_section": True,
                "ats_optimize": True
            }
        }


class ExperienceItem(BaseModel):
    """Single work experience item."""
    
    company: str = Field(..., description="Company name")
    role: str = Field(..., description="Job role/title")
    dates: Optional[str] = Field(None, description="Employment dates")
    bullets: List[str] = Field(..., description="Achievement bullets")
    
    class Config:
        schema_extra = {
            "example": {
                "company": "TechCorp",
                "role": "Software Engineer",
                "dates": "2020-2023",
                "bullets": [
                    "Developed Python applications serving 10k+ users",
                    "Implemented CI/CD pipelines reducing deployment time by 60%"
                ]
            }
        }


class OptimizedResume(BaseModel):
    """LLM output structure for optimized resume."""
    
    summary: Optional[str] = Field(None, description="Professional summary")
    experience: List[ExperienceItem] = Field(..., description="Work experience")
    skills_to_add: List[str] = Field([], description="Recommended skills to highlight")
    education: Optional[List[Dict[str, str]]] = Field(None, description="Education section")
    skills: Optional[List[str]] = Field(None, description="Technical skills")
    
    class Config:
        schema_extra = {
            "example": {
                "summary": "Experienced Python developer with expertise in web applications...",
                "experience": [
                    {
                        "company": "TechCorp",
                        "role": "Software Engineer",
                        "dates": "2020-2023",
                        "bullets": [
                            "Developed scalable Python applications using Flask and PostgreSQL"
                        ]
                    }
                ],
                "skills_to_add": ["Docker", "Kubernetes", "AWS"]
            }
        }


class GapReport(BaseModel):
    """Analysis of resume gaps compared to job description."""
    
    missing: List[str] = Field(..., description="Skills/keywords missing from resume")
    weak: List[str] = Field(..., description="Skills present but underemphasized")
    coverage_score: float = Field(..., description="Overall match score (0.0-1.0)")
    keyword_analysis: Dict[str, Any] = Field({}, description="Detailed keyword analysis")
    
    class Config:
        schema_extra = {
            "example": {
                "missing": ["Docker", "Kubernetes", "CI/CD"],
                "weak": ["Python", "PostgreSQL"],
                "coverage_score": 0.65,
                "keyword_analysis": {
                    "total_keywords": 20,
                    "matched_keywords": 13,
                    "missing_critical": 3
                }
            }
        }


class ChangeRationale(BaseModel):
    """Explanation for a specific resume change."""
    
    change: str = Field(..., description="What was changed")
    reason: str = Field(..., description="Why it was changed")
    
    class Config:
        schema_extra = {
            "example": {
                "change": "Added 'CI/CD pipelines' to experience bullet",
                "reason": "Job description emphasizes DevOps practices and automation"
            }
        }


class Rationale(BaseModel):
    """Complete explanation of resume changes."""
    
    rationale: List[ChangeRationale] = Field(..., description="List of changes and reasons")
    
    class Config:
        schema_extra = {
            "example": {
                "rationale": [
                    {
                        "change": "Added 'Docker' to skills section",
                        "reason": "Job requires containerization experience"
                    },
                    {
                        "change": "Emphasized 'scalable applications' in experience",
                        "reason": "Job description mentions high-scale systems"
                    }
                ]
            }
        }


class OptimizationResult(BaseModel):
    """Complete result of resume optimization process."""
    
    match_score: float = Field(..., description="Overall match score (0.0-1.0)")
    missing_keywords: List[str] = Field(..., description="Missing keywords")
    weak_keywords: List[str] = Field(..., description="Weak keywords")
    optimized_resume: OptimizedResume = Field(..., description="Optimized resume content")
    explanations: Rationale = Field(..., description="Change explanations")
    
    # Updated artifacts to include PDF
    artifacts: Dict[str, Optional[str]] = Field(
        default_factory=lambda: {"docx_url": None, "pdf_url": None}, 
        description="Generated file URLs"
    )
    
    model_info: Dict[str, str] = Field(..., description="Model and provider information")
    processing_time_ms: Optional[float] = Field(None, description="Processing time")
    input_type: Optional[str] = Field(None, description="Original input format (text/docx/pdf)")
    
    class Config:
        schema_extra = {
            "example": {
                "match_score": 0.85,
                "missing_keywords": ["Docker"],
                "weak_keywords": ["Python"],
                "optimized_resume": {"summary": "...", "experience": []},
                "explanations": {"rationale": []},
                "artifacts": {
                    "docx_url": "https://s3.../optimized_resume.docx",
                    "pdf_url": "https://s3.../optimized_resume.pdf"
                },
                "model_info": {"provider": "hf", "llm": "mistral-7b", "embed": "bge-large"},
                "processing_time_ms": 2500.0,
                "input_type": "pdf"
            }
        }


def validate_json_response(json_str: str, schema_class: BaseModel) -> BaseModel:
    """
    Validate and parse JSON response from LLM.
    Includes retry logic for malformed JSON.
    
    Args:
        json_str: JSON string from LLM
        schema_class: Pydantic model class to validate against
        
    Returns:
        Validated Pydantic model instance
        
    Raises:
        ValueError: If JSON is invalid after retry
    """
    import json
    from pydantic import ValidationError
    
    try:
        # Try to parse JSON
        json_data = json.loads(json_str)
        
        # Validate against schema
        return schema_class(**json_data)
        
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"Invalid JSON response: {str(e)}\nResponse: {json_str[:200]}...")


def validate_file_format(file_url: str) -> str:
    """
    Validate file format based on URL/path extension.
    
    Args:
        file_url: File URL or path
        
    Returns:
        File format ('pdf', 'docx', or raises ValueError)
    """
    import os
    
    if not file_url:
        raise ValueError("File URL cannot be empty")
    
    # Get file extension
    _, ext = os.path.splitext(file_url.lower())
    
    if ext == '.pdf':
        return 'pdf'
    elif ext in ['.docx', '.doc']:
        return 'docx'
    else:
        raise ValueError(f"Unsupported file format: {ext}. Only PDF and DOCX are supported.")


class SupportedFormats:
    """Constants for supported file formats."""
    PDF = "pdf"
    DOCX = "docx"
    TEXT = "text"
    
    ALL = [PDF, DOCX, TEXT]
    
    @classmethod
    def is_supported(cls, format_type: str) -> bool:
        """Check if format is supported."""
        return format_type.lower() in cls.ALL