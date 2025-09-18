from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field,field_validator

# Optional: light date pattern docstring; 
DATE_HINT = "Use one of: YYYY, YYYY-MM, or MM/YYYY; use 'Present' for ongoing roles"

class ContactInformation(BaseModel):
    name: str = Field(..., description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="Location (city, state/province, country)")
    website: Optional[str] = Field(None, description="Personal website")
    professional_profiles: Dict[str, str] = Field(
        default_factory=dict,
        description="Profiles like LinkedIn, GitHub, portfolio, etc."
    )
    
    @field_validator("professional_profiles", mode="before")
    @classmethod
    def clean_profiles(cls, v: Any) -> Dict[str, str]:
        """
        Accept dict-ish input, drop keys with falsy/non-string values,
        and normalize common keys.
        """
        if v is None:
            return {}
        if not isinstance(v, dict):
            # if someone sent a list/string, just ignore
            return {}

        normalized = {}
        for k, val in v.items():
            if not val:
                continue  # drop None/empty
            # stringify non-strings safely
            if not isinstance(val, str):
                try:
                    val = str(val)
                except Exception:
                    continue
            key = (k or "").strip()
            if not key:
                continue
            # optional: canonicalize common keys
            kl = key.lower()
            if kl in {"linkedin", "linked_in"}:
                key = "LinkedIn"
            elif kl in {"github", "git_hub"}:
                key = "GitHub"
            normalized[key] = val.strip()
        return normalized

class WorkExperienceItem(BaseModel):
    job_title: str = Field(..., description="Job title/role")
    company: str = Field(..., description="Company/organization name")
    start_date: Optional[str] = Field(None, description=f"Start date. {DATE_HINT}")
    end_date: Optional[str] = Field(None, description=f"End date or 'Present'. {DATE_HINT}")
    location: Optional[str] = Field(None, description="Job location")
    responsibilities: List[str] = Field(default_factory=list, description="Key responsibilities and achievements")
    tools_used: List[str] = Field(default_factory=list, description="Tools, software, technologies used")
    metrics_achieved: List[str] = Field(default_factory=list, description="Quantifiable achievements/results")
    industry_context: Dict[str, Any] = Field(default_factory=dict, description="Optional industry specifics")
    @field_validator('industry_context', mode='before')
    @classmethod
    def coerce_none_to_empty_dict(cls, v):
        return {} if v in (None, "", []) else v
class EducationItem(BaseModel):
    degree: Optional[str] = Field(None, description="Degree type/education level")
    field_of_study: Optional[str] = Field(None, description="Major/field/specialization")
    institution: str = Field(..., description="School/university/training institution")
    completion_date: Optional[str] = Field(None, description=f"Graduation/completion date. {DATE_HINT}")
    location: Optional[str] = Field(None, description="Institution location")
    grade: Optional[str] = Field(None, description="GPA/grade/class rank")
    achievements: List[str] = Field(default_factory=list, description="Honors/awards/coursework")

class SkillCategory(BaseModel):
    category_name: str = Field(..., description="Name of skill category")
    skills: List[str] = Field(default_factory=list, description="Skills in this category")
    proficiency_level: Optional[str] = Field(None, description="Overall proficiency if mentioned")

class UniversalSkills(BaseModel):
    core_competencies: List[str] = Field(default_factory=list, description="Primary professional skills")
    tools_and_software: List[str] = Field(default_factory=list, description="Software/platforms/equipment")
    methodologies: List[str] = Field(default_factory=list, description="Processes/frameworks/methodologies")
    soft_skills: List[str] = Field(default_factory=list, description="Interpersonal/communication skills")
    languages: List[str] = Field(default_factory=list, description="Spoken/written languages")
    specialized_skills: List[SkillCategory] = Field(
        default_factory=list,
        description="Industry-specific skill categories (e.g., Programming Languages, Medical Procedures)"
    )

class CertificationItem(BaseModel):
    name: str = Field(..., description="Certification/license name")
    issuing_organization: Optional[str] = Field(None, description="Issuing organization")
    issue_date: Optional[str] = Field(None, description=f"Issue/earned date. {DATE_HINT}")
    expiration_date: Optional[str] = Field(None, description=f"Expiration date. {DATE_HINT}")
    credential_id: Optional[str] = Field(None, description="Credential/License number")
    credential_url: Optional[str] = Field(None, description="Verification URL")
    status: Optional[str] = Field(None, description="Status (active, expired, pending)")

class ProjectItem(BaseModel):
    name: str = Field(..., description="Project/portfolio item name")
    description: Optional[str] = Field(None, description="Project description")
    role: Optional[str] = Field(None, description="Your role")
    start_date: Optional[str] = Field(None, description=f"Start date. {DATE_HINT}")
    end_date: Optional[str] = Field(None, description=f"End date. {DATE_HINT}")
    tools_used: List[str] = Field(default_factory=list, description="Tools/technologies used")
    outcomes: List[str] = Field(default_factory=list, description="Results/impact/achievements")
    links: Dict[str, str] = Field(default_factory=dict, description="URLs (portfolio, GitHub, demo, etc.)")

class AdditionalSection(BaseModel):
    section_title: str = Field(..., description="Section title as in resume")
    section_type: str = Field(..., description="Category (awards, publications, volunteer, licenses)")
    content: Dict[str, Any] = Field(..., description="Flexible content")
    relevance_keywords: List[str] = Field(default_factory=list, description="Keywords indicating role relevance")

class IndustryHints(BaseModel):
    primary_industry: Optional[str] = Field(None, description="Primary industry")
    secondary_industries: List[str] = Field(default_factory=list, description="Secondary industries")
    role_level: Optional[str] = Field(None, description="Role level (entry, mid, senior, executive)")
    specializations: List[str] = Field(default_factory=list, description="Specializations within industry")

class NormalizedResumeSchema(BaseModel):
    contact_information: ContactInformation = Field(..., description="Contact details")
    professional_summary: Optional[str] = Field(None, description="Professional summary/objective")
    work_experience: List[WorkExperienceItem] = Field(default_factory=list, description="Work history")
    education: List[EducationItem] = Field(default_factory=list, description="Education and training")
    skills: Optional[UniversalSkills] = Field(None, description="Skills and competencies")
    certifications_and_licenses: List[CertificationItem] = Field(default_factory=list, description="Certs/licenses")
    projects_and_portfolio: List[ProjectItem] = Field(default_factory=list, description="Projects/portfolio")
    additional_sections: List[AdditionalSection] = Field(default_factory=list, description="Other sections")
    industry_context: Optional[IndustryHints] = Field(None, description="Detected industry and role context")
    parsed_date: Optional[str] = Field(None, description="When this resume was parsed (ISO-8601 preferred)")
    source_format: Optional[str] = Field(None, description="Original file format")

