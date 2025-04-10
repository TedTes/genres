import asyncio
from playwright.async_api import async_playwright, Page, BrowserContext, ElementHandle
from typing import List, Dict, Optional
import logging
import re
import random
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebScraper:
    """Enhanced class for scraping web content with maximum robustness using Playwright."""

    def __init__(self, headless: bool = True, timeout: int = 60000, proxies: Optional[List[str]] = None):
        self.headless = headless
        self.timeout = timeout
        self.proxies = proxies 

    async def _get_proxy(self) -> Optional[Dict[str, str]]:
        """Select a random proxy from the pool."""
        if not self.proxies:
            return None
        proxy = random.choice(self.proxies)
        logger.info(f"Using proxy: {proxy}")
        return {"server": proxy}

    async def scrape_html_block(self, url: str, selector: str, wait_time: int = 6000) -> str:
        """Scrape HTML content from a specific selector."""
        logger.info(f"Scraping HTML block from: {url} with selector: {selector}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless, proxy=await self._get_proxy())
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            page = await context.new_page()
            try:
                await page.goto(url, timeout=self.timeout, wait_until='domcontentloaded')
                await page.wait_for_load_state('networkidle')
                await self._dismiss_common_popups(page)
                await page.wait_for_selector(selector, timeout=10000)
                html_content = await page.inner_html(selector)
                logger.info(f"Successfully scraped HTML block from {url}")
                return html_content
            except Exception as e:
                logger.error(f"Error scraping HTML block from {url}: {str(e)}")
                return await page.content()  # Fallback to full page content
            finally:
                await browser.close()

    async def scrape_paginated_listings(self, base_url: str, config: Dict, max_pages: int = 5) -> List[Dict]:
        """Scrape job listings across multiple pages."""
        logger.info(f"Scraping paginated listings from: {base_url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless, proxy=await self._get_proxy())
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            page = await context.new_page()
            all_pages_data = []
            current_page = 1
            current_url = base_url

            try:
                while current_page <= max_pages:
                    logger.info(f"Scraping page {current_page}: {current_url}")
                    await page.goto(current_url, timeout=self.timeout, wait_until='domcontentloaded')
                    await page.wait_for_load_state('networkidle')
                    await self._scroll_page_for_lazy_loading(page)
                    await self._dismiss_common_popups(page)

                    container_selector = config.get("container_selector", "body")
                    await page.wait_for_selector(container_selector, timeout=10000)
                    html_content = await page.inner_html(container_selector)

                    all_pages_data.append({
                        "page": current_page,
                        "url": current_url,
                        "html_content": html_content
                    })

                    next_page_selector = config.get("next_page_selector", ".next, .pagination a.next")
                    next_button = await page.query_selector(next_page_selector)
                    if not next_button or await next_button.get_attribute("disabled"):
                        logger.info(f"No more pages after {current_page}")
                        break

                    next_url = await next_button.get_attribute("href") or page.url
                    current_url = urljoin(base_url, next_url) if next_url.startswith('/') else next_url
                    current_page += 1

                return all_pages_data
            except Exception as e:
                logger.error(f"Error scraping paginated listings: {str(e)}")
                return all_pages_data
            finally:
                await browser.close()

    async def scrape_job_listings_with_details(self, url: str, config: Dict, batch_size: int = 3, max_jobs: int = 30) -> List[Dict]:
        """Scrape job listings and their details, with click simulation and JSON extraction."""
        logger.info(f"Scraping job listings with details from: {url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless, proxy=await self._get_proxy())
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            list_page = await context.new_page()

            try:
                await list_page.goto(url, timeout=self.timeout, wait_until='domcontentloaded')
                await list_page.wait_for_load_state('networkidle')
                await self._scroll_page_for_lazy_loading(list_page)
                await self._dismiss_common_popups(list_page)

                # Validate config selectors
                await self._validate_config_selectors(list_page, config)

                container_selector = config.get("container_selector", "body")
                await list_page.wait_for_selector(container_selector, timeout=15000)

                job_links_selector = f"{container_selector} {config.get('url', {}).get('selector', 'a[href]')}"
                job_links = await list_page.query_selector_all(job_links_selector)
                job_links = job_links[:max_jobs]

                jobs_basic_info = []
                for link in job_links:
                    job_info = await self._extract_basic_info(link, config, url)
                    href = job_info.get("detail_url")

                    # Simulate click if no href is found (e.g., modal-based sites)
                    if not href:
                        logger.info("No href found, simulating click on listing item")
                        try:
                            await link.click()
                            await list_page.wait_for_timeout(2000)  # Wait for modal/content to load
                            description = await list_page.text_content(config.get("description_selector", "body"))
                            if description and len(description.strip()) > 50:
                                job_info["description"] = description.strip()
                            else:
                                # Try JSON extraction as a fallback
                                description = await self._extract_from_json(list_page)
                                job_info["description"] = description or ""
                        except Exception as e:
                            logger.warning(f"Failed to extract description after click: {str(e)}")

                    if job_info.get("title"):  # Ensure basic info is valid
                        jobs_basic_info.append(job_info)

                complete_jobs = []
                for i in range(0, len(jobs_basic_info), batch_size):
                    batch = jobs_basic_info[i:i + batch_size]
                    tasks = [self._scrape_job_detail(context, job, config) for job in batch]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    complete_jobs.extend([r for r in results if not isinstance(r, Exception)])

                    await asyncio.sleep(2)  # Rate limiting

                logger.info(f"Scraped {len(complete_jobs)} jobs with details")
                return complete_jobs
            except Exception as e:
                logger.error(f"Error scraping job listings: {str(e)}")
                return []
            finally:
                await browser.close()

    async def _extract_basic_info(self, link: ElementHandle, config: Dict, base_url: str) -> Dict:
        """Extract basic job info from a listing link."""
        job_info = {}
        try:
            for field, rule in config.items():
                if field in ["site", "container_selector", "description_selector", "apply_selector"]:
                    continue
                selector = rule.get("selector")
                extract = rule.get("extract")
                if selector and extract:
                    element = await link.query_selector(selector) if selector != "self" else link
                    if element:
                        value = await element.get_attribute(extract) if extract != "text" else await element.text_content()
                        if value:
                            job_info[field] = value.strip()
            href = job_info.get("url", await link.get_attribute("href"))
            job_info["detail_url"] = urljoin(base_url, href) if href and href.startswith('/') else href
            return job_info
        except Exception as e:
            logger.error(f"Error extracting basic info: {str(e)}")
            return job_info

    async def _scrape_job_detail(self, context: BrowserContext, job_basic_info: Dict, config: Dict) -> Dict:
        """Scrape job details from a detail page."""
        detail_url = job_basic_info.get("detail_url")
        if not detail_url:
            return job_basic_info

        detail_page = await context.new_page()
        try:
            await detail_page.goto(detail_url, timeout=self.timeout, wait_until='domcontentloaded')
            await detail_page.wait_for_load_state('networkidle')
            await self._dismiss_common_popups(detail_page)

            job_detail = job_basic_info.copy()
            description_selector = config.get("description_selector")
            if description_selector:
                description = await self._extract_description(detail_page, description_selector)
                if description:
                    job_detail["description"] = description
                else:
                    # Fallback to JSON extraction if DOM scraping fails
                    description = await self._extract_from_json(detail_page)
                    job_detail["description"] = description or job_detail.get("description", "")

            apply_selector = config.get("apply_selector")
            if apply_selector:
                apply_url = await self._extract_apply_url(detail_page, apply_selector, detail_url)
                job_detail["apply_url"] = apply_url

            return job_detail
        except Exception as e:
            logger.error(f"Error scraping job detail from {detail_url}: {str(e)}")
            return job_basic_info
        finally:
            await detail_page.close()

    async def _extract_description(self, page: Page, selector: str) -> str:
        """Extract job description with fallback."""
        try:
            await page.wait_for_selector(selector, timeout=10000)
            description = await page.text_content(selector)
            if description and len(description.strip()) > 50:
                return description.strip()
            logger.info(f"Description too short or empty with selector {selector}, trying common selectors")
            return await self._try_common_description_selectors(page)
        except Exception as e:
            logger.warning(f"Failed to extract description with selector {selector}: {str(e)}")
            return await self._try_common_description_selectors(page)

    async def _try_common_description_selectors(self, page: Page) -> str:
        """Try common selectors for job descriptions when primary selector fails."""
        common_description_selectors = [
            ".job-description", "#job-description",
            ".description", "#description",
            ".job-details", ".job-content",
            "article.job", ".jobDetailsSection",
            ".main-content", ".content",
            ".position-details > .row"
        ]
        
        for selector in common_description_selectors:
            try:
                description_element = await page.query_selector(selector)
                if description_element:
                    text = await description_element.text_content()
                    if text and len(text.strip()) > 50:
                        logger.info(f"Found job description with common selector: {selector}")
                        return text.strip()
            except Exception:
                continue
        
        logger.warning("No substantial description found with common selectors")
        return ""

    async def _extract_from_json(self, page: Page) -> str:
        """Extract description from JSON data in script tags."""
        try:
            json_data = await page.evaluate("""() => {
                const scripts = Array.from(document.querySelectorAll('script[type="application/json"], script'));
                for (let script of scripts) {
                    try {
                        const content = script.textContent;
                        const json = JSON.parse(content);
                        if (json && typeof json === 'object') {
                            const findDescription = (obj) => {
                                for (let key in obj) {
                                    if (typeof obj[key] === 'string' && 
                                        (key.toLowerCase().includes('description') || 
                                         key.toLowerCase().includes('content')) && 
                                        obj[key].length > 50) {
                                        return obj[key];
                                    }
                                    if (typeof obj[key] === 'object' && obj[key]) {
                                        const nested = findDescription(obj[key]);
                                        if (nested) return nested;
                                    }
                                }
                            };
                            const desc = findDescription(json);
                            if (desc) return desc;
                        }
                    } catch (e) {
                        continue;
                    }
                }
                return '';
            }""")
            if json_data:
                logger.info("Extracted description from JSON data")
                return json_data.strip()
            return ""
        except Exception as e:
            logger.warning(f"Failed to extract description from JSON: {str(e)}")
            return ""

    async def _extract_apply_url(self, page: Page, selector: str, fallback_url: str) -> str:
        """Extract apply URL with improved logic."""
        try:
            apply_element = await page.query_selector(selector)
            if apply_element:
                href = await apply_element.get_attribute("href")
                return urljoin(page.url, href) if href else page.url
            return fallback_url
        except Exception:
            return fallback_url

    async def _scroll_page_for_lazy_loading(self, page: Page, scroll_delay: int = 1000, max_scrolls: int = 10):
        """Scroll page to load dynamic content."""
        for _ in range(max_scrolls):
            prev_height = await page.evaluate('document.documentElement.scrollHeight')
            await page.evaluate('window.scrollBy(0, window.innerHeight)')
            await page.wait_for_timeout(scroll_delay)
            if prev_height == await page.evaluate('document.documentElement.scrollHeight'):
                break

    async def _dismiss_common_popups(self, page: Page):
        """Dismiss popups with improved selector list."""
        popup_selectors = [
            'button[id*="accept"]', 'button[class*="accept"]', 'button:has-text("Accept")',
            '.cookie-banner button', '#cookie-consent button', 'button:has-text(" Agree")'
        ]
        for selector in popup_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await page.click(selector, timeout=2000)
                    await page.wait_for_timeout(1000)
                    break
            except Exception:
                continue

    async def _validate_config_selectors(self, page: Page, config: Dict):
        """Validate and log the effectiveness of config selectors."""
        for field, rule in config.items():
            if isinstance(rule, dict) and "selector" in rule:
                selector = rule["selector"]
                try:
                    element = await page.query_selector(selector)
                    if element:
                        logger.info(f"Selector validated for {field}: {selector}")
                    else:
                        logger.warning(f"Selector not found for {field}: {selector}")
                except Exception as e:
                    logger.error(f"Error validating selector for {field}: {selector} - {str(e)}")

    async def check_job_active(self, job_url: str, inactive_indicators: List[str] = None) -> bool:
        """Check if a job is active."""
        inactive_indicators = inactive_indicators or [
            "position has been filled", "job is no longer available", "position is closed"
        ]
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless, proxy=await self._get_proxy())
            page = await browser.new_context().new_page()
            try:
                response = await page.goto(job_url, timeout=self.timeout, wait_until='domcontentloaded')
                if not response.ok:
                    return False
                await page.wait_for_load_state('networkidle')
                text_content = await page.text_content('body')
                return not any(indicator.lower() in text_content.lower() for indicator in inactive_indicators)
            except Exception:
                return False
            finally:
                await browser.close()