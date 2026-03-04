"""Google Drive integration for Meeting Parser"""
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
import io

# Only show these file types in the browser
ALLOWED_MIME_TYPES = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
    'text/plain',  # .txt
    'application/vnd.google-apps.folder',  # folders for navigation
    'audio/mpeg',      # MP3
    'audio/mp4',       # M4A
    'audio/wav',       # WAV
    'audio/webm',      # WebM
    'video/mp4'        # MP4
]

MIME_TO_EXT = {
    'application/pdf': 'pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'text/plain': 'txt',
    'application/vnd.google-apps.folder': 'folder'
}


def build_drive_service(credentials_dict: dict):
    """Build Google Drive API service from credentials dict (stored in session)"""
    creds = Credentials(
        token=credentials_dict.get('token'),
        refresh_token=credentials_dict.get('refresh_token'),
        token_uri=credentials_dict.get('token_uri', 'https://oauth2.googleapis.com/token'),
        client_id=credentials_dict.get('client_id'),
        client_secret=credentials_dict.get('client_secret'),
        scopes=credentials_dict.get('scopes')
    )
    return build('drive', 'v3', credentials=creds)


def list_drive_files(credentials_dict: dict, folder_id: str = None) -> list:
    """
    List files and folders in a specific Drive folder.
    If folder_id is None, lists root 'My Drive'.
    Returns only PDF, DOCX, TXT files and subfolders.
    """
    service = build_drive_service(credentials_dict)

    if folder_id:
        query = f"'{folder_id}' in parents and trashed = false"
    else:
        query = "'root' in parents and trashed = false"

    # Filter: only allowed mime types
    mime_filter = " or ".join([f"mimeType = '{m}'" for m in ALLOWED_MIME_TYPES])
    query += f" and ({mime_filter})"

    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType, modifiedTime, size, parents)",
        orderBy="folder,name",
        pageSize=100
    ).execute()

    files = results.get('files', [])

    # Format output
    formatted = []
    for f in files:
        mime = f.get('mimeType', '')
        formatted.append({
            'id': f['id'],
            'name': f['name'],
            'mimeType': mime,
            'type': MIME_TO_EXT.get(mime, 'file'),
            'modifiedTime': f.get('modifiedTime', ''),
            'size': int(f.get('size', 0)) if f.get('size') else None,
            'isFolder': mime == 'application/vnd.google-apps.folder'
        })

    return formatted


def get_folder_name(credentials_dict: dict, folder_id: str) -> str:
    """Get the name of a folder by its ID"""
    try:
        service = build_drive_service(credentials_dict)
        folder = service.files().get(fileId=folder_id, fields='name').execute()
        return folder.get('name', folder_id)
    except Exception:
        return folder_id


def download_drive_file(credentials_dict: dict, file_id: str) -> tuple:
    """
    Download a file from Google Drive.
    Returns (filename, bytes_content, mime_type)
    """
    service = build_drive_service(credentials_dict)

    # Get file metadata
    file_meta = service.files().get(
        fileId=file_id,
        fields='name, mimeType, size'
    ).execute()

    filename = file_meta['name']
    mime_type = file_meta['mimeType']

    # Download file content
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    buffer.seek(0)
    return filename, buffer.read(), mime_type
