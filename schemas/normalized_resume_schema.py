from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ContactInformation(BaseModel):
    """Universal contact information."""
    name: str = Field(..., description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="Location (city, state/province, country)")
    website: Optional[str] = Field(None, description="Personal website")
    professional_profiles: Optional[Dict[str, str]] = Field(
        None, 
        description="Professional profiles (LinkedIn, GitHub, Behance, Medical License, etc.)"
    )

class WorkExperienceItem(BaseModel):
    """Universal work experience structure."""
    job_title: str = Field(..., description="Job title/role")
    company: str = Field(..., description="Company/organization name")
    start_date: Optional[str] = Field(None, description="Start date (normalized format)")
    end_date: Optional[str] = Field(None, description="End date (normalized format or 'Present')")
    location: Optional[str] = Field(None, description="Job location")
    
    # Core experience content
    responsibilities: List[str] = Field(default=[], description="Key responsibilities and achievements")
    
    # Flexible skill/tool mentions
    tools_used: Optional[List[str]] = Field(None, description="Tools, software, technologies, equipment used")
    
    # Quantifiable results (universal across industries)
    metrics_achieved: Optional[List[str]] = Field(None, description="Quantifiable achievements and results")
    
    # Industry-specific context
    industry_context: Optional[Dict[str, Any]] = Field(
        None, 
        description="Industry-specific details (e.g., patient load, revenue managed, team size)"
    )

class EducationItem(BaseModel):
    """Universal education structure."""
    degree: Optional[str] = Field(None, description="Degree type or education level")
    field_of_study: Optional[str] = Field(None, description="Major/field of study/specialization")
    institution: str = Field(..., description="School/university/training institution")
    completion_date: Optional[str] = Field(None, description="Graduation/completion date")
    location: Optional[str] = Field(None, description="Institution location")
    grade: Optional[str] = Field(None, description="GPA, grade, or class rank if mentioned")
    achievements: Optional[List[str]] = Field(None, description="Honors, awards, distinctions, relevant coursework")

class SkillCategory(BaseModel):
    """Flexible skill category that adapts to any industry."""
    category_name: str = Field(..., description="Name of skill category")
    skills: List[str] = Field(..., description="List of skills in this category")
    proficiency_level: Optional[str] = Field(None, description="Overall proficiency if mentioned")

class UniversalSkills(BaseModel):
    """Industry-agnostic skills structure."""
    # Core categories that apply to most roles
    core_competencies: Optional[List[str]] = Field(None, description="Primary professional skills")
    tools_and_software: Optional[List[str]] = Field(None, description="Software, platforms, equipment")
    methodologies: Optional[List[str]] = Field(None, description="Processes, frameworks, methodologies")
    soft_skills: Optional[List[str]] = Field(None, description="Interpersonal and communication skills")
    languages: Optional[List[str]] = Field(None, description="Spoken/written languages")
    
    # Flexible categories for industry-specific skills
    specialized_skills: Optional[List[SkillCategory]] = Field(
        None, 
        description="Industry-specific skill categories (e.g., Programming Languages, Medical Procedures, Sales Techniques)"
    )

class CertificationItem(BaseModel):
    """Universal certification/license structure."""
    name: str = Field(..., description="Certification/license name")
    issuing_organization: Optional[str] = Field(None, description="Issuing organization")
    issue_date: Optional[str] = Field(None, description="Issue/earned date")
    expiration_date: Optional[str] = Field(None, description="Expiration date")
    credential_id: Optional[str] = Field(None, description="Credential ID or license number")
    credential_url: Optional[str] = Field(None, description="Verification URL")
    status: Optional[str] = Field(None, description="Current status (active, expired, pending)")

class ProjectItem(BaseModel):
    """Universal project/portfolio structure."""
    name: str = Field(..., description="Project/portfolio item name")
    description: Optional[str] = Field(None, description="Project description")
    role: Optional[str] = Field(None, description="Your role in the project")
    start_date: Optional[str] = Field(None, description="Start date")
    end_date: Optional[str] = Field(None, description="End date")
    tools_used: Optional[List[str]] = Field(None, description="Tools, technologies, or methods used")
    outcomes: Optional[List[str]] = Field(None, description="Results, impact, or key achievements")
    links: Optional[Dict[str, str]] = Field(None, description="URLs (portfolio, GitHub, demo, etc.)")

class AdditionalSection(BaseModel):
    """Flexible section for industry-specific content."""
    section_title: str = Field(..., description="Section title as it appears in resume")
    section_type: str = Field(..., description="Category hint (awards, publications, volunteer, licenses)")
    content: Dict[str, Any] = Field(..., description="Flexible content structure")
    relevance_keywords: Optional[List[str]] = Field(
        None, 
        description="Keywords that indicate relevance to job roles"
    )

class IndustryHints(BaseModel):
    """Detected industry context from resume content."""
    primary_industry: Optional[str] = Field(None, description="Primary industry (detected or inferred)")
    secondary_industries: Optional[List[str]] = Field(None, description="Secondary industries")
    role_level: Optional[str] = Field(None, description="Role level (entry, mid, senior, executive)")
    specializations: Optional[List[str]] = Field(None, description="Specific specializations within industry")

class NormalizedResumeSchema(BaseModel):
    
    """
    Universal resume structure that adapts to any industry.
    Focuses on flexible, semantic content rather than rigid categories.
    """
    
    # Core required sections (universal)
    contact_information: ContactInformation = Field(..., description="Contact details")
    
    # Standard sections with flexible content
    professional_summary: Optional[str] = Field(None, description="Professional summary/objective")
    work_experience: Optional[List[WorkExperienceItem]] = Field(None, description="Work history")
    education: Optional[List[EducationItem]] = Field(None, description="Education and training")
    
    # Flexible skills structure
    skills: Optional[UniversalSkills] = Field(None, description="Skills and competencies")
    
    # Common optional sections
    certifications_and_licenses: Optional[List[CertificationItem]] = Field(
        None, 
        description="Professional certifications, licenses, credentials"
    )
    projects_and_portfolio: Optional[List[ProjectItem]] = Field(
        None, 
        description="Projects, portfolio items, significant work"
    )
    
    # Industry-specific or unique sections
    additional_sections: Optional[List[AdditionalSection]] = Field(
        default=[], 
        description="Industry-specific sections (Publications, Patents, Awards, Military Service, etc.)"
    )
    
    # Context and metadata
    industry_context: Optional[IndustryHints] = Field(
        None, 
        description="Detected industry and role context"
    )
    
    # System metadata
    parsed_date: Optional[str] = Field(None, description="When this resume was parsed")
    source_format: Optional[str] = Field(None, description="Original file format")
    
    class Config:
        schema_extra = {
            "examples": {
                "software_engineer": {
                    "contact_information": {
                        "name": "Sarah Chen",
                        "email": "sarah.chen@email.com",
                        "phone": "+1-555-123-4567",
                        "location": "Seattle, WA",
                        "professional_profiles": {
                            "linkedin": "linkedin.com/in/sarahchen",
                            "github": "github.com/sarahchen",
                            "portfolio": "sarahchen.dev"
                        }
                    },
                    "professional_summary": "Full-stack software engineer with 5+ years building scalable web applications...",
                    "work_experience": [
                        {
                            "job_title": "Senior Software Engineer",
                            "company": "TechCorp",
                            "start_date": "01/2021",
                            "end_date": "Present",
                            "responsibilities": [
                                "Led development of microservices architecture serving 1M+ users",
                                "Mentored team of 4 junior developers"
                            ],
                            "tools_used": ["Python", "React", "PostgreSQL", "AWS"],
                            "metrics_achieved": ["Reduced API response time by 60%", "Increased test coverage to 95%"]
                        }
                    ],
                    "skills": {
                        "core_competencies": ["Full-stack Development", "System Architecture", "Team Leadership"],
                        "tools_and_software": ["Git", "Docker", "Jenkins", "Jira"],
                        "methodologies": ["Agile", "Test-Driven Development", "CI/CD"],
                        "specialized_skills": [
                            {
                                "category_name": "Programming Languages",
                                "skills": ["Python", "JavaScript", "Java", "TypeScript"]
                            },
                            {
                                "category_name": "Frameworks",
                                "skills": ["React", "Django", "Flask", "Node.js"]
                            },
                            {
                                "category_name": "Cloud Platforms",
                                "skills": ["AWS", "GCP", "Azure"]
                            }
                        ]
                    },
                    "industry_context": {
                        "primary_industry": "Technology",
                        "role_level": "Senior",
                        "specializations": ["Web Development", "Backend Systems"]
                    }
                } 
            }
        }
    
    def dict(self, **kwargs):
        """Convert to dictionary for JSON serialization."""
        return super().dict(**kwargs)