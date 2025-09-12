

def extract_json_from_response(response: str) -> str:
    """
    Extract JSON from LLM response that might contain extra text.
    
    Args:
        response: Raw LLM response
        
    Returns:
        Cleaned JSON string
    """
    import re
    
    # Remove common prefixes/suffixes
    response = response.strip()
    
    # Look for JSON block markers
    json_patterns = [
        r'```json\s*(\{.*?\})\s*```',  # ```json { ... } ```
        r'```\s*(\{.*?\})\s*```',      # ``` { ... } ```
        r'(\{.*\})',                   # Just find { ... }
    ]
    
    for pattern in json_patterns:
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
    
    # If no pattern matches, return original
    return response