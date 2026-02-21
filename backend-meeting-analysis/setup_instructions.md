# Setup Instructions for Team Members

## Quick Start

### 1. Clone the Repository
```bash
git clone https://your-gitlab-url/mkss2.git
cd mkss2
```

### 2. Create Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment

**Copy template:**
```bash
cp .env.example .env
```

**Edit `.env` file:**
```bash
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
SECRET_KEY=generate-this-with-python-command-below
MOCK_MODE=false
```

**Generate secret key:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Get Google OAuth Credentials

**You have two options:**

#### Option A: Use Shared Credentials (Easier)
Ask Manek for the `client_secret.json` file and place it in project root.

#### Option B: Create Your Own (For Testing)
1. Go to https://console.cloud.google.com/
2. Create new project: "MKSS2-Dev-YourName"
3. Enable APIs: Google Calendar API
4. Create OAuth 2.0 Client:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8080/auth/google/callback`
5. Download JSON → rename to `client_secret.json`
6. Place in project root

### 6. Run the Application
```bash
python app.py
```

Should see:
```
 * Running on http://localhost:8080
```

### 7. Open Frontend

Open `index.html` in browser or use:
```bash
# Windows
start index.html


## Testing

### Test with Mock Mode

1. Set `MOCK_MODE=true` in `.env`
2. Upload any text file
3. Will return fake data without calling API

### Test with Real API

1. Set `MOCK_MODE=false` in `.env`
2. Make sure `OPENROUTER_API_KEY` is set
3. Upload real meeting protocol



### CORS Errors

Make sure backend is running on `http://localhost:8080` and frontend accesses same URL.
