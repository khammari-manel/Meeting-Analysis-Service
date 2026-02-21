"""Configuration for Meeting Analysis Backend"""
import os
import secrets
from datetime import timedelta

class Config:
    """Application configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(16))
    DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///meeting_analysis.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    REDIRECT_URI = 'http://localhost:8080/auth/google/callback'
    
    # AI
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    MOCK_MODE = os.getenv('MOCK_MODE', 'false').lower() == 'true'
    
    # RabbitMQ
    CLOUDAMQP_URL = os.getenv('CLOUDAMQP_URL')
    
    # CORS
    CORS_ORIGINS = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "file://"
    ]
    
    # Server
    PORT = int(os.getenv('PORT', 8080))