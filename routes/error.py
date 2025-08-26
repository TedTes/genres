
from flask import Blueprint, render_template, request

error_bp = Blueprint('error', __name__)

@error_bp.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 errors with custom page"""
    return render_template('error.html', 
                         error_code='404',
                         error_message='The page you\'re looking for doesn\'t exist or may have been moved.'), 404

@error_bp.app_errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors with custom page"""
    return render_template('error.html', 
                         error_code='403',
                         error_message='You don\'t have permission to access this resource.'), 403

@error_bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 errors with custom page"""
    return render_template('error.html', 
                         error_code='500',
                         error_message='We\'re experiencing technical difficulties. Please try again later.'), 500

@error_bp.app_errorhandler(429)
def rate_limit_error(error):
    """Handle rate limiting errors"""
    return render_template('error.html',
                         error_code='429', 
                         error_message='Too many requests. Please slow down and try again.'), 429