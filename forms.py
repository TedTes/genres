from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField,IntegerField,SelectMultipleField,widgets
from wtforms.validators import DataRequired, Email, EqualTo, Length,Regexp,Optional, NumberRange

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')

class JobSearchForm(FlaskForm):
    # Basic filters
    search = StringField('Search Term')
    location = StringField('Location')
    remote = BooleanField('Remote Only')
    
    # New primary filters
    date_posted = SelectField('Date Posted', choices=[
        ('', 'Any time'),
        ('1', 'Last 24 hours'),
        ('3', 'Last 3 days'),
        ('7', 'Last 7 days'),
        ('30', 'Last 30 days')
    ])
    
    salary_min = IntegerField('Minimum Salary', validators=[Optional(), NumberRange(min=0)])
    salary_max = IntegerField('Maximum Salary', validators=[Optional(), NumberRange(min=0)])
    
    # Advanced filters
    experience_level = MultiCheckboxField('Experience Level', choices=[
        ('', 'Any experience'),
        ('entry', 'Entry Level'),
        ('mid', 'Mid-Level'),
        ('senior', 'Senior'),
        ('executive', 'Executive')
    ])
    
    employment_type = MultiCheckboxField('Employment Type', choices=[
        ('', 'Any type'),
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('temporary', 'Temporary')
    ])
    
    industry = SelectField('Industry', choices=[
        ('', 'All industries'),
        ('technology', 'Technology'),
        ('healthcare', 'Healthcare'),
        ('finance', 'Finance'),
        ('education', 'Education'),
        ('marketing', 'Marketing'),
        ('retail', 'Retail'),
        ('manufacturing', 'Manufacturing'),
        ('hospitality', 'Hospitality')
    ])
    
    company_size = MultiCheckboxField('Company Size', choices=[
        ('', 'Any size'),
        ('startup', 'Startup'),
        ('small', 'Small (1-50 employees)'),
        ('medium', 'Medium (51-500 employees)'),
        ('large', 'Large (500+ employees)')
    ])
    
    skills_match = MultiCheckboxField('Skills Match', choices=[
        ('', 'Any match'),
        ('50', '50%+ match'),
        ('70', '70%+ match'),
        ('90', '90%+ match')
    ])
    
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