"""Jira API routes for creating issues from meeting analysis"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from integrations.jira_integration import (
    create_jira_issues_batch,
    is_jira_configured
)

jira_bp = Blueprint('jira', __name__)


@jira_bp.route('/status', methods=['GET'])
def jira_status():
    """Check if Jira is configured"""
    configured = is_jira_configured()
    
    return jsonify({
        'configured': configured,
        'status': 'ready' if configured else 'not_configured',
        'message': 'Jira integration is ready' if configured else 'Jira credentials not configured in .env'
    })


@jira_bp.route('/create-tasks', methods=['POST'])
@login_required
def create_jira_tasks():
    """
    Create Jira issues from action items
    
    Request body:
    {
        "events": [...]
    }
    
    Response:
    {
        "success": true,
        "created_count": 5,
        "failed_count": 1,
        "issues": [...],
        "failures": [...]
    }
    """
    
    # Check if Jira is configured
    if not is_jira_configured():
        return jsonify({
            'error': 'Jira is not configured. Please contact administrator to set up Jira credentials.',
            'configured': False
        }), 503
    
    # Get request data
    data = request.json
    events = data.get('events', [])
    
    if not events:
        return jsonify({'error': 'No events provided'}), 400
    
    print("\n" + "=" * 60)
    print("📋 JIRA CREATE REQUEST")
    print(f"👤 User: {current_user.email}")
    print(f"📊 Events count: {len(events)}")
    print("=" * 60)
    
    try:
        # Create Jira issues
        result = create_jira_issues_batch(
            events=events,
            user_email=current_user.email
        )
        
        # Build response
        response_data = {
            'success': True,
            'created_count': len(result['created_issues']),
            'failed_count': len(result['failed_issues']),
            'issues': result['created_issues'],
            'failures': result['failed_issues'],
            'user': current_user.email
        }
        
        print("✅ Jira operation completed")
        print(f"   Created: {response_data['created_count']}")
        print(f"   Failed: {response_data['failed_count']}")
        print("=" * 60 + "\n")
        
        return jsonify(response_data)
    
    except Exception as e:
        print(f"❌ Jira error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'error': f'Failed to create Jira issues: {str(e)}'
        }), 500


@jira_bp.route('/preview', methods=['POST'])
@login_required
def preview_jira_tasks():
    """
    Preview which Jira tasks would be created
    
    Returns summary without actually creating issues
    """
    
    data = request.json
    events = data.get('events', [])
    
    # Filter action items
    action_items = [e for e in events if e.get('type') == 'action_item']
    
    # Categorize
    with_assignee = []
    without_assignee = []
    
    for item in action_items:
        if item.get('assignee_email'):
            with_assignee.append({
                'description': item.get('description', 'No description'),
                'assignee': item.get('assignee'),
                'email': item.get('assignee_email'),
                'deadline': item.get('deadline'),
                'priority': item.get('priority', 'medium')
            })
        else:
            without_assignee.append({
                'description': item.get('description', 'No description'),
                'assignee': item.get('assignee', 'Unassigned'),
                'deadline': item.get('deadline'),
                'priority': item.get('priority', 'medium')
            })
    
    return jsonify({
        'total_action_items': len(action_items),
        'with_assignee': len(with_assignee),
        'without_assignee': len(without_assignee),
        'configured': is_jira_configured(),
        'details': {
            'assigned': with_assignee,
            'unassigned': without_assignee
        },
        'user': current_user.email
    })
