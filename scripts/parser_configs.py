configs = {
    "h-depo": {
        "site": "https://careers.homedepot.ca/job-search",
        "container_selector": ".jobs-content",
        "url": {"selector": "a[href]", "extract": "href"},
        "title": {"selector": ".job-data h3", "extract": "text"},
        "company": {"selector": ".job-logo img[alt]", "extract": "alt"},
        "location": {"selector": ".job-data h4", "extract": "text"},
        "job_id": {"selector": ".listing-attributes .job-attribute:nth-child(1)", "extract": "text"},
        "type": {"selector": ".listing-attributes .job-attribute:nth-child(2)", "extract": "text"},
        "description_selector": ".job-detail",
        "apply_selector": ".applyNowBtn"
    },
    "s-buck": {
        "site": "https://starbucks.eightfold.ai/careers",
        "container_selector": "div[role='list']",
        "url": {"selector": "a[href]", "extract": "href"},
        "title": {"selector": ".position-title", "extract": "text"},
        "company": {"value": "Starbucks"},
        "location": {"selector": ".position-location", "extract": "text"},
        "job_id": {"value": None},
        "type": {"selector": ".position-priority-container", "extract": "text"},
        "description_selector": ".position-details > .row",  # Fixed selector
        "apply_selector": "button[type='button']"  # Try a common apply button selector
    },
    "w-mart": {
        "site": "https://careers.walmart.ca/search-jobs",
        "container_selector": "#search-results-list > ul",
        "url": {"selector": "a[href]", "extract": "href"},
        "title": {"selector": "h2", "extract": "text"},
        "company": {"value": "Walmart"},
        "location": {"selector": ".job-location", "extract": "text", "multiple": True},
        "job_id": {"selector": "self", "extract": "data-job-id"},
        "type": {"selector": ".job-info.job-category", "extract": "text"},
        "description_selector": ".job-description",  # Simplified selector
        "apply_selector": ".job-apply"  # Simplified selector
    },
    "l-law": {
        "site": "https://careers.loblaw.ca/jobs",
        "container_selector": ".results-list.front",
        "url": {"selector": ".results-list__item-title[href]", "extract": "href"},
        "title": {"selector": ".results-list__item-title span", "extract": "text"},
        "company": {"selector": ".results-list__item-brand--label", "extract": "text"},
        "location": {"selector": ".results-list__item-street--label", "extract": "text"},
        "job_id": {"selector": "self", "extract": "data-testid", "post_process": "split('_')[-1]"},
        "description_selector": ".main-content",
        "apply_selector": ".apply-button, button[type='submit']"  # Try common apply buttons
    },
    "m-don": {
        "site": "https://careers.mcdonalds.ca/restaurant-jobs",
        "container_selector": ".results-list.front",
        "url": {"selector": ".results-list__item-title[href]", "extract": "href"},
        "title": {"selector": ".results-list__item-title span", "extract": "text"},
        "company": {"selector": ".results-list__item-brand--label", "extract": "text"},
        "location": {"selector": ".results-list__item-street--label", "extract": "text"},
        "job_id": {"selector": ".results-list__item-title[href]", "extract": "href", "post_process": "split('/')[-1]"},
        "description_selector": ".content",
        "apply_selector": ".apply-now, .apply-button"  # Try common apply buttons
    },
     "t-hort": {
        "site": "https://app.higherme.com/careers/58bd9e7f472bd?langCode=en",
        "container_selector": "div[class='hCXxvRc89YBhPXkzL9Wl'] > div",
        "url": {"selector": "button.sc-jbAkgO[href]", "extract": "href"},
        "title": {"selector": "h1.sc-gjcoXW", "extract": "text"},
        "company": {"value": "Tim Hortons"},
        "location": {"selector": ".e5KiSkcjp_YiIIkHDmU3", "extract": "text"},
        "job_id": {"value": None},
        "type": {"selector": ".sc-ezeoWd span", "extract": "text", "multiple": True},
        "description_selector" :".oz62RleGS6_qRlv03AmQ",
        "apply_selector": "sc-jbAkgO.hQrdnR"
    }
}