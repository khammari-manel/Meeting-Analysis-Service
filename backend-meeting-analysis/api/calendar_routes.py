from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from integrations.google_calendar import add_events_to_calendar_for_user

calendar_bp = Blueprint('calendar', __name__)


@calendar_bp.route('/add', methods=['POST'])
@login_required
def add_to_calendar():
    """
    Add events to user's Google Calendar
    
    Request body:
    {
        "events": [...],
        "sendInvitations": true/false
    }
    """
    
    # Check if user has calendar access
    if not current_user.google_access_token:
        return jsonify({
            'error': 'Calendar not connected. Please sign in with Google first.'
        }), 401
    
    # Get request data
    data = request.json
    events_data = data.get('events')
    send_invitations = data.get('sendInvitations', True)  # Default: true
    
    if not events_data:
        return jsonify({'error': 'No events provided'}), 400
    
    print("\n" + "=" * 60)
    print("📅 CALENDAR ADD REQUEST")
    print(f"👤 User: {current_user.email}")
    print(f"📊 Events count: {len(events_data)}")
    print(f"📧 Send invitations: {send_invitations}")
    print("=" * 60)
    
    try:
        # Call calendar integration
        result = add_events_to_calendar_for_user(
            access_token=current_user.google_access_token,
            events_data=events_data,
            organizer_email=current_user.email,
            send_invitations=send_invitations
        )
        
        # Build response
        response_data = {
            'status': 'success',
            'created_count': len(result['created_events']),
            'personal_tasks': result['personal_tasks'],
            'invitations_sent': result['invitations_sent'],
            'organizer': current_user.email,
            'organizer_name': current_user.name
        }
        
        print("✅ Calendar operation successful")
        print(f"   Created: {response_data['created_count']}")
        print(f"   Personal: {response_data['personal_tasks']}")
        print(f"   Invitations: {response_data['invitations_sent']}")
        print("=" * 60 + "\n")
        
        return jsonify(response_data)
    
    except Exception as e:
        print(f"❌ Calendar error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'error': f'Failed to add events to calendar: {str(e)}'
        }), 500


@calendar_bp.route('/preview', methods=['POST'])
@login_required
def preview_invitations():
    """
    Preview what invitations would be sent without actually creating events
    
    Useful for showing user a confirmation dialog
    """
    data = request.json
    events_data = data.get('events', [])
    
    # Count tasks by category
    tasks_for_self = []
    tasks_for_others = []
    tasks_without_email = []
    
    for event in events_data:
        if event.get('type') == 'action_item':
            assignee_email = event.get('assignee_email')
            assignee = event.get('assignee', 'Unknown')
            description = event.get('description', 'No description')
            
            if not assignee_email:
                tasks_without_email.append({
                    'assignee': assignee,
                    'description': description
                })
            elif assignee_email.lower() == current_user.email.lower():
                tasks_for_self.append({
                    'assignee': assignee,
                    'description': description
                })
            else:
                tasks_for_others.append({
                    'assignee': assignee,
                    'email': assignee_email,
                    'description': description
                })
    
    return jsonify({
        'total_events': len(events_data),
        'tasks_for_self': len(tasks_for_self),
        'tasks_for_others': len(tasks_for_others),
        'tasks_without_email': len(tasks_without_email),
        'details': {
            'self': tasks_for_self,
            'others': tasks_for_others,
            'no_email': tasks_without_email
        },
        'organizer': current_user.email,
        'organizer_name': current_user.name
    })