from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from app.models import User, normalize_email
from app.services.category_service import note_form_choices
from flask_login import current_user


class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', filters=[normalize_email], validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')
    
    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('Email already registered.')


class LoginForm(FlaskForm):
    email = StringField('Email', filters=[normalize_email], validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class ProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', filters=[normalize_email], validators=[DataRequired(), Email(), Length(max=120)])
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
    # validate_choice=False: category is free text with presets, not a real
    # enum (documents store an imported-from-filename category; users can
    # save any custom string). The durable fix for C9 - editing a note
    # whose category isn't one of these presets must not fail validation -
    # is to stop treating the dropdown as authoritative, rather than
    # patching the choices list per-request before validating.
    category = SelectField('Category', choices=note_form_choices(),
                            validators=[Optional()], validate_choice=False)
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
