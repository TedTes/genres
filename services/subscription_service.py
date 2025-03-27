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
    
    def get_user_subscription(user_id):
        """
        Retrieve the current active subscription for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            A dictionary with subscription details or None if no active subscription
        """
        # Query the database for the user's active subscription
        # subscription = Subscription.query.filter_by(
        #     user_id=user_id,
        #     status='active'
        # ).first()
        subscription = {
            'id': 123,
            'plan_id': '456',
            'plan_name': '3month',
            'status': 'active',
            'next_billing_date': '2025-03-29',
            'is_active': True,
            'gateway': 'stripe',
            'current_period_end': None,
        }
        
        if not subscription:
            return None
            
        # Get the plan details
        if subscription['plan_id'] == '3month':
            plan_name = '3-Month Plan'
            period = '3 months'
        elif subscription['plan_id'] == '6month':
            plan_name = '6-Month Plan'
            period = '6 months'
        elif subscription['plan_id'] == 'annual':
            plan_name = 'Annual Plan'
            period = '12 months'
        else:
            plan_name = 'Custom Plan'
            period = 'varies'
        
        # Calculate next billing date
        if subscription['current_period_end']:
            next_billing_date = subscription['current_period_end'].strftime('%B %d, %Y')
        else:
            next_billing_date = 'Not available'
        
       
        return {
            'id': subscription['id'],
            'plan_id': subscription['plan_id'],
            'plan_name': plan_name,
            'period': period,
            'status': subscription['status'],
            'next_billing_date': next_billing_date,
            'is_active': True,
            'gateway': subscription['gateway'],
        }
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