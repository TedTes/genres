import json
from typing import Dict, Any, Tuple
from schemas import NormalizedResumeSchema
def get_optimization_prompt(
    normalized_resume: Dict[str, Any],
    jd_text: str,
    jd_title: str | None = None,
    optimization_focus: str = "professional-concise"
) -> Tuple[str, str]:
    """
    Create a strict, schema-aware prompt for gap analysis + resume optimization
    that outputs JSON only, with `optimized_resume` conforming to NormalizedResumeSchema.
    """

    # 1) Embed the ACTUAL JSON schema for your normalized resume
    try:
        # Pydantic v2
          # adjust import if needed
        schema_obj = NormalizedResumeSchema.model_json_schema()  # type: ignore[attr-defined]
    except Exception:
        # Pydantic v1 fallback
        schema_obj = NormalizedResumeSchema.schema()

    schema_json = json.dumps(schema_obj, separators=(",", ":"))  # compact to save tokens
    normalized_resume_compact = json.dumps(normalized_resume, separators=(",", ":"))

    # 2) System message: strict rules + inclusivity
    system_message = (
        "You are an expert resume optimization specialist. Output MUST be a single valid JSON object "
        "with keys: gap_analysis, optimized_resume, optimization_changes, optimization_metadata. "
        "Do NOT include prose, markdown, code fences, or comments.\n\n"
        "Universal Rules:\n"
        "- Preserve authenticity. NEVER invent roles, employers, dates, or credentials.\n"
        "- Enhance clarity, ordering, quantification, and terminology; do not fabricate metrics.\n"
        "- Use inclusive, bias-aware language; avoid age, gender, ethnicity, or protected traits.\n"
        "- Dates: use one of 'YYYY', 'YYYY-MM', or 'MM/YYYY'. 'Present' allowed for ongoing roles.\n"
        "- Prefer {} for empty objects and [] for empty arrays (do not use null for object/array types).\n"
        "- Keep the candidate’s voice/tone; ensure the optimized resume remains defensible in interviews.\n"
        "- Keep content concise and high-signal; avoid redundancy.\n"
    )

    # 3) User message: contract with schema + delimited inputs
    user_message = (
        "TASK: Analyze the resume against the job description, produce (1) gap_analysis, (2) optimized_resume, "
        "and (3) optimization_changes with (4) optimization_metadata. Respond with ONE JSON object only.\n\n"
        "SCHEMA FOR optimized_resume (must validate):\n"
        "<<<RESUME_SCHEMA_START>>>\n"
        f"{schema_json}\n"
        "<<<RESUME_SCHEMA_END>>>\n\n"
        "JOB TITLE:\n"
        f"{(jd_title or 'Not specified')}\n\n"
        "JOB DESCRIPTION (verbatim):\n"
        "<<<JD_START>>>\n"
        f"{jd_text}\n"
        "<<<JD_END>>>\n\n"
        "CURRENT NORMALIZED RESUME (verbatim JSON):\n"
        "<<<RESUME_JSON_START>>>\n"
        f"{normalized_resume_compact}\n"
        "<<<RESUME_JSON_END>>>\n\n"
        "OUTPUT REQUIREMENTS:\n"
        "- Return a single JSON object with exactly these top-level keys:\n"
        "  gap_analysis: {\n"
        "    overall_match_score (0..1), industry_detected, role_level_detected,\n"
        "    keyword_analysis { missing_critical[], missing_preferred[], weak_mentions[], well_covered[] },\n"
        "    experience_analysis { relevance_score (0..1), experience_gaps[], experience_strengths[] },\n"
        "    skill_depth_analysis { under_emphasized[], appropriately_emphasized[], over_emphasized[] },\n"
        "    recommendations[] of { priority: high|medium|low, category, action, rationale }\n"
        "  },\n"
        "  optimized_resume:  // MUST VALIDATE against SCHEMA above (NormalizedResumeSchema)\n"
        "  optimization_changes: {\n"
        "    summary_changes[], experience_changes[], skills_changes { additions[], reorganizations[], enhancements[], rationale },\n"
        "    new_sections_added[], structural_improvements[]\n"
        "  },\n"
        "  optimization_metadata: { total_changes, authenticity_score (0..1), improvement_areas[], industry_alignment_score (0..1), ats_optimization_score (0..1) }\n\n"
        "OPTIMIZATION STRATEGY (apply generically to any field/industry):\n"
        "- Strategic positioning: reorder items to foreground JD-relevant content.\n"
        "- Keyword integration: integrate JD terms naturally where supported by resume evidence.\n"
        "- Quantification: strengthen with existing metrics; do not invent numbers.\n"
        "- Terminology: align to industry conventions without changing facts.\n"
        "- Structure: keep the normalized schema; enrich, don’t mutate keys.\n"
        "- Tone/style: "
        f"{optimization_focus}.\n\n"
        "STRICT OUTPUT CONSTRAINTS:\n"
        "- JSON only. No markdown, no fences, no comments, no extra text.\n"
        "- For object/array fields, emit {} or [] instead of null (unless the schema explicitly allows null).\n"
        "- Keep dates within the specified formats; use 'Present' where applicable.\n"
        "- If information is missing, include the field with an empty value per schema ({} or [] or null) rather than inventing content.\n"
    )

    return system_message, user_message
