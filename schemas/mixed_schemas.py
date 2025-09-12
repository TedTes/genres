from typing import List, Dict, Optional,  Any
from pydantic import BaseModel, Field, model_validator



class ResumeInput(BaseModel):
    """Input for resume optimization - text, DOCX, or PDF file."""
    
    text: Optional[str] = Field(None, description="Raw resume text")
    docx_url: Optional[str] = Field(None, description="URL or path to DOCX file")
    pdf_url: Optional[str] = Field(None, description="URL or path to PDF file")

    @model_validator(mode='after')
    def validate_input(self):
        """Ensure exactly one input method is provided."""
        text = self.text
        docx_url = self.docx_url
        pdf_url = self.pdf_url
        provided = [inp for inp in [text, docx_url, pdf_url] if inp is not None]
        
        if len(provided) == 0:
                raise ValueError("One of 'text', 'docx_url', or 'pdf_url' must be provided")
        elif len(provided) > 1:
                raise ValueError("Only one input method should be provided")
            
        return self
    
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
    def dict(self, **kwargs):
        """Convert to dictionary for JSON serialization."""
        return super().dict(**kwargs)

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
    def dict(self, **kwargs):
        """Convert to dictionary for JSON serialization."""
        return super().dict(**kwargs)


class OptimizationOptions(BaseModel):
    """Options for resume optimization."""
    
    locale: str = Field("en-US", description="Locale for optimization")
    tone: str = Field("professional-concise", description="Writing tone")
    max_bullets_per_job: int = Field(4, description="Maximum bullets per job")
    include_skills_section: bool = Field(True, description="Include skills section")
    ats_optimize: bool = Field(True, description="Optimize for ATS systems")
    include_pdf: bool = Field(True, description="Generate PDF version")
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
    def dict(self, **kwargs):
        """Convert to dictionary for JSON serialization."""
        return super().dict(**kwargs)


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
    def dict(self, **kwargs):
        """Convert to dictionary for JSON serialization."""
        return super().dict(**kwargs)



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
    def dict(self, **kwargs):
        """Convert to dictionary for JSON serialization."""
        return super().dict(**kwargs)


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
    def dict(self, **kwargs):
        """Convert to dictionary for JSON serialization."""
        return super().dict(**kwargs)


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
    def dict(self, **kwargs):
        """Convert to dictionary for JSON serialization."""
        return super().dict(**kwargs)


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
    def dict(self, **kwargs):
        """Convert to dictionary for JSON serialization."""
        return super().dict(**kwargs)


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
    def dict(self, **kwargs):
        """Convert to dictionary for JSON serialization."""
        return super().dict(**kwargs)


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

