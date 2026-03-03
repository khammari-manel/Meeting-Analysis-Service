"""Meeting Analysis Backend v2.0 - Multi-User"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_login import LoginManager

from config import Config
from database.models import db, User
from api.auth_routes import auth_bp
from api.parse_routes import parse_bp
from api.calendar_routes import calendar_bp
from api.task_routes import task_bp
from api.notification_routes import notification_bp
from api.jira_routes import jira_bp

from integrations.email_service import init_mail
def create_app():
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configure CORS to allow all origins (including file://)
    CORS(app,
         resources={r"/*": {
             "origins": "*",
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "Accept"],
             "expose_headers": ["Content-Type"],
             "supports_credentials": True,
             "max_age": 3600
         }})
    #testgit
    db.init_app(app)
    
    init_mail(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(parse_bp, url_prefix='')
    app.register_blueprint(calendar_bp, url_prefix='/calendar')
    app.register_blueprint(task_bp, url_prefix='/tasks')  
    app.register_blueprint(notification_bp, url_prefix='/notifications')
    app.register_blueprint(jira_bp, url_prefix='/jira')
    
    # Additional CORS handler for all requests
    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,Accept'
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
        return response
    
    @app.route("/", methods=["GET"])
    def home():
        return jsonify({
            "status": "healthy",
            "service": "Meeting Analysis Backend",
            "version": "2.0",
            "endpoints": {
                "/": "GET - Service info",
                "/health": "GET - Health check",
                "/auth/google": "GET - Sign in with Google",
                "/auth/google/callback": "GET - OAuth callback",
                "/auth/me": "GET - Get current user",
                "/auth/logout": "POST - Logout",
                "/parse": "POST - Parse meeting documents",
                "/calendar/add": "POST - Add events to calendar"
            }
        })
    
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "healthy",
            "rabbitmq_configured": bool(Config.CLOUDAMQP_URL),
            "openrouter_configured": bool(Config.OPENROUTER_API_KEY),
            "mock_mode": Config.MOCK_MODE
        })
        
    
    @app.route("/me", methods=["GET"])
    def me():
        """Get current user - kept at root for backward compatibility"""
        from flask_login import current_user
        if current_user.is_authenticated:
            return jsonify({
                'id': current_user.id,
                'email': current_user.email,
                'name': current_user.name,
                'has_calendar': bool(current_user.google_access_token)
            })
        else:
            return jsonify({'error': 'Not authenticated'}), 401
    return app


if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        db.create_all()
        print(" Database initialized")
    
    print("=" * 70)
    print("🚀 Meeting Analysis Backend v2.0 - Multi-User")
    print("=" * 70)
    print(f"\n Server starting on port {Config.PORT}")
    print(f"\n Available Endpoints:")
    print(f"   GET  /              → Service info")
    print(f"   GET  /health        → Health check")
    print(f"   GET  /auth/google   → Sign in with Google")
    print(f"   GET  /auth/me       → Current user info")
    print(f"   POST /parse         → Parse meeting documents")
    print(f"   POST /calendar/add  → Add events to calendar")
    print(f"   POST /auth/logout   → Logout")
    print(f"\n Configuration:")
    print(f"   MOCK_MODE:  {Config.MOCK_MODE}")
    print(f"   RabbitMQ:   {'✅ Configured' if Config.CLOUDAMQP_URL else '❌ Not configured'}")
    print(f"   OpenRouter: {'✅ Configured' if Config.OPENROUTER_API_KEY else '❌ Not configured'}")
    print("\n" + "=" * 70)
    print("✅ Ready for multi-user meeting analysis!")
    print("=" * 70 + "\n")
    
    app.run(host="0.0.0.0", port=Config.PORT, debug=True)