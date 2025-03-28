from flask import Flask
from .auth import auth_bp
from .payment import payment_bp

def register_routes(app: Flask):
    """Register all routes (Blueprints) in the app"""
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(payment_bp,url_prefix="/payment")