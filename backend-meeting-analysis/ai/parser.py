import os
import json
import re
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

# Get the OpenRouter API key and mock mode from environment variables
api_key = os.getenv("OPENROUTER_API_KEY")
mock_mode = os.getenv("MOCK_MODE", "false").lower() == "true"
print("✅ MOCK_MODE aktiviert:", mock_mode)

if not api_key and not mock_mode:
    raise ValueError("Bitte OPENROUTER_API_KEY in der Umgebung setzen!")
# API Configuration
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "mistralai/mistral-7b-instruct"
HEADERS = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost",
    "X-Title": "meeting-parser",
}


def build_prompt(text):
    """Comprehensive prompt - handles formal, informal, English, German protocols."""
    return f"""[INST] You are an expert meeting protocol analyzer. Extract ALL tasks, decisions, participants, and events.

═══════════════════════════════════════════════════════════════════
STEP 1: EXTRACT PARTICIPANTS FIRST
═══════════════════════════════════════════════════════════════════

Look for sections named:
- "ATTENDEES" / "Attendees:" / "PARTICIPANTS"
- "Teilnehmer:" (German)

Extract ALL name-email pairs using these patterns:
✓ "Name Email" → e.g., "Manel Khammari khamarimanel11@gmail.com"
✓ "Name, Email" → e.g., "Lena M., lena@company.com"
✓ "Name (Email)" → e.g., "Thomas (thomas@company.com)"
✓ Emails mentioned anywhere in document

Create a NAME → EMAIL mapping to use for task assignments.

═══════════════════════════════════════════════════════════════════
STEP 2: EXTRACT ACTION ITEMS
═══════════════════════════════════════════════════════════════════

Search the ENTIRE document (not just specific sections) for tasks using these patterns:

FORMAL PATTERNS:
✓ "Action: Name to do X by DATE"
✓ "Name will do X by DATE"
✓ "Name should do X by DATE"
✓ "Name must do X by DATE"
✓ "Name needs to do X by DATE"
✓ "Name agreed to do X by DATE"
✓ "Name volunteered to do X"
✓ "Name (email@domain.com) will do X by DATE"
✓ "email@domain.com will do X by DATE"

GERMAN STANDUP PATTERNS:
✓ "Name - does X" (in Standup section)
✓ "Name: does X" (in task sections)
✓ "Ticket ### Description → Name"
✓ Tasks under "Aufgaben zu nächster Woche"
✓ Tasks under "Neue Tickets"

IMPLICIT PATTERNS:
✓ Sentences in DECISION, AGREEMENT, ACTION REQUIRED, RESPONSIBILITIES sections
✓ "Someone should..." → task with no assignee
✓ "We need to..." → team task

SECTIONS TO CHECK:
- Entire document (don't limit to specific sections!)
- DECISION sections
- ACTION sections
- ACTION REQUIRED sections
- AGREEMENT sections
- RESPONSIBILITIES sections
- Standup sections
- "Aufgaben zu nächster Woche" (German: Tasks for next week)
- "Neue Tickets" (German: New tickets)

FOR EACH TASK EXTRACT:
- **description**: Clear task description
- **assignee**: Person NAME (not email)
- **assignee_email**: Email address (lookup from participants or extract from text)
- **deadline**: Date in DD.MM.YYYY format
- **priority**: high/medium/low

═══════════════════════════════════════════════════════════════════
STEP 3: DATE CONVERSION
═══════════════════════════════════════════════════════════════════

Convert ALL dates to DD.MM.YYYY format (assume year 2026 if not specified):

ENGLISH DATES:
- "June 17" → 17.06.2026
- "Friday (June 13)" → 13.06.2026
- "next Tuesday (June 17)" → 17.06.2026
- "February 18th" → 18.02.2026
- "March 1st" → 01.03.2026
- "by end of this week" → find closest Friday
- "Thursday EOD" → find Thursday date

GERMAN DATES:
- "17.06.2025" → 17.06.2025 (keep as is)
- "01.07.2025" → 01.07.2025
- "Ende august" → 31.08.2026

RELATIVE DATES:
- "next week" → next Monday
- "by Friday noon" → find Friday date

═══════════════════════════════════════════════════════════════════
CRITICAL EXTRACTION RULES
═══════════════════════════════════════════════════════════════════

1. **IMPEDIMENTS = RISKS**: "impediments", "Hindernis" → extract as RISK
2. **PROBLEMS = RISKS**: "problems", "Problem" → extract as RISK  
3. **BLOCKERS = RISKS**: "blocker", "Blocker" → extract as RISK
4. **ISSUES = RISKS**: "issues" → extract as RISK
5. **TICKETS = ACTION ITEMS**: "Ticket XX → Name" → Name assigned to Ticket XX
6. **DATES = MILESTONES**: "DD.MM.YYYY event description" → milestone
7. **DEADLINES = COMPLIANCE**: "documentation must be finished by X" → compliance
8. **Extract participants BEFORE extracting tasks** (to map names → emails)
9. **Include ALL tasks**, even if assignee unclear
10. **Use participant list to find emails** for task assignees

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT (VALID JSON ONLY)
═══════════════════════════════════════════════════════════════════

{{
  "participants": [
    {{
      "name": "Full Name",
      "email": "email@domain.com"
    }}
  ],
  "action_items": [
    {{
      "description": "Task description",
      "assignee": "Person Name",
      "assignee_email": "email@domain.com",
      "deadline": "DD.MM.YYYY",
      "priority": "high|medium|low"
    }}
  ],
  "decisions": ["Decision text"],
  "changes": ["Change description"],
  "risks": [
    {{
      "description": "Risk description",
      "severity": "high|medium|low",
      "raised_by": "Person Name or null"
    }}
  ],
  "questions": [
    {{
      "question": "Question text",
      "asked_by": "Person Name or null"
    }}
  ],
  "agreements": ["Agreement text"],
  "delays": [
    {{
      "item": "What was delayed",
      "original_date": "DD.MM.YYYY or null",
      "new_date": "DD.MM.YYYY or null",
      "reason": "Reason"
    }}
  ],
  "milestones": [
    {{
      "event": "Event name",
      "date": "DD.MM.YYYY",
      "owner": "Person Name or null"
    }}
  ],
  "reminders": [
    {{
      "reminder": "Reminder text",
      "deadline": "DD.MM.YYYY or null"
    }}
  ],
  "compliance": [
    {{
      "item": "Compliance item",
      "type": "audit|security|compliance|documentation",
      "deadline": "DD.MM.YYYY or null",
      "owner": "Person Name or null"
    }}
  ]
}}

═══════════════════════════════════════════════════════════════════
EXAMPLES
═══════════════════════════════════════════════════════════════════

INPUT: "Manel Khammari khamarimanel11@gmail.com"
OUTPUT: {{"participants": [{{"name": "Manel Khammari", "email": "khamarimanel11@gmail.com"}}]}}

INPUT: "Lilwan will create documentation by February 18th"
+ PARTICIPANTS: [{{"name": "Lilwan Akid", "email": "lakid@stud.hs-bremen.de"}}]
OUTPUT: {{
  "action_items": [{{
    "description": "Create comprehensive architecture documentation",
    "assignee": "Lilwan Akid",
    "assignee_email": "lakid@stud.hs-bremen.de",
    "deadline": "18.02.2026",
    "priority": "high"
  }}]
}}

INPUT: "Thomas to prepare benchmarks by next Tuesday (June 17)"
OUTPUT: {{
  "action_items": [{{
    "description": "Prepare benchmarks comparing RabbitMQ and NATS",
    "assignee": "Thomas",
    "assignee_email": null,
    "deadline": "17.06.2026",
    "priority": "high"
  }}]
}}

INPUT: "Ticket 70 Test Imens Crawler → Jonas"
OUTPUT: {{
  "action_items": [{{
    "description": "Test Imens Crawler (Ticket 70)",
    "assignee": "Jonas",
    "assignee_email": null,
    "deadline": null,
    "priority": "medium"
  }}]
}}

INPUT: "Maya volunteered to write unit tests. Goal: 70% coverage by March 1st"
OUTPUT: {{
  "action_items": [{{
    "description": "Write unit tests for document parsing module (70% coverage)",
    "assignee": "Maya",
    "assignee_email": null,
    "deadline": "01.03.2026",
    "priority": "high"
  }}]
}}

INPUT: "Manel (khamarimanel11@gmail.com) should enhance AI parser by February 20th"
OUTPUT: {{
  "action_items": [{{
    "description": "Enhance AI parser to detect natural language assignments",
    "assignee": "Manel",
    "assignee_email": "khamarimanel11@gmail.com",
    "deadline": "20.02.2026",
    "priority": "high"
  }}]
}}

INPUT: "Still some impediments like unreliableJonas"
OUTPUT: {{
  "risks": [{{
    "description": "Unreliable Jonas causing impediments",
    "severity": "medium",
    "raised_by": null
  }}]
}}

═══════════════════════════════════════════════════════════════════
MEETING DOCUMENT TO ANALYZE
═══════════════════════════════════════════════════════════════════

{text[:4500]}

═══════════════════════════════════════════════════════════════════

CRITICAL: Extract participants FIRST, then use their emails for task assignments.
Return ONLY valid JSON. No explanations, no markdown, no code blocks.
[/INST]"""


def clean_json_response(text):
    """Extract JSON from markdown code blocks or raw text."""
    try:
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Method 1: Remove markdown code fences (```json ... ``` or ``` ... ```)
        if text.startswith('```'):
            # Split by ``` and take the middle part
            parts = text.split('```')
            if len(parts) >= 3:
                # parts[0] = empty, parts[1] = "json\n{...}", parts[2] = empty/rest
                json_text = parts[1]
                # Remove language identifier if present (e.g., "json\n")
                if '\n' in json_text:
                    json_text = json_text.split('\n', 1)[1]
                json_text = json_text.strip()
                return json.loads(json_text)
        
        # Method 2: Direct JSON parse
        return json.loads(text)
        
    except Exception as e:
        print(f" JSON-Parsing-Fehler: {e}")
        print(f" Received text: {text[:500]}")
        return None
    """Extract participant emails from document text using regex."""
    import re
    
    participants = []
    
    # Pattern 1: "Name email@domain.com" (on same line)
    pattern1 = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    matches1 = re.findall(pattern1, text)
    for name, email in matches1:
        participants.append({"name": name.strip(), "email": email.strip()})
    
    # Pattern 2: Just emails (for fallback)
    pattern2 = r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
    emails = re.findall(pattern2, text)
    
    # Create lookup: name → email
    lookup = {p["name"]: p["email"] for p in participants}
    
    # Also try partial name matching (first name only)
    for p in participants:
        first_name = p["name"].split()[0]
        if first_name not in lookup:
            lookup[first_name] = p["email"]
    
    return participants, lookup
def extract_participants_from_text(text):
    """Extract participant emails from document text using regex."""
    import re
    
    participants = []
    
    # Pattern: "Name email@domain.com" (on same line)
    pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    matches = re.findall(pattern, text)
    
    for name, email in matches:
        participants.append({"name": name.strip(), "email": email.strip()})
    
    # Create lookup: name → email
    lookup = {}
    for p in participants:
        # Full name
        lookup[p["name"]] = p["email"]
        # First name only
        first_name = p["name"].split()[0]
        lookup[first_name] = p["email"]
    
    return participants, lookup
def extract_insights(text):
    # Extract participants first (before AI call)
    participants, name_to_email = extract_participants_from_text(text)
    print(f" Extracted {len(participants)} participants from text")
    for p in participants:
        print(f"   - {p['name']}: {p['email']}")
    data = None
    # Fake data for testing
    if mock_mode:
        print(" MOCK-MODUS AKTIV – OpenRouter wird nicht aufgerufen.")
        data = {
            "tasks": ["Amira erstellt UX-Mockups bis zum 21. Juni"],
            "decisions": ["Die Beta-Veröffentlichung wird auf den 5. August verschoben"],
            "changes": ["Ersetze den Message Broker durch NATS (abhängig vom Benchmark)"]
        }
    # Real AI call
    else:
        prompt = build_prompt(text)
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        try:
            print(" Calling OpenRouter API...")
            response = requests.post(API_URL, headers=HEADERS, json=payload)
            
            print("=" * 60)
            print("🔍 STATUS CODE:", response.status_code)
            print("🔍 FULL RESPONSE JSON:")
            result = response.json()
            print(json.dumps(result, indent=2))
            print("=" * 60)
            
            if response.status_code != 200:
                print(f" API-Fehler {response.status_code}: {response.text}")
                return []

            print(" API Response received")
            
            # Check if response has expected structure
            if "choices" not in result or len(result["choices"]) == 0:
                print(" ERROR: No choices in API response")
                return []
            
            content = result["choices"][0]["message"]["content"]
            print("=" * 60)
            print("🔍 EXTRACTED CONTENT:")
            print(content)
            print("=" * 60)
            data = clean_json_response(content)
            print("🔍 CLEANED DATA:", data)
        except Exception as e:
            print(f" Unerwarteter Fehler beim API-Aufruf: {e}")
            return []

    # Make sure we have valid data
    if not data or not isinstance(data, dict):
        print(" Invalid data format")
        return []

    # Ergebnisliste für Events
    events = []
# create an empty list to store events
    def create_individual_events(label, items):
        """Create events from simple list items (decisions, changes, agreements)."""
        if not items:
            return
        for i, item in enumerate(items):
            message = f"{label} {i+1}: {item}"
            events.append({
                "type": label.lower(),
                "message": message,
                "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                "priority": "medium"   
            })

    def create_action_item_events(items):
        """Create events from action items with assignee and deadline."""
        if not items:
            return
        for i, item in enumerate(items):
            # Handle both dict and string formats for backward compatibility
            if isinstance(item, dict):
                description = item.get('description', 'No description')
                assignee = item.get('assignee')
                deadline = item.get('deadline')
                priority = item.get('priority', 'medium')
                description = item.get('description', 'No description')
                assignee = item.get('assignee')
                assignee_email = item.get('assignee_email')  # ← ADD THIS LINE
                deadline = item.get('deadline')
                priority = item.get('priority', 'medium')
                
                # Build message
                message = f"Action Item {i+1}: {description}"
                if assignee:
                    message += f" (Assigned to: {assignee})"
                if deadline:
                    message += f" – Deadline: {deadline}"
                
                event = {
                    "type": "action_item",
                    "message": message,
                    "description": description,
                    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "priority": priority
                }
                
                if assignee:
                    event['assignee'] = assignee
                if deadline:
                    event['deadline'] = deadline
                if assignee_email:  # ← ADD THIS
                    event['assignee_email'] = assignee_email  # ← ADD THIS
                if deadline:
                    event['deadline'] = deadline    
                events.append(event)
            else:
                # Fallback for string format
                events.append({
                    "type": "action_item",
                    "message": f"Action Item {i+1}: {item}",
                    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "priority": "medium"
                })

    def create_risk_events(items):
        """Create events from risks."""
        if not items:
            return
        for i, item in enumerate(items):
            if isinstance(item, dict):
                description = item.get('description', 'No description')
                severity = item.get('severity', 'medium')
                raised_by = item.get('raised_by')
                
                message = f"Risk {i+1}: {description}"
                if raised_by:
                    message += f" (Raised by: {raised_by})"
                
                events.append({
                    "type": "risk",
                    "message": message,
                    "description": description,
                    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "priority": "high" if severity == "high" else "medium",
                    "severity": severity,
                    "raised_by": raised_by
                })
            else:
                events.append({
                    "type": "risk",
                    "message": f"Risk {i+1}: {item}",
                    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "priority": "medium"
                })

    def create_question_events(items):
        """Create events from questions."""
        if not items:
            return
        for i, item in enumerate(items):
            if isinstance(item, dict):
                question = item.get('question', 'No question')
                asked_by = item.get('asked_by')
                
                message = f"Question {i+1}: {question}"
                if asked_by:
                    message += f" (Asked by: {asked_by})"
                
                events.append({
                    "type": "question",
                    "message": message,
                    "question": question,
                    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "priority": "medium",
                    "asked_by": asked_by,
                    "status": "open"
                })
            else:
                events.append({
                    "type": "question",
                    "message": f"Question {i+1}: {item}",
                    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "priority": "medium",
                    "status": "open"
                })

    def create_delay_events(items):
        """Create events from delays."""
        if not items:
            return
        for i, item in enumerate(items):
            if isinstance(item, dict):
                item_name = item.get('item', 'Unknown item')
                original_date = item.get('original_date')
                new_date = item.get('new_date')
                reason = item.get('reason', 'No reason provided')
                
                message = f"Delay {i+1}: {item_name}"
                if original_date and new_date:
                    message += f" (from {original_date} to {new_date})"
                message += f" – Reason: {reason}"
                
                events.append({
                    "type": "delay",
                    "message": message,
                    "item": item_name,
                    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "priority": "high",
                    "original_date": original_date,
                    "new_date": new_date,
                    "reason": reason
                })
            else:
                events.append({
                    "type": "delay",
                    "message": f"Delay {i+1}: {item}",
                    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "priority": "high"
                })
    def create_milestone_events(items):
        """Create events from milestones."""
        if not items:
            return
        for i, item in enumerate(items):
            if isinstance(item, dict):
                event_name = item.get('event', 'Unknown event')
                date = item.get('date')
                owner = item.get('owner')
                
                message = f"Milestone {i+1}: {event_name}"
                if date:
                    message += f" – Date: {date}"
                if owner:
                    message += f" (Owner: {owner})"
                
                event = {
                    "type": "milestone",
                    "message": message,
                    "event": event_name,
                    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "priority": "high"
                }
                
                if date:
                    event['date'] = date
                if owner:
                    event['owner'] = owner
                    
                events.append(event)
            else:
                events.append({
                    "type": "milestone",
                    "message": f"Milestone {i+1}: {item}",
                    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "priority": "high"
                })

    def create_reminder_events(items):
        """Create events from reminders."""
        if not items:
            return
        for i, item in enumerate(items):
            if isinstance(item, dict):
                reminder = item.get('reminder', 'No reminder')
                deadline = item.get('deadline')
                
                message = f"Reminder {i+1}: {reminder}"
                if deadline:
                    message += f" – Deadline: {deadline}"
                
                event = {
                    "type": "reminder",
                    "message": message,
                    "reminder": reminder,
                    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "priority": "medium"
                }
                
                if deadline:
                    event['deadline'] = deadline
                    
                events.append(event)
            else:
                events.append({
                    "type": "reminder",
                    "message": f"Reminder {i+1}: {item}",
                    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "priority": "medium"
                })

    def create_compliance_events(items):
        """Create events from compliance items."""
        if not items:
            return
        for i, item in enumerate(items):
            if isinstance(item, dict):
                compliance_item = item.get('item', 'Unknown item')
                comp_type = item.get('type', 'compliance')
                deadline = item.get('deadline')
                owner = item.get('owner')
                
                message = f"Compliance {i+1}: {compliance_item}"
                if deadline:
                    message += f" – Deadline: {deadline}"
                if owner:
                    message += f" (Owner: {owner})"
                
                event = {
                    "type": "compliance",
                    "message": message,
                    "item": compliance_item,
                    "compliance_type": comp_type,
                    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "priority": "high"
                }
                
                if deadline:
                    event['deadline'] = deadline
                if owner:
                    event['owner'] = owner
                    
                events.append(event)
            else:
                events.append({
                    "type": "compliance",
                    "message": f"Compliance {i+1}: {item}",
                    "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "priority": "high"
                })
    
    # create all events 
    # Create events for each category
    # Add emails to action items using participant lookup
    action_items = data.get("action_items", [])
    for item in action_items:
        if isinstance(item, dict) and item.get('assignee'):
            assignee_name = item['assignee']
            
            # Try exact name match first
            if assignee_name in name_to_email:
                item['assignee_email'] = name_to_email[assignee_name]
                print(f"✅ Mapped {assignee_name} → {item['assignee_email']}")
            else:
                # Try first name match
                first_name = assignee_name.split()[0]
                if first_name in name_to_email:
                    item['assignee_email'] = name_to_email[first_name]
                    print(f"✅ Mapped {first_name} → {item['assignee_email']}")
                else:
                    print(f"⚠️ No email found for {assignee_name}")

    create_action_item_events(action_items)    
    create_individual_events("Decision", data.get("decisions", []))
    create_individual_events("Change", data.get("changes", []))
    create_risk_events(data.get("risks", []))
    create_question_events(data.get("questions", []))
    create_individual_events("Agreement", data.get("agreements", []))
    create_delay_events(data.get("delays", []))
    create_milestone_events(data.get("milestones", [])) 
    create_reminder_events(data.get("reminders", []))        
    create_compliance_events(data.get("compliance", []))

    print(f"✅ Created {len(events)} events")
    return events