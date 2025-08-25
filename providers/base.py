"""
Abstract base classes for LLM providers.
Defines the interface that all providers must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union, AsyncGenerator, Optional

class Embedder(ABC):
    """Abstract base class for text embedding providers."""
    
    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (one per input text)
        """
        pass
    
    def embed_sync(self, texts: List[str]) -> List[List[float]]:
        """Synchronous wrapper for embed method."""
        import asyncio
        return asyncio.run(self.embed(texts))


class ChatModel(ABC):
    """Abstract base class for chat/completion model providers."""
    
    @abstractmethod
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        **generation_options
    ) -> str:
        """
        Generate chat completion from messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            **generation_options: Provider-specific options (temperature, max_tokens, etc.)
            
        Returns:
            Generated text response
        """
        pass
    
    def chat_sync(
        self, 
        messages: List[Dict[str, str]], 
        **generation_options
    ) -> str:
        """Synchronous wrapper for chat method."""
        import asyncio
        return asyncio.run(self.chat(messages, **generation_options))


class LLMProvider(ABC):
    """Abstract base class for LLM providers that provide both embedding and chat capabilities."""
    
    @abstractmethod
    def get_embedder(self) -> Embedder:
        """Get an embedder instance."""
        pass
    
    @abstractmethod
    def get_chat_model(self) -> ChatModel:
        """Get a chat model instance."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the provider name (e.g., 'openai', 'hf')."""
        pass