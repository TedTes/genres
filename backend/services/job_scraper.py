import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from datetime import datetime
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobScraper:
    """Base scraper class with common functionality"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        # Add proxy support if needed
        self.proxies = None

    def _make_request(self, url: str) -> str:
        """Make HTTP request with error handling and retries"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=10)
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"Failed to retrieve {url} after {max_retries} attempts")
                    return ""
    
    def _delay(self):
        """Add random delay between requests to avoid rate limiting"""
        time.sleep(random.uniform(1, 3))


class CraigslistScraper(JobScraper):
    """Scraper for Craigslist job listings"""
    
    def __init__(self, city: str):
        super().__init__()
        self.city = city
        self.base_url = f"https://{city}.craigslist.org"
    
    def get_jobs(self, category: str = "general-labor", limit: int = 20) -> List[Dict[str, Any]]:
        """Scrape jobs from Craigslist based on category"""
        url = f"{self.base_url}/search/jjj?query={category}"
        logger.info(f"Scraping Craigslist: {url}")
        
        html = self._make_request(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        jobs = []
        
        # Find job listings
        listings = soup.select(".result-info")
        for i, listing in enumerate(listings):
            if i >= limit:
                break
                
            try:
                title_elem = listing.select_one(".result-title")
                title = title_elem.text.strip()
                job_url = title_elem['href']
                
                location_elem = listing.select_one(".result-hood")
                location = location_elem.text.strip(" ()") if location_elem else self.city
                
                date_elem = listing.select_one(".result-date")
                posted_date = date_elem['datetime'] if date_elem else datetime.now().isoformat()
                
                # Get job details from the job page
                job_details = self._get_job_details(job_url)
                
                job = {
                    "id": job_url.split("/")[-1],
                    "title": title,
                    "company": "Not specified",  # Often not available on Craigslist
                    "location": location,
                    "type": job_details.get("type", "Not specified"),
                    "description": job_details.get("description", ""),
                    "requirements": job_details.get("requirements", []),
                    "postedDate": posted_date,
                    "category": category,
                    "source": "Craigslist",
                    "url": job_url
                }
                
                jobs.append(job)
                self._delay()
                
            except Exception as e:
                logger.error(f"Error parsing job listing: {str(e)}")
                continue
                
        return jobs
    
    def _get_job_details(self, url: str) -> Dict[str, Any]:
        """Get detailed information from a job posting page"""
        html = self._make_request(url)
        if not html:
            return {}
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Get job description
        description_elem = soup.select_one("#postingbody")
        description = description_elem.text.strip() if description_elem else ""
        
        # Try to extract requirements from description
        requirements = []
        description_lower = description.lower()
        
        # Look for common requirement patterns
        if "requirements" in description_lower or "qualifications" in description_lower:
            try:
                # Try to find bullet points or numbered lists
                list_items = soup.select("#postingbody ul li, #postingbody ol li")
                if list_items:
                    for item in list_items:
                        text = item.text.strip()
                        if text and len(text) > 5:  # Minimal validation
                            requirements.append(text)
                else:
                    # Try to extract based on common patterns
                    lines = description.split('\n')
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if "requirements:" in line.lower() or "qualifications:" in line.lower():
                            # Collect the lines that follow until a blank line or another section
                            j = i + 1
                            while j < len(lines) and lines[j].strip() and not any(x in lines[j].lower() for x in ["benefits:", "salary:", "about us:"]):
                                req_line = lines[j].strip()
                                if req_line.startswith("- ") or req_line.startswith("* "):
                                    requirements.append(req_line[2:])
                                elif req_line and len(req_line) > 5:
                                    requirements.append(req_line)
                                j += 1
            except Exception as e:
                logger.error(f"Error extracting requirements: {str(e)}")
        
        # If no specific requirements found, extract key skills from the description
        if not requirements:
            common_skills = ["experience", "years", "education", "degree", "diploma", "certification", 
                            "license", "skilled", "ability", "proficient", "knowledge"]
            for line in description.split('\n'):
                line = line.strip()
                if any(skill in line.lower() for skill in common_skills) and 5 < len(line) < 200:
                    requirements.append(line)
        
        # Determine job type based on description text
        job_type = "Not specified"
        if "part-time" in description_lower or "part time" in description_lower:
            job_type = "Part-time"
        elif "full-time" in description_lower or "full time" in description_lower:
            job_type = "Full-time"
        elif "contract" in description_lower:
            job_type = "Contract"
        elif "temporary" in description_lower:
            job_type = "Temporary"
        
        return {
            "description": description,
            "requirements": requirements[:10],  # Limit to top 10 requirements
            "type": job_type
        }


class KijijiScraper(JobScraper):
    """Scraper for Kijiji job listings (Canada-specific)"""
    
    def __init__(self, city: str):
        super().__init__()
        self.city = city
        # Map city to Kijiji location code
        self.city_codes = {
            "toronto": "1700273",
            "vancouver": "1700287", 
            "montreal": "1700281",
            "calgary": "1700234",
            # TODOo:Add more cities 
        }
        self.city_code = self.city_codes.get(city.lower(), "")
        
    def get_jobs(self, category: str = "general-labour", limit: int = 20) -> List[Dict[str, Any]]:
        """Scrape jobs from Kijiji based on category"""
        # Map category to Kijiji category code
        category_mapping = {
            "general-labour": "152", 
            "retail": "149",
            "restaurant": "150",
            "customer-service": "146",
            "cleaning": "142",
            "sales": "147"
            # TODOo more categories as needed
        }
        
        category_code = category_mapping.get(category, "152")  # Default to general labour
        
        url = f"https://www.kijiji.ca/b-jobs/{self.city_code}/{category_code}l0c45"
        logger.info(f"Scraping Kijiji: {url}")
        
        html = self._make_request(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        jobs = []
        
        # Find job listings
        listings = soup.select(".search-item")
        for i, listing in enumerate(listings):
            if i >= limit:
                break
                
            try:
                title_elem = listing.select_one("a.title")
                title = title_elem.text.strip() if title_elem else "No Title"
                job_url = "https://www.kijiji.ca" + title_elem['href'] if title_elem and 'href' in title_elem.attrs else ""
                
                location_elem = listing.select_one(".location")
                location = location_elem.text.strip() if location_elem else self.city
                
                date_elem = listing.select_one(".date-posted")
                posted_date = date_elem.text.strip() if date_elem else "Unknown"
                
                # Convert relative dates to ISO format
                if posted_date == "Yesterday":
                    # Use yesterday's date
                    import datetime
                    posted_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                elif posted_date.lower().startswith(("minute", "hour", "day")):
                    # For relative dates like "minutes ago", use today
                    posted_date = datetime.now().strftime("%Y-%m-%d")
                    
                # Get job details
                if job_url:
                    job_details = self._get_job_details(job_url)
                else:
                    job_details = {}
                
                # Extract company name if available
                company_elem = listing.select_one(".business-name")
                company = company_elem.text.strip() if company_elem else job_details.get("company", "Not specified")
                
                job = {
                    "id": job_url.split("/")[-1].split("?")[0] if job_url else str(i),
                    "title": title,
                    "company": company,
                    "location": location,
                    "type": job_details.get("type", "Not specified"),
                    "description": job_details.get("description", ""),
                    "requirements": job_details.get("requirements", []),
                    "postedDate": posted_date,
                    "category": category,
                    "source": "Kijiji",
                    "url": job_url
                }
                
                jobs.append(job)
                self._delay()
                
            except Exception as e:
                logger.error(f"Error parsing Kijiji job listing: {str(e)}")
                continue
                
        return jobs
    
    def _get_job_details(self, url: str) -> Dict[str, Any]:
        """Get detailed information from a Kijiji job posting page"""
        html = self._make_request(url)
        if not html:
            return {}
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Get job description
        description_elem = soup.select_one("[itemprop='description']")
        description = description_elem.text.strip() if description_elem else ""
        
        # Try to get company name
        company_elem = soup.select_one(".business-name")
        company = company_elem.text.strip() if company_elem else "Not specified"
        
        # Extract job type from attributes or description
        job_type_elem = soup.select_one("li:contains('Job Type')")
        job_type = "Not specified"
        
        if job_type_elem:
            job_type = job_type_elem.text.replace("Job Type:", "").strip()
        else:
            description_lower = description.lower()
            if "part-time" in description_lower or "part time" in description_lower:
                job_type = "Part-time"
            elif "full-time" in description_lower or "full time" in description_lower:
                job_type = "Full-time"
            elif "contract" in description_lower:
                job_type = "Contract"
            elif "temporary" in description_lower:
                job_type = "Temporary"
        
        # Extract requirements similar to Craigslist method
        requirements = []
        
        # Try to find bullet points
        list_items = soup.select("[itemprop='description'] ul li, [itemprop='description'] ol li")
        if list_items:
            for item in list_items:
                text = item.text.strip()
                if text and len(text) > 5:
                    requirements.append(text)
        else:
            # Try to extract based on common patterns
            if description:
                lines = description.split('\n')
                in_requirements_section = False
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    if "requirements" in line.lower() or "qualifications" in line.lower():
                        in_requirements_section = True
                        continue
                    elif in_requirements_section and any(x in line.lower() for x in ["benefits:", "salary:", "about us:"]):
                        in_requirements_section = False
                        
                    if in_requirements_section and line.startswith(("- ", "• ", "* ")):
                        requirements.append(line[2:])
                    elif in_requirements_section and line and len(line) > 5 and len(line) < 200:
                        requirements.append(line)
        
        # If still no requirements, extract key skills from description
        if not requirements:
            common_skills = ["experience", "years", "education", "degree", "diploma", "certification", 
                           "license", "skilled", "ability", "proficient", "knowledge"]
            for line in description.split('\n'):
                line = line.strip()
                if any(skill in line.lower() for skill in common_skills) and 5 < len(line) < 200:
                    requirements.append(line)
        
        return {
            "description": description,
            "requirements": requirements[:10],  # Limit to top 10 requirements
            "company": company,
            "type": job_type
        }


class FacebookJobsScraper(JobScraper):
    """
    Scraper for Facebook Jobs
    Note: Facebook's structure is complex and frequently changes.
    This is a simplified implementation and may require regular updates.
    Consider using Selenium for more robust scraping of Facebook.
    """
    
    def __init__(self, location: str):
        super().__init__()
        self.location = location
        self.base_url = "https://www.facebook.com/jobs"
    
    def get_jobs(self, category: str = "cleaning", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Note: Facebook Jobs is difficult to scrape with requests alone.
        A headless browser like Selenium would be more effective.
        This is a placeholder implementation.
        """
        logger.warning("Facebook Jobs scraping requires a Selenium implementation for reliability")
        return []


# Aggregator class to combine results from multiple scrapers
class JobAggregator:
    def __init__(self, location: str):
        self.location = location
        self.scrapers = [
            CraigslistScraper(location),
            KijijiScraper(location)
            # Add more scrapers as implemented
        ]
    
    def get_jobs(self, category: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get jobs from all sources and combine results"""
        all_jobs = []
        
        for scraper in self.scrapers:
            try:
                logger.info(f"Using {scraper.__class__.__name__} for {category} jobs")
                jobs = scraper.get_jobs(category, limit=limit)
                all_jobs.extend(jobs)
                logger.info(f"Found {len(jobs)} jobs from {scraper.__class__.__name__}")
            except Exception as e:
                logger.error(f"Error with {scraper.__class__.__name__}: {str(e)}")
        
        # Deduplicate jobs based on title and company
        unique_jobs = {}
        for job in all_jobs:
            key = f"{job['title']}_{job['company']}_{job['location']}"
            if key not in unique_jobs:
                unique_jobs[key] = job
        
        return list(unique_jobs.values())


# Example usage
if __name__ == "__main__":
    # Test with a single source
    scraper = CraigslistScraper("toronto")
    jobs = scraper.get_jobs(category="general-labor", limit=5)
    
    print(f"Found {len(jobs)} jobs")
    for job in jobs:
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Type: {job['type']}")
        print(f"Posted: {job['postedDate']}")
        print(f"Requirements: {job['requirements']}")
        print("-" * 50)
    
    # Test with aggregator
    print("\nTesting aggregator:")
    aggregator = JobAggregator("toronto")
    all_jobs = aggregator.get_jobs(category="cleaning", limit=10)
    
    print(f"Found {len(all_jobs)} total jobs from all sources")