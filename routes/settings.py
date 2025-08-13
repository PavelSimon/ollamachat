from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from marshmallow import ValidationError
from forms import SettingsForm
from database_operations import SettingsOperations
from validation_schemas import SettingsUpdateSchema, validate_request_data, create_validation_error_response
from error_handlers import ErrorHandler

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


@settings_bp.route('/api/settings', methods=['GET', 'PUT'])
@login_required
def api_settings():
    """API endpoint for user settings management"""
    current_settings = SettingsOperations.get_user_settings(current_user.id)
    
    if request.method == 'GET':
        return jsonify({
            'ollama_host': current_settings.ollama_host,
            'updated_at': current_settings.updated_at.isoformat()
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            if not data:
                return ErrorHandler.validation_error(
                    ValidationError("No data provided"),
                    "Chýbajú dáta v požiadavke"
                )
            
            validated_data = validate_request_data(SettingsUpdateSchema, data)
            
            settings = SettingsOperations.update_ollama_host(
                current_user.id, 
                validated_data['ollama_host']
            )
            
            return jsonify({
                'message': 'Nastavenia boli úspešne uložené',
                'ollama_host': settings.ollama_host,
                'updated_at': settings.updated_at.isoformat()
            })
        except ValidationError as e:
            return jsonify(create_validation_error_response(e)[0]), 400
        except Exception as e:
            return ErrorHandler.internal_error(
                e,
                "updating user settings",
                "Chyba pri ukladaní nastavení"
            )