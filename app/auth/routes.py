import math
from urllib.parse import urlsplit

from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from app.auth import bp
from app.models import User, db
from app.forms import RegisterForm, LoginForm, ProfileForm
from app.services.onboarding_service import prepare_starter_garden


def _safe_next_url(target):
    """Return `target` only if it is a path on this site, else None."""
    if not target or not target.startswith('/') or target.startswith('//'):
        return None
    # Browsers treat backslashes as slashes and strip tabs/newlines, so
    # "/\evil.com" or "/\t/evil.com" would resolve to another host.
    if '\\' in target or any(ord(ch) < 0x20 or ord(ch) == 0x7f for ch in target):
        return None
    parts = urlsplit(target)
    if parts.scheme or parts.netloc:
        return None
    return target


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            # A concurrent registration won the race past the form's check.
            db.session.rollback()
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html', form=form)
        note_count, connection_count = prepare_starter_garden(user)
        login_user(user)
        if note_count:
            flash(
                f'Your garden is ready: {note_count} starter notes and '
                f'{connection_count} connections were prepared for you.',
                'success'
            )
            return redirect(url_for('garden.index'))
        flash('Registration successful. Your garden is ready!', 'success')
        return redirect(url_for('notes.create'))
    return render_template('auth/register.html', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        limiter = current_app.extensions['login_limiter']
        client = request.remote_addr or 'unknown'
        window = current_app.config['LOGIN_LOCKOUT_SECONDS']
        # Checked before the password so a blocked client gets no signal
        # about whether its guess was right.
        retry_after = limiter.retry_after(
            client, current_app.config['LOGIN_MAX_FAILED_ATTEMPTS'], window)
        if retry_after:
            minutes = max(1, math.ceil(retry_after / 60))
            flash(f'Too many failed login attempts. Try again in {minutes} minute(s).', 'danger')
            return render_template('auth/login.html', form=form), 429

        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = _safe_next_url(request.args.get('next'))
            flash('Welcome back!', 'success')
            return redirect(next_page or url_for('main.dashboard'))
        limiter.record_failure(client, window)
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html', form=form)


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        email_changed = form.email.data != current_user.email
        if form.current_password.data:
            if not current_user.check_password(form.current_password.data):
                flash('Current password is incorrect.', 'danger')
                return render_template('auth/profile.html', form=form)
            if form.new_password.data:
                current_user.set_password(form.new_password.data)
        elif email_changed:
            flash('Enter your current password to change your email.', 'danger')
            return render_template('auth/profile.html', form=form)
        current_user.name = form.name.data
        current_user.email = form.email.data
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Email already in use.', 'danger')
            return render_template('auth/profile.html', form=form)
        flash('Profile updated.', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('auth/profile.html', form=form)
