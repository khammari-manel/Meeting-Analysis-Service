# Import SQLAlchemy - this is the library that helps us work with databases in Python
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime


# Create a SQLAlchemy instance - this is our database manager
# We'll use this 'db' object to create tables and query data
db = SQLAlchemy()

# Define our User table
# UserMixin = adds login features (is_authenticated, get_id, etc.)
# db.Model = tells SQLAlchemy this is a database table
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # GOOGLE ID - Google's unique identifier for this user
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(100))
    # GOOGLE ACCESS TOKEN - The key to access their Google Calendar
    google_access_token = db.Column(db.String(500))
    # GOOGLE REFRESH TOKEN - Used to get new access tokens when they expire
    google_refresh_token = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.email}>'