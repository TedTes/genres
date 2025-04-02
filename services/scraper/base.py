# services/scraper/base.py
import requests
from bs4 import BeautifulSoup
import logging
import time
import random
from datetime import datetime
from app import db
from models import Job, ScraperRun

logger = logging.getLogger(__name__)

class BaseScraper:
    """Base job scraper class with common functionality"""
    
    def __init__(self, source_name, base_url, headers=None):
        self.source_name = source_name
        self.base_url = base_url
        self.headers = headers or {
            'User-Agent': 'ResumeMatch Job Scraper - contact@resumematch.com',
        }
        self.scraper_run = None
    
    def start_run(self, keywords=None, location=None):
        """Start a scraper run and record in database"""
        self.scraper_run = ScraperRun(
            source=self.source_name,
            start_time=datetime.utcnow(),
            keywords=keywords,
            location=location,
            status='running'
        )
        db.session.add(self.scraper_run)
        db.session.commit()
        return self.scraper_run
    
    def end_run(self, status='success', error_message=None):
        """End a scraper run and update statistics"""
        if self.scraper_run:
            self.scraper_run.end_time = datetime.utcnow()
            self.scraper_run.status = status
            self.scraper_run.error_message = error_message
            db.session.commit()
    
    def scrape_jobs(self, keywords=None, location=None, max_jobs=100):
        """Main method to scrape jobs from the configured source"""
        self.start_run(keywords, location)
        
        try:
            search_url = self._build_search_url(keywords, location)
            logger.info(f"Scraping {self.source_name} with URL: {search_url}")
            
            response = requests.get(search_url, headers=self.headers)
            response.raise_for_status()
            
            jobs = self._parse_search_results(response.text, max_jobs)
            logger.info(f"Found {len(jobs)} jobs from {self.source_name}")
            
            if self.scraper_run:
                self.scraper_run.jobs_found = len(jobs)
            
            # Get full details for each job
            detailed_jobs = []
            for job in jobs[:max_jobs]:
                try:
                    job_details = self._get_job_details(job['job_url'])
                    detailed_jobs.append({**job, **job_details})
                    # Be polite - add a small delay between requests
                    time.sleep(random.uniform(1, 3))
                except Exception as e:
                    logger.error(f"Error getting details for job {job['title']}: {str(e)}")
            
            self.end_run('success')
            return detailed_jobs
            
        except Exception as e:
            logger.error(f"Error scraping {self.source_name}: {str(e)}")
            self.end_run('failed', str(e))
            return []
    
    def _build_search_url(self, keywords, location):
        """Build search URL based on source-specific format"""
        raise NotImplementedError("Subclasses must implement this method")
        
    def _parse_search_results(self, html_content, max_jobs):
        """Parse job listings from search results page"""
        raise NotImplementedError("Subclasses must implement this method")
        
    def _get_job_details(self, job_url):
        """Get detailed job information from job page"""
        raise NotImplementedError("Subclasses must implement this method")
        
    def _normalize_job_data(self, job_data):
        """Standardize job data to match database schema"""
        # Implementation in base class
        pass