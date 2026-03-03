"""Jira Integration - Create issues from action items"""
import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

# Jira Configuration
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")  # e.g. "https://your-company.atlassian.net"
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "MKSS")  # Default: MKSS


def is_jira_configured():
    """Check if Jira is properly configured"""
    return bool(JIRA_BASE_URL and JIRA_EMAIL and JIRA_API_TOKEN)


def get_auth_header():
    """Generate Basic Auth header for Jira API"""
    if not JIRA_EMAIL or not JIRA_API_TOKEN:
        raise ValueError("Jira credentials not configured")
    
    auth_string = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    auth_bytes = auth_string.encode('ascii')
    base64_bytes = base64.b64encode(auth_bytes)
    return base64_bytes.decode('ascii')


def convert_date_to_jira(date_str):
    """Convert DD.MM.YYYY to YYYY-MM-DD for Jira"""
    if not date_str:
        return None
    
    try:
        from datetime import datetime
        # Try DD.MM.YYYY format
        date_obj = datetime.strptime(date_str, "%d.%m.%Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        # Already in correct format or invalid
        return date_str if date_str else None


def create_jira_issue(event, user_email=None):
    """
    Create a Jira issue from an action item
    
    Args:
        event: Action item dict with description, assignee_email, deadline, priority
        user_email: Email of the user creating the issue (for tracking)
    
    Returns:
        dict with success status, issue_key, and url or error message
    """
    
    if not is_jira_configured():
        return {
            "success": False,
            "error": "Jira is not configured. Please set JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN in .env"
        }
    
    try:
        # Build authentication
        auth_header = get_auth_header()
        
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Map priority
        priority_map = {
            "high": "Highest",
            "medium": "Medium",
            "low": "Low"
        }
        
        # Build description text
        description_text = f"Extracted from meeting protocol\n\n"
        
        if event.get('deadline'):
            description_text += f"Deadline: {event.get('deadline')}\n"
        
        if event.get('assignee'):
            description_text += f"Assignee: {event.get('assignee')}\n"
        
        if user_email:
            description_text += f"\nCreated by: {user_email}"
        
        # Build Jira issue payload (Atlassian Document Format)
        payload = {
            "fields": {
                "project": {
                    "key": JIRA_PROJECT_KEY
                },
                "summary": event.get('description', 'Task from Meeting'),
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description_text
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {
                    "name": "Task"
                },
                "priority": {
                    "name": priority_map.get(event.get('priority', 'medium'), 'Medium')
                }
            }
        }
        
        # Add assignee if email exists
        assignee_email = event.get('assignee_email')
        if assignee_email:
            # First, find user by email
            user_search_url = f"{JIRA_BASE_URL}/rest/api/3/user/search"
            user_search_params = {"query": assignee_email}
            user_search_response = requests.get(
                user_search_url,
                headers=headers,
                params=user_search_params
            )
            
            if user_search_response.status_code == 200:
                users = user_search_response.json()
                if users and len(users) > 0:
                    # Use accountId for Jira Cloud
                    payload["fields"]["assignee"] = {
                        "accountId": users[0]["accountId"]
                    }
                    print(f"  ✅ Found Jira user: {users[0].get('displayName')} ({assignee_email})")
                else:
                    print(f"  ⚠️ No Jira user found for {assignee_email}")
            else:
                print(f"  ⚠️ Could not search for assignee: {user_search_response.text}")
        
        # Add due date if deadline exists
        deadline = event.get('deadline')
        if deadline:
            jira_date = convert_date_to_jira(deadline)
            if jira_date:
                payload["fields"]["duedate"] = jira_date
        
        # Add labels
        payload["fields"]["labels"] = ["meeting-analysis", "auto-created"]
        
        # Create issue
        create_url = f"{JIRA_BASE_URL}/rest/api/3/issue"
        response = requests.post(
            create_url,
            headers=headers,
            json=payload
        )
        
        if response.status_code == 201:
            issue_data = response.json()
            issue_key = issue_data["key"]
            issue_url = f"{JIRA_BASE_URL}/browse/{issue_key}"
            
            print(f"  ✅ Created Jira issue: {issue_key}")
            
            return {
                "success": True,
                "issue_key": issue_key,
                "issue_url": issue_url,
                "issue_id": issue_data.get("id")
            }
        else:
            error_msg = response.text
            print(f"  ❌ Failed to create issue: {error_msg}")
            return {
                "success": False,
                "error": f"Jira API error ({response.status_code}): {error_msg}"
            }
    
    except Exception as e:
        print(f"  ❌ Exception creating Jira issue: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Exception: {str(e)}"
        }


def create_jira_issues_batch(events, user_email=None):
    """
    Create multiple Jira issues from action items
    
    Args:
        events: List of event dicts
        user_email: Email of the user creating the issues
    
    Returns:
        dict with created_issues list and failed_issues list
    """
    
    if not is_jira_configured():
        return {
            "created_issues": [],
            "failed_issues": [],
            "error": "Jira is not configured"
        }
    
    created_issues = []
    failed_issues = []
    
    print("=" * 60)
    print("📋 Creating Jira Issues")
    print(f"👤 User: {user_email}")
    print(f"📊 Total events: {len(events)}")
    print("=" * 60)
    
    action_items = [e for e in events if e.get('type') == 'action_item']
    print(f"  Found {len(action_items)} action items")
    
    for event in action_items:
        result = create_jira_issue(event, user_email)
        
        if result['success']:
            created_issues.append({
                'task': event.get('description', 'No description'),
                'assignee': event.get('assignee'),
                'assignee_email': event.get('assignee_email'),
                'deadline': event.get('deadline'),
                'priority': event.get('priority', 'medium'),
                'jira_key': result['issue_key'],
                'jira_url': result['issue_url']
            })
        else:
            failed_issues.append({
                'task': event.get('description', 'No description'),
                'assignee': event.get('assignee'),
                'error': result['error']
            })
    
    print("=" * 60)
    print(f"✅ Created: {len(created_issues)} issues")
    print(f"❌ Failed: {len(failed_issues)} issues")
    print("=" * 60)
    
    return {
        "created_issues": created_issues,
        "failed_issues": failed_issues
    }
