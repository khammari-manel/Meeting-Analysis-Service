from flask import Blueprint, request, jsonify
from flask_login import login_required
from documents.handlers import extract_text_from_file, extract_text_from_url
from ai.parser import extract_insights
from integrations.rabbitmq import send_to_queue
from integrations.whisper_service import (
    transcribe_audio, 
    is_whisper_configured, 
    is_allowed_file,
    get_supported_formats
)
import os
import tempfile
from werkzeug.utils import secure_filename

parse_bp = Blueprint('parse', __name__)

@parse_bp.route('/parse', methods=['POST'])
@login_required
def parse():
    try:
        content = None
        
        if 'file' in request.files:
            file = request.files['file']
            content = extract_text_from_file(file)
        elif 'url' in request.form:
            url = request.form['url']
            content = extract_text_from_url(url)
        else:
            return jsonify({"error": "No file or URL provided"}), 400
        
        if not content or len(content.strip()) == 0:
            return jsonify({"error": "Could not extract text from document"}), 400
        
        print("Extracting insights from document...")
        raw_events = extract_insights(content)
        
        if not raw_events:
            return jsonify({"error": "No events could be extracted"}), 500
        
        try:
            send_to_queue(raw_events)
        except Exception as e:
            print(f"RabbitMQ error (non-critical): {e}")
        
        return jsonify(raw_events), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Error in /parse endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@parse_bp.route('/transcribe', methods=['POST'])
@login_required
def transcribe():
    """
    Transcribe audio/video file to text using Whisper API
    Then optionally analyze it like /parse endpoint
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No audio/video file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Check if Whisper is configured
        if not is_whisper_configured():
            return jsonify({
                "error": "Whisper API not configured. Set OPENAI_API_KEY in .env"
            }), 503
        
        # Validate file type
        if not is_allowed_file(file.filename):
            return jsonify({
                "error": f"Unsupported file format. Allowed: {', '.join(get_supported_formats())}"
            }), 400
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        
        try:
            file.save(temp_path)
            
            # Get language from request (default: German)
            language = request.form.get('language', 'de')
            
            # Transcribe using Whisper
            print(f"Transcribing audio file: {filename}")
            result = transcribe_audio(temp_path, language=language)
            
            if not result['success']:
                return jsonify({"error": result['error']}), 500
            
            transcript = result['transcript']
            
            # Check if user wants immediate analysis
            analyze = request.form.get('analyze', 'false').lower() == 'true'
            
            if analyze:
                # Analyze transcript like /parse endpoint
                print("Analyzing transcript...")
                raw_events = extract_insights(transcript)
                
                if not raw_events:
                    return jsonify({
                        "transcript": transcript,
                        "error": "Transcription successful but no events could be extracted"
                    }), 200
                
                try:
                    send_to_queue(raw_events)
                except Exception as e:
                    print(f"RabbitMQ error (non-critical): {e}")
                
                return jsonify({
                    "transcript": transcript,
                    "events": raw_events
                }), 200
            else:
                # Just return transcript
                return jsonify({
                    "transcript": transcript,
                    "message": "Transcription successful. Use 'analyze=true' to extract action items."
                }), 200
        
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        print(f"Error in /transcribe endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Transcription failed: {str(e)}"}), 500


@parse_bp.route('/transcribe/status', methods=['GET'])
def transcribe_status():
    """Check if Whisper transcription is available"""
    configured = is_whisper_configured()
    return jsonify({
        "available": configured,
        "supported_formats": get_supported_formats(),
        "message": "Whisper API configured" if configured else "Set OPENAI_API_KEY in .env to enable transcription"
    }), 200