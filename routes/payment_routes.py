from flask import Blueprint, request, redirect, url_for, current_app, render_template
from flask_login import login_required, current_user
from services.subscription_service import SubscriptionService

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/checkout/<plan_id>', methods=['GET'])
@login_required
def checkout(plan_id):
    """Display the checkout page for a subscription plan."""
    # Define plans 
    plans = {
        '3month': {
            'name': '3-Month Plan', 
            'price': 30, 
            'period': '3 months',
            'description': 'Access to all premium features for 3 months',
            'savings': 'Only $10/month'
        },
        '6month': {
            'name': '6-Month Plan', 
            'price': 48, 
            'period': '6 months',
            'description': 'Access to all premium features for 6 months',
            'savings': 'Only $8/month (Save 44%)'
        },
        'annual': {
            'name': 'Annual Plan', 
            'price': 80, 
            'period': '12 months',
            'description': 'Full access to all premium features for a full year',
            'savings': 'Only $6.67/month (Best value)'
        }
    }
    # Check if the plan exists
    if plan_id not in plans:
        flash('Invalid plan selected.', 'error')
        return redirect(url_for('home'))
    return render_template(
        'checkout.html', 
        plan=plans[plan_id], 
        plan_id=plan_id,
        stripe_public_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY')
    )

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


@payment_bp.route('/process-checkout/<plan_id>', methods=['POST'])
@login_required
def process_checkout(plan_id):
    """Process checkout and redirect to payment gateway."""
    
    # Get selected payment gateway
    gateway_type = request.form.get('gateway', current_app.config.get('DEFAULT_PAYMENT_GATEWAY'))
    
    # Store the gateway choice in session so we can use it later
    session['payment_gateway'] = gateway_type
    # Create subscription service with selected gateway
    service = SubscriptionService(gateway_type=gateway_type)
    
    try:
        # Initiate checkout with the payment gateway
        checkout_url = service.initiate_checkout(current_user.id, plan_id)
        
        # Redirect to payment gateway's checkout page
        return redirect(checkout_url)
    except PaymentError as e:
        flash(f"Payment error: {str(e)}", "error")
        return redirect(url_for('payment.checkout', plan_id=plan_id))