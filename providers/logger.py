"""
Observability utilities for LLM provider requests.
Handles logging, metrics, and request tracking.
"""

import time
import json
from typing import Dict, Any, Optional
from functools import wraps
from flask import current_app


class RequestLogger:
    """Logs LLM requests for monitoring and debugging."""
    
    @staticmethod
    def log_request(
        provider: str,
        model: str,
        request_type: str,  # 'embedding' or 'chat'
        tokens_in: Optional[int] = None,
        tokens_out: Optional[int] = None,
        latency_ms: Optional[float] = None,
        cache_hit: bool = False,
        error: Optional[str] = None,
        cost_estimate: Optional[float] = None
    ):
        """Log a complete LLM request with metrics."""
        
        log_data = {
            "timestamp": time.time(),
            "provider": provider,
            "model": model,
            "request_type": request_type,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "latency_ms": latency_ms,
            "cache_hit": cache_hit,
            "error": error,
            "cost_estimate": cost_estimate,
            "success": error is None
        }
        
        # Log to console (you can extend this to send to external logging service)
        if error:
            print(f"🔴 LLM Request Failed: {json.dumps(log_data, indent=2)}")
        else:
            print(f"🟢 LLM Request: {model} | {latency_ms:.0f}ms | {tokens_in}→{tokens_out} tokens")


def track_llm_request(request_type: str):
    """
    Decorator to track LLM requests with automatic timing and logging.
    
    Args:
        request_type: 'embedding' or 'chat'
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            start_time = time.time()
            provider_name = getattr(self, 'provider_name', 'unknown')
            model_name = getattr(self, 'model_name', 'unknown')
            
            try:
                # Execute the actual function
                result = await func(self, *args, **kwargs)
                
                # Calculate metrics
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000
                
                # Estimate token counts
                if request_type == 'embedding':
                    tokens_in = sum(len(text.split()) for text in args[0]) if args else 0
                    tokens_out = len(result) if result else 0
                elif request_type == 'chat':
                    tokens_in = sum(len(msg.get('content', '').split()) for msg in args[0]) if args else 0
                    tokens_out = len(result.split()) if result else 0
                else:
                    tokens_in = tokens_out = 0
                
                # Estimate cost (rough approximation)
                cost_estimate = estimate_cost(provider_name, model_name, tokens_in, tokens_out)
                
                # Log successful request
                RequestLogger.log_request(
                    provider=provider_name,
                    model=model_name,
                    request_type=request_type,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    latency_ms=latency_ms,
                    cost_estimate=cost_estimate
                )
                
                return result
                
            except Exception as e:
                # Log failed request
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000
                
                RequestLogger.log_request(
                    provider=provider_name,
                    model=model_name,
                    request_type=request_type,
                    latency_ms=latency_ms,
                    error=str(e)
                )
                
                raise
        
        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            """Sync version of the wrapper for sync methods."""
            import asyncio
            return asyncio.run(async_wrapper(self, *args, **kwargs))
        
        # Return async wrapper if original function is async, sync otherwise
        import inspect

        if inspect.iscoroutinefunction(func):
           return async_wrapper
        else:
           return sync_wrapper
    
    return decorator


def estimate_cost(provider: str, model: str, tokens_in: int, tokens_out: int) -> float:
    """
    Rough cost estimation for LLM requests.
    
    Args:
        provider: 'openai' or 'hf'
        model: Model name
        tokens_in: Input tokens
        tokens_out: Output tokens
        
    Returns:
        Estimated cost in USD
    """
    
    # OpenAI pricing (approximate, per 1K tokens)
    openai_prices = {
        'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
        'gpt-4o': {'input': 0.0025, 'output': 0.01},
        'text-embedding-3-small': {'input': 0.00002, 'output': 0},
        'text-embedding-3-large': {'input': 0.00013, 'output': 0}
    }
    
    if provider == 'openai' and model in openai_prices:
        prices = openai_prices[model]
        cost = (tokens_in / 1000 * prices['input']) + (tokens_out / 1000 * prices['output'])
        return round(cost, 6)
    
    # HuggingFace is often free or very cheap
    elif provider == 'hf':
        return 0.0  # Most inference API usage is free
    
    return 0.0  # Unknown cost


class ProviderHealthCheck:
    """Health check utilities for LLM providers."""
    
    @staticmethod
    async def check_provider_status(provider_instance: Any) -> Dict[str, Any]:
        """
        Check if a provider is healthy and responsive.
        
        Args:
            provider_instance: Instance of LLMProvider
            
        Returns:
            Health status dictionary
        """
        try:
            start_time = time.time()
            
            # Test embedding
            embedder = provider_instance.get_embedder()
            test_embedding = await embedder.embed(["health check"])
            
            # Test chat
            chat_model = provider_instance.get_chat_model()
            test_response = await chat_model.chat(
                [{"role": "user", "content": "Reply with just 'OK'"}],
                max_tokens=5
            )
            
            end_time = time.time()
            
            return {
                "status": "healthy",
                "provider": provider_instance.provider_name,
                "response_time_ms": round((end_time - start_time) * 1000, 2),
                "embedding_dimensions": len(test_embedding[0]) if test_embedding else 0,
                "chat_response": test_response[:50],  # First 50 chars
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": getattr(provider_instance, 'provider_name', 'unknown'),
                "error": str(e),
                "timestamp": time.time()
            }