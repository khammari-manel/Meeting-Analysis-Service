# Tests für Meeting Analysis Backend

## Setup

Installiere die Test-Dependencies:

```bash
pip install pytest pytest-mock pytest-cov
```

Oder installiere alle requirements inklusive Testing:

```bash
pip install -r requirements.txt
```

## Tests ausführen

### Alle Tests ausführen

```bash
# Im backend-meeting-analysis Verzeichnis
pytest tests/

# Mit verbose output
pytest tests/ -v

# Mit Coverage Report
pytest tests/ --cov=. --cov-report=html
```

### Einzelne Test-Datei ausführen

```bash
pytest tests/test_app.py -v
```

### Spezifischen Test ausführen

```bash
pytest tests/test_app.py::test_home_endpoint -v
```

## Test-Kategorien

Die Tests decken folgende Bereiche ab:

### 1. Basic Endpoints
- `test_home_endpoint` - Service Info
- `test_health_endpoint` - Health Check
- `test_me_endpoint_*` - User Info (authenticated/unauthenticated)

### 2. Parse Endpoints
- `test_parse_txt_file` - Dokument-Upload
- `test_parse_empty_file` - Fehlerbehandlung
- `test_parse_from_url` - URL-Parsing
- `test_parse_requires_authentication` - Auth-Check

### 3. Transcription
- `test_transcribe_audio_success` - Audio-Transkription
- `test_transcribe_not_configured` - Whisper-Check
- `test_transcribe_status` - Status-Endpoint

### 4. Calendar Integration
- `test_calendar_add_events` - Events hinzufügen
- `test_calendar_preview` - Event-Vorschau

### 5. Google Drive
- `test_drive_files_*` - Drive-Dateien auflisten
- `test_drive_team_folder_*` - Team-Ordner

### 6. Jira Integration
- `test_jira_status` - Jira-Status
- `test_jira_create_tasks` - Tasks erstellen

### 7. Error Handling
- `test_404_error` - 404-Fehler
- `test_method_not_allowed` - 405-Fehler
- `test_parse_with_ai_error` - AI-Fehler

### 8. Integration Tests
- `test_full_parse_workflow` - Kompletter Workflow

## Fixtures

### `app`
Erstellt eine Test-Flask-App mit In-Memory Database

### `client`
Test-Client für HTTP-Requests

### `authenticated_client`
Test-Client mit eingeloggtem User

## Mocking

Die Tests verwenden Mocks für:
- `extract_insights` - AI-Parser
- `send_to_queue` - RabbitMQ
- `transcribe_audio` - Whisper
- `create_calendar_events` - Google Calendar
- `list_drive_files` - Google Drive
- `create_jira_issues` - Jira API

## Coverage Report

Nach dem Ausführen mit `--cov`:

```bash
# HTML Report öffnen
open htmlcov/index.html  # Mac/Linux
start htmlcov/index.html # Windows
```

## Umgebungsvariablen für Tests

Die Tests setzen automatisch:
- `OPENROUTER_API_KEY=dummykeyfortesting`
- `SECRET_KEY=test_secret_key_for_testing_only`
- `MOCK_MODE=false`

## Continuous Integration

Beispiel für GitHub Actions:

```yaml
- name: Run Tests
  run: |
    pip install -r requirements.txt
    pytest tests/ -v --cov=. --cov-report=xml
```

## Troubleshooting

### Import-Fehler
Stelle sicher, dass du im richtigen Verzeichnis bist:
```bash
cd backend-meeting-analysis
pytest tests/
```

### Database-Fehler
Tests verwenden SQLite In-Memory Database - keine Migration nötig.

### Mock-Fehler
Prüfe, ob `pytest-mock` installiert ist:
```bash
pip install pytest-mock
```

## Neue Tests hinzufügen

1. Erstelle Test-Funktion mit `test_` Prefix
2. Verwende Fixtures: `client`, `authenticated_client`
3. Mocke externe Abhängigkeiten mit `@patch`
4. Assertions mit `assert`

Beispiel:

```python
@patch('api.parse_routes.extract_insights')
def test_my_new_feature(mock_extract, authenticated_client):
    mock_extract.return_value = {"test": "data"}
    response = authenticated_client.post('/endpoint', json={})
    assert response.status_code == 200
```
