# MKSS2 - Meeting Analysis Service

Automatic meeting protocol analysis system that extracts tasks and integrates with Google Calendar.

##  Features

- OAuth 2.0 Authentication (Google)
- AI-Powered Task Extraction (100% accuracy)
- Google Calendar Integration with Invitations
- Multi-user Support
- Document Parsing (PDF, DOCX, TXT)
- Multilingual Support (German + English)

##  Prerequisites

- Python 3.8 or higher
- Google Cloud Project with OAuth 2.0 credentials
- OpenRouter API key

##  Installation

### 1. Clone the Repository
```bash
git clone https://your-gitlab-url/mkss2.git
cd mkss2
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a `.env` file in the project root:
```bash
# .env
OPENROUTER_API_KEY=your-openrouter-api-key
MOCK_MODE=false
SECRET_KEY=your-secret-key-here
```

Generate a secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Set Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials (Web application)
5. Add authorized redirect URI: `http://localhost:8080/auth/google/callback`
6. Download credentials as `client_secret.json`
7. Place `client_secret.json` in project root

### 5. Initialize Database
```bash
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

Or simply run the app once - it will create the database automatically.

### 6. Run the Application
```bash
python app.py
```

The application will be available at `http://localhost:8080`

Open `index.html` in your browser.

##  Project Structure
```
mkss2/
├── api/                      # API routes
│   ├── auth_routes.py
│   ├── calendar_routes.py
│   ├── parse_routes.py
│   └── task_routes.py
├── database/                 # Database models
│   └── models.py
├── documents/                # Document handlers
│   └── handlers.py
├── integrations/            # External integrations
│   ├── google_auth.py
│   ├── google_calendar.py
│   └── email_service.py
├── ai/                      # AI parsing
│   └── parser.py
├── app.py                   # Main application
├── config.py                # Configuration
├── index.html               # Frontend
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (NOT in Git)
└── client_secret.json       # Google OAuth (NOT in Git)
```

### "No module named 'flask'"
```bash
pip install -r requirements.txt
```

### "client_secret.json not found"
Make sure you've downloaded OAuth credentials from Google Cloud Console.

### "OPENROUTER_API_KEY not set"
Check that `.env` file exists and contains the API key.

### Database errors
Delete `instance/mkss2.db` and restart the app to recreate database.

