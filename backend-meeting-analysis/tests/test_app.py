import io
import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os
os.environ["OPENROUTER_API_KEY"] = "dummykeyfortesting"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# Mock für extract_insights
@patch("app.extract_insights")
@patch("app.send_to_queue_batch")
def test_parse_txt_file(mock_send, mock_extract, client):
    mock_extract.return_value = [{"type": "decision", "text": "Approve budget"}]

    data = {
        'file': (io.BytesIO(b"This is a test meeting text."), 'test.txt')
    }

    response = client.post('/parse', content_type='multipart/form-data', data=data)

    assert response.status_code == 200
    json_data = response.get_json()
    assert "events" in json_data
    assert json_data["message"] == "Successfully parsed and sent to queue"
    mock_send.assert_called_once()


@patch("app.extract_insights")
@patch("app.send_to_queue_batch")
def test_parse_empty_file(mock_send, mock_extract, client):
    data = {
        'file': (io.BytesIO(b""), 'empty.txt')
    }

    response = client.post('/parse', content_type='multipart/form-data', data=data)
    assert response.status_code == 400
    assert "Extrahierter Text ist leer" in response.get_data(as_text=True)
    mock_send.assert_not_called()


@patch("app.extract_insights")
@patch("app.send_to_queue_batch")
def test_parse_from_url(mock_send, mock_extract, client):
    mock_extract.return_value = [{"type": "action", "text": "Send email"}]

    with patch("app.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "Meeting content from URL"

        response = client.post('/parse', json={"url": "http://example.com/mom.txt"})
        assert response.status_code == 200
        assert "events" in response.get_json()
        mock_send.assert_called_once()
        mock_extract.assert_called_once()


@patch("app.extract_insights")
def test_extract_insights_returns_invalid_json(mock_extract, client):
    mock_extract.return_value = "this is not json"
    data = {
        'file': (io.BytesIO(b"Some text"), 'test.txt')
    }

    response = client.post('/parse', content_type='multipart/form-data', data=data)
    assert response.status_code == 500
    assert "AI response is not valid JSON" in response.get_data(as_text=True)


def test_missing_file_and_url(client):
    response = client.post('/parse', json={})
    assert response.status_code == 400
    assert "Provide either 'file' or 'url'" in response.get_data(as_text=True)


def test_url_fetch_fails(client):
    with patch("app.requests.get") as mock_get:
        mock_get.side_effect = Exception("Not reachable")
        response = client.post('/parse', json={"url": "http://invalid.url"})
        assert response.status_code == 400
        assert "Failed to fetch URL" in response.get_data(as_text=True)
