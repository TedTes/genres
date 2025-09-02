"""
HuggingFace provider implementation using InferenceClient.
Supports both embeddings and chat completions via the new API.
"""

import asyncio
from typing import List, Dict, Any
from flask import current_app
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from huggingface_hub import InferenceClient
from huggingface_hub.errors import InferenceTimeoutError, HfHubHTTPError
from .logger import track_llm_request
from .base import Embedder, ChatModel, LLMProvider


class HuggingFaceEmbedder(Embedder):
    """HuggingFace embeddings implementation using InferenceClient."""
    
    def __init__(self, model_name: str, api_token: str):
        self.model_name = model_name
        self.api_token = api_token
        self.client = InferenceClient(token=api_token)

    @track_llm_request("embedding")   
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((InferenceTimeoutError, HfHubHTTPError))
    )
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using HuggingFace InferenceClient."""
        
        try:
            # Run the synchronous InferenceClient in a thread pool
            embeddings = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.client.feature_extraction(
                    text=texts[0] if len(texts) == 1 else texts,
                    model=self.model_name
                )
            )
            
            # Handle different response formats (list, numpy array, etc.)
            import numpy as np
            
            # Convert numpy array to list if needed
            if isinstance(embeddings, np.ndarray):
                embeddings = embeddings.tolist()
            
            if isinstance(embeddings, list):
                # Single text input returns single embedding
                if len(texts) == 1 and isinstance(embeddings[0], (int, float)):
                    return [embeddings]
                # Multiple texts or already proper format
                elif all(isinstance(emb, list) for emb in embeddings):
                    return embeddings
                else:
                    # Single embedding for single text
                    return [embeddings]
            else:
                raise ValueError(f"Unexpected embedding response format: {type(embeddings)}")
                
        except Exception as e:
            print(f"HuggingFace embedding error: {str(e)}")
            raise


class HuggingFaceChatModel(ChatModel):
    """HuggingFace chat completion implementation using InferenceClient."""
    
    def __init__(self, model_name: str, api_token: str):
        self.model_name = model_name
        self.api_token = api_token
        # Use auto provider for best compatibility
        self.client = InferenceClient(token=api_token)

    @track_llm_request("chat")
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((InferenceTimeoutError, HfHubHTTPError))
    )
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        **generation_options
    ) -> str:
        """Generate chat completion using HuggingFace InferenceClient."""
        
        try:
            # Extract parameters with defaults
            max_tokens = generation_options.get("max_tokens", 1024)
            temperature = generation_options.get("temperature", 0.7)
            
            # Run the synchronous InferenceClient in a thread pool
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            )
            
            # Extract the response content
            if hasattr(response, 'choices') and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                raise ValueError(f"Unexpected chat response format: {type(response)}")
                
        except Exception as e:
            print(f"HuggingFace chat error: {str(e)}")
            # Fallback to text generation for non-chat models
            try:
                return await self._fallback_text_generation(messages, **generation_options)
            except Exception as fallback_error:
                print(f"Fallback text generation also failed: {str(fallback_error)}")
                raise e

    async def _fallback_text_generation(
        self, 
        messages: List[Dict[str, str]], 
        **generation_options
    ) -> str:
        """Fallback to text generation for models that don't support chat completions."""
        
        # Convert messages to prompt format
        prompt = self._messages_to_prompt(messages)
        
        # Extract parameters
        max_new_tokens = generation_options.get("max_tokens", 1024)
        temperature = generation_options.get("temperature", 0.7)
        
        # Run text generation in thread pool
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.client.text_generation(
                prompt=prompt,
                model=self.model_name,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                return_full_text=False
            )
        )
        
        return response.strip()
    
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
    """HuggingFace provider implementation using InferenceClient."""
    
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
