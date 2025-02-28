# ResumeMatch - Job-Tailored Resume Builder

ResumeMatch is a web application that helps job seekers create tailored resumes optimized for specific job listings. The application fetches real-time job listings, analyzes job descriptions to extract key skills, and guides users through creating professional resumes targeted to their desired positions.

## Features

- **Real-time Job Listings**: Browse jobs from the Arbeitnow API with filtering options for keywords, location, and remote work.
- **Job Analysis**: Automatically extract key skills and requirements from job descriptions using NLP.
- **Tailored Resume Creation**: Multi-step form process to create resumes specifically designed for individual job listings.
- **Skills Matching**: Compare your skills with job requirements to see how well you match with positions.
- **PDF Generation**: Download professionally formatted PDF resumes ready for submission.
- **User Dashboard**: Manage all your created resumes in one place.

## Technology Stack

- **Backend**: Flask web framework with Python
- **Database**: SQLAlchemy ORM with PostgreSQL (via Supabase)
- **Authentication**: Flask-Login for user management
- **Forms**: Flask-WTF for form handling and validation
- **API Integration**: Requests library for Arbeitnow API integration
- **Text Analysis**: spaCy for Natural Language Processing
- **PDF Generation**: WeasyPrint for converting HTML to PDF
- **Frontend**: HTML, CSS, JavaScript with responsive design

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/resume-matcher.git
   cd resume-matcher
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```
   # Create a .env file with the following variables
   FLASK_APP=app.py
   FLASK_ENV=development
   DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:6543/postgres
   FLASK_SECRET_KEY=[YOUR_SECRET_KEY]
   ```

5. Initialize the database:
   ```
   flask db upgrade
   ```

6. Run the application:
   ```
   flask run
   ```

## Project Structure

```
resume-matcher/
├── app.py              # Main application initialization
├── routes.py           # Route definitions
├── models.py           # Database models
├── forms.py            # Form definitions
├── static/             # Static assets
│   ├── css/            # CSS files
│   ├── js/             # JavaScript files
│   └── images/         # Image assets
├── templates/          # HTML templates
│   ├── base.html       # Base template
│   ├── home.html       # Landing page
│   ├── dashboard.html  # User dashboard
│   ├── jobs.html       # Job listings
│   ├── job_detail.html # Job details
│   └── resume/         # Resume creation templates
├── migrations/         # Database migrations
└── requirements.txt    # Dependencies
```

## Usage

1. Register a new account or log in to an existing account.
2. Browse jobs on the Jobs page, using filters to find relevant positions.
3. View job details to see the full job description and skills match.
4. Click "Create Resume" to start building a tailored resume for a specific job.
5. Follow the step-by-step form to enter your information.
6. Preview your resume and download the PDF.
7. Manage all your resumes from the Dashboard.

## API Integration

The application integrates with the Arbeitnow API to fetch real-time job listings. The API endpoint is:
```
https://www.arbeitnow.com/api/job-board-api
```

## Database 

The application uses PostgreSQL hosted on Supabase. The database schema includes these main tables:
- Users: Authentication and profile information
- Jobs: Cached job listings from the API
- Resumes: User-created resumes linked to jobs

## Future Enhancements

- Enhanced job matching algorithm
- Cover letter generation
- Application tracking system
- Email notifications
- Multiple resume templates
- Social media login integration

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.