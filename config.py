# config.py
import os

class Config:

    # Default payment gateway
    DEFAULT_PAYMENT_GATEWAY = os.environ.get('DEFAULT_PAYMENT_GATEWAY', 'stripe')
    
    # Stripe configuration
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    STRIPE_3MONTH_PRICE_ID = os.environ.get('STRIPE_3MONTH_PRICE_ID')
    STRIPE_6MONTH_PRICE_ID = os.environ.get('STRIPE_6MONTH_PRICE_ID')
    STRIPE_ANNUAL_PRICE_ID = os.environ.get('STRIPE_ANNUAL_PRICE_ID')
    
    # PayPal configuration
    PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')
    PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
    PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')

    PAYPAL_3MONTH_PLAN_ID = os.environ.get('PAYPAL_3MONTH_PLAN_ID')
    PAYPAL_6MONTH_PLAN_ID = os.environ.get('PAYPAL_6MONTH_PLAN_ID')
    PAYPAL_ANNUAL_PLAN_ID = os.environ.get('PAYPAL_ANNUAL_PLAN_ID')
    PAYPAL_WEBHOOK_ID = os.environ.get('PAYPAL_WEBHOOK_ID')

    #base web urls
    S_BUCK = os.environ.get('S_BUCK_BASE_URL')
    T_HORT = os.environ.get('T_HORT_BASE_URL')
    H_DEPO = os.environ.get('H_DEPO_BASE_URL')
    W_MAR = os.environ.get('W_MAR_BASE_URL')


    #selectors
    S_BUCK_SELECTOR = os.environ.get('S_BUCK_SELECTOR')
    T_HORT_SELECTOR = os.environ.get('T_HORT_SELECTOR')
    H_DEPO_SELECTOR = os.environ.get('H_DEPO_SELECTOR')
    W_MAR_SELECTOR = os.environ.get('W_MAR_SELECTOR')


    # LLM API keys
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')