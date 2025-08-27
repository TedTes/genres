from flask import Flask
from .auth import auth_bp
from .payment import payment_bp
from .root import root_bp



from .optimizer import optimizer_bp
from .error import error_bp

def register_routes(app: Flask):
    """Register all routes (Blueprints) in the app"""
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(payment_bp,url_prefix="/api/v1/payment")
    app.register_blueprint(root_bp)
 



    app.register_blueprint(optimizer_bp, url_prefix="/api/v1/resume/llm")
    app.register_blueprint(error_bp, url_prefix="/api/v1/error")