from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, URL, Regexp
from database_operations import UserOperations
import re

def validate_strong_password(form, field):
    """Custom validator for strong password requirements"""
    password = field.data
    if not password:
        return
    
    errors = []
    
    if len(password) < 8:
        errors.append("aspoň 8 znakov")
    
    if not re.search(r'[A-Z]', password):
        errors.append("aspoň jedno veľké písmeno")
    
    if not re.search(r'[a-z]', password):
        errors.append("aspoň jedno malé písmeno")
    
    if not re.search(r'\d', password):
        errors.append("aspoň jednu číslicu")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("aspoň jeden špeciálny znak (!@#$%^&*)")
    
    if errors:
        raise ValidationError(f"Heslo musí obsahovať: {', '.join(errors)}")

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Email je povinný'),
        Email(message='Neplatný email formát')
    ])
    password = PasswordField('Heslo', validators=[
        DataRequired(message='Heslo je povinné')
    ])
    submit = SubmitField('Prihlásiť sa')

class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Email je povinný'),
        Email(message='Neplatný email formát'),
        Length(max=120, message='Email môže mať maximálne 120 znakov')
    ])
    password = PasswordField('Heslo', validators=[
        DataRequired(message='Heslo je povinné'),
        Length(min=8, max=128, message='Heslo musí mať 8-128 znakov'),
        validate_strong_password
    ])
    password_confirm = PasswordField('Potvrdiť heslo', validators=[
        DataRequired(message='Potvrdenie hesla je povinné'),
        EqualTo('password', message='Heslá sa nezhodujú')
    ])
    submit = SubmitField('Registrovať sa')
    
    def validate_email(self, email):
        """Check if email is already registered"""
        user = UserOperations.get_user_by_email(email.data)
        if user:
            raise ValidationError('Tento email je už registrovaný. Použite iný email alebo sa prihláste.')

class SettingsForm(FlaskForm):
    ollama_host = StringField('OLLAMA Server URL', validators=[
        DataRequired(message='OLLAMA server URL je povinná'),
        Length(max=255, message='URL môže mať maximálne 255 znakov')
    ], description='Napríklad: http://192.168.1.23:11434')
    submit = SubmitField('Uložiť nastavenia')
    
    def validate_ollama_host(self, ollama_host):
        """Validate OLLAMA host URL format"""
        url = ollama_host.data.strip()
        if not url.startswith(('http://', 'https://')):
            raise ValidationError('URL musí začínať http:// alebo https://')
        
        # Basic URL validation
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if not parsed.netloc:
                raise ValidationError('Neplatný formát URL')
        except Exception:
            raise ValidationError('Neplatný formát URL')