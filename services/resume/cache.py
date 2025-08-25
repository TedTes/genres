"""
Caching and idempotency for resume optimization.
Implements Redis-based caching with fallback to in-memory storage.
"""

import json
import hashlib
import time
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from flask import current_app

# Redis imports with fallback
try:
    import redis
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Warning: redis not installed. Using in-memory cache fallback.")

from .schemas import OptimizedResume, GapReport, OptimizationResult
from .storage import generate_resume_hash_sync


class CacheKeyGenerator:
    """Generates consistent cache keys for different data types."""
    
    @staticmethod
    def request_key(
        resume_text: str,
        jd_text: str,
        options: Dict[str, Any] = None,
        model_info: Dict[str, str] = None
    ) -> str:
        """
        Generate cache key for complete optimization request.
        
        Args:
            resume_text: Resume content
            jd_text: Job description  
            options: Optimization options
            model_info: Model and provider info
            
        Returns:
            Cache key string
        """
        
        # Create comprehensive hash input
        hash_components = [
            resume_text.strip(),
            jd_text.strip(),
            json.dumps(options or {}, sort_keys=True),
            json.dumps(model_info or {}, sort_keys=True)
        ]
        
        hash_input = "|".join(hash_components)
        hash_object = hashlib.sha256(hash_input.encode('utf-8'))
        
        return f"resume_opt:{hash_object.hexdigest()[:16]}"
    
    @staticmethod
    def embedding_key(text: str, model_name: str) -> str:
        """Generate cache key for embeddings."""
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:12]
        model_hash = hashlib.md5(model_name.encode('utf-8')).hexdigest()[:8]
        return f"embed:{model_hash}:{text_hash}"
    
    @staticmethod
    def chunk_embeddings_key(chunks: List[str], model_name: str) -> str:
        """Generate cache key for chunk embeddings."""
        chunks_text = "|".join(chunks)
        chunks_hash = hashlib.md5(chunks_text.encode('utf-8')).hexdigest()[:12]
        model_hash = hashlib.md5(model_name.encode('utf-8')).hexdigest()[:8]
        return f"chunks:{model_hash}:{chunks_hash}"
    
    @staticmethod
    def gap_analysis_key(resume_hash: str, jd_hash: str) -> str:
        """Generate cache key for gap analysis."""
        return f"gaps:{resume_hash[:8]}:{jd_hash[:8]}"


class RedisCache:
    """Redis-based caching implementation."""
    
    def __init__(self):
        self.redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        self.default_ttl = 24 * 60 * 60  # 24 hours
        self.redis_client = None
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection."""
        if not REDIS_AVAILABLE:
            return
        
        try:
            # Create async Redis client
            self.redis_client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0
            )
            
            print(f"✅ Redis cache initialized: {self.redis_url}")
            
        except Exception as e:
            print(f"❌ Redis initialization failed: {str(e)}")
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_client:
            return None
        
        try:
            cached_data = await self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            print(f"❌ Cache get failed for {key}: {str(e)}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with TTL."""
        if not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, default=str)  # Handle datetime objects
            
            await self.redis_client.setex(key, ttl, serialized)
            return True
            
        except Exception as e:
            print(f"❌ Cache set failed for {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            return result > 0
            
        except Exception as e:
            print(f"❌ Cache delete failed for {key}: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.exists(key)
            return result > 0
            
        except Exception as e:
            print(f"❌ Cache exists check failed for {key}: {str(e)}")
            return False


class InMemoryCache:
    """Fallback in-memory cache implementation."""
    
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
        self.default_ttl = 24 * 60 * 60  # 24 hours
        self.max_size = 1000  # Maximum cache entries
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        
        # Check if key exists and not expired
        if key in self.cache:
            timestamp = self.timestamps.get(key, 0)
            if time.time() - timestamp < self.default_ttl:
                return self.cache[key]
            else:
                # Expired - remove
                self.cache.pop(key, None)
                self.timestamps.pop(key, None)
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in memory cache."""
        
        # Implement simple LRU eviction if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            self.cache.pop(oldest_key, None)
            self.timestamps.pop(oldest_key, None)
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from memory cache."""
        existed = key in self.cache
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
        return existed
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in memory cache."""
        if key in self.cache:
            timestamp = self.timestamps.get(key, 0)
            return time.time() - timestamp < self.default_ttl
        return False


class ResumeCache:
    """Main caching service for resume optimization."""
    
    def __init__(self):
        if REDIS_AVAILABLE:
            self.cache = RedisCache()
            self.cache_type = "redis"
        else:
            self.cache = InMemoryCache()
            self.cache_type = "memory"
        
        print(f"🔄 Cache initialized: {self.cache_type}")
    
    async def get_cached_result(
        self,
        resume_text: str,
        jd_text: str,
        options: Dict[str, Any] = None,
        model_info: Dict[str, str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached optimization result if available.
        
        Args:
            resume_text: Resume content
            jd_text: Job description
            options: Optimization options  
            model_info: Model information
            
        Returns:
            Cached result or None
        """
        
        cache_key = CacheKeyGenerator.request_key(resume_text, jd_text, options, model_info)
        
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            print(f"🎯 Cache hit: {cache_key}")
            # Add cache metadata
            cached_result['cache_hit'] = True
            cached_result['cached_at'] = cached_result.get('cached_at', datetime.now().isoformat())
            return cached_result
        
        print(f"❌ Cache miss: {cache_key}")
        return None
    
    async def cache_result(
        self,
        resume_text: str,
        jd_text: str,
        result: Dict[str, Any],
        options: Dict[str, Any] = None,
        model_info: Dict[str, str] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache optimization result.
        
        Args:
            resume_text: Resume content
            jd_text: Job description
            result: Optimization result to cache
            options: Optimization options
            model_info: Model information
            ttl: Cache TTL in seconds
            
        Returns:
            True if cached successfully
        """
        
        cache_key = CacheKeyGenerator.request_key(resume_text, jd_text, options, model_info)
        
        # Add cache metadata
        cache_data = result.copy()
        cache_data.update({
            'cached_at': datetime.now().isoformat(),
            'cache_key': cache_key,
            'ttl': ttl or 24 * 60 * 60
        })
        
        success = await self.cache.set(cache_key, cache_data, ttl)
        
        if success:
            print(f"💾 Result cached: {cache_key}")
        else:
            print(f"❌ Cache set failed: {cache_key}")
        
        return success
    
    async def get_cached_embeddings(
        self,
        texts: List[str],
        model_name: str
    ) -> Optional[List[List[float]]]:
        """Get cached embeddings for text chunks."""
        
        cache_key = CacheKeyGenerator.chunk_embeddings_key(texts, model_name)
        
        cached_embeddings = await self.cache.get(cache_key)
        if cached_embeddings:
            print(f"🎯 Embedding cache hit: {len(texts)} chunks")
            return cached_embeddings
        
        return None
    
    async def cache_embeddings(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        model_name: str,
        ttl: int = 7 * 24 * 60 * 60  # 7 days for embeddings
    ) -> bool:
        """Cache embeddings for reuse."""
        
        cache_key = CacheKeyGenerator.chunk_embeddings_key(texts, model_name)
        
        cache_data = {
            'embeddings': embeddings,
            'model_name': model_name,
            'cached_at': datetime.now().isoformat(),
            'text_count': len(texts)
        }
        
        success = await self.cache.set(cache_key, cache_data, ttl)
        
        if success:
            print(f"💾 Embeddings cached: {len(texts)} chunks")
        
        return success
    
    async def clear_user_cache(self, user_id: str) -> int:
        """Clear all cached results for a specific user."""
        
        if not REDIS_AVAILABLE or not self.cache.redis_client:
            return 0
        
        try:
            # Find all keys containing user_id
            pattern = f"*{user_id}*"
            keys = await self.cache.redis_client.keys(pattern)
            
            if keys:
                deleted = await self.cache.redis_client.delete(*keys)
                print(f"🧹 Cleared {deleted} cache entries for user {user_id}")
                return deleted
            
            return 0
            
        except Exception as e:
            print(f"❌ Cache clear failed for user {user_id}: {str(e)}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        
        if not REDIS_AVAILABLE or not self.cache.redis_client:
            return {
                'cache_type': 'memory',
                'total_keys': len(getattr(self.cache, 'cache', {})),
                'memory_usage': 'unknown'
            }
        
        try:
            info = await self.cache.redis_client.info()
            
            return {
                'cache_type': 'redis',
                'total_keys': info.get('db0', {}).get('keys', 0),
                'memory_usage': info.get('used_memory_human', 'unknown'),
                'hit_rate': info.get('keyspace_hit_rate', 'unknown'),
                'connected_clients': info.get('connected_clients', 0)
            }
            
        except Exception as e:
            print(f"❌ Cache stats failed: {str(e)}")
            return {'cache_type': 'redis', 'error': str(e)}


class CacheManager:
    """High-level cache management for the resume optimization pipeline."""
    
    def __init__(self):
        self.cache = ResumeCache()
    
    async def get_or_process(
        self,
        cache_key_data: Dict[str, Any],
        processor_func,
        *processor_args,
        ttl: Optional[int] = None,
        **processor_kwargs
    ) -> Tuple[Any, bool]:
        """
        Get from cache or process and cache the result.
        
        Args:
            cache_key_data: Data to generate cache key
            processor_func: Function to call if not in cache
            *processor_args: Arguments for processor function
            ttl: Cache TTL
            **processor_kwargs: Keyword arguments for processor function
            
        Returns:
            Tuple of (result, was_cached)
        """
        
        # Try to get from cache first
        cached_result = await self.cache.get_cached_result(**cache_key_data)
        
        if cached_result:
            return cached_result, True
        
        # Not in cache - process
        start_time = time.time()
        result = await processor_func(*processor_args, **processor_kwargs)
        processing_time = (time.time() - start_time) * 1000
        
        # Add processing metadata
        if isinstance(result, dict):
            result['processing_time_ms'] = round(processing_time, 2)
            result['cache_hit'] = False
        
        # Cache the result
        await self.cache.cache_result(
            result=result,
            ttl=ttl,
            **cache_key_data
        )
        
        return result, False
    
    async def invalidate_related_cache(
        self,
        user_id: str,
        resume_text: Optional[str] = None,
        jd_text: Optional[str] = None
    ):
        """
        Invalidate cache entries related to user/resume/job.
        
        Args:
            user_id: User ID to invalidate
            resume_text: Specific resume to invalidate (optional)
            jd_text: Specific job description to invalidate (optional)
        """
        
        if resume_text and jd_text:
            # Invalidate specific resume+JD combination
            cache_key = CacheKeyGenerator.request_key(resume_text, jd_text)
            await self.cache.cache.delete(cache_key)
            print(f"🧹 Invalidated specific cache: {cache_key[:16]}...")
        else:
            # Invalidate all user cache
            cleared_count = await self.cache.clear_user_cache(user_id)
            print(f"🧹 Cleared {cleared_count} cache entries for user {user_id}")


class CacheWarmer:
    """Proactively warms cache with commonly needed data."""
    
    def __init__(self):
        self.cache = ResumeCache()
    
    async def warm_common_embeddings(
        self,
        common_job_descriptions: List[str],
        model_name: str
    ):
        """
        Pre-generate embeddings for common job descriptions.
        
        Args:
            common_job_descriptions: List of popular JD texts
            model_name: Embedding model name
        """
        
        print(f"🔥 Warming cache with {len(common_job_descriptions)} JD embeddings...")
        
        from ..embedding import ResumeEmbedder
        
        embedder = ResumeEmbedder()
        
        for jd_text in common_job_descriptions:
            # Check if already cached
            cache_key = CacheKeyGenerator.embedding_key(jd_text, model_name)
            
            if not await self.cache.cache.exists(cache_key):
                try:
                    # Generate and cache embedding
                    embedding_result = await embedder.embed_job_description(jd_text)
                    
                    cache_data = {
                        'embedding': embedding_result.embedding,
                        'model_name': model_name,
                        'text_length': len(jd_text)
                    }
                    
                    await self.cache.cache.set(cache_key, cache_data, ttl=7*24*60*60)  # 7 days
                    
                except Exception as e:
                    print(f"❌ Cache warm failed for JD: {str(e)}")
        
        print(f"✅ Cache warming complete")


# Sync wrappers
def get_cached_result_sync(*args, **kwargs) -> Optional[Dict[str, Any]]:
    """Synchronous wrapper for get_cached_result."""
    cache = ResumeCache()
    return asyncio.run(cache.get_cached_result(*args, **kwargs))


def cache_result_sync(*args, **kwargs) -> bool:
    """Synchronous wrapper for cache_result."""
    cache = ResumeCache()
    return asyncio.run(cache.cache_result(*args, **kwargs))


# Global cache instance
_cache_instance = None

def get_cache() -> ResumeCache:
    """Get global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ResumeCache()
    return _cache_instance