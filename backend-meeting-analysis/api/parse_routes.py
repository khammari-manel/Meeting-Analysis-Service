from flask import Blueprint, request, jsonify
from flask_login import login_required
from documents.handlers import extract_text_from_file, extract_text_from_url
from ai.parser import extract_insights
from integrations.rabbitmq import send_to_queue

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