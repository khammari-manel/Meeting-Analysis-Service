from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import re


def convert_date(date_str):
    """Convert DD.MM.YYYY to YYYY-MM-DD"""
    if not date_str or date_str == "Not specified":
        return None
    try:
        pattern = r'(\d{2})\.(\d{2})\.(\d{4})'
        match = re.search(pattern, date_str)
        if match:
            day, month, year = match.groups()
            return f"{year}-{month}-{day}"
        return None
    except Exception as e:
        print(f"❌ Date conversion error: {e}")
        return None


def add_events_to_calendar_for_user(access_token, events_data, organizer_email=None, send_invitations=True):
    """
    Add events to Google Calendar with smart attendee handling
    
    Args:
        access_token: User's OAuth token
        events_data: List of events to add
        organizer_email: Email of logged-in user creating events
        send_invitations: Whether to send email invitations to attendees
    
    Returns:
        dict with created_events, personal_tasks, invitations_sent
    """
    credentials = Credentials(token=access_token)
    service = build('calendar', 'v3', credentials=credentials)
    
    created_events = []
    personal_tasks = 0
    invitations_sent = 0
    
    print("=" * 60)
    print(f"📅 Calendar Integration - Adding Events")
    print(f"👤 Organizer: {organizer_email}")
    print(f"📧 Send invitations: {send_invitations}")
    print("=" * 60)
    
    for item in events_data:
        event_type = item.get('type')
        
        # ==================== ACTION ITEMS (TASKS) ====================
        if event_type == 'action_item' and item.get('deadline'):
            date = convert_date(item['deadline'])
            
            if not date:
                print(f"⚠️ Skipping task - invalid date: {item.get('deadline')}")
                continue
            
            assignee = item.get('assignee', 'Unassigned')
            assignee_email = item.get('assignee_email')
            description = item.get('description', 'No description')
            priority = item.get('priority', 'medium')
            
            # Build basic event
            event = {
                'summary': f"{description}",
                'description': f"""Task Assignment

Assignee: {assignee}
Priority: {priority.upper()}
Deadline: {date}

This task was extracted from a meeting protocol.""",
                
                'start': {'date': date},
                'end': {'date': date},
                
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 1440},   # 24h before
                        {'method': 'popup', 'minutes': 1440}
                    ]
                }
            }
            
            # ============ SMART ATTENDEE LOGIC ============
            should_invite = False
            
            if assignee_email and send_invitations:
                # Check if assignee is the same as organizer
                if organizer_email and assignee_email.lower() == organizer_email.lower():
                    # DON'T add as attendee - it's the user's own task
                    print(f"📝 Personal task: {description} (assigned to you)")
                    event['description'] += f"\n\n✓ Your personal task"
                    personal_tasks += 1
                else:
                    # DIFFERENT person - add as attendee
                    event['attendees'] = [
                        {
                            'email': assignee_email,
                            'displayName': assignee,
                            'responseStatus': 'needsAction',
                            'comment': f'Task assigned with {priority} priority'
                        }
                    ]
                    should_invite = True
                    invitations_sent += 1
                    print(f"📧 Task with invitation: {description} → {assignee_email}")
                    event['description'] += f"\n\n✉️ Invitation sent to {assignee}"
            
            # Color code by priority
            if priority == 'high':
                event['colorId'] = '11'  # Red
            elif priority == 'medium':
                event['colorId'] = '5'   # Yellow
            else:
                event['colorId'] = '2'   # Green
            
            try:
                # Insert event
                result = service.events().insert(
                    calendarId='primary',
                    body=event,
                    sendUpdates='all' if should_invite else 'none'
                ).execute()
                
                created_events.append(result)
                print(f"  ✅ Created: {event['summary']}")
                
            except Exception as e:
                print(f"  ❌ Failed: {e}")
        
        # ==================== MILESTONES ====================
        elif event_type == 'milestone' and item.get('date'):
            date = convert_date(item['date'])
            
            if not date:
                print(f"⚠️ Skipping milestone - invalid date: {item.get('date')}")
                continue
            
            event_name = item.get('event', 'Milestone')
            owner = item.get('owner')
            owner_email = item.get('owner_email')
            
            event = {
                'summary': f"📍 {event_name}",
                'description': f"Milestone event\n\nOwner: {owner or 'Team'}",
                'start': {'date': date},
                'end': {'date': date},
                'colorId': '9',  # Blue
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 2880},  # 2 days before
                        {'method': 'popup', 'minutes': 1440}
                    ]
                }
            }
            
            # Add owner as attendee if different person
            should_invite_milestone = False
            if owner_email and send_invitations:
                if organizer_email and owner_email.lower() != organizer_email.lower():
                    event['attendees'] = [
                        {
                            'email': owner_email,
                            'displayName': owner,
                            'responseStatus': 'needsAction'
                        }
                    ]
                    should_invite_milestone = True
                    invitations_sent += 1
            
            try:
                result = service.events().insert(
                    calendarId='primary',
                    body=event,
                    sendUpdates='all' if should_invite_milestone else 'none'
                ).execute()
                
                created_events.append(result)
                print(f"   Created milestone: {event_name}")
                
            except Exception as e:
                print(f"   Failed: {e}")
    
    print("=" * 60)
    print(f" Summary:")
    print(f"   Total created: {len(created_events)}")
    print(f"   Personal tasks: {personal_tasks}")
    print(f"   Invitations sent: {invitations_sent}")
    print("=" * 60)
    
    return {
        'created_events': created_events,
        'personal_tasks': personal_tasks,
        'invitations_sent': invitations_sent
    }