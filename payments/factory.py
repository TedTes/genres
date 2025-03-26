from flask import current_app
from .stripe_gateway import StripeGateway
from .paypal_gateway import PayPalGateway

class PaymentGatewayFactory:
    """Factory for creating payment gateway instances."""
    
    @staticmethod
    def create(gateway_type=None):
        """Create and return a payment gateway instance.
        
        Args:
            gateway_type: Type of gateway to create. If None, uses the default gateway
                          from configuration.
        
        Returns:
            An instance of a PaymentGateway implementation.
        """
        if gateway_type is None:
            gateway_type = current_app.config.get('DEFAULT_PAYMENT_GATEWAY', 'stripe')
            
        gateway_type = gateway_type.lower()
        
        if gateway_type == 'stripe':
            return StripeGateway()
        elif gateway_type == 'paypal':
            return PayPalGateway()
        else:
            raise ValueError(f"Unsupported payment gateway type: {gateway_type}")