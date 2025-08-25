"""
LLM Provider abstraction layer.
Supports multiple AI providers (OpenAI, HuggingFace) with unified interface.
"""

from flask import current_app
from .base import Embedder, ChatModel, LLMProvider
from .openai_provider import OpenAIProvider
from .hf_provider import HuggingFaceProvider


def get_models():
    """
    Factory function to get Embedder and ChatModel based on configuration.
    
    Returns:
        tuple: (Embedder, ChatModel) instances
        
    Raises:
        ValueError: If MODEL_PROVIDER is not supported or required config is missing
    """
    provider = current_app.config.get('MODEL_PROVIDER', 'hf').lower()
    
    try:
        if provider == 'openai':
            provider_instance = OpenAIProvider()
        elif provider == 'hf':
            provider_instance = HuggingFaceProvider()
        else:
            raise ValueError(f"Unsupported MODEL_PROVIDER: {provider}. Supported: 'openai', 'hf'")
        
        # Get embedder and chat model instances
        embedder = provider_instance.get_embedder()
        chat_model = provider_instance.get_chat_model()
        
        # Log successful initialization
        print(f"✓ Initialized {provider_instance.provider_name} provider")
        print(f"  - LLM Model: {current_app.config.get('LLM_MODEL')}")
        print(f"  - Embed Model: {current_app.config.get('EMBED_MODEL')}")
        
        return embedder, chat_model
        
    except Exception as e:
        print(f"❌ Failed to initialize {provider} provider: {str(e)}")
        raise


def get_provider() -> LLMProvider:
    """
    Get the configured LLM provider instance.
    
    Returns:
        LLMProvider: Configured provider instance
    """
    provider = current_app.config.get('MODEL_PROVIDER', 'hf').lower()
    
    if provider == 'openai':
        return OpenAIProvider()
    elif provider == 'hf':
        return HuggingFaceProvider()
    else:
        raise ValueError(f"Unsupported MODEL_PROVIDER: {provider}")


def test_provider_connection():
    """
    Test if the configured provider is working correctly.
    
    Returns:
        dict: Test results with status and details
    """
    try:
        embedder, chat_model = get_models()
        
        # Test embedding with a simple text
        test_embeddings = embedder.embed_sync(["test text"])
        
        # Test chat with a simple message
        test_messages = [{"role": "user", "content": "Say 'Hello World'"}]
        test_response = chat_model.chat_sync(test_messages, max_tokens=10)
        
        return {
            "status": "success",
            "provider": current_app.config.get('MODEL_PROVIDER'),
            "embedding_dimensions": len(test_embeddings[0]) if test_embeddings else 0,
            "chat_response_length": len(test_response),
            "details": "Provider connection successful"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "provider": current_app.config.get('MODEL_PROVIDER'),
            "error": str(e),
            "details": "Provider connection failed"
        }


__all__ = [
    'Embedder', 
    'ChatModel', 
    'LLMProvider',
    'get_models', 
    'get_provider',
    'test_provider_connection'
]