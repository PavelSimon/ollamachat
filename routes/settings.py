from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from forms import SettingsForm
from database_operations import SettingsOperations

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()
    current_settings = SettingsOperations.get_user_settings(current_user.id)
    
    if form.validate_on_submit():
        SettingsOperations.update_ollama_host(current_user.id, form.ollama_host.data.strip())
        flash('Nastavenia boli úspešne uložené!', 'success')
        return redirect(url_for('settings.settings'))
    
    # Pre-populate form with current settings
    if request.method == 'GET':
        form.ollama_host.data = current_settings.ollama_host
    
    return render_template('settings.html', form=form, current_host=current_settings.ollama_host)