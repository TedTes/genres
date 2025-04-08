import asyncio
from playwright.async_api import async_playwright, ElementHandle
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebScraper:
    """A class for scraping web content using Playwright."""
    
    def __init__(self, headless: bool = True, timeout: int = 60000):
        """
        Initialize the scraper with configuration options.
        
        Args:
            headless: Whether to run the browser in headless mode
            timeout: Default timeout for operations in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
    
    async def scrape_html_block(self, url: str, selector: str, wait_time: int = 3000):
        """
        Scrape elements from a web page.
        
        Args:
            url: URL of the page to scrape
            selector: CSS selector to locate elements
            wait_time: Additional time to wait after page load (ms)
            
        Returns:
            List of ElementHandle objects representing the scraped elements
        """
        logger.info(f"Scraping elements from: {url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Navigate to the URL
                await page.goto(url, timeout=self.timeout)
                
                # Wait for the page to load
                await page.wait_for_load_state('networkidle')
                
                # Additional wait for dynamic content if needed
                if wait_time > 0:
                    await page.wait_for_timeout(wait_time)
                
                # Wait for the selector to be present in the DOM
                await page.wait_for_selector(selector, timeout=10000)
                
                # Create a locator and wait for elements to be visible
                elements_locator = page.locator(selector)
                await elements_locator.wait_for(state='visible', timeout=10000)
                
                # Get the html content
                html_content = await elements_locator.inner_html()
                
                logger.info(f"Successfully completed scraping html block content for {url}")
                
                return html_content
                
            except Exception as e:
                logger.error(f"Error scraping elements: {str(e)}")
                raise
            finally:
                await browser.close()