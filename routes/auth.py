from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from forms import LoginForm, RegisterForm
from database_operations import UserOperations
import time
import secrets

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.chat'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Add timing attack protection - always take similar time
        start_time = time.time()
        
        user = UserOperations.authenticate_user(form.email.data, form.password.data)
        
        # Ensure minimum processing time to prevent timing attacks
        elapsed = time.time() - start_time
        delay = current_app.config['AUTH_TIMING_DELAY']
        if elapsed < delay:  # Minimum delay to prevent timing attacks
            time.sleep(delay - elapsed)
        
        if user:
            # Clear existing session data to prevent session fixation
            session.clear()
            login_user(user)
            
            # Validate and sanitize next_page to prevent open redirects
            next_page = request.args.get('next')
            if next_page and not next_page.startswith('/'):
                next_page = None
                
            flash('Úspešne ste sa prihlásili!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.chat'))
        else:
            flash('Neplatný email alebo heslo.', 'error')
    
    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.chat'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = UserOperations.create_user(form.email.data, form.password.data)
        if user:
            flash('Registrácia bola úspešná! Môžete sa prihlásiť.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Chyba pri registrácii. Skúste to znovu.', 'error')
    
    return render_template('register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    # Clear all session data on logout for security
    session.clear()
    logout_user()
    flash('Boli ste odhlásení.', 'success')
    return redirect(url_for('auth.login'))