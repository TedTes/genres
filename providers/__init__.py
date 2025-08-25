"""
LLM Provider abstraction layer.
Supports multiple AI providers (OpenAI, HuggingFace) with unified interface.
"""

from flask import current_app
from .base import Embedder, ChatModel
from .openai_provider import OpenAIProvider
from .hf_provider import HuggingFaceProvider

def get_models():
    """
    Factory function to get Embedder and ChatModel based on configuration.
    
    Returns:
        tuple: (Embedder, ChatModel) instances
    """
    provider = current_app.config.get('MODEL_PROVIDER', 'hf')
    
    if provider == 'openai':
        provider_instance = OpenAIProvider()
    elif provider == 'hf':
        provider_instance = HuggingFaceProvider()
    else:
        raise ValueError(f"Unsupported MODEL_PROVIDER: {provider}")
    
    return provider_instance.get_embedder(), provider_instance.get_chat_model()

__all__ = ['Embedder', 'ChatModel', 'get_models']