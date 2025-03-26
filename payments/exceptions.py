class PaymentError(Exception):
    """Base class for payment-related exceptions."""
    pass

class GatewayConnectionError(PaymentError):
    """Error connecting to payment gateway."""
    pass

class PaymentDeclinedError(PaymentError):
    """Payment was declined."""
    pass

class SubscriptionCreationError(PaymentError):
    """Error creating subscription."""
    pass