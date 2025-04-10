import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .web_scraper import WebScraper
from .parser import parse_jobs, parse_job_detail
import logging
from models import Job, ScraperRun
from db import db

logger = logging.getLogger(__name__)

class DataAggregator:
    """Class to aggregate job data from multiple sites."""

    def __init__(self, configs: Dict[str, dict]):
        self.configs = configs
        self.scraper = WebScraper(headless=True)

    async def scrape_site_with_details(self, site_key: str, max_jobs: int = 30) -> List[dict]:
        """Scrape a site including job details."""
        config = self.configs.get(site_key)
        if not config:
            logger.error(f"No config for {site_key}")
            return []

        url = config["site"]
        scraper_run = ScraperRun(source=site_key, start_time=datetime.utcnow(), status="running")
        db.session.add(scraper_run)
        db.session.commit()

        try:
            jobs = await self.scraper.scrape_job_listings_with_details(url, config, batch_size=5, max_jobs=max_jobs)
            for job in jobs:
                job["source"] = site_key
                job["source_job_id"] = job.get("job_id", f"{site_key}_{len(jobs)}")
                job["site"] = url
                for field in ["title", "company", "location", "description"]:
                    job.setdefault(field, "")

            scraper_run.jobs_found = len(jobs)
            scraper_run.end_time = datetime.utcnow()
            scraper_run.status = "success" if jobs else "no_results"
            db.session.commit()
            return jobs
        except Exception as e:
            scraper_run.status = "failed"
            scraper_run.error_message = str(e)
            db.session.commit()
            logger.error(f"Failed to scrape {site_key}: {str(e)}")
            return []

    async def aggregate_with_details(self, include_sites: Optional[List[str]] = None) -> List[dict]:
        """Aggregate data from specified sites."""
        site_keys = include_sites or list(self.configs.keys())
        logger.info(f"Aggregating {len(site_keys)} sites: {', '.join(site_keys)}")

        tasks = [self.scrape_site_with_details(site_key) for site_key in site_keys]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_jobs = []
        for site_key, site_jobs in zip(site_keys, results):
            if isinstance(site_jobs, Exception):
                logger.error(f"Error in {site_key}: {site_jobs}")
                continue
            all_jobs.extend(site_jobs)
            await self._store_jobs(site_jobs)

        logger.info(f"Aggregated {len(all_jobs)} jobs")
        return all_jobs

    async def _store_jobs(self, jobs: List[Dict]) -> int:
        """Store jobs in the database."""
        if not jobs:
            return 0

        new_jobs_count = 0
        for job_dict in jobs:
            job_id = job_dict.get("source_job_id")
            source = job_dict.get("source")
            job_slug = f"{source}-{job_id}"

            existing_job = Job.query.filter_by(slug=job_slug).first()
            if existing_job:
                for field, value in job_dict.items():
                    if value and getattr(existing_job, field, None) != value:
                        setattr(existing_job, field, value)
                existing_job.last_seen = datetime.utcnow()
            else:
                new_job = Job(
                    slug=job_slug,
                    title=job_dict.get("title", "Unknown"),
                    company=job_dict.get("company", "Unknown"),
                    location=job_dict.get("location", ""),
                    description=job_dict.get("description", ""),
                    source=source,
                    source_job_id=job_id,
                    is_active=True,
                    last_seen=datetime.utcnow(),
                    url=job_dict.get("apply_url", job_dict.get("detail_url")),
                    remote=job_dict.get("remote", False)
                )
                db.session.add(new_job)
                new_jobs_count += 1

        db.session.commit()
        return new_jobs_count

    async def update_job_details(self, days_old: int = 7, limit: int = 50) -> int:
        """Update job details for jobs missing descriptions."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        jobs_to_update = db.session.query(Job).filter(
            (Job.description == None) | (Job.description == ""),
            Job.created_at >= cutoff_date
        ).limit(limit).all()

        updated_count = 0
        for job in jobs_to_update:
            config = self.configs.get(job.source)
            if config and job.url:
                html = await self.scraper.scrape_html_block(job.url, config.get("description_selector", "body"))
                details = parse_job_detail(html, config)
                if details.get("description"):
                    job.description = details["description"]
                    job.url = details.get("apply_url", job.url)
                    job.last_seen = datetime.utcnow()
                    updated_count += 1
                    db.session.commit()

        logger.info(f"Updated details for {updated_count} jobs")
        return updated_count