from pydantic import BaseModel
from utils import extract_json_from_response
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


async def validate_json_with_retry(
    json_str: str, 
    schema_class: BaseModel, 
    chat_model=None,
    max_retries: int = 1
) -> BaseModel:
    """
    Validate JSON response from LLM with automatic retry and repair.
    
    Args:
        json_str: JSON string from LLM
        schema_class: Pydantic model class to validate against
        chat_model: ChatModel instance for JSON repair (optional)
        max_retries: Number of repair attempts
        
    Returns:
        Validated Pydantic model instance
        
    Raises:
        ValueError: If JSON is invalid after all retries
    """
    import json
    from pydantic import ValidationError
    
    # Attempt 1: Try original response
    try:
        json_data = json.loads(json_str)
        return schema_class(**json_data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"⚠️  JSON validation failed: {str(e)}")
        original_error = str(e)
    
    # If no chat model provided, can't retry
    if not chat_model or max_retries <= 0:
        raise ValueError(f"Invalid JSON response: {original_error}\nResponse: {json_str[:200]}...")
    
    # Attempt 2: Ask LLM to fix the JSON
    for attempt in range(max_retries):
        try:
            print(f"🔄 Attempting JSON repair (attempt {attempt + 1}/{max_retries})")
            
            repair_messages = [
                {
                    "role": "system",
                    "content": "You are a JSON repair assistant. Fix malformed JSON to match the required schema. Return ONLY valid JSON, no explanations."
                },
                {
                    "role": "user", 
                    "content": f"""Fix this malformed JSON to match the schema:

                    MALFORMED JSON:
                    {json_str}

                    ERROR:
                    {original_error}

                    REQUIRED SCHEMA EXAMPLE:
                    {json.dumps(schema_class.Config.schema_extra.get('example', {}), indent=2)}

                    Return ONLY the corrected JSON:"""
                }
            ]
            
            repaired_json = await chat_model.chat(
                repair_messages, 
                temperature=0.1,  # Low temperature for precise JSON
                max_tokens=2048
            )
            
            # Clean the response (remove any non-JSON text)
            repaired_json = extract_json_from_response(repaired_json)
            
            # Try to validate the repaired JSON
            json_data = json.loads(repaired_json)
            validated = schema_class(**json_data)
            
            print("✅ JSON repair successful")
            return validated
            
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"❌ JSON repair attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                # Final attempt failed
                raise ValueError(
                    f"JSON validation failed after {max_retries + 1} attempts.\n"
                    f"Original error: {original_error}\n"
                    f"Final response: {repaired_json[:200] if 'repaired_json' in locals() else json_str[:200]}..."
                )
        except Exception as e:
            print(f"❌ Unexpected error during JSON repair: {str(e)}")
            raise ValueError(f"JSON repair failed: {str(e)}")



# Sync wrapper for non-async code
def validate_json_with_retry_sync(
    json_str: str, 
    schema_class: BaseModel, 
    chat_model=None,
    max_retries: int = 1
) -> BaseModel:
    """Synchronous wrapper for validate_json_with_retry."""
    import asyncio
    return asyncio.run(validate_json_with_retry(json_str, schema_class, chat_model, max_retries))