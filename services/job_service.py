from datetime import datetime, timezone
from sqlalchemy import or_, and_
from models import Job
from db import db
from helpers.job_helper import extract_job_tags
from utils.date import format_job_posted_date
class JobService:
    """Service class for handling job-related business logic"""
    
    def get_jobs(self, search_term=None, location=None, remote_only=False):
        """
        Fetch jobs from database with optional filters
        
        Args:
            search_term (str, optional): Term to search in title, description, company
            location (str, optional): Location filter
            remote_only (bool, optional): Filter for remote jobs only
            
        Returns:
            list: List of Job objects
        """
        query = db.session.query(Job)
        
        # Apply filters if provided
        if search_term:
            search_filter = or_(
                Job.title.ilike(f'%{search_term}%'),
                Job.description.ilike(f'%{search_term}%'),
                Job.company.ilike(f'%{search_term}%')
            )
            query = query.filter(search_filter)
        
        if location:
            query = query.filter(Job.location.ilike(f'%{location}%'))
        
        if remote_only:
            query = query.filter(Job.remote.is_(True))
        
        # Order by most recent
        # query = query.order_by(Job.created_at.desc())
        
        return query.all()
    
    def get_job_by_id(self, job_id):
        """
        Fetch a specific job by ID
        
        Args:
            job_id: The ID of the job to fetch
            
        Returns:
            Job: Job object if found, None otherwise
        """
        return db.session.query(Job).filter(Job.id == job_id).first()
    
    def get_job_by_slug(self, slug):
        """
        Fetch a specific job by slug
        
        Args:
            slug: The slug of the job to fetch
            
        Returns:
            Job: Job object if found, None otherwise
        """
        return db.session.query(Job).filter(Job.slug == slug).first()
    
    
    
    def find_similar_jobs(self, job_id, limit=3):
        """
        Find jobs similar to the specified job
        
        Args:
            job_id: ID of the reference job
            limit: Maximum number of similar jobs to return
            
        Returns:
            list: List of similar Job objects
        """
        # Get the reference job
        reference_job = self.get_job_by_id(job_id)
        
        if not reference_job:
            return []
        
        # Get all jobs except the reference job
        all_jobs = db.session.query(Job).filter(Job.id != job_id).all()
        
        # Extract skills from the reference job
        reference_skills = extract_job_tags(reference_job.title, reference_job.description)
        
        # Calculate similarity score for each job
        job_scores = []
        for job in all_jobs:
            job_skills = extract_job_tags(job.title, job.description)
            
            # Calculate score based on common skills
            common_skills = set(reference_skills) & set(job_skills)
            score = len(common_skills)
            
            # Add location bonus if locations match
            if job.location and reference_job.location and job.location.lower() == reference_job.location.lower():
                score += 2
                
            job_scores.append((job, score))
        
        # Sort by score and get top matches
        job_scores.sort(key=lambda x: x[1], reverse=True)
        similar_jobs = [job for job, score in job_scores[:limit]]
        
        return similar_jobs