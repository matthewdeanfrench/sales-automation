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

# Rate limiting - max 20 requests per minute per IP
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
        error_body = e.read().decode()
        return f"API Error: {error_body}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

def validate(data, required_fields):
    for field in required_fields:
        if not data.get(field) or not data[field].strip():
            return False, f"Missing required field: {field}"
    return True, None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/family-update", methods=["POST"])
@limiter.limit("10 per minute")
def family_update():
    data = request.json
    valid, error = validate(data, ["resident_name", "notes"])
    if not valid:
        return jsonify({"error": error}), 400
    
    prompt = f"""You are a compassionate senior living care coordinator.

A caregiver wrote these rough notes about resident {data['resident_name']} today:
{data['notes']}

Please turn these notes into a warm, professional family update email. Include:
1. A friendly greeting
2. How {data['resident_name']} is doing overall
3. Highlights from their day
4. Any important health or care notes (in reassuring language)
5. A warm closing

Keep it under 200 words. Sound human and caring, not clinical."""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/incident-report", methods=["POST"])
@limiter.limit("10 per minute")
def incident_report():
    data = request.json
    valid, error = validate(data, ["resident_name", "staff_name", "notes"])
    if not valid:
        return jsonify({"error": error}), 400
    
    today = datetime.now().strftime("%B %d, %Y %I:%M %p")
    prompt = f"""You are a senior living facility administrator.

Staff member {data['staff_name']} reported this incident involving resident {data['resident_name']}:
{data['notes']}

Generate a formal incident report with:
1. INCIDENT SUMMARY
2. DATE & TIME - use {today}
3. RESIDENT - {data['resident_name']}
4. STAFF PRESENT - {data['staff_name']}
5. DETAILED DESCRIPTION
6. IMMEDIATE ACTIONS TAKEN
7. RESIDENT CONDITION AFTER INCIDENT
8. FOLLOW UP REQUIRED

Use professional, clinical language suitable for regulatory review."""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/staff-scheduling", methods=["POST"])
@limiter.limit("10 per minute")
def staff_scheduling():
    data = request.json
    valid, error = validate(data, ["facility_name", "problem"])
    if not valid:
        return jsonify({"error": error}), 400
    
    prompt = f"""You are an expert in senior living facility operations.

The facility manager at {data['facility_name']} has this scheduling problem:
{data['problem']}

Please provide:
1. IMMEDIATE FIX
2. STAFF TO CALL (in order)
3. OVERTIME RISK
4. PREVENT IT NEXT TIME
5. PHONE SCRIPT to use when calling staff

Be direct and practical."""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/move-in", methods=["POST"])
@limiter.limit("10 per minute")
def move_in():
    data = request.json
    valid, error = validate(data, ["facility_name", "resident_name", "room_number", "move_in_date", "care_level", "family_contact"])
    if not valid:
        return jsonify({"error": error}), 400
    
    prompt = f"""You are a warm senior living coordinator at {data['facility_name']}.

New resident moving in:
- Name: {data['resident_name']}
- Room: {data['room_number']}
- Move-in date: {data['move_in_date']}
- Care level: {data['care_level']}
- Family contact: {data['family_contact']}
- Notes: {data.get('notes', 'None')}

Generate a complete move-in package:
1. WELCOME LETTER (warm, personal, under 200 words)
2. FAMILY CHECKLIST (what to bring, what not to bring, contacts)
3. DAY ONE SCHEDULE (personalized hourly schedule)"""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/research", methods=["POST"])
@limiter.limit("10 per minute")
def research():
    data = request.json
    valid, error = validate(data, ["company"])
    if not valid:
        return jsonify({"error": error}), 400
    
    prompt = f"""I have a sales call with {data['company']} today. I sell AI automation tools to senior living facilities.

Give me:
1. What {data['company']} likely does and their biggest challenges
2. 3 specific talking points connecting their challenges to AI automation
3. 3 smart questions to ask on the call

Be specific and practical. I have 2 minutes to prep."""
    return jsonify({"result": ask_claude(prompt)})

@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({"error": "Too many requests. Please wait a moment and try again."}), 429

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Something went wrong on our end. Please try again."}), 500

if __name__ == "__main__":
    app.run(debug=True)