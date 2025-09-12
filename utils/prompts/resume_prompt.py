
from schemas import NormalizedResumeSchema
import json
from typing import List,Dict
def create_normalization_prompt(raw_text: str, file_type: str) -> tuple[str, str]:
    """
    Create system and user messages for resume normalization with explicit schema.

    Args:
    raw_text: Raw extracted text from document
    file_type: Source file type for context

    Returns:
    Tuple of (system_message, user_message)
    """

    # Get the schema example from NormalizedResumeSchema
    schema_example = NormalizedResumeSchema.Config.schema_extra["example"]

    system_message = f"""You are an expert resume parser and data extraction specialist. Your task is to extract and normalize resume information from raw text that may contain formatting issues or OCR errors.

    CRITICAL INSTRUCTIONS:
    1. Extract ALL available information accurately
    2. Normalize dates to consistent format (YYYY-YYYY or MM/YYYY-MM/YYYY)
    3. Clean up garbled text and fix obvious OCR errors
    4. Structure work experience chronologically (most recent first)
    5. Separate and categorize all skills appropriately
    6. Extract contact information comprehensively
    7. Preserve all quantifiable achievements and metrics
    8. If information is unclear or missing, use null or empty arrays
    9. Return ONLY valid JSON matching the EXACT schema below

    REQUIRED JSON SCHEMA - You MUST follow this structure exactly:

    {json.dumps(schema_example, indent=2)}

    SCHEMA RULES:
    - contact_information: REQUIRED - extract name, email, phone, location, social profiles
    - work_experience: Array of jobs, most recent first, with detailed responsibilities
    - education: Array of educational background with degrees, institutions, dates
    - skills: Categorize into technical_skills, programming_languages, frameworks, tools, etc.
    - professional_summary: Extract or infer from objective/summary sections
    - certifications: Professional certifications with issuing organizations
    - projects: Personal/side projects mentioned
    - additional_sections: For non-standard sections like Patents, Publications, Awards, Volunteer Work

    FIELD MAPPING GUIDANCE:
    - Put programming languages in "programming_languages", not "technical_skills"
    - Separate frameworks/libraries from core programming languages  
    - Cloud platforms (AWS, GCP, Azure) go in "cloud_platforms"
    - Databases get their own "databases" category
    - Soft skills like "communication" go in "soft_skills"
    - Put unusual sections (Patents, Publications, Speaking, Military, etc.) in "additional_sections"

    ADDITIONAL SECTIONS FORMAT:
    For any non-standard sections, use this structure:
    {{
    "section_title": "exact title from resume",
    "section_type": "category like 'publications', 'awards', 'volunteer'", 
    "content": {{ flexible structure preserving all information }}
    }}

    Return ONLY the JSON object, no explanations or markdown formatting."""

    user_message = f"""Parse and normalize this resume text extracted from a {file_type} file:

    RAW TEXT:
    {raw_text}

    SPECIFIC EXTRACTION REQUIREMENTS:
    - Fix obvious formatting and OCR errors
    - Extract complete contact information (name, email, phone, location, all social profiles)
    - Structure work experience with normalized date formats and detailed responsibilities
    - Categorize skills into appropriate technical subcategories
    - Capture education with degrees, institutions, graduation dates, honors
    - Extract certifications with issuing organizations and dates
    - Identify projects with technologies and descriptions
    - Preserve ALL quantifiable metrics and achievements exactly as stated
    - Map unusual sections (Patents, Publications, Awards, etc.) to additional_sections

    Return the complete structured JSON following the exact schema provided:"""

    return system_message, user_message



def create_json_prompt(system_message: str, user_content: str) -> List[Dict[str, str]]:
    """
    Create a standardized prompt for JSON generation.

    Args:
    system_message: System instruction
    user_content: User request
    schema_class: Expected response schema

    Returns:
    Formatted messages for LLM
    """

    enhanced_system = f"""{system_message}
    Rules:
    - Return ONLY JSON, no explanations or markdown
    - All required fields must be present
    - Use exact field names and types as shown
    - No additional fields beyond the schema"""

    return [
        {"role": "system", "content": enhanced_system},
        {"role": "user", "content": user_content}
    ]
