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

### 3.1 Install ffmpeg (Required for Speech-to-Text)

**Was ist ffmpeg?**
ffmpeg ist ein Audio/Video-Decoder, den OpenAI Whisper benötigt, um Audio-Dateien (MP3, WAV, M4A, etc.) zu verarbeiten. Ohne ffmpeg kann Whisper keine Audio-Dateien transkribieren.

**Windows (mit Admin-Rechten - EMPFOHLEN):**
```powershell
# PowerShell als Administrator öffnen (Rechtsklick → "Als Administrator ausführen")
choco install ffmpeg -y
# ODER
winget install ffmpeg
```

**Windows (ohne Admin):**
1. Download: https://github.com/BtbN/FFmpeg-Builds/releases
2. Suche: `ffmpeg-master-latest-win64-gpl.zip` (~100MB)
3. Entpacke nach `C:\ffmpeg\`
4. Füge `C:\ffmpeg\bin` zu PATH hinzu:
   - Windows-Suche: "Umgebungsvariablen"
   - "Umgebungsvariablen bearbeiten"
   - Unter "Benutzervariablen" → PATH → "Bearbeiten" → "Neu"
   - Pfad hinzufügen: `C:\ffmpeg\bin`
   - Alle Fenster mit "OK" schließen
5. **PowerShell NEU STARTEN** (wichtig!)

**Mac:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Testen (nach Installation PowerShell NEU STARTEN!):**
```bash
ffmpeg -version
```

Du solltest die ffmpeg-Version sehen (z.B. `ffmpeg version 8.0.1`).

> ⚠️ **WICHTIG:** 
> - ffmpeg MUSS installiert sein, sonst funktioniert Speech-to-Text nicht!
> - Nach Installation: PowerShell/Terminal NEU STARTEN
> - Bei Fehler "Das System kann die angegebene Datei nicht finden" → ffmpeg fehlt

### 3.2 Install OpenAI Whisper (Automatisch bei pip install)

Das lokale Whisper-Paket wird automatisch mit `pip install -r requirements.txt` installiert.

**Was ist Whisper?**
- OpenAI's Speech-to-Text AI (Open Source, kostenlos)
- Läuft lokal auf deinem Computer (keine API-Kosten)
- Unterstützt 99+ Sprachen (Deutsch, Englisch, etc.)
- Base-Modell: ~140MB, gute Balance zwischen Geschwindigkeit/Qualität

**Beim ersten Mal:**
- Whisper lädt automatisch das Base-Modell (~140MB) herunter
- Dauert ca. 1-2 Minuten (nur einmal!)
- Modell wird gespeichert: `~/.cache/whisper/`

**Danach:**
- Transkription: ~30-60 Sekunden pro Minute Audio
- Komplett offline und kostenlos
- Keine API-Limits

**Verfügbare Modelle (optional):**
Standardmäßig nutzen wir das `base` Modell (empfohlen). Änderbar in `integrations/whisper_service.py`:
- `tiny`: 39MB, sehr schnell, weniger genau
- `base`: 74MB, schnell, gut genau ✅ (Standard)
- `small`: 244MB, langsamer, sehr genau
- `medium`: 769MB, langsam, sehr genau
- `large`: 1550MB, sehr langsam, höchste Genauigkeit

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

# Optional: OpenAI API Key für Whisper API (kostenpflichtig)
# Wenn nicht gesetzt, wird automatisch lokales Whisper verwendet (kostenlos)
# OPENAI_API_KEY=sk-proj-your-key-here
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
```

## Features

### 📄 Document Analysis
- Upload PDF, DOCX, TXT meeting protocols
- AI-powered extraction of action items, dates, attendees
- Google Calendar & Jira integration

### 🎤 Speech-to-Text (Audio/Video Transcription)
- Upload MP3, MP4, WAV, M4A, WebM (max 25MB)
- Automatic transcription with OpenAI Whisper (local, FREE)
- First transcription: 1-2 minutes (downloads model ~140MB)
- Subsequent transcriptions: 30-60 seconds per minute of audio
- Automatically analyzes transcript with AI

## Testing

### Test with Mock Mode

1. Set `MOCK_MODE=true` in `.env`
2. Upload any text file
3. Will return fake data without calling API

### Test with Real API

1. Set `MOCK_MODE=false` in `.env`
2. Make sure `OPENROUTER_API_KEY` is set
3. Upload real meeting protocol

### Test Speech-to-Text

1. Make sure ffmpeg is installed: `ffmpeg -version`
2. Sign in with Google in the app
3. Upload audio/video file (MP3, WAV, M4A, etc.)
4. Click "🎤 Transkribieren & Analysieren"
5. Wait for transcription (first time takes longer)
6. View transcript and extracted action items



### CORS Errors

Make sure backend is running on `http://localhost:8080` and frontend accesses same URL.
