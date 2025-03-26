from flask import current_app, url_for
from payments.factory import PaymentGatewayFactory
from models import Subscription, User, db
from payments.exceptions import *
import logging

class SubscriptionService:
    """Service for handling subscription-related operations."""
    
    def __init__(self, gateway_type=None):
        self.gateway = PaymentGatewayFactory.create(gateway_type)
    
    def initiate_checkout(self, user_id, plan_id):
        """Start the checkout process for a user.
        
        Args:
            user_id: The ID of the user.
            plan_id: The plan identifier (3month, 6month, annual).
            
        Returns:
            URL to redirect the user to for checkout.
        """
        try:
            user = User.query.get(user_id)
            
            success_url = url_for('payment_success', _external=True)
            cancel_url = url_for('payment_cancel', _external=True)
            
            return self.gateway.create_checkout_session(
                plan_id=plan_id,
                user_id=user_id,
                success_url=success_url,
                cancel_url=cancel_url
            )
        except Exception as e:
            logging.error(f"Payment error for user {user_id}: {str(e)}")
            # Categorize the error if possible
            if "connection" in str(e).lower():
                raise GatewayConnectionError(f"Could not connect to payment provider: {str(e)}")
            else:
                raise PaymentError(f"Payment error: {str(e)}")
    
    def process_subscription_event(self, event_data, gateway_type=None):
        """Process a subscription-related webhook event.
        
        Args:
            event_data: The event data from the payment provider webhook.
            gateway_type: The type of payment gateway that sent the event.
        """
        gateway = PaymentGatewayFactory.create(gateway_type)
        
        # Processing logic will depend on the event type and gateway
        # This is a simplified example
        if gateway_type == 'stripe':
            event_type = event_data.get('type')
            obj = event_data.get('data', {}).get('object', {})
            
            if event_type == 'customer.subscription.created':
                self._handle_subscription_created(obj)
            elif event_type == 'customer.subscription.updated':
                self._handle_subscription_updated(obj)
            elif event_type == 'customer.subscription.deleted':
                self._handle_subscription_deleted(obj)
    
    def _handle_subscription_created(self, subscription_data):
        """Handle a subscription creation event."""
        # Extract relevant data and update database
        # ...
        
    def _handle_subscription_updated(self, subscription_data):
        """Handle a subscription update event."""
        # ...
        
    def _handle_subscription_deleted(self, subscription_data):
        """Handle a subscription deletion event."""
        # ...