

def fetch_jobs(search_term=None, location=None, remote=None):
    url = "https://job-board.arbeitnow.com/api/jobs"  # Correct endpoint as per API docs ????
    params = {}
    if search_term:
        params['q'] = search_term
    if location:
        params['location'] = location
    if remote is not None:
        params['remote'] = 'true' if remote else 'false'
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()['data']
    except requests.RequestException:
        flash('Error fetching jobs from API.', 'danger')
        return []



def analyze_job_description(description):
    doc = nlp(description)
    skills = [token.text for token in doc if token.pos_ in ['NOUN', 'PROPN']]
    return list(set(skills))  # Remove duplicates


# from weasyprint import HTML
# def generate_pdf(html_string):
#     html = HTML(string=html_string)
#     pdf = html.write_pdf()
#     return pdf