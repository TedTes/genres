from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length,Regexp

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class JobSearchForm(FlaskForm):
    search = StringField('Search Term')
    location = StringField('Location')
    remote = BooleanField('Remote Only')
    submit = SubmitField('Search')

class ContactForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(message="Please enter your full name"),Length(min=2, max=100, message="Name must be between 2 and 100 characters")])
    email = StringField('Email', validators=[DataRequired(message="Please enter your email address"), Email(message="Please enter a valid email address")])
    phone = StringField('Phone', validators=[DataRequired(message="Please enter your phone number"),Regexp(r'^\+?[\d\s\(\)-]{10,20}$', message="Please enter a valid phone number")])
    submit = SubmitField('Next')

class SummaryForm(FlaskForm):
    summary = TextAreaField('Summary', validators=[DataRequired()])
    submit = SubmitField('Finish')

class ExperienceForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired()])
    company = StringField('Company', validators=[DataRequired()])
    start_date = StringField('Start Date', validators=[DataRequired()])
    end_date = StringField('End Date')
    bullets = TextAreaField('Achievements (one per line)', validators=[DataRequired()])
    submit = SubmitField('Next')

class EducationForm(FlaskForm):
    degree = StringField('Degree', validators=[DataRequired()])
    school = StringField('School', validators=[DataRequired()])
    year = StringField('Year', validators=[DataRequired()])
    submit = SubmitField('Next')

class SkillsForm(FlaskForm):
    skills = TextAreaField('Skills (comma-separated)', validators=[DataRequired()])
    submit = SubmitField('Next')


class ApplicationForm(FlaskForm):
    status = SelectField('Application Status', choices=[
        ('applied', 'Applied'),
        ('interviewing', 'Interviewing'),
        ('offered', 'Received Offer'),
        ('rejected', 'Rejected'),
        ('accepted', 'Accepted Offer')
    ])
    notes = TextAreaField('Notes')
    submit = SubmitField('Save')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message="Password must be at least 6 characters long")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')