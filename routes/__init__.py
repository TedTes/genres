from flask import Flask
from .auth import auth_bp
from .payment import payment_bp
from .root import root_bp
from .job import job_bp
from .resume import resume_bp
from .application import application_bp


def register_routes(app: Flask):
    """Register all routes (Blueprints) in the app"""
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(payment_bp,url_prefix="/payment")
    app.register_blueprint(root_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(application_bp)