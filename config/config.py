# config.py
import os
import secrets

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



    # LLM API keys
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')



    #DATABASE
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    #flask secret key
    SECRET_KEY = secrets.token_hex(16)



    MODEL_PROVIDER = os.environ.get('MODEL_PROVIDER', 'hf')  # default to huggingface
    
    if MODEL_PROVIDER == 'openai':
       EMBED_MODEL = os.environ.get('OPENAI_EMBED_MODEL', 'text-embedding-3-small')
       LLM_MODEL = os.environ.get('OPENAI_LLM_MODEL', 'gpt-4o-mini')
    elif MODEL_PROVIDER == 'hf':
       EMBED_MODEL = os.environ.get('HF_EMBED_MODEL', 'BAAI/bge-large-en-v1.5')
       LLM_MODEL = os.environ.get('HF_LLM_MODEL', 'mistralai/Mistral-7B-Instruct-v0.3')
    else:
       EMBED_MODEL = os.environ.get('EMBED_MODEL', 'BAAI/bge-large-en-v1.5')
    #LLM API Keys
    HF_TOKEN = os.environ.get('HF_TOKEN')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    #Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    #Resume Optimizer Settings
    RESUME_OPTIMIZER_ENABLED = os.environ.get('RESUME_OPTIMIZER_ENABLED', 'true').lower() == 'true'
    MAX_RESUME_SIZE_MB = int(os.environ.get('MAX_RESUME_SIZE_MB', '5'))
    RATE_LIMIT_PER_HOUR = int(os.environ.get('RATE_LIMIT_PER_HOUR', '10'))
    
    @classmethod
    def validate_llm_config(cls):
        """Validate LLM configuration based on selected provider"""
        if cls.MODEL_PROVIDER == 'openai':
            if not cls.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required when MODEL_PROVIDER=openai")
        elif cls.MODEL_PROVIDER == 'hf':
            if not cls.HF_TOKEN:
                print("Warning: HF_TOKEN not set. Some HuggingFace models may not work.")
        else:
            raise ValueError(f"Unsupported MODEL_PROVIDER: {cls.MODEL_PROVIDER}")
        
        return True