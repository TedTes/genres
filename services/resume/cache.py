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



class CacheAnalytics:
    """Analytics and logging for cache performance."""
    
    def __init__(self):
        self.cache = get_cache()
        self.session_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0,
            'total_requests': 0,
            'cache_savings_ms': 0.0,
            'session_start': time.time()
        }
    
    async def log_cache_operation(
        self,
        operation: str,  # 'hit', 'miss', 'set', 'error'
        key: str,
        data_type: str = None,  # 'optimization', 'embedding', 'gap_analysis'
        processing_time_saved: float = 0.0,
        error_details: str = None
    ):
        """
        Log cache operation with detailed analytics.
        
        Args:
            operation: Type of cache operation
            key: Cache key used
            data_type: Type of data being cached
            processing_time_saved: Time saved by cache hit (ms)
            error_details: Error information if operation failed
        """
        
        # Update session stats
        self.session_stats['total_requests'] += 1
        
        if operation == 'hit':
            self.session_stats['hits'] += 1
            self.session_stats['cache_savings_ms'] += processing_time_saved
        elif operation == 'miss':
            self.session_stats['misses'] += 1
        elif operation == 'set':
            self.session_stats['sets'] += 1
        elif operation == 'error':
            self.session_stats['errors'] += 1
        
        # Calculate current hit rate
        hit_rate = (self.session_stats['hits'] / self.session_stats['total_requests'] * 100) if self.session_stats['total_requests'] > 0 else 0
        
        # Create log entry
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'data_type': data_type,
            'key_prefix': key[:16] + '...' if len(key) > 16 else key,
            'session_hit_rate': round(hit_rate, 1),
            'cumulative_savings_ms': round(self.session_stats['cache_savings_ms'], 2),
            'error_details': error_details
        }
        
        # Log based on operation type
        if operation == 'hit':
            print(f"🎯 Cache HIT ({hit_rate:.1}% session rate): {data_type or 'unknown'} | Saved {processing_time_saved:.0f}ms")
        elif operation == 'miss':
            print(f"❌ Cache MISS ({hit_rate:.1}% session rate): {data_type or 'unknown'} | Key: {log_data['key_prefix']}")
        elif operation == 'set':
            print(f"💾 Cache SET: {data_type or 'unknown'} | Key: {log_data['key_prefix']}")
        elif operation == 'error':
            print(f"🔴 Cache ERROR: {error_details} | Key: {log_data['key_prefix']}")
        
        # Optional: Store detailed logs for analytics (could send to external service)
        await self._store_analytics_log(log_data)
    
    async def _store_analytics_log(self, log_data: Dict[str, Any]):
        """Store detailed analytics log (extend this for external analytics)."""
        
        # For MVP, just store in Redis with short TTL for recent analytics
        try:
            analytics_key = f"analytics:{int(time.time())}"
            await self.cache.cache.set(analytics_key, log_data, ttl=60*60)  # 1 hour
        except:
            pass  # Don't fail main operation if analytics storage fails
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session cache statistics."""
        
        total_requests = self.session_stats['total_requests']
        hit_rate = (self.session_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        session_duration = time.time() - self.session_stats['session_start']
        
        return {
            'session_duration_minutes': round(session_duration / 60, 2),
            'total_requests': total_requests,
            'cache_hits': self.session_stats['hits'],
            'cache_misses': self.session_stats['misses'],
            'hit_rate_percentage': round(hit_rate, 2),
            'total_time_saved_ms': round(self.session_stats['cache_savings_ms'], 2),
            'average_savings_per_hit': round(
                self.session_stats['cache_savings_ms'] / self.session_stats['hits'], 2
            ) if self.session_stats['hits'] > 0 else 0,
            'cache_errors': self.session_stats['errors'],
            'sets_performed': self.session_stats['sets']
        }
    
    async def generate_cache_report(self) -> Dict[str, Any]:
        """Generate comprehensive cache performance report."""
        
        session_stats = self.get_session_stats()
        cache_stats = await self.cache.get_cache_stats()
        
        # Performance assessment
        hit_rate = session_stats['hit_rate_percentage']
        if hit_rate >= 70:
            performance_grade = 'Excellent'
            performance_color = 'green'
        elif hit_rate >= 50:
            performance_grade = 'Good'
            performance_color = 'blue'
        elif hit_rate >= 30:
            performance_grade = 'Fair'
            performance_color = 'yellow'
        else:
            performance_grade = 'Poor'
            performance_color = 'red'
        
        return {
            'session_performance': session_stats,
            'cache_infrastructure': cache_stats,
            'performance_assessment': {
                'grade': performance_grade,
                'color': performance_color,
                'recommendation': CacheAnalytics._get_performance_recommendation(hit_rate)
            },
            'generated_at': datetime.now().isoformat()
        }
    
    @staticmethod
    def _get_performance_recommendation(hit_rate: float) -> str:
        """Get recommendation based on cache hit rate."""
        
        if hit_rate >= 70:
            return "Cache performing excellently. Consider extending TTL for stable data."
        elif hit_rate >= 50:
            return "Good cache performance. Monitor for optimization opportunities."
        elif hit_rate >= 30:
            return "Fair cache performance. Review cache key strategy and TTL settings."
        else:
            return "Poor cache performance. Check Redis connectivity and review caching strategy."


# Enhanced ResumeCache with analytics
class EnhancedResumeCache(ResumeCache):
    """ResumeCache enhanced with analytics and logging."""
    
    def __init__(self):
        super().__init__()
        self.analytics = CacheAnalytics()
    
    async def get_cached_result(self, *args, **kwargs) -> Optional[Dict[str, Any]]:
        """Enhanced get with analytics logging."""
        
        start_time = time.time()
        result = await super().get_cached_result(*args, **kwargs)
        
        if result:
            # Cache hit
            processing_time_saved = 2000.0  # Estimate average processing time saved
            await self.analytics.log_cache_operation(
                'hit', 
                CacheKeyGenerator.request_key(
                    kwargs.get('resume_text', ''),
                    kwargs.get('jd_text', ''),
                    kwargs.get('options'),
                    kwargs.get('model_info')
                ),
                'optimization',
                processing_time_saved
            )
        else:
            # Cache miss
            await self.analytics.log_cache_operation(
                'miss',
                CacheKeyGenerator.request_key(
                    kwargs.get('resume_text', ''),
                    kwargs.get('jd_text', ''),
                    kwargs.get('options'),
                    kwargs.get('model_info')
                ),
                'optimization'
            )
        
        return result
    
    async def cache_result(self, *args, **kwargs) -> bool:
        """Enhanced cache set with analytics logging."""
        
        result = await super().cache_result(*args, **kwargs)
        
        cache_key = CacheKeyGenerator.request_key(
            kwargs.get('resume_text', ''),
            kwargs.get('jd_text', ''),
            kwargs.get('options'),
            kwargs.get('model_info')
        )
        
        if result:
            await self.analytics.log_cache_operation('set', cache_key, 'optimization')
        else:
            await self.analytics.log_cache_operation('error', cache_key, 'optimization', error_details="Cache set failed")
        
        return result
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive cache performance report."""
        return await self.analytics.generate_cache_report()


# Update global cache instance to use enhanced version
def get_enhanced_cache() -> EnhancedResumeCache:
    """Get global enhanced cache instance."""
    global _cache_instance
    if _cache_instance is None or not isinstance(_cache_instance, EnhancedResumeCache):
        _cache_instance = EnhancedResumeCache()
    return _cache_instance


# Decorator for automatic caching
def cache_result(
    data_type: str = 'generic',
    ttl: Optional[int] = None,
    key_generator = None
):
    """
    Decorator for automatic caching of function results.
    
    Args:
        data_type: Type of data being cached
        ttl: Cache TTL in seconds
        key_generator: Function to generate cache key from args
    """
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = get_enhanced_cache()
            
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                # Default key generation
                func_name = func.__name__
                args_hash = hashlib.md5(str(args).encode()).hexdigest()[:8]
                kwargs_hash = hashlib.md5(str(sorted(kwargs.items())).encode()).hexdigest()[:8]
                cache_key = f"{func_name}:{args_hash}:{kwargs_hash}"
            
            # Try cache first
            cached = await cache.cache.get(cache_key)
            if cached:
                await cache.analytics.log_cache_operation('hit', cache_key, data_type, 1000.0)
                return cached
            
            # Execute function
            start_time = time.time()
            result = await func(*args, **kwargs)
            processing_time = (time.time() - start_time) * 1000
            
            # Cache result
            cache_success = await cache.cache.set(cache_key, result, ttl)
            
            if cache_success:
                await cache.analytics.log_cache_operation('set', cache_key, data_type)
            else:
                await cache.analytics.log_cache_operation('error', cache_key, data_type, error_details="Cache set failed")
            
            await cache.analytics.log_cache_operation('miss', cache_key, data_type)
            
            return result
        
        return wrapper
    return decorator