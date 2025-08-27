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
