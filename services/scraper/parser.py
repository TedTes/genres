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
    Parse multiple job blocks from a single HTML string.
    
    Args:
        config (dict): Config for one company, including container_selector
        html (str): Single HTML string with job blocks one after another
    
    Returns:
        list: List of parsed job dictionaries
    """
    if "container_selector" not in config:
        raise ValueError("container_selector must be provided in config")
    
    soup = BeautifulSoup(html, 'html.parser')
    job_blocks = soup.select(config["container_selector"])
    if not job_blocks:
        return []  # No jobs found
    
    return [parse_job(config, block) for block in job_blocks]