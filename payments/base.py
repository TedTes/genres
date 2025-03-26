from abc import ABC, abstractmethod

class PaymentGateway(ABC):
    """Abstract base class for payment gateway implementations."""
    
    @abstractmethod
    def create_customer(self, user):
        """Create a customer in the payment gateway system."""
        pass
    
    @abstractmethod
    def create_subscription(self, customer_id, plan_id, metadata=None):
        """Create a subscription for a customer."""
        pass
    
    @abstractmethod
    def cancel_subscription(self, subscription_id):
        """Cancel an existing subscription."""
        pass
    
    @abstractmethod
    def update_subscription(self, subscription_id, new_plan_id):
        """Update a subscription to a different plan."""
        pass
    
    @abstractmethod
    def get_subscription_status(self, subscription_id):
        """Get the current status of a subscription."""
        pass
    
    @abstractmethod
    def handle_webhook(self, payload, headers):
        """Process webhook events from the payment gateway."""
        pass
    
    @abstractmethod
    def create_checkout_session(self, plan_id, user_id, success_url, cancel_url):
        """Create a checkout session for a subscription plan."""
        pass