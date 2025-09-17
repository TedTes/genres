
from schemas import NormalizedResumeSchema
import json
from typing import List,Dict
def get_normalization_prompt(raw_text: str, file_type: str):
    import json
    # Schema extraction (v2 then v1)
    try:
        schema_obj = NormalizedResumeSchema.model_json_schema()  # Pydantic v2
    except Exception:
        schema_obj = NormalizedResumeSchema.schema()              # Pydantic v1

    schema_json = json.dumps(schema_obj, separators=(",", ":"))

    system_message = (
        "You are an expert resume parser. Output MUST be a single valid JSON object that "
        "conforms to the provided JSON Schema. No prose/markdown/comments.\n\n"
        "Rules:\n"
        "- Extract all available info.\n"
        "- Dates: use 'YYYY', 'YYYY-MM', or 'MM/YYYY'; use 'Present' for ongoing roles; if unclear, use null.\n"
        "- Reverse-chronological work_experience.\n"
        "- Deduplicate skills; keep canonical casing (Node.js, AWS).\n"
        "- If data is missing, emit null or [] per schema; never invent.\n"
        "- One JSON object only."
    )

    user_message = (
        "JSON_SCHEMA:\n<<<SCHEMA_START>>>\n"
        f"{schema_json}\n"
        "<<<SCHEMA_END>>>\n\n"
        f"SOURCE_FILE_TYPE:\n{file_type}\n\n"
        "RAW_RESUME_TEXT (verbatim):\n<<<RESUME_START>>>\n"
        f"{raw_text}\n"
        "<<<RESUME_END>>>\n\n"
        "Task: Parse and normalize into a JSON object that VALIDATES against JSON_SCHEMA.\n"
        "Strict output: JSON object only; no markdown; use null/[] for missing fields; "
        "apply the date rules and ordering."
    )
    return system_message, user_message



def get_json_prompt(system_message: str, user_content: str) -> List[Dict[str, str]]:
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
