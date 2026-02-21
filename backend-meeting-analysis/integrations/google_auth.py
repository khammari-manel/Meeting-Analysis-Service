"""Google OAuth authentication"""
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import requests

CLIENT_SECRET_FILE = 'client_secret.json'
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]


def get_auth_url_with_user_info():
    """Generate Google OAuth URL with user info scope"""
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri='http://localhost:8080/auth/google/callback'
    )
    auth_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent'
    )
    return auth_url, state


def exchange_code_for_credentials(code):
    """Exchange auth code for credentials and user info"""
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri='http://localhost:8080/auth/google/callback'
    )
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    # Get user info from Google
    user_info_response = requests.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers={'Authorization': f'Bearer {credentials.token}'}
    )
    user_info = user_info_response.json()
    print(f"✅ Got user info: {user_info.get('email')}")
    
    return credentials, user_info