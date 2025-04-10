# ResumeMatch

ResumeMatch is an AI-powered resume builder that helps job seekers create professional, ATS-optimized resumes tailored to specific job listings with intelligent skills matching.

## Features

- **AI-powered resume creation**: Generate professional resumes with optimal formatting and content
- **Job-specific tailoring**: Customize your resume to match specific job listings
- **ATS optimization**: Create resumes that pass through Applicant Tracking Systems
- **Skills matching**: Automatically identify and highlight relevant skills for job positions
- **Multiple templates**: Choose from various professional resume templates
- **Job search**: Browse job listings and create tailored resumes for each position
- **Application tracking**: Track your job applications and their statuses
- **PDF download**: Export your resume as a PDF ready for submission

## Tech Stack

- **Backend**: Python/Flask
- **Database**: PostgreSQL (with SQLAlchemy ORM)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Flask-Login
- **Form Handling**: WTForms
- **PDF Generation**: WeasyPrint
- **Job Scraping**: PlayWright, BeautifulSoup
- **NLP**: spaCy for skills extraction and matching
- **Payment Processing**: Stripe integration (with PayPal support)
- **Storage**: Supabase for file storage

## Project Structure

```
ResumeMatch/
├── app.py                  # Main application entry point
├── db.py                   # Database configuration
├── forms.py                # WTForms form definitions
├── models.py               # SQLAlchemy models
├── routes/                 # Route handlers
│   ├── admin.py            # Admin dashboard routes
│   ├── application.py      # Job application tracking routes
│   ├── auth.py             # Authentication routes
│   ├── job.py              # Job listing and search routes
│   ├── payment.py          # Payment processing routes
│   ├── resume.py           # Resume creation/editing routes
│   └── root.py             # Home and dashboard routes
├── helpers/                # Helper functions
│   ├── job_helper.py       # Job data processing helpers
│   ├── resume_helper.py    # Resume generation helpers
│   ├── layouts_helper.py   # Resume layout definitions
│   └── themes_helper.py    # Resume theme definitions
├── services/               # Business logic services
│   ├── job_service.py      # Job-related business logic
│   ├── subscription_service.py # Subscription management
│   └── scraper/            # Job scraping functionality
│       ├── web_scraper.py  # Web scraping using PlayWright
│       ├── parser.py       # HTML parsing with BeautifulSoup
│       └── data_aggregator.py # Combines scraped data
├── pages/                  # HTML templates
│   ├── base.html           # Base template with common structure
│   ├── home.html           # Landing page
│   ├── dashboard.html      # User dashboard
│   ├── jobs.html           # Job search page
│   ├── job_detail.html     # Individual job listing
│   └── resume_*.html       # Various resume creation forms
├── static/                 # Static assets (CSS, JS, images)
└── payments/               # Payment gateway implementations
    ├── base.py             # Abstract payment gateway
    ├── stripe_gateway.py   # Stripe integration
    └── paypal_gateway.py   # PayPal integration
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL
- Node.js and npm (for frontend development)

### Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/resumematch.git
   cd resumematch
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables in a `.env` file:
   ```
   DATABASE_URL=postgresql://username:password@localhost/resumematch
   SECRET_KEY=your_secret_key
   STRIPE_SECRET_KEY=your_stripe_secret_key
   STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

5. Initialize the database:
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

### Running the Application

1. Start the Flask development server:
   ```bash
   flask run
   ```

2. Visit `http://localhost:5000` in your browser

## Subscription Plans

ResumeMatch offers the following subscription options:

- **Free Plan**: Basic features with limited templates
- **3-Month Plan**: $30 (Premium features for 3 months)
- **6-Month Plan**: $48 (Premium features for 6 months)
- **Annual Plan**: $80 (Premium features for 12 months)

## Resume Templates

The application includes multiple professional resume templates:

- Classic
- Modern
- Sidebar
- Minimalist
- Professional
- Timeline
- Cards
- Grid
- Portfolio
- Compact

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Open a pull request
