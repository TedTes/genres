import asyncio
from typing import List, Dict
from .web_scraper import WebScraper
from .parser import parse_jobs
import logging
from datetime import datetime
from db import db
from models import Job

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataAggregator:
    """A class to aggregate job data from multiple sites and store in Supabase."""
    
    def __init__(self, configs: Dict[str, dict]):
        """
        Initialize the aggregator with configs.
        
        Args:
            configs: Dictionary of site configs (e.g., {"h-depo": {...}, ...})
        """
        self.configs = configs
        self.scraper = WebScraper(headless=True)
    
    async def scrape_site(self, site_key: str) -> List[dict]:
        """Scrape and parse data for a single site."""
        config = self.configs.get(site_key)
        if not config:
            logger.error(f"No config found for site: {site_key}")
            return []
        
        url = config["site"]
        selector = config["container_selector"]
        try:
            html_content = await self.scraper.scrape_html_block(url, selector)
            jobs = parse_jobs(config, html_content)
            for job in jobs:
                job["source"] = site_key
                job["source_job_id"] = job.pop("job_id", None)  # Rename job_id to source_job_id
                job["site"] = url  # Store full URL as source reference

            return jobs
        except Exception as e:
            logger.error(f"Failed to scrape {site_key}: {str(e)}")
            return []
    
    async def aggregate(self) -> List[dict]:
        """Scrape all sites concurrently, store in DB, and return results."""
        tasks = [self.scrape_site(site_key) for site_key in self.configs.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_jobs = []
        for site_key, site_jobs in zip(self.configs.keys(), results):
            if isinstance(site_jobs, Exception):
                logger.error(f"Error in site {site_key}: {site_jobs}")
                continue
            all_jobs.extend(site_jobs)
        
        self._store_jobs(all_jobs)
        return all_jobs
    
    def _store_jobs(self, jobs: List[dict]):
        """Store jobs in Supabase via SQLAlchemy."""
        if not jobs:
            logger.info("No jobs to store")
            return
        
        try:
            for job_dict in jobs:
                # Map scraped fields to Job model
                job = Job(
                    slug=f"{job_dict.get('source')}-{job_dict.get('source_job_id', 'unknown')}",  # Unique slug
                    title=job_dict.get("title", "Unknown"),
                    company=job_dict.get("company", "Unknown"),
                    location=job_dict.get("location"),
                    description=None,  # Not scraped yet
                    posted_at=None,  # Not scraped yet
                    source=job_dict.get("source"),
                    source_job_id=job_dict.get("source_job_id"),
                    is_active=True,
                    last_seen=datetime.utcnow(),
                    #TODO: url if needed
                )
                # Merge to update existing or insert new
                db.session.merge(job)
            
            db.session.commit()
            logger.info(f"Stored {len(jobs)} jobs in Supabase")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to store jobs: {str(e)}")
            raise
