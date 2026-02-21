"""Routes for task acceptance/decline"""
from flask import Blueprint
from database.models import db, User
from integrations.google_calendar import add_events_to_calendar_for_user
from sqlalchemy import text

task_bp = Blueprint('tasks', __name__)

@task_bp.route('/accept/<token>')
def accept_task(token):
    """Accept task and add to calendar"""
    try:
        # Get task from database
        result = db.session.execute(
            text("SELECT * FROM pending_tasks WHERE token = :token AND status = 'pending'"),
            {"token": token}
        ).fetchone()
        
        if not result:
            return "❌ Task not found or already processed", 404
        
        task_id, description, email, deadline, priority, _, status, _ = result
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.google_access_token:
            return f"""
            <html>
            <head><title>Error</title>
            <style>
                body {{ font-family: Arial; display: flex; justify-content: center; 
                       align-items: center; height: 100vh; margin: 0;
                       background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
                .box {{ background: white; padding: 40px; border-radius: 10px; 
                       text-align: center; max-width: 500px; }}
            </style></head>
            <body><div class="box">
                <h1 style="color: #dc3545;">⚠️ Not Connected</h1>
                <p>Please log in to the system first and connect your Google Calendar.</p>
                <a href="http://localhost:8080" style="display: inline-block; margin-top: 20px;
                   padding: 10px 20px; background: #667eea; color: white; 
                   text-decoration: none; border-radius: 5px;">Go to App</a>
            </div></body></html>
            """
        
        # Create event
        events = [{
            "type": "action_item",
            "message": description,
            "deadline": deadline,
            "priority": priority
        }]
        
        # Add to calendar
        count = add_events_to_calendar_for_user(user, events)
        
        if count > 0:
            # Mark as accepted
            db.session.execute(
                text("UPDATE pending_tasks SET status = 'accepted' WHERE token = :token"),
                {"token": token}
            )
            db.session.commit()
            
            return f"""
            <html>
            <head><title>Task Accepted</title>
            <style>
                body {{ font-family: Arial; display: flex; justify-content: center; 
                       align-items: center; height: 100vh; margin: 0;
                       background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
                .box {{ background: white; padding: 40px; border-radius: 10px; 
                       text-align: center; max-width: 500px; }}
                .icon {{ font-size: 64px; margin-bottom: 20px; }}
                .details {{ background: #f0f0f0; padding: 15px; border-radius: 5px; 
                           margin: 20px 0; text-align: left; }}
            </style></head>
            <body><div class="box">
                <div class="icon">✅</div>
                <h1 style="color: #28a745;">Task Accepted!</h1>
                <p>The task has been added to your Google Calendar.</p>
                <div class="details">
                    <p><strong>Task:</strong> {description}</p>
                    <p><strong>Deadline:</strong> {deadline}</p>
                    <p><strong>Priority:</strong> {priority.upper()}</p>
                </div>
                <a href="https://calendar.google.com" target="_blank"
                   style="display: inline-block; padding: 10px 20px; background: #667eea; 
                          color: white; text-decoration: none; border-radius: 5px;">
                    View Calendar
                </a>
            </div></body></html>
            """
        else:
            return "❌ Failed to add to calendar", 500
            
    except Exception as e:
        print(f"❌ Error accepting task: {e}")
        return f"Error: {str(e)}", 500

@task_bp.route('/decline/<token>')
def decline_task(token):
    """Decline task"""
    try:
        # Get task from database
        result = db.session.execute(
            text("SELECT * FROM pending_tasks WHERE token = :token AND status = 'pending'"),
            {"token": token}
        ).fetchone()
        
        if not result:
            return "❌ Task not found or already processed", 404
        
        task_id, description, email, deadline, priority, _, status, _ = result
        
        # Mark as declined
        db.session.execute(
            text("UPDATE pending_tasks SET status = 'declined' WHERE token = :token"),
            {"token": token}
        )
        db.session.commit()
        
        return f"""
        <html>
        <head><title>Task Declined</title>
        <style>
            body {{ font-family: Arial; display: flex; justify-content: center; 
                   align-items: center; height: 100vh; margin: 0;
                   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
            .box {{ background: white; padding: 40px; border-radius: 10px; 
                   text-align: center; max-width: 500px; }}
            .icon {{ font-size: 64px; margin-bottom: 20px; }}
            .details {{ background: #f0f0f0; padding: 15px; border-radius: 5px; 
                       margin: 20px 0; text-align: left; }}
        </style></head>
        <body><div class="box">
            <div class="icon">❌</div>
            <h1 style="color: #dc3545;">Task Declined</h1>
            <p>You have declined this task.</p>
            <div class="details">
                <p><strong>Task:</strong> {description}</p>
                <p><strong>Deadline:</strong> {deadline}</p>
            </div>
            <p style="color: #666; font-size: 14px; margin-top: 20px;">
                If you change your mind, please contact the meeting organizer.
            </p>
        </div></body></html>
        """
        
    except Exception as e:
        print(f"❌ Error declining task: {e}")
        return f"Error: {str(e)}", 500