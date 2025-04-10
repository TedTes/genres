from bs4 import BeautifulSoup
import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

def parse_job(config: Dict, job_block: BeautifulSoup) -> Dict[str, Any]:
    """
    Parse a single job block from a pre-parsed BeautifulSoup element.
    
    Args:
        config: Configuration dictionary with parsing rules
        job_block: BeautifulSoup element representing a job
        
    Returns:
        Dictionary with parsed job data
    """
    job_data = {}
    
    # Process each field according to config rules
    for field, rule in config.items():
        # Skip non-field configuration items
        if field in ["site", "container_selector", "listing_selector", "next_page_selector", 
                    "description_selector", "apply_selector"]:
            continue
            
        # Process structured rules (as dictionaries)
        if isinstance(rule, dict):
            selector = rule.get("selector")
            extract = rule.get("extract")
            multiple = rule.get("multiple", False)
            post_process = rule.get("post_process")
            default_value = rule.get("default", "N/A")
            
            # Use the root element itself
            if selector == "self":
                if extract in job_block.attrs:
                    value = job_block[extract]
                    value = _apply_post_processing(value, post_process)
                    job_data[field] = value
                else:
                    job_data[field] = default_value
            
            # Extract from multiple elements
            elif multiple and selector:
                elements = job_block.select(selector)
                if extract == "text":
                    values = [el.get_text(strip=True) for el in elements if el]
                else:
                    values = [el.get(extract) for el in elements if el and extract in el.attrs]
                    
                # Filter out None values
                values = [v for v in values if v]
                
                if values:
                    # For multiple values, join with comma or return as list based on config
                    if rule.get("return_list", False):
                        job_data[field] = values
                    else:
                        job_data[field] = ", ".join(values)
                else:
                    job_data[field] = default_value
            
            # Extract from a single element
            elif selector:
                element = job_block.select_one(selector)
                if element:
                    if extract == "text":
                        value = element.get_text(strip=True)
                    elif extract in element.attrs:
                        value = element[extract]
                    else:
                        value = default_value
                        
                    value = _apply_post_processing(value, post_process)
                    job_data[field] = value
                else:
                    job_data[field] = default_value
            
            # Use a fixed value from config
            elif "value" in rule:
                job_data[field] = rule["value"] or default_value
            
            else:
                job_data[field] = default_value
        
        # Fixed value as a string
        elif isinstance(rule, str):
            job_data[field] = rule
        
        # Default case
        else:
            job_data[field] = "N/A"
    
    # Add any derived fields or post-processing for the whole job
    
    # Check if job is remote based on location
    if "location" in job_data:
        location = job_data["location"].lower() if job_data["location"] else ""
        job_data["remote"] = 'remote' in location or 'work from home' in location or 'wfh' in location
    
    # Clean up description field if present
    if "description" in job_data and job_data["description"]:
        job_data["description"] = clean_job_description(job_data["description"])
    
    return job_data

def parse_jobs(config: Dict, html: str) -> List[Dict[str, Any]]:
    """
    Parse multiple job blocks from HTML content.
    
    Args:
        config: Configuration dictionary with parsing rules
        html: HTML content containing job listings
        
    Returns:
        List of parsed job dictionaries
    """
    if not html or not html.strip():
        logger.warning("No HTML content to parse")
        return []

    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all top-level elements in the container
        job_blocks = [child for child in soup.children if child.name]
        
        # If no direct children have names (i.e., they're all text nodes),
        # try to find job blocks within the HTML
        if not job_blocks:
            # Try alternative methods to find job blocks
            container_selector = config.get("listing_selector")
            if container_selector:
                job_blocks = soup.select(container_selector)
            
            # If still no blocks, try common job listing patterns
            if not job_blocks:
                common_patterns = [
                    "li.job-listing", "div.job-card", ".job-item", 
                    ".job-result", "[data-testid='job-listing']",
                    ".job-listing", ".search-result", ".job-row",
                    ".result-card", "article.job"
                ]
                
                for pattern in common_patterns:
                    job_blocks = soup.select(pattern)
                    if job_blocks:
                        logger.info(f"Found job blocks using pattern: {pattern}")
                        break
            
            # If still no blocks, use any divs or list items that might contain jobs
            if not job_blocks:
                job_blocks = soup.select("div.card, li.card, div.listing, li.listing, div[class*='job'], li[class*='job']")
        
        if not job_blocks:
            logger.warning("No job blocks found in HTML content")
            return []
        
        logger.info(f"Found {len(job_blocks)} job blocks to parse")
        parsed_jobs = []
        
        for block in job_blocks:
            try:
                parsed_job = parse_job(config, block)
                # Only add jobs with at least title and either company or location
                if parsed_job.get("title") and (parsed_job.get("company") or parsed_job.get("location")):
                    parsed_jobs.append(parsed_job)
            except Exception as e:
                logger.error(f"Error parsing job block: {str(e)}")
                continue
        
        return parsed_jobs
    
    except Exception as e:
        logger.error(f"Error parsing jobs HTML: {str(e)}")
        return []

def parse_job_detail(html: str, config: Dict) -> Dict[str, Any]:
    """
    Parse job details from HTML content of a job detail page.
    
    Args:
        html: HTML content of the job detail page
        config: Configuration dictionary with parsing rules
        
    Returns:
        Dictionary with parsed job details
    """
    if not html or not html.strip():
        logger.warning("No HTML content to parse job details")
        return {}
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        job_detail = {}
        
        # Extract description if selector is in config
        if "description_selector" in config:
            description_element = soup.select_one(config["description_selector"])
            if description_element:
                job_detail["description"] = clean_job_description(description_element.get_text(strip=True))
            else:
                # Try common description selectors
                common_selectors = [
                    ".job-description", "#job-description", 
                    ".description", "#description",
                    ".job-details", ".job-content",
                    "article.job", ".jobDetailsSection"
                ]
                
                for selector in common_selectors:
                    description_element = soup.select_one(selector)
                    if description_element:
                        job_detail["description"] = clean_job_description(description_element.get_text(strip=True))
                        break
        
        # Extract apply URL if selector is in config
        if "apply_selector" in config:
            apply_element = soup.select_one(config["apply_selector"])
            if apply_element and apply_element.name == 'a' and 'href' in apply_element.attrs:
                job_detail["apply_url"] = apply_element['href']
        
        # Extract additional fields based on common selectors
        # Location
        location_element = soup.select_one(".location, .job-location, [data-test='location']")
        if location_element:
            job_detail["location"] = location_element.get_text(strip=True)
        
        # Salary
        salary_element = soup.select_one(".salary, .job-salary, .compensation")
        if salary_element:
            job_detail["salary"] = salary_element.get_text(strip=True)
        
        # Job type/employment type
        type_element = soup.select_one(".type, .job-type, .employment-type")
        if type_element:
            job_detail["job_type"] = type_element.get_text(strip=True)
        
        # Posted date
        date_element = soup.select_one(".date, .posted-date, .job-date")
        if date_element:
            job_detail["posted_at"] = date_element.get_text(strip=True)
            
        return job_detail
    
    except Exception as e:
        logger.error(f"Error parsing job detail HTML: {str(e)}")
        return {}

def _apply_post_processing(value: str, post_process: Optional[str]) -> str:
    """
    Apply post-processing to extracted value.
    
    Args:
        value: The string value to process
        post_process: String describing the post-processing to apply
        
    Returns:
        Processed value
    """
    if not post_process or not value:
        return value
    
    try:
        if post_process == "split('/')[-1]":
            return value.split('/')[-1]
        elif post_process == "split()[-1]":
            return value.split()[-1]
        elif post_process == "split('_')[-1]":
            return value.split('_')[-1]
        elif post_process == "split('-')[-1]":
            return value.split('-')[-1]
        elif post_process == "lowercase":
            return value.lower()
        elif post_process == "uppercase":
            return value.upper()
        elif post_process == "strip":
            return value.strip()
        elif post_process.startswith("regex:"):
            # Extract pattern from the post-process string
            pattern = post_process[6:]  # Remove "regex:" prefix
            match = re.search(pattern, value)
            if match:
                return match.group(0)
        
        return value
    except Exception as e:
        logger.error(f"Error in post-processing: {str(e)}")
        return value

def clean_job_description(description: str) -> str:
    """
    Clean up job description text.
    
    Args:
        description: Raw job description text
        
    Returns:
        Cleaned description text
    """
    if not description:
        return ""
        
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', description)
    
    # Remove common boilerplate phrases
    boilerplate = [
        "Please upload your resume and apply online",
        "Please apply online",
        "Apply now",
        "Click the apply button",
        "Click apply now"
    ]
    
    for phrase in boilerplate:
        cleaned = re.sub(re.escape(phrase), '', cleaned, flags=re.IGNORECASE)
    
    # Remove URLs
    cleaned = re.sub(r'https?://\S+', '', cleaned)
    
    # Remove email addresses
    cleaned = re.sub(r'\S+@\S+\.\S+', '', cleaned)
    
    return cleaned.strip()