from pydantic import BaseModel
from typing import Dict, Optional,  Any
class DocumentChunk(BaseModel):
    """Represents a chunk of resume text with metadata."""
    
    text: str
    section: str  # 'summary', 'experience', 'education', 'skills'
    chunk_index: int
    token_count: Optional[int] = None
    metadata: Dict[str, Any] = {}