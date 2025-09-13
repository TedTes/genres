import json
from typing import Dict, Any

def get_optimization_prompt(
    normalized_resume: Dict[str, Any],
    jd_text: str,
    jd_title: str = None,
    optimization_focus: str = "professional-concise"
) -> tuple[str, str]:
    """
    Create comprehensive prompt for gap analysis + resume optimization in one LLM call.
    
    Args:
        normalized_resume: MultiNicheResume dictionary
        jd_text: Job description text
        jd_title: Job title (optional)
        optimization_focus: Tone/style for optimization
        
    Returns:
        Tuple of (system_message, user_message)
    """
    
    system_message = """You are an expert resume optimization specialist with deep knowledge across all industries. Your task is to perform comprehensive gap analysis and resume optimization in a single response.

CRITICAL INSTRUCTIONS:
1. Analyze gaps between the resume and job description with industry-specific expertise
2. Optimize the resume to better match the job requirements while maintaining authenticity
3. Provide detailed analysis and rationale for all changes
4. Adapt your approach based on the detected industry and role level
5. Return ONLY valid JSON with the exact structure specified

ANALYSIS METHODOLOGY:

INDUSTRY DETECTION:
- Analyze both resume and JD to identify primary industry and role type
- Adapt analysis criteria to industry standards and expectations
- Consider role seniority level (entry, mid, senior, executive)

GAP ANALYSIS DIMENSIONS:
1. KEYWORD ALIGNMENT: Missing critical skills, technologies, tools mentioned in JD
2. EXPERIENCE RELEVANCE: How well experience matches role requirements
3. SKILL DEPTH: Whether skills are mentioned with appropriate depth/context
4. INDUSTRY FIT: Alignment with industry standards and expectations
5. ROLE LEVEL: Match between experience level and job requirements
6. CULTURAL FIT: Soft skills and values alignment

OPTIMIZATION STRATEGY:
1. PRESERVE AUTHENTICITY: Never add false information or exaggerate
2. ENHANCE EXISTING: Strengthen and better articulate existing experience
3. STRATEGIC POSITIONING: Reorder and emphasize most relevant information
4. KEYWORD INTEGRATION: Naturally incorporate missing keywords where appropriate
5. QUANTIFY IMPACT: Add or enhance metrics and achievements
6. INDUSTRY ALIGNMENT: Use industry-appropriate terminology and formats

INDUSTRY-SPECIFIC CONSIDERATIONS:

TECHNOLOGY:
- Focus on technical skills, frameworks, methodologies
- Emphasize scale, performance, and measurable improvements
- Include relevant certifications and continuous learning

SALES/BUSINESS:
- Highlight quota achievement, revenue impact, territory management
- Emphasize relationship building and business development
- Include CRM experience and sales methodologies

HEALTHCARE:
- Prioritize patient care, safety, and clinical outcomes
- Highlight certifications, licenses, and continuing education
- Emphasize compliance and quality metrics

FINANCE:
- Focus on risk management, regulatory knowledge, analytical skills
- Highlight AUM, portfolio performance, compliance record
- Include relevant licenses and certifications

MARKETING/CREATIVE:
- Emphasize campaign results, brand impact, creative achievements
- Include portfolio work and recognition
- Show understanding of digital marketing trends

EDUCATION:
- Focus on student outcomes, curriculum development, assessment
- Highlight teaching methodologies and classroom management
- Include professional development and certifications

OUTPUT REQUIREMENTS:
Return a JSON object with this exact structure:

{
  "gap_analysis": {
    "overall_match_score": 0.85,
    "industry_detected": "Technology",
    "role_level_detected": "Senior",
    "keyword_analysis": {
      "missing_critical": ["Docker", "Kubernetes"],
      "missing_preferred": ["GraphQL", "Microservices"],
      "weak_mentions": ["Python", "AWS"],
      "well_covered": ["React", "Node.js"]
    },
    "experience_analysis": {
      "relevance_score": 0.8,
      "experience_gaps": ["No leadership experience mentioned", "Limited enterprise-scale projects"],
      "experience_strengths": ["Strong full-stack background", "Proven problem-solving skills"]
    },
    "skill_depth_analysis": {
      "under_emphasized": ["Team collaboration", "System architecture"],
      "appropriately_emphasized": ["Frontend development", "API development"],
      "over_emphasized": []
    },
    "recommendations": [
      {
        "priority": "high",
        "category": "technical_skills",
        "action": "Add container orchestration experience",
        "rationale": "JD requires Docker/Kubernetes for microservices architecture"
      }
    ]
  },
  "optimized_resume": {
    // RETURN THE COMPLETE MultiNicheResume STRUCTURE WITH ALL FIELDS
    // Use the exact same JSON schema as the input resume but with enhanced content
    // Every field from the input should be present in the output
    "contact_information": {
      "name": "enhanced if needed",
      "email": "keep original",
      "phone": "keep original", 
      "location": "keep original",
      "professional_profiles": "enhance with missing relevant profiles"
    },
    "professional_summary": "Rewrite to better align with JD while staying authentic",
    "work_experience": [
      {
        "job_title": "keep original",
        "company": "keep original",
        "start_date": "keep original",
        "end_date": "keep original",
        "location": "keep original",
        "responsibilities": ["enhance with keywords and better articulation"],
        "tools_used": ["add JD-relevant tools if authentic"],
        "metrics_achieved": ["enhance and add quantifiable achievements"],
        "industry_context": "enhance with role-specific details"
      }
    ],
    "education": "keep structure, enhance if relevant",
    "skills": {
      "core_competencies": "reorder by JD priority, add missing if authentic",
      "tools_and_software": "add JD-relevant tools",
      "methodologies": "enhance with JD-mentioned approaches",
      "soft_skills": "keep and enhance",
      "languages": "keep original",
      "specialized_skills": [
        {
          "category_name": "prioritize categories mentioned in JD",
          "skills": "add missing skills if authentic, reorder by importance"
        }
      ]
    },
    "certifications_and_licenses": "keep structure, add if mentioned in JD and authentic",
    "projects_and_portfolio": "enhance descriptions, add JD-relevant projects if authentic",
    "additional_sections": "keep and enhance existing sections",
    "industry_context": "update based on JD analysis",
    "parsed_date": "keep original",
    "source_format": "keep original"
  },
  "optimization_changes": {
    "summary_changes": [
      {
        "change_type": "enhancement",
        "original": "exact original text",
        "optimized": "exact optimized text",
        "rationale": "specific reason for change"
      }
    ],
    "experience_changes": [
      {
        "company": "company name",
        "changes": [
          {
            "change_type": "keyword_integration",
            "section": "responsibilities",
            "original": "original bullet point",
            "optimized": "enhanced bullet point",
            "rationale": "specific reason"
          }
        ]
      }
    ],
    "skills_changes": {
      "additions": ["list of added skills"],
      "reorganizations": ["description of reordering"],
      "enhancements": ["description of improvements"],
      "rationale": "overall skills optimization strategy"
    },
    "new_sections_added": [],
    "structural_improvements": [
      {
        "change": "description of structural change",
        "rationale": "reason for change"
      }
    ]
  },
  "optimization_metadata": {
    "total_changes": 12,
    "authenticity_score": 0.95,
    "improvement_areas": ["areas where resume was strengthened"],
    "industry_alignment_score": 0.9,
    "ats_optimization_score": 0.88
  }
}

QUALITY GUIDELINES:
- Maintain complete authenticity - never fabricate experience
- Enhance rather than invent - strengthen existing content
- Preserve the candidate's voice and professional identity
- Ensure all changes are defensible in an interview
- Balance keyword optimization with natural language
- Maintain industry-appropriate professional tone
- Ensure optimized resume tells a coherent career story"""

    user_message = f"""Analyze this resume against the job description and provide comprehensive gap analysis with optimized resume.

JOB DESCRIPTION:
{jd_text}

JOB TITLE: {jd_title or "Not specified"}

CURRENT RESUME DATA:
{json.dumps(normalized_resume, indent=2)}

OPTIMIZATION REQUIREMENTS:
1. Perform thorough gap analysis considering industry standards and role requirements
2. Optimize the resume to better match the job description while maintaining authenticity
3. Enhance existing experience and skills without fabricating information
4. Improve ATS compatibility through strategic keyword integration
5. Strengthen quantifiable achievements and impact statements
6. Ensure industry-appropriate terminology and formatting
7. Maintain professional tone: {optimization_focus}

ANALYSIS FOCUS AREAS:
- Critical skill gaps that could eliminate candidacy
- Experience positioning and relevance emphasis
- Industry-specific terminology and standards alignment
- Role level appropriateness and leadership indicators
- Quantifiable achievement enhancement opportunities
- Strategic content reorganization for maximum impact

Return the complete analysis and optimized resume following the exact JSON structure specified."""

    return system_message, user_message