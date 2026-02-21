"""Routes for sending email notifications"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from database.models import db
from integrations.email_service import mail, Message
from sqlalchemy import text
import secrets

notification_bp = Blueprint('notifications', __name__)

@notification_bp.route('/send', methods=['POST'])
@login_required
def send_notifications():
    """Send email notifications to all assignees"""
    try:
        # Get events from request
        data = request.json
        events = data.get('events', [])
        
        if not events:
            return jsonify({'error': 'No events provided'}), 400
        
        # Group tasks by email
        tasks_by_email = {}
        for event in events:
            if event.get('type') == 'action_item' and event.get('assignee_email'):
                email = event['assignee_email']
                if email not in tasks_by_email:
                    tasks_by_email[email] = []
                tasks_by_email[email].append(event)
        
        if not tasks_by_email:
            return jsonify({'error': 'No tasks with emails found'}), 400
        
        # Send emails
        sent_count = 0
        for email, tasks in tasks_by_email.items():
            if send_notification_email(email, tasks):
                sent_count += 1
        
        return jsonify({
            'success': True,
            'sent_to': sent_count,
            'total_emails': len(tasks_by_email)
        })
        
    except Exception as e:
        print(f"❌ Error sending notifications: {e}")
        return jsonify({'error': str(e)}), 500

def send_notification_email(to_email, tasks):
    """Send email with Accept/Decline buttons"""
    try:
        # Store tasks in database and generate tokens
        task_data = []
        for task in tasks:
            token = secrets.token_urlsafe(32)
            
            # Insert into database
            db.session.execute(text("""
                INSERT INTO pending_tasks 
                (description, assignee_email, deadline, priority, token)
                VALUES (:desc, :email, :deadline, :priority, :token)
            """), {
                "desc": task.get('description', task.get('message', 'No description')),
                "email": to_email,
                "deadline": task.get('deadline', 'No deadline'),
                "priority": task.get('priority', 'medium'),
                "token": token
            })
            
            task_data.append({
                'task': task,
                'token': token
            })
        
        db.session.commit()
        
        # Get assignee name
        assignee_name = tasks[0].get('assignee', 'Team Member')
        
        # Build email HTML
        high_priority = len([t for t in tasks if t.get('priority') == 'high'])
        
        tasks_html = ""
        for item in task_data:
            task = item['task']
            token = item['token']
            priority = task.get('priority', 'medium')
            description = task.get('description', task.get('message', 'No description'))
            deadline = task.get('deadline', 'No deadline')
            
            priority_color = '#dc3545' if priority == 'high' else '#ffc107' if priority == 'medium' else '#28a745'
            
            tasks_html += f"""
                <div style="background: white; padding: 15px; margin: 10px 0; 
                            border-left: 4px solid {priority_color}; border-radius: 5px;">
                    <p style="margin: 0 0 5px 0;">
                        <span style="display: inline-block; padding: 3px 8px; border-radius: 3px; 
                                     font-size: 12px; font-weight: bold; color: white; background: {priority_color}">
                            {priority.upper()}
                        </span>
                    </p>
                    <p style="margin: 5px 0; font-weight: bold;">{description}</p>
                    <p style="margin: 5px 0; color: #666;">
                        📅 Deadline: <strong>{deadline}</strong>
                    </p>
                    <div style="margin-top: 15px;">
                        <a href="http://localhost:8080/tasks/accept/{token}"
                           style="display: inline-block; padding: 10px 20px; background: #28a745; 
                                  color: white; text-decoration: none; border-radius: 5px; margin-right: 10px;">
                            ✅ Accept & Add to Calendar
                        </a>
                        <a href="http://localhost:8080/tasks/decline/{token}"
                           style="display: inline-block; padding: 10px 20px; background: #dc3545; 
                                  color: white; text-decoration: none; border-radius: 5px;">
                            ❌ Decline
                        </a>
                    </div>
                </div>
            """
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📋 New Tasks Assigned</h2>
                <p>Hi {assignee_name},</p>
            </div>
            
            <div class="content">
                <p>You have been assigned <strong>{len(tasks)}</strong> task(s) from a recent meeting:</p>
                
                {f'<p style="color: #dc3545;">⚠️ <strong>{high_priority}</strong> high priority task(s) require immediate attention!</p>' if high_priority > 0 else ''}
                
                {tasks_html}
            </div>
            
            <div class="footer">
                <p>This is an automated notification from Meeting Analysis Service</p>
                <p>Click "Accept" to add the task to your Google Calendar, or "Decline" to reject it.</p>
            </div>
        </body>
        </html>
        """
        
        # Send email
        msg = Message(
            subject=f"🎯 You have {len(tasks)} new task(s) assigned",
            recipients=[to_email],
            html=html_body
        )
        mail.send(msg)
        
        print(f"✅ Email sent to {to_email} ({len(tasks)} tasks)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
        return False