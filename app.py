from dotenv import load_dotenv
load_dotenv()
import urllib.request
import json
import os
from flask import Flask, request, jsonify, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["20 per minute"],
    storage_uri="memory://"
)

API_KEY = os.environ.get("ANTHROPIC_API_KEY")

def ask_claude(prompt):
    if not API_KEY:
        return "Error: API key not configured."
    url = "https://api.anthropic.com/v1/messages"
    data = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01"
    })
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            return result["content"][0]["text"]
    except urllib.error.HTTPError as e:
        return f"API Error: {e.read().decode()}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

def validate(data, required_fields):
    for field in required_fields:
        if not data.get(field) or not data[field].strip():
            return False, f"Missing required field: {field}"
    return True, None

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/app")
def home():
    return render_template("index.html")

@app.route("/api/family-update", methods=["POST"])
@limiter.limit("10 per minute")
def family_update():
    data = request.json
    valid, error = validate(data, ["resident_name", "notes"])
    if not valid:
        return jsonify({"error": error}), 400
    prompt = f"""You are a compassionate senior living care coordinator writing to a resident's family.

Caregiver notes for {data['resident_name']} today:
{data['notes']}

Write a warm, professional family update email that:
- Opens with a personal, caring greeting
- Summarizes how {data['resident_name']} is doing overall
- Highlights specific positive moments from their day
- Addresses any health or care notes in reassuring, non-alarming language
- Closes warmly and invites the family to reach out

Keep it under 200 words. Sound like a real human who cares about this resident, not a form letter."""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/incident-report", methods=["POST"])
@limiter.limit("10 per minute")
def incident_report():
    data = request.json
    valid, error = validate(data, ["resident_name", "staff_name", "notes"])
    if not valid:
        return jsonify({"error": error}), 400
    today = datetime.now().strftime("%B %d, %Y %I:%M %p")
    prompt = f"""You are a senior living facility administrator generating a formal incident report for regulatory compliance.

Staff member {data['staff_name']} reported this incident involving resident {data['resident_name']}:
{data['notes']}

Generate a complete, formal incident report with these exact sections:

INCIDENT REPORT
Date/Time: {today}
Resident: {data['resident_name']}
Staff Present: {data['staff_name']}

1. INCIDENT SUMMARY
One clear sentence describing what occurred.

2. DETAILED DESCRIPTION
Full factual account. Include: what happened, where, when, who was present, sequence of events. No speculation.

3. IMMEDIATE ACTIONS TAKEN
Bullet list of every action taken by staff in response.

4. RESIDENT CONDITION AFTER INCIDENT
Current physical and emotional status. Vital signs if taken.

5. NOTIFICATIONS MADE
Who was contacted (family, physician, supervisor) and when.

6. FOLLOW-UP REQUIRED
Specific next steps with suggested timeframes.

7. PREVENTION RECOMMENDATIONS
One specific process change to prevent recurrence.

Use formal clinical language appropriate for state regulatory review."""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/staff-scheduling", methods=["POST"])
@limiter.limit("10 per minute")
def staff_scheduling():
    data = request.json
    valid, error = validate(data, ["facility_name", "problem"])
    if not valid:
        return jsonify({"error": error}), 400
    prompt = f"""You are an expert senior living operations consultant. A facility manager at {data['facility_name']} needs urgent help:

{data['problem']}

Provide a structured, actionable response:

IMMEDIATE ACTION PLAN
Step-by-step what to do RIGHT NOW in the next 30 minutes.

CALL LIST (in priority order)
Name each type of staff to contact, in what order, and why.

OVERTIME & COMPLIANCE RISK
Flag any labor law or staffing ratio concerns. How to stay compliant.

WORD-FOR-WORD PHONE SCRIPT
Exact script to use when calling staff to cover. Include what to say if they say no.

ROOT CAUSE & PREVENTION
One specific policy or process change to prevent this exact situation from recurring.

Be direct. This manager is stressed and needs fast, clear answers."""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/move-in", methods=["POST"])
@limiter.limit("10 per minute")
def move_in():
    data = request.json
    valid, error = validate(data, ["facility_name", "resident_name", "room_number", "move_in_date", "care_level", "family_contact"])
    if not valid:
        return jsonify({"error": error}), 400
    prompt = f"""You are a warm, experienced senior living coordinator at {data['facility_name']}.

New resident details:
- Name: {data['resident_name']}
- Room: {data['room_number']}
- Move-in date: {data['move_in_date']}
- Care level: {data['care_level']}
- Primary family contact: {data['family_contact']}
- Personal notes: {data.get('notes', 'None provided')}

Generate a complete, personalized move-in package with three documents:

---WELCOME LETTER---
Personal, warm letter to {data['resident_name']} and family. Reference their specific details and notes. Signed by Executive Director. Under 200 words.

---FAMILY CHECKLIST---
What to bring / what NOT to bring / key contacts / first week expectations / how to stay connected. Use checkboxes format.

---DAY ONE SCHEDULE---
Personalized hour-by-hour schedule for move-in day. Make it warm and specific to this resident based on their notes."""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/research", methods=["POST"])
@limiter.limit("10 per minute")
def research():
    data = request.json
    valid, error = validate(data, ["company"])
    if not valid:
        return jsonify({"error": error}), 400
    prompt = f"""I have a sales call with {data['company']} today. I sell ClarityCare — AI automation tools built specifically for senior living facilities.

Research this company and give me:

COMPANY OVERVIEW
What they do, how many facilities, their market position, recent news.

TOP 3 PAIN POINTS
Their most likely operational challenges based on their size and type.

TAILORED TALKING POINTS
3 specific ways ClarityCare solves their exact problems. Be concrete.

DISCOVERY QUESTIONS
3 smart questions that will uncover their biggest needs and open the door to a demo.

COMPETITIVE ANGLE
What makes this a good time to approach them specifically.

Be specific and practical. I have 2 minutes to prep."""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/medication-log", methods=["POST"])
@limiter.limit("10 per minute")
def medication_log():
    data = request.json
    valid, error = validate(data, ["resident_name", "medications", "notes"])
    if not valid:
        return jsonify({"error": error}), 400
    today = datetime.now().strftime("%B %d, %Y %I:%M %p")
    prompt = f"""You are a senior living nurse generating a formal medication administration summary.

Resident: {data['resident_name']}
Date/Time: {today}
Medications listed: {data['medications']}
Nurse notes: {data['notes']}

Generate a professional medication log summary with:

MEDICATION ADMINISTRATION SUMMARY
Date/Time: {today}
Resident: {data['resident_name']}

MEDICATIONS ADMINISTERED
List each medication with: name, dose, route, time, administered by.

RESIDENT RESPONSE
How the resident responded. Any side effects or concerns noted.

REFUSALS OR MISSED DOSES
Any medications not taken and reason why.

FOLLOW-UP REQUIRED
Any medications needing physician review or family notification.

NURSE SIGNATURE LINE
Space for nurse name, credentials, and signature.

Use clinical language appropriate for medical records."""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/care-plan", methods=["POST"])
@limiter.limit("10 per minute")
def care_plan():
    data = request.json
    valid, error = validate(data, ["resident_name", "diagnosis", "care_needs"])
    if not valid:
        return jsonify({"error": error}), 400
    prompt = f"""You are a senior living Director of Nursing creating a comprehensive care plan.

Resident: {data['resident_name']}
Primary diagnosis/conditions: {data['diagnosis']}
Identified care needs: {data['care_needs']}
Additional notes: {data.get('notes', 'None')}

Generate a professional care plan with these sections:

RESIDENT CARE PLAN
Resident: {data['resident_name']}
Date: {datetime.now().strftime("%B %d, %Y")}

1. MEDICAL DIAGNOSES & CONDITIONS
List all conditions with clinical descriptions.

2. CARE GOALS (90-day)
3-5 specific, measurable goals for this resident.

3. NURSING INTERVENTIONS
Specific daily actions staff must take. Frequency and method for each.

4. DIETARY REQUIREMENTS
Meal plans, restrictions, hydration goals, dining assistance needed.

5. MOBILITY & ACTIVITY PLAN
Physical activity level, fall risk assessment, assistive devices needed.

6. PSYCHOSOCIAL NEEDS
Emotional support, social activities, family involvement plan.

7. SAFETY MEASURES
Specific safety protocols for this resident's conditions.

8. FAMILY COMMUNICATION PLAN
How and how often to update the family.

Use professional clinical language compliant with CMS guidelines."""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/discharge-summary", methods=["POST"])
@limiter.limit("10 per minute")
def discharge_summary():
    data = request.json
    valid, error = validate(data, ["resident_name", "discharge_destination", "stay_summary"])
    if not valid:
        return jsonify({"error": error}), 400
    prompt = f"""You are a senior living Director of Nursing generating a formal discharge summary.

Resident: {data['resident_name']}
Discharge destination: {data['discharge_destination']}
Summary of stay: {data['stay_summary']}
Additional notes: {data.get('notes', 'None')}

Generate a complete discharge summary with:

DISCHARGE SUMMARY
Resident: {data['resident_name']}
Discharge Date: {datetime.now().strftime("%B %d, %Y")}
Discharge Destination: {data['discharge_destination']}

1. REASON FOR ADMISSION
Why the resident originally came to the facility.

2. SUMMARY OF STAY
Key events, treatments, and progress during their time at the facility.

3. CURRENT HEALTH STATUS AT DISCHARGE
Physical and cognitive status at time of discharge.

4. MEDICATIONS AT DISCHARGE
Complete medication list with doses and instructions.

5. FOLLOW-UP CARE REQUIRED
Appointments, therapies, or treatments needed after discharge.

6. INSTRUCTIONS FOR RECEIVING FACILITY OR FAMILY
Specific care instructions, warnings, and preferences.

7. EMERGENCY CONTACTS
Key contacts if issues arise after discharge.

Use formal clinical language suitable for medical record transfer."""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/stream", methods=["POST"])
@limiter.limit("10 per minute")
def stream():
    data = request.json
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    def generate():
        url = "https://api.anthropic.com/v1/messages"
        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2048,
            "stream": True,
            "messages": [{"role": "user", "content": prompt}]
        }).encode()
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01"
        })
        try:
            with urllib.request.urlopen(req) as response:
                for line in response:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data:"):
                        line = line[5:].strip()
                        if line == "[DONE]":
                            break
                        try:
                            event = json.loads(line)
                            if event.get("type") == "content_block_delta":
                                text = event["delta"].get("text", "")
                                if text:
                                    yield f"data: {json.dumps({'text': text})}\n\n"
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return app.response_class(generate(), mimetype="text/event-stream",
                               headers={"Cache-Control": "no-cache",
                                        "X-Accel-Buffering": "no"})

@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({"error": "Too many requests. Please wait a moment and try again."}), 429

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Something went wrong. Please try again."}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)