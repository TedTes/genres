from flask import Blueprint, request, redirect, url_for, current_app, render_template
from flask_login import login_required, current_user
from ..services.subscription_service import SubscriptionService

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/checkout/<plan_id>', methods=['GET'])
@login_required
def checkout(plan_id):
    """Initiate checkout for a subscription plan."""
    service = SubscriptionService()
    checkout_url = service.initiate_checkout(current_user.id, plan_id)
    return redirect(checkout_url)

@payment_bp.route('/payment-success', methods=['GET'])
@login_required
def payment_success():
    """Handle successful payment."""
    # Note: Most of the subscription handling will be done via webhooks
    return render_template('payment_success.html')

@payment_bp.route('/payment-cancel', methods=['GET'])
@login_required
def payment_cancel():
    """Handle canceled payment."""
    return render_template('payment_cancel.html')

@payment_bp.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events."""
    service = SubscriptionService(gateway_type='stripe')
    event = service.gateway.handle_webhook(
        payload=request.data,
        headers=request.headers
    )
    
    if event:
        service.process_subscription_event(event, gateway_type='stripe')
        return '', 200
    else:
        return 'Webhook Error', 400

@payment_bp.route('/webhooks/paypal', methods=['POST'])
def paypal_webhook():
    """Handle PayPal webhook events."""
    # Similar implementation for PayPal webhook handling
    pass