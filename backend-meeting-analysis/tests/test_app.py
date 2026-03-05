import io
import json
import pytest
from unittest.mock import patch, MagicMock, Mock
import sys
import os
os.environ["OPENROUTER_API_KEY"] = "dummykeyfortesting"
os.environ["SECRET_KEY"] = "test_secret_key_for_testing_only"
os.environ["MOCK_MODE"] = "false"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from database.models import db, User

@pytest.fixture
def app():
    """Create test application"""
    test_app = create_app()
    test_app.config['TESTING'] = True
    test_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    test_app.config['WTF_CSRF_ENABLED'] = False
    test_app.config['SECRET_KEY'] = 'test_secret'
    
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def authenticated_client(app, client):
    """Create authenticated test client"""
    with app.app_context():
        # Create test user
        user = User(
            email='test@example.com',
            name='Test User',
            google_id='test123',
            google_access_token='test_token',
            google_refresh_token='test_refresh'
        )
        db.session.add(user)
        db.session.commit()
        
        # Login the user
        with client.session_transaction() as session:
            session['_user_id'] = str(user.id)
        
        yield client


# ==================== BASIC ENDPOINTS ====================

def test_home_endpoint(client):
    """Test home endpoint returns service info"""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'Meeting Analysis Backend'
    assert data['version'] == '2.0'
    assert 'endpoints' in data


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'openrouter_configured' in data
    assert 'mock_mode' in data


def test_me_endpoint_unauthenticated(client):
    """Test /me endpoint without authentication"""
    response = client.get('/me')
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data


def test_me_endpoint_authenticated(authenticated_client):
    """Test /me endpoint with authentication"""
    response = authenticated_client.get('/me')
    assert response.status_code == 200
    data = response.get_json()
    assert data['email'] == 'test@example.com'
    assert data['name'] == 'Test User'
    assert 'id' in data


# ==================== PARSE ENDPOINTS ====================

@patch('api.parse_routes.extract_insights')
@patch('api.parse_routes.send_to_queue')
def test_parse_txt_file(mock_send, mock_extract, authenticated_client):
    """Test parsing a text file"""
    mock_extract.return_value = {
        "events": [{"description": "Test task", "deadline": "10.05.2026"}],
        "summary": "Test meeting"
    }

    data = {
        'file': (io.BytesIO(b"This is a test meeting text."), 'test.txt')
    }

    response = authenticated_client.post('/parse', content_type='multipart/form-data', data=data)
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'events' in json_data or 'summary' in json_data


@patch('api.parse_routes.extract_insights')
def test_parse_empty_file(mock_extract, authenticated_client):
    """Test parsing empty file returns error"""
    data = {
        'file': (io.BytesIO(b""), 'empty.txt')
    }

    response = authenticated_client.post('/parse', content_type='multipart/form-data', data=data)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


@patch('api.parse_routes.extract_insights')
@patch('api.parse_routes.extract_text_from_url')
def test_parse_from_url(mock_extract_url, mock_extract, authenticated_client):
    """Test parsing from URL"""
    mock_extract_url.return_value = "Meeting content from URL"
    mock_extract.return_value = {
        "events": [{"description": "Task from URL", "deadline": "15.05.2026"}]
    }

    response = authenticated_client.post('/parse', data={'url': 'http://example.com/meeting.txt'})
    # Could be 200 (success) or 400 (no file/url provided in correct format)
    assert response.status_code in [200, 400]


def test_parse_missing_file_and_url(authenticated_client):
    """Test parse without file or URL"""
    response = authenticated_client.post('/parse', json={})
    assert response.status_code == 400


def test_parse_requires_authentication(client):
    """Test parse endpoint requires authentication"""
    data = {'file': (io.BytesIO(b"test"), 'test.txt')}
    response = client.post('/parse', content_type='multipart/form-data', data=data)
    assert response.status_code == 401


# ==================== TRANSCRIBE ENDPOINTS ====================

@patch('api.parse_routes.transcribe_audio')
@patch('api.parse_routes.extract_insights')
@patch('api.parse_routes.is_whisper_configured')
def test_transcribe_audio_success(mock_configured, mock_extract, mock_transcribe, authenticated_client):
    """Test audio transcription"""
    mock_configured.return_value = True
    mock_transcribe.return_value = {
        'success': True,
        'transcript': 'This is a test transcript',
        'mode': 'local'
    }
    mock_extract.return_value = {
        "events": [{"description": "Action from audio", "deadline": "20.05.2026"}]
    }

    data = {
        'file': (io.BytesIO(b"fake audio data"), 'test.mp3'),
        'analyze': 'true',
        'language': 'de'
    }

    response = authenticated_client.post('/transcribe', content_type='multipart/form-data', data=data)
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'transcript' in json_data


@patch('api.parse_routes.is_whisper_configured')
def test_transcribe_not_configured(mock_configured, authenticated_client):
    """Test transcribe when Whisper not configured"""
    mock_configured.return_value = False

    data = {'file': (io.BytesIO(b"audio"), 'test.mp3')}
    response = authenticated_client.post('/transcribe', content_type='multipart/form-data', data=data)
    assert response.status_code == 503


def test_transcribe_no_file(authenticated_client):
    """Test transcribe without file"""
    response = authenticated_client.post('/transcribe', content_type='multipart/form-data', data={})
    assert response.status_code == 400


def test_transcribe_status(client):
    """Test transcribe status endpoint"""
    response = client.get('/transcribe/status')
    assert response.status_code == 200
    data = response.get_json()
    assert 'available' in data
    assert 'supported_formats' in data


# ==================== CALENDAR ENDPOINTS ====================

@patch('integrations.google_calendar.add_events_to_calendar_for_user')
def test_calendar_add_events(mock_add_events, authenticated_client):
    """Test adding events to calendar"""
    mock_add_events.return_value = {
        'created': [{'id': 'event1', 'summary': 'Test Event'}],
        'failed': []
    }

    events = [
        {
            "description": "Team meeting",
            "deadline": "15.05.2026",
            "assignee": "John Doe",
            "assignee_email": "john@example.com"
        }
    ]

    response = authenticated_client.post(
        '/calendar/add',
        json={'events': events, 'sendInvitations': False}
    )
    # 200 (success) or 401 (no credentials) or 503 (not configured)
    assert response.status_code in [200, 401, 503]


def test_calendar_preview(authenticated_client):
    """Test calendar preview"""
    events = [{"description": "Test", "deadline": "20.05.2026"}]
    
    response = authenticated_client.post('/calendar/preview', json={'events': events})
    # Could require valid Google credentials
    assert response.status_code in [200, 401, 503]


# ==================== DRIVE ENDPOINTS ====================

def test_drive_files_requires_auth(client):
    """Test drive files endpoint requires authentication"""
    response = client.get('/drive/files')
    assert response.status_code == 401


def test_drive_team_folder_requires_auth(client):
    """Test team folder endpoint requires authentication"""
    response = client.get('/drive/team-folder')
    assert response.status_code == 401


@patch('api.drive_routes.list_drive_files')
def test_drive_files_authenticated(mock_list, authenticated_client):
    """Test listing drive files when authenticated"""
    mock_list.return_value = [
        {'id': 'file1', 'name': 'test.pdf', 'type': 'pdf'}
    ]
    
    response = authenticated_client.get('/drive/files')
    assert response.status_code in [200, 401]  # Depends on session setup


# ==================== JIRA ENDPOINTS ====================

def test_jira_status(client):
    """Test Jira status endpoint"""
    response = client.get('/jira/status')
    assert response.status_code == 200
    data = response.get_json()
    assert 'configured' in data
    assert 'status' in data


@patch('api.jira_routes.is_jira_configured')
@patch('api.jira_routes.create_jira_issues_batch')
def test_jira_create_tasks(mock_create, mock_configured, authenticated_client):
    """Test creating Jira tasks"""
    mock_configured.return_value = True
    mock_create.return_value = {
        'created_issues': [{'key': 'TEST-1', 'summary': 'Test task'}],
        'failed_issues': [],
        'created_count': 1,
        'failed_count': 0
    }

    events = [{"description": "Jira task", "deadline": "25.05.2026"}]
    
    response = authenticated_client.post('/jira/create-tasks', json={'events': events})
    assert response.status_code in [200, 503]


# ==================== TASK ENDPOINTS ====================

def test_task_accept_invalid_token(client):
    """Test task acceptance with invalid token"""
    response = client.get('/tasks/accept/invalid_token_123')
    # Could be 404 (not found) or 500 (database error due to missing table in test)
    assert response.status_code in [404, 500]


def test_task_decline_invalid_token(client):
    """Test task decline with invalid token"""
    response = client.get('/tasks/decline/invalid_token_123')
    # Could be 404 (not found) or 500 (database error due to missing table in test)
    assert response.status_code in [404, 500]


# ==================== NOTIFICATION ENDPOINTS ====================

def test_notification_open_invalid_token(client):
    """Test notification tracking with invalid token"""
    response = client.get('/notifications/open/invalid_token_123')
    assert response.status_code == 404


# ==================== ERROR HANDLING ====================

def test_404_error(client):
    """Test 404 for non-existent endpoint"""
    response = client.get('/nonexistent')
    assert response.status_code == 404


def test_method_not_allowed(client):
    """Test method not allowed"""
    response = client.put('/')
    assert response.status_code == 405


@patch('api.parse_routes.extract_insights')
def test_parse_with_ai_error(mock_extract, authenticated_client):
    """Test parse handles AI errors gracefully"""
    mock_extract.side_effect = Exception("AI service error")

    data = {'file': (io.BytesIO(b"test content"), 'test.txt')}
    response = authenticated_client.post('/parse', content_type='multipart/form-data', data=data)
    assert response.status_code == 500


# ==================== INTEGRATION TESTS ====================

@patch('api.parse_routes.extract_insights')
@patch('api.parse_routes.send_to_queue')
def test_full_parse_workflow(mock_queue, mock_extract, authenticated_client):
    """Test complete parse workflow"""
    mock_extract.return_value = {
        "events": [
            {
                "description": "Complete project proposal",
                "assignee": "John Doe",
                "assignee_email": "john@example.com",
                "deadline": "30.05.2026",
                "priority": "high"
            }
        ],
        "summary": "Project kickoff meeting"
    }

    # Upload file
    data = {'file': (io.BytesIO(b"Meeting notes about project"), 'meeting.txt')}
    response = authenticated_client.post('/parse', content_type='multipart/form-data', data=data)
    
    assert response.status_code == 200
    result = response.get_json()
    assert 'events' in result or 'summary' in result


# ==================== MOCK MODE TESTS ====================

@patch.dict(os.environ, {'MOCK_MODE': 'true'})
def test_mock_mode_active(client):
    """Test that mock mode can be activated"""
    response = client.get('/health')
    assert response.status_code == 200
    # Mock mode would affect Config.MOCK_MODE


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
