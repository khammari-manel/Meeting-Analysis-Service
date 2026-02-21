"""Email notification service"""
from flask_mail import Mail, Message
import os

mail = Mail()

def init_mail(app):
    """Initialize Flask-Mail with app"""
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('EMAIL_USERNAME')
    mail.init_app(app)
    
    if app.config['MAIL_USERNAME']:
        print(f"✅ Email service initialized with {app.config['MAIL_USERNAME']}")
    else:
        print(" Email service not configured (no EMAIL_USERNAME)")