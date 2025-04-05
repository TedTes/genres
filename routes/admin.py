from flask import Blueprint, render_template, request
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from models import Job, ScraperRun
from db import db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/job-scraper')
def job_scraper_dashboard():
    """Admin dashboard for job scraper statistics"""
    # Get basic job stats
    total_jobs = Job.query.count()
    jobs_by_source = db.session.query(
        Job.source, func.count(Job.id).label('count')
    ).group_by(Job.source).all()
    
    # Recent jobs
    recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(20).all()
    
    # Daily job counts for last 14 days
    two_weeks_ago = datetime.utcnow() - timedelta(days=14)
    daily_counts = db.session.query(
        func.date(Job.created_at).label('date'),
        func.count(Job.id).label('count')
    ).filter(Job.created_at >= two_weeks_ago).group_by(
        func.date(Job.created_at)
    ).order_by(func.date(Job.created_at).desc()).all()
    
    # Recent scraper runs
    recent_runs = ScraperRun.query.order_by(
        ScraperRun.start_time.desc()
    ).limit(50).all()
    
    # Scraper success rate
    success_rate = db.session.query(
        ScraperRun.source,
        func.count(ScraperRun.id).label('total'),
        func.sum(
            case([(ScraperRun.status == 'success', 1)], else_=0)
        ).label('success')
    ).group_by(ScraperRun.source).all()
    
    return render_template(
        'admin/job_scraper.html',
        total_jobs=total_jobs,
        jobs_by_source=jobs_by_source,
        recent_jobs=recent_jobs,
        daily_counts=daily_counts,
        recent_runs=recent_runs,
        success_rate=success_rate
    )

# Add more admin routes for manual triggering, etc.