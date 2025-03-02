from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length

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
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired()])
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