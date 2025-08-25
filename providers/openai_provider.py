"""
OpenAI provider implementation using official OpenAI SDK.
Supports both embeddings and chat completions.
"""

import openai
from typing import List, Dict, Any
from flask import current_app
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base import Embedder, ChatModel, LLMProvider


class OpenAIEmbedder(Embedder):
    """OpenAI embeddings implementation."""
    
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.client = openai.AsyncOpenAI(api_key=api_key)
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError))
    )
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI Embeddings API."""
        
        try:
            response = await self.client.embeddings.create(
                model=self.model_name,
                input=texts,
                encoding_format="float"
            )
            
            # Extract embeddings in order
            embeddings = []
            for data_point in response.data:
                embeddings.append(data_point.embedding)
            
            return embeddings
            
        except openai.APIError as e:
            print(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            print(f"OpenAI embedding error: {str(e)}")
            raise


class OpenAIChatModel(ChatModel):
    """OpenAI chat completion implementation."""
    
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.client = openai.AsyncOpenAI(api_key=api_key)
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError))
    )
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        **generation_options
    ) -> str:
        """Generate chat completion using OpenAI Chat API."""
        
        # Default parameters
        params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024,
        }
        
        # Override with user-provided options
        params.update(generation_options)
        
        try:
            response = await self.client.chat.completions.create(**params)
            
            # Extract the generated text
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                raise ValueError("No response generated from OpenAI")
                
        except openai.APIError as e:
            print(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            print(f"OpenAI chat error: {str(e)}")
            raise


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation."""
    
    def __init__(self):
        self.api_key = current_app.config.get('OPENAI_API_KEY')
        self.llm_model = current_app.config.get('LLM_MODEL', 'gpt-4o-mini')
        self.embed_model = current_app.config.get('EMBED_MODEL', 'text-embedding-3-small')
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
    
    def get_embedder(self) -> Embedder:
        """Get OpenAI embedder instance."""
        return OpenAIEmbedder(self.embed_model, self.api_key)
    
    def get_chat_model(self) -> ChatModel:
        """Get OpenAI chat model instance."""
        return OpenAIChatModel(self.llm_model, self.api_key)
    
    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "openai"