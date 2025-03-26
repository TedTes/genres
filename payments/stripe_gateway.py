import stripe
from .base import PaymentGateway
from flask import current_app

class StripeGateway(PaymentGateway):
    """Stripe payment gateway implementation."""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or current_app.config.get('STRIPE_SECRET_KEY')
        stripe.api_key = self.api_key
        
        # Plan ID mapping (user plan IDs to Stripe's price IDs)
        self.price_mapping = {
            '3month': current_app.config.get('STRIPE_3MONTH_PRICE_ID'),
            '6month': current_app.config.get('STRIPE_6MONTH_PRICE_ID'),
            'annual': current_app.config.get('STRIPE_ANNUAL_PRICE_ID')
        }
    
    def create_customer(self, user):
        customer = stripe.Customer.create(
            email=user.email,
            name=user.username,
            metadata={'user_id': user.id}
        )
        return customer.id
    
    def create_subscription(self, customer_id, plan_id, metadata=None):
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{'price': self.price_mapping[plan_id]}],
            metadata=metadata or {}
        )
        return subscription.id
    
    def cancel_subscription(self, subscription_id):
        return stripe.Subscription.delete(subscription_id)
    
    def update_subscription(self, subscription_id, new_plan_id):
        # Get subscription to find the subscription item ID
        subscription = stripe.Subscription.retrieve(subscription_id)
        subscription_item_id = subscription['items']['data'][0]['id']
        
        # Update the subscription
        stripe.Subscription.modify(
            subscription_id,
            items=[{
                'id': subscription_item_id,
                'price': self.price_mapping[new_plan_id]
            }]
        )
        return subscription_id
    
    def get_subscription_status(self, subscription_id):
        subscription = stripe.Subscription.retrieve(subscription_id)
        return {
            'status': subscription.status,
            'current_period_end': subscription.current_period_end,
            'cancel_at_period_end': subscription.cancel_at_period_end
        }
    
    def handle_webhook(self, payload, headers):
        webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
        try:
            event = stripe.Webhook.construct_event(
                payload, headers.get('Stripe-Signature'), webhook_secret
            )
            return event
        except Exception as e:
            current_app.logger.error(f"Webhook error: {str(e)}")
            return None
    
    def create_checkout_session(self, plan_id, user_id, success_url, cancel_url):
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': self.price_mapping[plan_id],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(user_id)
        )
        return session.url