"""Google Drive routes for Meeting Parser"""
from flask import Blueprint, request, jsonify, session
from flask_login import login_required
from integrations.google_drive import list_drive_files, download_drive_file, get_folder_name
from documents.handlers import extract_text_from_bytes
from ai.parser import extract_insights
from integrations.rabbitmq import send_to_queue
from config import Config
import os

drive_bp = Blueprint('drive', __name__)


def get_credentials_from_session():
    """Get Google credentials dict from session"""
    creds = session.get('google_credentials')
    if not creds:
        return None
    return creds


@drive_bp.route('/files', methods=['GET'])
@login_required
def list_files():
    """
    List files in a Drive folder.
    Query param: folder_id (optional) - defaults to My Drive root
    """
    try:
        credentials = get_credentials_from_session()
        if not credentials:
            return jsonify({"error": "No Google credentials found. Please log in again."}), 401

        folder_id = request.args.get('folder_id', None)

        files = list_drive_files(credentials, folder_id=folder_id)

        folder_name = "Mein Drive"
        if folder_id:
            folder_name = get_folder_name(credentials, folder_id)

        return jsonify({
            "files": files,
            "folder_id": folder_id,
            "folder_name": folder_name,
            "count": len(files)
        }), 200

    except Exception as e:
        print(f"Error listing Drive files: {e}")
        return jsonify({"error": f"Could not load Drive files: {str(e)}"}), 500


@drive_bp.route('/team-folder', methods=['GET'])
@login_required
def team_folder():
    """
    List files from the shared team folder.
    Folder ID comes from TEAM_DRIVE_FOLDER_ID in .env
    """
    try:
        credentials = get_credentials_from_session()
        if not credentials:
            return jsonify({"error": "No Google credentials found. Please log in again."}), 401

        team_folder_id = os.getenv('TEAM_DRIVE_FOLDER_ID')
        if not team_folder_id:
            return jsonify({
                "error": "Team folder not configured.",
                "hint": "Add TEAM_DRIVE_FOLDER_ID to your .env file"
            }), 503

        folder_id = request.args.get('folder_id', team_folder_id)

        files = list_drive_files(credentials, folder_id=folder_id)
        folder_name = get_folder_name(credentials, folder_id)

        return jsonify({
            "files": files,
            "folder_id": folder_id,
            "folder_name": folder_name,
            "team_root_id": team_folder_id,
            "count": len(files)
        }), 200

    except Exception as e:
        print(f"Error loading team folder: {e}")
        return jsonify({"error": f"Could not load team folder: {str(e)}"}), 500


@drive_bp.route('/parse', methods=['POST'])
@login_required
def parse_from_drive():
    """
    Download a file from Drive and parse it directly.
    Body: { "file_id": "...", "file_name": "..." }
    """
    try:
        credentials = get_credentials_from_session()
        if not credentials:
            return jsonify({"error": "No Google credentials found. Please log in again."}), 401

        data = request.get_json()
        if not data or 'file_id' not in data:
            return jsonify({"error": "file_id is required"}), 400

        file_id = data['file_id']

        print(f"📥 Downloading file from Drive: {file_id}")
        filename, file_bytes, mime_type = download_drive_file(credentials, file_id)

        print(f"📄 Extracting text from: {filename}")
        content = extract_text_from_bytes(file_bytes, filename)

        if not content or len(content.strip()) == 0:
            return jsonify({"error": "Could not extract text from document"}), 400

        print(f"🤖 Extracting insights from: {filename}")
        raw_events = extract_insights(content)

        if not raw_events:
            return jsonify({"error": "No events could be extracted"}), 500

        try:
            send_to_queue(raw_events)
        except Exception as e:
            print(f"RabbitMQ error (non-critical): {e}")

        return jsonify(raw_events), 200

    except Exception as e:
        print(f"Error in /drive/parse: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Drive parse failed: {str(e)}"}), 500