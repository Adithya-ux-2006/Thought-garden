from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from app.models import User, Tag
from flask_login import current_user


class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')
    
    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('Email already registered.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class ProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    current_password = PasswordField('Current Password', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    confirm_new_password = PasswordField('Confirm New Password', validators=[Optional(), EqualTo('new_password')])
    submit = SubmitField('Update Profile')
    
    def validate_email(self, email):
        if email.data != current_user.email:
            if User.query.filter_by(email=email.data).first():
                raise ValidationError('Email already in use.')


class NoteForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('', 'Select Category'),
        ('AI', 'Artificial Intelligence'),
        ('Cybersecurity', 'Cybersecurity'),
        ('Software Engineering', 'Software Engineering'),
        ('Operating Systems', 'Operating Systems'),
        ('Research', 'Research'),
        ('Ideas', 'Ideas'),
        ('Study', 'Study Material'),
        ('Other', 'Other')
    ], validators=[Optional()])
    tags = StringField('Tags (comma-separated)', validators=[Optional()])
    is_pinned = BooleanField('Pin this note')
    submit = SubmitField('Save Note')


class SearchForm(FlaskForm):
    q = StringField('Search', validators=[Optional()])
    category = SelectField('Category', choices=[('', 'All Categories')], validators=[Optional()])
    tag = SelectField('Tag', choices=[('', 'All Tags')], validators=[Optional()])
    source_type = SelectField('Source', choices=[
        ('', 'All Sources'),
        ('manual', 'Manual'),
        ('pdf', 'PDF'),
        ('md', 'Markdown'),
        ('txt', 'Text')
    ], validators=[Optional()])
    submit = SubmitField('Search')


class DocumentUploadForm(FlaskForm):
    file = FileField('Document', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('', 'Select Category'),
        ('AI', 'Artificial Intelligence'),
        ('Cybersecurity', 'Cybersecurity'),
        ('Software Engineering', 'Software Engineering'),
        ('Operating Systems', 'Operating Systems'),
        ('Research', 'Research'),
        ('Ideas', 'Ideas'),
        ('Study', 'Study Material'),
        ('Other', 'Other')
    ], validators=[Optional()])
    submit = SubmitField('Import Document')