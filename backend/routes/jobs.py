from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from typing import List, Optional
import logging
from datetime import datetime, timedelta
import os
import json
import time

from services.job_scraper import JobAggregator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

CACHE_DIR = "cache"
CACHE_EXPIRATION = 3600  


os.makedirs(CACHE_DIR, exist_ok=True)


JOB_CATEGORIES = {
        "General Labor": "general-labor",
        "Cleaning": "cleaning",
        "Retail": "retail",
        "Restaurant & Food Service": "restaurant",
        "Customer Service": "customer-service",
        "Delivery & Driving": "delivery",
        "Warehouse": "warehouse",
        "Sales": "sales",
        "Grocery": "grocery",
        "Healthcare Support": "healthcare"
    }


# In-memory job cache
job_cache = {}
last_fetch_time = {}

def get_cache_file_path(location: str, category: str) -> str:
    """Generate cache file path based on location and category"""
    return os.path.join(CACHE_DIR, f"jobs_{location}_{category}.json")

def save_to_cache(jobs: list, location: str, category: str) -> None:
    """Save job data to cache file"""
    try:
        cache_file = get_cache_file_path(location, category)
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "jobs": jobs
        }
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
            
        # Update in-memory cache
        cache_key = f"{location}_{category}"
        job_cache[cache_key] = jobs
        last_fetch_time[cache_key] = datetime.now()
        
        logger.info(f"Saved {len(jobs)} jobs to cache for {location} - {category}")
    except Exception as e:
        logger.error(f"Error saving to cache: {str(e)}")

def load_from_cache(location: str, category: str) -> List[dict]:
    """Load job data from cache if available and not expired"""
    try:
        cache_file = get_cache_file_path(location, category)
        
        # Check in-memory cache first
        cache_key = f"{location}_{category}"
        if cache_key in job_cache and cache_key in last_fetch_time:
            if datetime.now() - last_fetch_time[cache_key] < timedelta(seconds=CACHE_EXPIRATION):
                logger.info(f"Using in-memory cache for {location} - {category}")
                return job_cache[cache_key]
        
        # Check file cache if not in memory or expired
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
                
            timestamp = datetime.fromisoformat(cache_data["timestamp"])
            if datetime.now() - timestamp < timedelta(seconds=CACHE_EXPIRATION):
                logger.info(f"Loading from cache file for {location} - {category}")
                
                # Update in-memory cache
                job_cache[cache_key] = cache_data["jobs"]
                last_fetch_time[cache_key] = timestamp
                
                return cache_data["jobs"]
    except Exception as e:
        logger.error(f"Error loading from cache: {str(e)}")
    
    return None

async def fetch_jobs_background(location: str, category: str) -> None:
    """Background task to fetch jobs and update cache"""
    try:
        logger.info(f"Background task: Fetching jobs for {location} - {category}")
        aggregator = JobAggregator(location)
        jobs = aggregator.get_jobs(category=category, limit=50)
        save_to_cache(jobs, location, category)
        logger.info(f"Background task completed: Found {len(jobs)} jobs for {location} - {category}")
    except Exception as e:
        logger.error(f"Error in background job fetching: {str(e)}")

@router.get("/categories")
async def get_categories():
    """Get all available job categories"""
    return [
        "General Labor",
        "Cleaning",
        "Retail",
        "Restaurant & Food Service",
        "Customer Service",
        "Delivery & Driving",
        "Warehouse",
        "Sales",
        "Grocery",
        "Healthcare Support"
    ]

@router.get("/locations")
async def get_locations():
    """Get available locations for job search"""
    return {
        "toronto": "Toronto, ON",
        "vancouver": "Vancouver, BC",
        "montreal": "Montreal, QC",
        "calgary": "Calgary, AB",
        "ottawa": "Ottawa, ON",
        "edmonton": "Edmonton, AB",
        "winnipeg": "Winnipeg, MB",
        "halifax": "Halifax, NS"
    }

@router.get("")
async def get_jobs(
    background_tasks: BackgroundTasks,
    location: str = Query("toronto", description="Location to search for jobs"),
    category: Optional[str] = Query(None, description="Job category"),
    refresh: bool = Query(False, description="Force refresh from sources")
):
    """
    Get jobs based on location and optional category.
    Uses cache when available unless refresh is requested.
    """
    try:
        # Validate category
        if category and category not in JOB_CATEGORIES:
            raise HTTPException(status_code=400, detail=f"Invalid category. Available categories: {list(JOB_CATEGORIES.keys())}")
        
        # Default to general-labor if no category specified
        if not category:
            category = "general-labor"
        
        # Try to get from cache unless refresh is requested
        if not refresh:
            cached_jobs = load_from_cache(location, category)
            if cached_jobs:
                # Schedule a background refresh if cache is getting old
                cache_key = f"{location}_{category}"
                if cache_key in last_fetch_time:
                    cache_age = datetime.now() - last_fetch_time[cache_key]
                    if cache_age > timedelta(seconds=CACHE_EXPIRATION * 0.75):  # If cache is 75% of the way to expiring
                        logger.info(f"Cache getting old ({cache_age.total_seconds()} seconds), scheduling background refresh")
                        background_tasks.add_task(fetch_jobs_background, location, category)
                return cached_jobs
        
        # If no cache or refresh requested, fetch new data
        logger.info(f"Fetching fresh jobs for {location} - {category}")
        aggregator = JobAggregator(location)
        jobs = aggregator.get_jobs(category=category, limit=50)
        
        # Save to cache
        save_to_cache(jobs, location, category)
        
        return jobs
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")

@router.get("/stats")
async def get_job_stats():
    """Get statistics about job listings"""
    stats = {
        "total_jobs_cached": sum(len(jobs) for jobs in job_cache.values()),
        "categories_available": len(JOB_CATEGORIES),
        "cache_info": {
            category: {
                "job_count": len(jobs),
                "last_updated": last_fetch_time.get(cat_key, "never").isoformat() 
                if isinstance(last_fetch_time.get(cat_key, "never"), datetime) else "never"
            }
            for cat_key, jobs in job_cache.items()
            for category in [cat_key.split("_")[1]]
        }
    }
    return stats