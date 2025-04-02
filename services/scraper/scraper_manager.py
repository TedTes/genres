from services.scraper.indeed import IndeedScraper
from services.scraper.linkedin import LinkedInScraper
from services.scraper.processors import JobProcessor
import logging

logging.basicConfig(level=logging.INFO)

sources = {
        'indeed': IndeedScraper(),
        'linkedin': LinkedInScraper()
    }
def get_all_sources_name() -> list[str]:
    """Return a list of available scraper source names."""
    return sources.keys()
def get_source_instance(source_name:str):
    """Get a scraper instance by name"""
    
    return sources.get(source_name)

def run_scraper(source_name:str, keywords:str=None, locatio:str=None, max_jobs:int=100)->int:
    """Run a specific scraper and save results to database"""
    scraper = get_source_instance(source_name)
    if not scraper:
        logging.error(f"Unknown source: {source_name}")
        return 0
    
    jobs = scraper.scrape_jobs(keywords, location, max_jobs)
    return JobProcessor.process_jobs(jobs, scraper)