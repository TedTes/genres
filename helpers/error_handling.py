from typing import Dict,Any,Tuple

def handle_optimization_error(error: Exception, context: str = "optimization") -> Tuple[Dict[str, Any], int]:
    """
    Handle optimization errors with appropriate user messages and status codes.
    
    Args:
        error: The exception that occurred
        context: Context where error occurred
        
    Returns:
        Tuple of (error_response_dict, http_status_code)
    """
    
    error_id = f"err_{int(time.time())}_{hash(str(error)) % 10000}"
    
    # Log full error details for debugging
    print(f"🔥 Error {error_id} in {context}: {str(error)}")
    print(f"🔍 Traceback: {traceback.format_exc()}")
    
    # Categorize error types
    if isinstance(error, ValueError):
        return _handle_validation_error(error, error_id)
    elif isinstance(error, ConnectionError):
        return _handle_connection_error(error, error_id)
    elif isinstance(error, TimeoutError):
        return _handle_timeout_error(error, error_id)
    elif "rate limit" in str(error).lower():
        return _handle_rate_limit_error(error, error_id)
    elif "api" in str(error).lower() and ("key" in str(error).lower() or "auth" in str(error).lower()):
        return _handle_api_auth_error(error, error_id)
    else:
        return _handle_generic_error(error, error_id)


def _handle_validation_error(error: Exception, error_id: str) -> Tuple[Dict[str, Any], int]:
    """Handle validation errors (400 status)."""
    
    return {
        'error': 'Input Validation Error',
        'message': str(error),
        'error_id': error_id,
        'category': 'validation',
        'suggested_actions': [
            'Check that your resume contains standard sections (experience, skills, etc.)',
            'Ensure file is not corrupted or empty',
            'Try using plain text instead of file upload'
        ]
    }, 400


def _handle_connection_error(error: Exception, error_id: str) -> Tuple[Dict[str, Any], int]:
    """Handle connection errors (503 status)."""
    
    return {
        'error': 'Service Connection Error',
        'message': 'Unable to connect to AI optimization service. Please try again in a moment.',
        'error_id': error_id,
        'category': 'connection',
        'retry_recommended': True,
        'retry_delay_seconds': 30
    }, 503


def _handle_timeout_error(error: Exception, error_id: str) -> Tuple[Dict[str, Any], int]:
    """Handle timeout errors (408 status)."""
    
    return {
        'error': 'Request Timeout',
        'message': 'Optimization is taking longer than expected. Please try again with a shorter resume.',
        'error_id': error_id,
        'category': 'timeout',
        'retry_recommended': True,
        'suggested_actions': [
            'Try shortening your resume content',
            'Use simpler job description',
            'Check your internet connection stability'
        ]
    }, 408


def _handle_rate_limit_error(error: Exception, error_id: str) -> Tuple[Dict[str, Any], int]:
    """Handle rate limiting errors (429 status)."""
    
    return {
        'error': 'Rate Limit Exceeded',
        'message': 'You\'ve reached the optimization limit. Please try again later.',
        'error_id': error_id,
        'category': 'rate_limit',
        'retry_recommended': True,
        'retry_after_seconds': 3600,
        'suggested_actions': [
            'Wait an hour before trying again',
            'Consider upgrading to premium for higher limits'
        ]
    }, 429


def _handle_api_auth_error(error: Exception, error_id: str) -> Tuple[Dict[str, Any], int]:
    """Handle API authentication errors (502 status)."""
    
    return {
        'error': 'AI Service Unavailable',
        'message': 'AI optimization service is temporarily unavailable. Please try again later.',
        'error_id': error_id,
        'category': 'service_unavailable',
        'retry_recommended': True,
        'retry_delay_seconds': 300  # 5 minutes
    }, 502


def _handle_generic_error(error: Exception, error_id: str) -> Tuple[Dict[str, Any], int]:
    """Handle generic errors (500 status)."""
    
    return {
        'error': 'Internal Processing Error',
        'message': 'An unexpected error occurred during optimization. Please try again.',
        'error_id': error_id,
        'category': 'internal',
        'retry_recommended': True,
        'suggested_actions': [
            'Try again with the same input',
            'If problem persists, try with a different resume format',
            'Contact support if errors continue'
        ]
    }, 500




# Add CSRF token endpoint for frontend
@optimizer_bp.route('/csrf-token', methods=['GET'])
def get_csrf_token():
    """Get CSRF token for form submissions."""
    try:
        # Generate or get CSRF token
        from flask_wtf.csrf import generate_csrf
        token = generate_csrf()
        return jsonify({'csrf_token': token}), 200
    except:
        # Fallback if CSRF is not configured
        return jsonify({'csrf_token': 'not-required'}), 200


@optimizer_bp.errorhandler(400)
def handle_bad_request(error):
    """Handle bad request errors."""
    return jsonify({
        'error': 'Bad Request',
        'message': 'Invalid request format or missing required fields',
        'status_code': 400
    }), 400


@optimizer_bp.errorhandler(429)
def handle_rate_limit(error):
    """Handle rate limit errors."""
    return jsonify({
        'error': 'Rate Limit Exceeded',
        'message': 'Too many requests. Please try again later.',
        'status_code': 429,
        'retry_after': 3600  # 1 hour
    }), 429


@optimizer_bp.errorhandler(500)
def handle_internal_error(error):
    """Handle internal server errors."""
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'Resume optimization service encountered an error',
        'status_code': 500
    }), 500