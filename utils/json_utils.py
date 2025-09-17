import json
import re
from datetime import datetime
from typing import Tuple, Any, Dict
from schemas import NormalizedResumeSchema
# ---  balanced extractor as a fallback ---
def _balanced_json_slice(s: str) -> str | None:
    opens = {'{': '}', '[': ']'}
    start = None
    stack = []
    in_str = False
    esc = False
    quote = '"'
    # find first { or [
    for i, ch in enumerate(s):
        if ch in opens:
            start = i
            stack.append(opens[ch])
            break
    if start is None:
        return None
    for i in range(start + 1, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == quote:
                in_str = False
        else:
            if ch == '"' or ch == "'":
                in_str = True
                quote = ch
            elif ch in opens:
                stack.append(opens[ch])
            elif stack and ch == stack[-1]:
                stack.pop()
                if not stack:
                    return s[start:i+1]
    return None

def extract_json_from_response(response: str) -> Any:
    # Try fenced blocks
    patterns = [
        r'```json\s*(\{.*?\}|\[.*?\])\s*```',
        r'```\s*(\{.*?\}|\[.*?\])\s*```',
    ]
    for p in patterns:
        m = re.search(p, response, re.DOTALL)
        if m:
            return json.loads(m.group(1).strip())
    # Try balanced slice
    payload = _balanced_json_slice(response)
    if payload is not None:
        return json.loads(payload)
    # Last resort: treat whole thing as JSON
    return json.loads(response.strip())

# --- strict parse → validate → coerce helper ---
def parse_and_validate_normalized_resume(
    response_text: str, file_type: str
) -> "NormalizedResumeSchema":
    # 1) strict first
    try:
        obj = json.loads(response_text)
    except Exception:
        obj = extract_json_from_response(response_text)

    # 3) pydantic validation/coercion
    if hasattr(NormalizedResumeSchema, "model_validate"):         # v2
        model = NormalizedResumeSchema.model_validate(obj)
    else:                                                         # v1
        model = NormalizedResumeSchema.parse_obj(obj)

    # 4) enrich metadata (without breaking immutability)
    d = model.model_dump() if hasattr(model, "model_dump") else model.dict()
    d.setdefault("parsed_date", datetime.now().isoformat())
    d.setdefault("source_format", file_type)

    # Return dict:
    if hasattr(NormalizedResumeSchema, "model_validate"):
        return NormalizedResumeSchema.model_validate(d)
    return NormalizedResumeSchema.parse_obj(d)
