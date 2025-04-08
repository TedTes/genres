from bs4 import BeautifulSoup

def parse_job(config, job_block):
    """Parse a single job block from a pre-parsed BeautifulSoup element."""
    job_data = {}
    for field, rule in config.items():
        if field == "site" or field == "container_selector":
            continue
        if isinstance(rule, dict):
            selector = rule.get("selector")
            extract = rule.get("extract")
            multiple = rule.get("multiple", False)
            post_process = rule.get("post_process")
            if selector == "self":  # Use the root element of the block
                if extract in job_block.attrs:
                    value = job_block[extract]
                    if post_process:
                        if post_process == "split('/')[-1]":
                            value = value.split('/')[-1]
                        elif post_process == "split()[-1]":
                            value = value.split()[-1]
                        elif post_process == "split('_')[-1]":
                            value = value.split('_')[-1]
                        elif post_process == "split('-')[-1]":
                            value = value.split('-')[-1]
                    job_data[field] = value
                else:
                    job_data[field] = "N/A"
            elif multiple:
                elements = job_block.select(selector)
                values = [el.get_text(strip=True) if extract == "text" else el[extract] for el in elements]
                job_data[field] = ", ".join(values) if values else "N/A"
            elif selector:
                element = job_block.select_one(selector)
                if element:
                    value = element.get_text(strip=True) if extract == "text" else element[extract]
                    if post_process:
                        if post_process == "split('/')[-1]":
                            value = value.split('/')[-1]
                        elif post_process == "split()[-1]":
                            value = value.split()[-1]
                        elif post_process == "split('_')[-1]":
                            value = value.split('_')[-1]
                        elif post_process == "split('-')[-1]":
                            value = value.split('-')[-1]
                    job_data[field] = value
                else:
                    job_data[field] = "N/A"
            else:
                job_data[field] = rule.get("value", "N/A")
        else:
            job_data[field] = "N/A"
    return job_data

def parse_jobs(config, html):
    """
    Parse multiple job blocks from a flat HTML string (e.g., <li>...</li><li>...</li>).
    
    Args:
        config (dict): Config for one company, container_selector unused in parsing
        html (str): Flat string of job blocks from WebScraper
    
    Returns:
        list: List of parsed job dictionaries
    """
    if not html.strip():
        return []

    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all top-level elements (e.g., <li>, <div>, <article>) in the flat string
    job_blocks = [child for child in soup.children if child.name]  # Filter out text nodes
    
    if not job_blocks:
        return []
    
    return [parse_job(config, block) for block in job_blocks]