
import time
from flask import current_app

class PaymentMetrics:
    @staticmethod
    def record_checkout_attempt(gateway_type, success):
        """Record a checkout attempt metric."""
        #TODO: In production, send to monitoring system (Prometheus, DataDog, etc.)
        current_app.logger.info(f"METRIC: checkout_attempt gateway={gateway_type} success={success}")
    
    @staticmethod
    def time_operation(operation_name):
        """Decorator to time payment operations."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                current_app.logger.info(f"METRIC: payment_operation operation={operation_name} duration_ms={duration*1000:.2f}")
                return result
            return wrapper
        return decorator