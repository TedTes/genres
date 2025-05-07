from flask import Flask
from .auth import auth_bp
from .payment import payment_bp
from .root import root_bp
from .job import job_bp
from .resume import resume_bp
from .application import application_bp
from .admin import admin_bp
from .resume_llm import resume_llm_bp

def register_routes(app: Flask):
    """Register all routes (Blueprints) in the app"""
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(payment_bp,url_prefix="/api/v1/payment")
    app.register_blueprint(root_bp)
    app.register_blueprint(job_bp,url_prefix="/api/v1/job")
    app.register_blueprint(resume_bp,url_prefix="/api/v1/resume")
    app.register_blueprint(application_bp,url_prefix="/api/v1/application")
    app.register_blueprint(admin_bp,url_prefix="/api/v1/admin")
    app.register_blueprint(resume_llm_bp, url_prefix="/api/v1/resume/llm")