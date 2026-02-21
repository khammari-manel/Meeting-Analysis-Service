
📅 Automatic meeting protocol analysis with AI-powered task extraction and Google Calendar integration

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![React](https://img.shields.io/badge/React-18-blue.svg)

## 🚀 Features

- ✅ **OAuth 2.0 Authentication** - Secure Google Sign-In
- ✅ **AI-Powered Extraction** - 100% task extraction accuracy
- ✅ **Google Calendar Integration** - Smart invitations with attendee management
- ✅ **Multi-user Support** - Complete user isolation
- ✅ **Document Parsing** - PDF, DOCX, TXT support
- ✅ **Multilingual** - German & English
- ✅ **Microservices Architecture** - Backend + Frontend + Message Queue

## 📁 Project Structure
``````
Meeting-Analysis-Service/
├── backend-meeting-analysis/     # Flask Backend
│   ├── api/                      # API routes
│   ├── ai/                       # AI parsing (OpenRouter)
│   ├── database/                 # SQLAlchemy models
│   ├── integrations/             # Google OAuth & Calendar
│   ├── documents/                # PDF/DOCX handlers
│   └── app.py                    # Main application
├── frontend-meeting-analysis/    # React Frontend
│   ├── src/                      # React components
│   └── index.html                # Main interface
└── message-queue/                # RabbitMQ Configuration
    └── docker-compose.yml
``````

## Installation

### Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend)
- Google Cloud Project with OAuth credentials
- OpenRouter API key

### Backend Setup
``````bash
cd backend-meeting-analysis

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env  # Windows
# or
cp .env.example .env    # Mac/Linux

# Edit .env with your credentials:
# - OPENROUTER_API_KEY
# - SECRET_KEY (generate with: python -c \"import secrets; print(secrets.token_hex(32))\")

# Add client_secret.json from Google Cloud Console

# Run backend
python app.py
``````

Backend runs on: http://localhost:8080

### Frontend Setup
``````bash
cd frontend-meeting-analysis

# Install dependencies
npm install

# Run development server
npm run dev
``````

Frontend runs on: http://localhost:5173

Or use the standalone `index.html` for simple deployment.

##  Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project or select existing
3. Enable **Google Calendar API**
4. Create OAuth 2.0 credentials
5. Add redirect URI: `http://localhost:8080/auth/google/callback`
6. Download JSON as `client_secret.json`
7. Place in `backend-meeting-analysis/` folder

##  Testing
``````bash
# Backend tests
cd backend-meeting-analysis
python -m pytest tests/

# Frontend (standalone)
# Open backend-meeting-analysis/index.html in browser
``````



