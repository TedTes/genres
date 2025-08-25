"""
HuggingFace provider implementation using Inference API.
Supports both embeddings and chat completions via HTTP client.
"""

import httpx
import json
from typing import List, Dict, Any
from flask import current_app
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .logger import track_llm_request
from .base import Embedder, ChatModel, LLMProvider


class HuggingFaceEmbedder(Embedder):
    """HuggingFace embeddings implementation."""
    
    def __init__(self, model_name: str, api_token: str):
        self.model_name = model_name
        self.api_token = api_token
        self.base_url = "https://api-inference.huggingface.co"
        self.provider_name = "huggingface"
    @track_llm_request("embedding")   
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException))
    )
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using HuggingFace Inference API."""
        
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # HuggingFace expects different payload formats depending on model
        payload = {
            "inputs": texts,
            "options": {
                "wait_for_model": True,
                "use_cache": True
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/pipeline/feature-extraction/{self.model_name}",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                embeddings = response.json()
                
                # Handle different response formats
                if isinstance(embeddings, list) and len(embeddings) > 0:
                    # If it's already a list of embeddings
                    if isinstance(embeddings[0], list):
                        return embeddings
                    # If it's a single embedding, wrap in list
                    else:
                        return [embeddings]
                else:
                    raise ValueError(f"Unexpected embedding response format: {type(embeddings)}")
                    
            except httpx.HTTPStatusError as e:
                print(f"HuggingFace API error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                print(f"HuggingFace embedding error: {str(e)}")
                raise


class HuggingFaceChatModel(ChatModel):
    """HuggingFace chat completion implementation."""
    
    def __init__(self, model_name: str, api_token: str):
        self.model_name = model_name
        self.api_token = api_token
        self.base_url = "https://api-inference.huggingface.co"
        self.provider_name = "huggingface"

    @track_llm_request("chat")
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException))
    )
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        **generation_options
    ) -> str:
        """Generate chat completion using HuggingFace Inference API."""
        
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # Convert messages to prompt format (most HF models expect single prompt)
        prompt = self._messages_to_prompt(messages)
        
        # Default generation parameters
        params = {
            "max_new_tokens": generation_options.get("max_tokens", 1024),
            "temperature": generation_options.get("temperature", 0.7),
            "do_sample": True,
            "return_full_text": False
        }
        params.update(generation_options)
        
        payload = {
            "inputs": prompt,
            "parameters": params,
            "options": {
                "wait_for_model": True,
                "use_cache": False  # Don't cache for generation
            }
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/models/{self.model_name}",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                elif isinstance(result, dict):
                    generated_text = result.get("generated_text", "")
                else:
                    raise ValueError(f"Unexpected chat response format: {type(result)}")
                
                return generated_text.strip()
                
            except httpx.HTTPStatusError as e:
                print(f"HuggingFace API error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                print(f"HuggingFace chat error: {str(e)}")
                raise
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI-style messages to a single prompt string."""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        # Add final "Assistant:" to prompt for completion
        prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)


class HuggingFaceProvider(LLMProvider):
    """HuggingFace provider implementation."""
    
    def __init__(self):
        self.api_token = current_app.config.get('HF_TOKEN')
        self.llm_model = current_app.config.get('LLM_MODEL')
        self.embed_model = current_app.config.get('EMBED_MODEL')
        
        if not self.api_token:
            print("Warning: HF_TOKEN not set. Some models may not work.")
    
    def get_embedder(self) -> Embedder:
        """Get HuggingFace embedder instance."""
        return HuggingFaceEmbedder(self.embed_model, self.api_token)
    
    def get_chat_model(self) -> ChatModel:
        """Get HuggingFace chat model instance."""
        return HuggingFaceChatModel(self.llm_model, self.api_token)
    
    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "huggingface"