"""
OpenAI Whisper Integration for Speech-to-Text
Supports both API (paid, fast) and Local (free, slower) modes
"""
import os
import requests
from werkzeug.utils import secure_filename

# OpenAI Whisper API Configuration
WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"
WHISPER_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Local Whisper model (lazy loaded)
LOCAL_WHISPER_MODEL = None

# Supported audio/video formats
ALLOWED_EXTENSIONS = {
    'mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm'
}

# Max file size: 25MB (Whisper API limit, local has no limit but keep for consistency)
MAX_FILE_SIZE = 25 * 1024 * 1024


def is_whisper_configured():
    """Check if any Whisper mode is available (API or local)"""
    # Check if API key is available
    if WHISPER_API_KEY and WHISPER_API_KEY.startswith('sk-'):
        return True
    
    # Check if local whisper is available
    try:
        import whisper
        return True
    except ImportError:
        return False


def get_whisper_mode():
    """Determine which Whisper mode to use"""
    # Prefer API if available (faster)
    if WHISPER_API_KEY and WHISPER_API_KEY.startswith('sk-'):
        return 'api'
    
    # Fallback to local
    try:
        import whisper
        return 'local'
    except ImportError:
        return None


def load_local_whisper_model():
    """Lazy load local Whisper model"""
    global LOCAL_WHISPER_MODEL
    
    if LOCAL_WHISPER_MODEL is not None:
        return LOCAL_WHISPER_MODEL
    
    try:
        import whisper
        print("🎤 Loading local Whisper model (base)... This may take a minute on first run.")
        # Use 'base' model - good balance between speed and accuracy
        # Options: tiny, base, small, medium, large
        LOCAL_WHISPER_MODEL = whisper.load_model("base")
        print("✅ Local Whisper model loaded successfully!")
        return LOCAL_WHISPER_MODEL
    except Exception as e:
        print(f"❌ Failed to load local Whisper model: {e}")
        return None


def is_allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def transcribe_audio(file_path, language='de'):
    """
    Transcribe audio/video file using Whisper (API or local)
    Automatically selects best available method and falls back on errors
    
    Args:
        file_path: Path to audio/video file
        language: Language code (de, en, etc.) - optional, Whisper auto-detects
    
    Returns:
        dict: {
            'success': bool,
            'transcript': str,
            'mode': str ('api' or 'local'),
            'error': str (if failed)
        }
    """
    mode = get_whisper_mode()
    
    if mode is None:
        return {
            'success': False,
            'error': 'Whisper not available. Install with: pip install openai-whisper OR set OPENAI_API_KEY'
        }
    
    # Check file size
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        return {
            'success': False,
            'error': f'File too large. Max size: 25MB, your file: {file_size / 1024 / 1024:.1f}MB'
        }
    
    # Try API first if available (faster)
    if mode == 'api':
        result = transcribe_with_api(file_path, language)
        
        # If API fails with quota error, automatically fallback to local
        if not result['success'] and ('quota' in result.get('error', '').lower() or 'insufficient_quota' in result.get('error', '')):
            print("⚠️  API quota exceeded. Falling back to local Whisper (free)...")
            return transcribe_with_local(file_path, language)
        
        return result
    
    # Otherwise use local Whisper (free)
    return transcribe_with_local(file_path, language)


def transcribe_with_api(file_path, language='de'):
    """Transcribe using OpenAI Whisper API (paid, fast)"""
    try:
        headers = {
            'Authorization': f'Bearer {WHISPER_API_KEY}'
        }
        
        with open(file_path, 'rb') as audio_file:
            files = {
                'file': audio_file,
            }
            data = {
                'model': 'whisper-1',
                'language': language,
                'response_format': 'text'
            }
            
            print(f"🎤 Transcribing with OpenAI API...")
            response = requests.post(
                WHISPER_API_URL,
                headers=headers,
                files=files,
                data=data,
                timeout=300
            )
        
        if response.status_code == 200:
            transcript = response.text
            return {
                'success': True,
                'transcript': transcript,
                'mode': 'api',
                'language': language
            }
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
            error_message = error_data.get('error', {}).get('message', response.text)
            
            # If quota exceeded, suggest local mode
            if 'quota' in error_message.lower() or 'insufficient_quota' in response.text:
                return {
                    'success': False,
                    'error': f'OpenAI quota exceeded. Install local Whisper (free): pip install openai-whisper'
                }
            
            return {
                'success': False,
                'error': f'Whisper API error: {error_message}'
            }
    
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Transcription timeout. File may be too large or API is slow.'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'API transcription failed: {str(e)}'
        }


def transcribe_with_local(file_path, language='de'):
    """Transcribe using local Whisper model (free, slower)"""
    try:
        model = load_local_whisper_model()
        
        if model is None:
            return {
                'success': False,
                'error': 'Could not load local Whisper model. Install with: pip install openai-whisper'
            }
        
        print(f"🎤 Transcribing with local Whisper (this may take 30-60 seconds)...")
        
        # Transcribe
        result = model.transcribe(
            file_path,
            language=language if language != 'de' else 'german',  # Whisper uses full language names
            fp16=False  # Use FP32 for CPU compatibility
        )
        
        transcript = result['text']
        
        print(f"✅ Local transcription complete!")
        
        return {
            'success': True,
            'transcript': transcript,
            'mode': 'local',
            'language': language
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'Local transcription failed: {str(e)}'
        }


def transcribe_with_timestamps(file_path, language='de'):
    """
    Transcribe with timestamps (verbose JSON format)
    Useful for identifying when action items were mentioned
    
    Returns:
        dict: {
            'success': bool,
            'transcript': str (full text),
            'segments': list (with timestamps),
            'error': str (if failed)
        }
    """
    if not is_whisper_configured():
        return {
            'success': False,
            'error': 'Whisper API key not configured'
        }
    
    try:
        headers = {
            'Authorization': f'Bearer {WHISPER_API_KEY}'
        }
        
        with open(file_path, 'rb') as audio_file:
            files = {
                'file': audio_file,
            }
            data = {
                'model': 'whisper-1',
                'language': language,
                'response_format': 'verbose_json',
                'timestamp_granularities[]': 'segment'
            }
            
            response = requests.post(
                WHISPER_API_URL,
                headers=headers,
                files=files,
                data=data,
                timeout=300
            )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'transcript': result.get('text', ''),
                'segments': result.get('segments', []),
                'language': result.get('language', language)
            }
        else:
            return {
                'success': False,
                'error': f'API error: {response.text}'
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'Transcription with timestamps failed: {str(e)}'
        }


def get_supported_formats():
    """Return list of supported audio/video formats"""
    return list(ALLOWED_EXTENSIONS)
