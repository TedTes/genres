from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from db import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    resumes = db.relationship('Resume', backref='user', lazy=True)
    verified = db.Column(db.Boolean, default=False)
    verification_sent_at = db.Column(db.DateTime, nullable=True)

    subscriptions = db.relationship('Subscription', backref='user', lazy=True)
    
    @property
    def active_subscription(self):
        """Get the user's active subscription, if any."""
        return Subscription.query.filter_by(
            user_id=self.id, 
            status='active'
        ).first()
    
    @property
    def is_premium(self):
        """Check if the user has an active premium subscription."""
        return self.active_subscription is not None

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)  # From Arbeitnow API
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    description = db.Column(db.Text)
    posted_at = db.Column(db.DateTime)
    resumes = db.relationship('Resume', back_populates='job', lazy=True)
    remote = db.Column(db.Boolean, default=False)
    #scraper-specific fields:
    source = db.Column(db.String(50), nullable=True)
    source_job_id = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    url = db.Column(db.String(50), nullable=True)

# Update the Resume model in models.py

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=True)  # Changed to nullable
    title = db.Column(db.String(200), nullable=False, default="Untitled Resume")
    resume_data = db.Column(db.JSON)  # Stores resume sections as JSON
    template = db.Column(db.String(50), default="1")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Make the job relationship optional
    job = db.relationship('Job', back_populates='resumes', lazy=True, foreign_keys=[job_id])

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey('resume.id'), nullable=True)
    status = db.Column(db.String(50), default='applied')  # applied, interviewing, offered, rejected, accepted
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('applications', lazy=True))
    job = db.relationship('Job', backref=db.backref('applications', lazy=True))
    resume = db.relationship('Resume', backref=db.backref('applications', lazy=True))
    
    def __repr__(self):
        return f'<Application {self.id} - {self.job.title if self.job else "Unknown Job"}>'

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Payment gateway details
    gateway_type = db.Column(db.String(50), nullable=False, default='stripe')
    gateway_customer_id = db.Column(db.String(255))
    gateway_subscription_id = db.Column(db.String(255))
    
    # Subscription details
    plan_id = db.Column(db.String(50), nullable=False)  # '3month', '6month', 'annual'
    status = db.Column(db.String(50), default='pending')  # 'active', 'canceled', 'past_due'
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    
    # Additional info
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Subscription {self.id} for User {self.user_id} ({self.plan_id})>'

class ScraperRun(db.Model):
    """Track individual scraper runs for monitoring"""
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20))  # success, failed, partial
    jobs_found = db.Column(db.Integer, default=0)
    jobs_added = db.Column(db.Integer, default=0)
    keywords = db.Column(db.String(255))
    location = db.Column(db.String(255))
    error_message = db.Column(db.Text)