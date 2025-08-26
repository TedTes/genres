# ResumeMatch

ResumeMatch is an AI-powered resume optimization platform that helps job seekers create professional, ATS-optimized resumes tailored to specific job descriptions with intelligent skills matching and enhancement.

## Features

- **AI-powered resume optimization**: Generate professional resumes with optimal formatting, content enhancement, and keyword optimization
- **Job-specific tailoring**: Customize your resume to match specific job descriptions and requirements
- **ATS optimization**: Create resumes that pass through Applicant Tracking Systems with improved keyword matching
- **Skills gap analysis**: Automatically identify missing skills and optimize your resume content
- **Multiple templates**: Choose from various professional resume templates with modern designs
- **Resume enhancement**: Improve existing resumes with AI-powered content suggestions and optimization
- **Performance tracking**: Monitor your resume optimization success and improvement metrics
- **PDF & DOCX export**: Export your optimized resume in multiple formats ready for submission

## Tech Stack

- **Backend**: Python/Flask
- **Database**: PostgreSQL (with SQLAlchemy ORM)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Flask-Login
- **Form Handling**: WTForms
- **PDF Generation**: WeasyPrint
- **AI Integration**: OpenAI API for resume optimization
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
│   ├── application.py      # Application tracking routes
│   ├── auth.py             # Authentication routes
│   ├── resume.py           # Resume creation/editing/optimization routes
│   ├── payment.py          # Payment processing routes
│   └── root.py             # Home and dashboard routes
├── helpers/                # Helper functions
│   ├── resume_helper.py    # Resume generation and optimization helpers
│   ├── layouts_helper.py   # Resume layout definitions
│   └── themes_helper.py    # Resume theme definitions
├── services/               # Business logic services
│   ├── resume/             # Resume optimization services
│   │   ├── optimizer.py    # AI-powered resume optimization
│   │   ├── analyzer.py     # Skills gap analysis
│   │   └── rewrite.py      # Content enhancement
│   └── subscription_service.py # Subscription management
├── pages/                  # HTML templates
│   ├── base.html           # Base template with common structure
│   ├── home.html           # Landing page
│   ├── dashboard.html      # User dashboard
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
   OPENAI_API_KEY=your_openai_api_key
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


