from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, URL
from database_operations import UserOperations

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
        Length(min=6, message='Heslo musí mať aspoň 6 znakov')
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