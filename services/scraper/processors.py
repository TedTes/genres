from slugify import slugify
from datetime import datetime
from app import db
from models import Job

class JobProcessor:
    """Process scraped job data and save to database"""
    
    @staticmethod
    def process_jobs(jobs, scraper_instance):
        """Process multiple jobs and save to database"""
        saved_count = 0
        
        for job in jobs:
            try:
                normalized_job = scraper_instance._normalize_job_data(job)
                if JobProcessor.save_job(normalized_job):
                    saved_count += 1
            except Exception as e:
                print(f"Error processing job: {str(e)}")
        
        # Update scraper run record
        if scraper_instance.scraper_run:
            scraper_instance.scraper_run.jobs_added = saved_count
            db.session.commit()
            
        return saved_count
    
    @staticmethod
    def save_job(job_data):
        """Save a single normalized job to database"""
        # Check for duplicates
        existing_job = Job.query.filter_by(
            source=job_data['source'],
            source_job_id=job_data['source_job_id']
        ).first()
        
        if existing_job:
            # Update last_seen timestamp
            existing_job.last_seen = datetime.utcnow()
            db.session.commit()
            return False
            
        # Create slug
        base_slug = slugify(f"{job_data['title']}-{job_data['company_name']}")
        slug = base_slug
        counter = 1
        
        while Job.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        # Create new job
        new_job = Job(
            title=job_data['title'],
            company_name=job_data['company_name'],
            location=job_data['location'],
            description=job_data['description'],
            remote=job_data['remote'],
            apply_url=job_data['apply_url'],
            source=job_data['source'],
            source_job_id=job_data['source_job_id'],
            tags=job_data['tags'],
            slug=slug,
            created_at=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        
        db.session.add(new_job)
        db.session.commit()
        return True