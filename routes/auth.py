


from flask import Blueprint, request, render_template,flash,request,redirect,url_for,current_app
from flask_login import login_user, logout_user, current_user, login_required
from forms import RegistrationForm, LoginForm ,ResetPasswordForm,ResetPasswordRequestForm
from models import  User
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from datetime import datetime
from flask_mail import Mail, Message
from db import db
auth_bp = Blueprint("auth", __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('root.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        try:
            # Get user by email using SQLAlchemy
            user = User.query.filter_by(email=form.email.data).first()
            
            if user:
                # Verify password
                if check_password_hash(user.password_hash, form.password.data):

                    # if not user.verified:
                    #     flash('Please verify your email address before logging in.', 'warning')
                    #     return render_template('login.html', form=form, show_resend=True, email=user.email)
                    # Log in user
                    login_user(user)
                    
                    # Get next page or default to dashboard
                    next_page = request.args.get('next')
                    flash('Login successful!', 'success')
                    return redirect(next_page or url_for('root.dashboard'))
                else:
                    flash('Invalid password. Please try again.', 'danger')
            else:
                flash('Email not found. Please check your email or register.', 'danger')
        
        except Exception as e:
            print(f"Login error: {e}")
            flash('An error occurred during login. Please try again.', 'danger')
    
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('root.dashboard'))
    
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Generate a token
            token = serializer.dumps(user.email, salt='password-reset-salt')
            
            # Build reset URL
            reset_url = url_for(
                'auth.reset_password',
                token=token,
                _external=True
            )
            
            # Send email
            msg = Message(
                subject='Password Reset Request',
                recipients=[user.email],
                html=render_template('email/reset_password.html', reset_url=reset_url, user=user),
                sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@resumematch.com')
            )
            mail.send(msg)
            
        # Always to show this message even if email is not found (security best practice)
        flash('If an account exists with that email, you will receive password reset instructions.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password_request.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('root.dashboard'))
    
    # Verify token - valid for 24 hours
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=86400)
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Invalid or expired reset link.', 'danger')
            return redirect(url_for('auth.reset_password_request'))
    except (SignatureExpired, BadSignature):
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('atuh.reset_password_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Update password
        user.password_hash = generate_password_hash(form.password.data)
        db.session.commit()
        
        flash('Your password has been reset! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', form=form)



@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('root.dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        try:
            #serializer for generating secure tokens
            serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            # Check if email already exists using SQLAlchemy
            existing_user = User.query.filter_by(email=form.email.data).first()
            
            if existing_user:
                flash('Email already registered. Please log in.', 'danger')
                return redirect(url_for('auth.login'))
            
            hashed_password = generate_password_hash(form.password.data)
            # Create new user with SQLAlchemy model
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=hashed_password,
                verified=False,
                verification_sent_at=datetime.now()
            )
            
            # Add and commit to database
            db.session.add(new_user)
            db.session.commit()
            
            # Generate verification token
            token = serializer.dumps(new_user.email, salt='email-verification-salt')

            # Create verification URL
            verification_url = url_for(
                'auth.verify_email',
                token=token,
                _external=True
            )
            # Send verification email
            msg = Message(
                subject='Verify Your ResumeMatch Account',
                recipients=[new_user.email],
                html=render_template('verify_email.html', verification_url=verification_url, user=new_user),
                sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@resumematch.com')
            )
            mail.send(msg)
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()  # Roll back the session on error
            print(f"Registration error: {e}")
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('register.html', form=form)
@auth_bp.route('/resend-verification', methods=['POST'])
def process_resend_verification():
    email = request.form.get('email')
    
    if not email:
        flash('Please provide your email address.', 'danger')
        return redirect(url_for('auth.resend_verification'))
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # Not to reveal if email exists or not for security
        flash('If your email is registered, you will receive a verification link shortly.', 'info')
        return redirect(url_for('auth.login'))
    
    if user.verified:
        flash('Your account is already verified. Please log in.', 'info')
        return redirect(url_for('auth.login'))
    
    # Check if last verification was sent less than 10 minutes ago
    if user.verification_sent_at and (datetime.now() - user.verification_sent_at).total_seconds() < 600:
        flash('A verification email was recently sent. Please check your inbox or wait a few minutes before requesting another.', 'info')
        return redirect(url_for('auth.login'))
    
    # Generate new verification token
    token = serializer.dumps(user.email, salt='email-verification-salt')
    
    # Create verification URL
    verification_url = url_for(
        'auth.verify_email',
        token=token,
        _external=True
    )
    mail = Mail(auth_bp)
    # Send verification email
    msg = Message(
        subject='Verify Your ResumeMatch Account',
        recipients=[user.email],
        html=render_template('verify_email.html', verification_url=verification_url, user=user),
        sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@resumematch.com')
    )
    mail.send(msg)
    
    # Update verification sent time
    user.verification_sent_at = datetime.now()
    db.session.commit()
    
    flash('Verification email sent. Please check your inbox.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    try:
        # Verify token - valid for 7 days
        email = serializer.loads(token, salt='email-verification-salt', max_age=604800)
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('Invalid verification link.', 'danger')
            return redirect(url_for('auth.login'))
            
        if user.verified:
            flash('Your account is already verified. Please log in.', 'info')
            return redirect(url_for('auth.login'))
        
        # Verify user
        user.verified = True
        db.session.commit()
        
        flash('Your account has been verified! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    except (SignatureExpired, BadSignature):
        flash('The verification link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/resend-verification')
def resend_verification():
    if current_user.is_authenticated:
        return redirect(url_for('root.dashboard'))
    
    return render_template('resend_verification.html')