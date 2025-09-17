from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from db import db
from sqlalchemy.dialects.postgresql import ARRAY,JSONB

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)

    name = db.Column(db.String(100), nullable=True) 
    phone = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    linkedin = db.Column(db.String(200), nullable=True)
    github = db.Column(db.String(200), nullable=True)
    website = db.Column(db.String(200), nullable=True)
 
    verified = db.Column(db.Boolean, default=False)
    verification_sent_at = db.Column(db.DateTime, nullable=True)
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)
    optimization_count = db.Column(db.Integer, default=0)
    last_optimization_at = db.Column(db.DateTime)

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

class ResumeOptimization(db.Model):
    __tablename__ = 'resume_optimizations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey('resume.id'), nullable=False)
    
    # Input data
    original_resume_data = db.Column(db.JSON)
    job_description = db.Column(db.Text)
    job_title = db.Column(db.String(200))
    company_name = db.Column(db.String(200))
    
    # Optimization settings
    optimization_style = db.Column(db.String(50), default='balanced')
    
    # Results
    optimized_resume_data = db.Column(db.JSON)
    match_score_before = db.Column(db.Float)
    match_score_after = db.Column(db.Float)
    missing_keywords = db.Column(db.JSON)
    added_keywords = db.Column(db.JSON)
    
    # Files
    docx_url = db.Column(db.String(500))
    pdf_url = db.Column(db.String(500))
    
    # Processing info
    processing_time_ms = db.Column(db.Float)
    model_provider = db.Column(db.String(50))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        out = {}
        for col in self.__table__.columns:
            val = getattr(self, col.name)
            # Handle JSON stored as text (fallback)
            if isinstance(val, str):
                if (val.startswith("{") and val.endswith("}")) or (val.startswith("[") and val.endswith("]")):
                    try:
                        val = json.loads(val)
                    except Exception:
                        pass
            out[col.name] = val
        return out

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False, default="Untitled Resume")
    resume_data = db.Column(db.JSON)
    template = db.Column(db.String(50), default="professional_classic")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    is_optimized = db.Column(db.Boolean, default=False)
    last_optimized_at = db.Column(db.DateTime)


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
