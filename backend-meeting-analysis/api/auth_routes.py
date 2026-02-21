from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from integrations.google_auth import get_auth_url_with_user_info, exchange_code_for_credentials
from database.models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/google', methods=['GET'])
def google_signin():
    try:
        auth_url, state = get_auth_url_with_user_info()
        session['oauth_state'] = state
        return jsonify({'auth_url': auth_url})
    except Exception as e:
        print(f"Error generating auth URL: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/google/callback', methods=['GET'])
def google_callback():
    code = request.args.get('code')
    if not code:
        return "Error: No authorization code received", 400
    
    try:
        credentials, user_info = exchange_code_for_credentials(code)
        google_id = user_info.get('id')
        email = user_info.get('email')
        name = user_info.get('name')
        
        print(f"Google login: {email}")
        
        user = User.query.filter_by(google_id=google_id).first()
        
        if not user:
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                google_access_token=credentials.token,
                google_refresh_token=credentials.refresh_token
            )
            db.session.add(user)
            print(f"New user created: {email}")
        else:
            user.google_access_token = credentials.token
            user.google_refresh_token = credentials.refresh_token
            print(f"User tokens updated: {email}")
        
        db.session.commit()
        login_user(user)
        
        return """
        <html>
            <body>
                <h1>Erfolgreich angemeldet!</h1>
                <p>Sie können dieses Fenster schließen.</p>
                <script>
                    window.opener.postMessage('login_success', '*');
                    window.close();
                </script>
            </body>
        </html>
        """
    except Exception as e:
        print(f"OAuth callback error: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    if current_user.is_authenticated:
        return jsonify({
            'id': current_user.id,
            'email': current_user.email,
            'name': current_user.name,
            'has_calendar': bool(current_user.google_access_token)
        })
    else:
        return jsonify({'error': 'Not authenticated'}), 401

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    email = current_user.email
    logout_user()
    print(f"User logged out: {email}")
    return jsonify({'status': 'success'})