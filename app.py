from dotenv import load_dotenv
load_dotenv()
import urllib.request
import json
import os
from flask import Flask, request, jsonify, render_template, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_required, current_user
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///claritycare.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(150))
    tool = db.Column(db.String(50), nullable=False)
    resident_name = db.Column(db.String(100))
    facility_name = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_email': self.user_email,
            'tool': self.tool,
            'resident_name': self.resident_name,
            'facility_name': self.facility_name,
            'content': self.content[:100] + '...' if len(self.content) > 100 else self.content,
            'created_at': self.created_at.strftime('%b %d, %Y %I:%M %p')
        }
class ResidentCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    resident_name = db.Column(db.String(100), nullable=False)
    facility_name = db.Column(db.String(100))
    created_by = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class FamilyUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resident_code = db.Column(db.String(20), nullable=False)
    resident_name = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    published_by = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'resident_name': self.resident_name,
            'content': self.content,
            'published_by': self.published_by,
            'created_at': self.created_at.strftime('%B %d, %Y %I:%M %p')
        }

class FamilyUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100))
    resident_code = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(150))
    action = db.Column(db.String(100), nullable=False)
    resource = db.Column(db.String(100))
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'user_email': self.user_email,
            'action': self.action,
            'resource': self.resource,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.strftime('%b %d, %Y %I:%M %p'),
            'details': self.details
        }

    def to_dict(self):
        return {
            'id': self.id,
            'user_email': self.user_email,
            'action': self.action,
            'resource': self.resource,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.strftime('%b %d, %Y %I:%M %p'),
            'details': self.details
        }

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["20 per minute"],
    storage_uri="memory://"
)

API_KEY = os.environ.get("ANTHROPIC_API_KEY")

def log_action(action, resource=None, details=None):
    try:
        email = current_user.email if current_user.is_authenticated else "anonymous"
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        log = AuditLog(
            user_email=email,
            action=action,
            resource=resource,
            ip_address=ip,
            details=details
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        pass

def ask_claude(prompt):
    if not API_KEY:
        return "Error: API key not configured."
    url = "https://api.anthropic.com/v1/messages"
    data = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
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

from auth import auth_bp, init_auth
User = init_auth(app, db)
app.register_blueprint(auth_bp)

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/app")
@login_required
def home():
    return render_template("index.html")

@app.route("/api/family-update", methods=["POST"])
@login_required
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
- Opens with a personal, caring greeting using the resident's first name
- Summarizes their overall wellbeing with specific, concrete details
- Highlights 2-3 meaningful moments from their day
- Addresses any health notes in reassuring but honest language
- Closes warmly and invites the family to visit or call

Sign off from "The Care Team at [Facility Name]".
Keep it under 200 words. Never use generic phrases like "doing well" without specifics."""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/incident-report", methods=["POST"])
@login_required
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

Generate a complete, formal incident report:

INCIDENT REPORT
Date/Time: {today}
Resident: {data['resident_name']}
Staff Present: {data['staff_name']}

1. INCIDENT SUMMARY
One precise sentence. Include: what happened, where, when.

2. DETAILED DESCRIPTION
Chronological, factual account. No opinions or speculation. Include exact times, locations, witnesses.

3. IMMEDIATE ACTIONS TAKEN
Numbered list of every intervention. Include who did what and when.

4. RESIDENT CONDITION AFTER INCIDENT
Objective assessment. Vital signs if taken. Pain level if reported. Emotional state.

5. NOTIFICATIONS MADE
Name, relationship, time contacted, method of contact, response given.

6. FOLLOW-UP REQUIRED
Specific action items with responsible parties and deadlines.

7. PREVENTION RECOMMENDATIONS
One concrete, implementable process change.

Use clinical language. Avoid passive voice. This document may be reviewed by state regulators."""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/staff-scheduling", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def staff_scheduling():
    data = request.json
    valid, error = validate(data, ["facility_name", "problem"])
    if not valid:
        return jsonify({"error": error}), 400
    prompt = f"""You are an expert senior living operations consultant with 20 years experience.

A facility manager at {data['facility_name']} has this urgent situation:
{data['problem']}

Respond with:

IMMEDIATE ACTION PLAN
Numbered steps for the next 30 minutes. Be specific — who to call first and why.

CALL LIST
Priority order with role title, not generic names. Include what to offer each person.

COMPLIANCE RISK ASSESSMENT
Specific staffing ratios at risk. Relevant state regulations to be aware of.

WORD-FOR-WORD PHONE SCRIPT
Opening line. What to say if they say yes. What to say if they say no. Closing.

ROOT CAUSE & PREVENTION
One policy change that eliminates this exact scenario recurring.

Be direct. No filler. This manager needs answers in 60 seconds."""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/move-in", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def move_in():
    data = request.json
    valid, error = validate(data, ["facility_name", "resident_name", "room_number", "move_in_date", "care_level", "family_contact"])
    if not valid:
        return jsonify({"error": error}), 400
    prompt = f"""You are a warm, experienced senior living coordinator at {data['facility_name']}.

New resident:
- Name: {data['resident_name']}
- Room: {data['room_number']}
- Move-in: {data['move_in_date']}
- Care level: {data['care_level']}
- Family contact: {data['family_contact']}
- Personal notes: {data.get('notes', 'None provided')}

Generate three distinct documents:

---WELCOME LETTER---
Address the resident by first name. Reference their specific personal notes naturally.
Mention their room number and move-in date. Express genuine excitement.
Sign from Executive Director. Warm, human, specific. Under 200 words.

---FAMILY CHECKLIST---
Format as checkboxes. Sections: What to Bring, Do Not Bring, Key Contacts, First Week Timeline, Staying Connected.
Make it practical and specific to their care level.

---DAY ONE SCHEDULE---
Hour by hour from arrival to bedtime. Reference their personal interests from notes.
Include: arrival, room setup, care team introductions, first meal, orientation tour, evening routine.
Make it feel welcoming not clinical."""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/research", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def research():
    data = request.json
    valid, error = validate(data, ["company"])
    if not valid:
        return jsonify({"error": error}), 400
    prompt = f"""You are a senior living industry expert preparing me for a sales call with {data['company']}.
I sell ClarityCare — AI automation that eliminates documentation burden for senior living staff.

Give me:

COMPANY PROFILE
Size, locations, care types offered, ownership structure, recent news or challenges.

PAIN POINTS SPECIFIC TO THEIR PROFILE
3 operational problems they almost certainly face given their size and type.
Be specific — not generic "staffing challenges" but WHY their specific situation creates this.

CLARITYCARE FIT
3 concrete ways our tools solve their specific problems. Use their language, not ours.

DISCOVERY QUESTIONS
3 questions that make them realize they have a problem I can solve.
Each question should feel consultative, not salesy.

COMPETITIVE INTELLIGENCE
What solutions they likely use now and why ClarityCare is better.

ONE SENTENCE OPENER
The single best line to open the call that will make them want to keep talking."""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/medication-log", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def medication_log():
    data = request.json
    valid, error = validate(data, ["resident_name", "medications", "notes"])
    if not valid:
        return jsonify({"error": error}), 400
    today = datetime.now().strftime("%B %d, %Y %I:%M %p")
    prompt = f"""You are a licensed nurse generating a formal medication administration record.

Resident: {data['resident_name']}
Date/Time: {today}
Raw medication data: {data['medications']}
Nurse observations: {data['notes']}

Generate a formal MAR summary:

MEDICATION ADMINISTRATION RECORD
Resident: {data['resident_name']}
Date: {today}

MEDICATIONS ADMINISTERED
For each medication include: Generic name, Brand name if known, Dose, Route, Time administered, Administered by (leave blank for nurse signature), Response observed.

MEDICATION REFUSALS
Any medications not administered. Reason. Interventions attempted.

ADVERSE REACTIONS OR CONCERNS
Any side effects, allergic responses, or unexpected reactions noted.

CLINICAL OBSERVATIONS
Resident's overall status during medication pass. Relevant vitals if taken.

FOLLOW-UP ACTIONS REQUIRED
Physician notification needed? Family notification? Next dose adjustments?

SIGNATURE BLOCK
Nurse Name: _______________ RN/LPN License #: _______________ Date: _______________

Use standard clinical abbreviations (PO, SL, IM, PRN, etc.)"""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/care-plan", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def care_plan():
    data = request.json
    valid, error = validate(data, ["resident_name", "diagnosis", "care_needs"])
    if not valid:
        return jsonify({"error": error}), 400
    prompt = f"""You are a Director of Nursing creating a CMS-compliant care plan.

Resident: {data['resident_name']}
Diagnoses: {data['diagnosis']}
Care needs: {data['care_needs']}
Notes: {data.get('notes', 'None')}

Generate a comprehensive care plan:

RESIDENT CARE PLAN
Resident: {data['resident_name']}
Date initiated: {datetime.now().strftime("%B %d, %Y")}
Review date: {datetime.now().strftime("%B %d, %Y")} + 90 days

For each section below, be specific and measurable:

1. PROBLEM/NEED IDENTIFICATION
List each diagnosis with ICD-10 codes where applicable.

2. GOALS (90-DAY)
3-5 goals. Each must be: Specific, Measurable, Achievable, Relevant, Time-bound.
Format: "Resident will [action] by [date] as evidenced by [measure]"

3. INTERVENTIONS
Who does what, when, how often. Assign to specific role (RN, CNA, PT, etc.)

4. NUTRITIONAL PLAN
Diet type, texture modifications, hydration goals, dining assistance level, restrictions.

5. MOBILITY & FALL RISK
Braden/Fall risk score if known. Assistive devices. Activity level. PT/OT involvement.

6. PSYCHOSOCIAL & COGNITIVE
Mental status. Behavioral approaches. Activity preferences. Social engagement plan.

7. SAFETY PROTOCOLS
Specific to their diagnoses. Elopement risk if applicable. Side rail policy.

8. FAMILY/RESPONSIBLE PARTY INVOLVEMENT
Communication frequency. Decision-making role. Education needs.

This plan must meet F-tag requirements for CMS survey readiness."""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/discharge-summary", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def discharge_summary():
    data = request.json
    valid, error = validate(data, ["resident_name", "discharge_destination", "stay_summary"])
    if not valid:
        return jsonify({"error": error}), 400
    prompt = f"""You are a Director of Nursing generating a clinical discharge summary for medical record continuity.

Resident: {data['resident_name']}
Discharge destination: {data['discharge_destination']}
Stay summary: {data['stay_summary']}
Additional notes: {data.get('notes', 'None')}

Generate a complete discharge summary:

DISCHARGE SUMMARY
Resident: {data['resident_name']}
Discharge Date: {datetime.now().strftime("%B %d, %Y")}
Discharge Destination: {data['discharge_destination']}
Attending Physician: _______________

1. ADMISSION DIAGNOSIS & REASON FOR STAY
Primary and secondary diagnoses. Functional status at admission.

2. CLINICAL COURSE
Chronological summary of stay. Key interventions, progress, setbacks.

3. FUNCTIONAL STATUS AT DISCHARGE
ADL independence level. Cognitive status. Mobility. Compare to admission baseline.

4. DISCHARGE MEDICATIONS
Complete reconciled medication list. Dose, frequency, route, purpose, prescriber.

5. PENDING RESULTS OR FOLLOW-UP
Outstanding labs, imaging, specialist referrals. Specific appointment dates if known.

6. DISCHARGE INSTRUCTIONS
Activity restrictions. Diet. Warning signs requiring immediate medical attention.
Written in plain language suitable for patient/family.

7. CARE TRANSITION PLAN
Who is responsible for ongoing care. Home health orders if applicable.
Emergency contacts and who to call for what.

Flag any high-risk discharge concerns (falls, readmission risk, medication complexity)."""
    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/stream", methods=["POST"])
@login_required
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

@app.route("/api/staffing-predict", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def staffing_predict():
    data = request.json
    valid, error = validate(data, ["facility_name", "historical_data"])
    if not valid:
        return jsonify({"error": error}), 400
    prompt = f"""You are an expert in senior living facility operations and workforce analytics.

A facility manager at {data['facility_name']} has provided this staffing history:

{data['historical_data']}

Analyze this data and provide:

RISK ASSESSMENT
Overall staffing risk level for the next 7 days: Critical / High / Medium / Low
Explain why in 2 sentences.

PREDICTED SHORTAGE DAYS
List specific days in the next 7 days with high call-out risk.
For each day include: day, shift at risk, probability of shortage, reason.

PATTERN ANALYSIS
What patterns do you see in this data?
- Day of week patterns
- Shift patterns
- Individual staff patterns

IMMEDIATE ACTIONS
3 specific things the manager should do TODAY to prevent shortages.
Be concrete — who to call, what to offer, what policy to implement.

STAFF TO CONTACT NOW
Which types of staff should be contacted proactively and what to offer them.

30-DAY RECOMMENDATION
One structural change to prevent this pattern from recurring.

Format as a clear operational report a facility manager can act on immediately."""

    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/save-document", methods=["POST"])
@login_required
@limiter.limit("30 per minute")
def save_document():
    data = request.json
    if not data.get("content") or not data.get("tool"):
        return jsonify({"error": "Missing required fields"}), 400
    doc = Document(
        user_email=current_user.email,
        tool=data.get("tool"),
        resident_name=data.get("resident_name", ""),
        facility_name=data.get("facility_name", ""),
        content=data.get("content")
    )
    db.session.add(doc)
    db.session.commit()
    log_action("document_saved", resource=data.get("tool"), 
               details=f"Resident: {data.get('resident_name', 'N/A')}")
    return jsonify({"success": True, "id": doc.id})

@app.route("/api/documents", methods=["GET"])
@login_required
def get_documents():
    if current_user.is_admin:
        docs = Document.query.order_by(Document.created_at.desc()).limit(50).all()
    else:
        docs = Document.query.filter_by(user_email=current_user.email).order_by(Document.created_at.desc()).limit(50).all()
    return jsonify([d.to_dict() for d in docs])

@app.route("/api/documents/<int:doc_id>", methods=["GET"])
@login_required
def get_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    return jsonify({
        'id': doc.id,
        'tool': doc.tool,
        'resident_name': doc.resident_name,
        'facility_name': doc.facility_name,
        'content': doc.content,
        'created_at': doc.created_at.strftime('%b %d, %Y %I:%M %p')
    })

@app.route("/api/documents/<int:doc_id>", methods=["DELETE"])
@login_required
def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    log_action("document_deleted", resource=doc.tool,
               details=f"Resident: {doc.resident_name}, ID: {doc_id}")
    db.session.delete(doc)
    db.session.commit()
    return jsonify({"success": True})

@app.route("/api/audit-log", methods=["GET"])
@login_required
def audit_log():
    try:
        if current_user.is_admin:
            logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
        else:
            logs = AuditLog.query.filter_by(user_email=current_user.email).order_by(AuditLog.timestamp.desc()).limit(100).all()
        return jsonify([l.to_dict() for l in logs])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/audit")
@login_required
def audit_page():
    return render_template("audit.html")

@app.route("/family")
def family_landing():
    return render_template("family_login.html")

@app.route("/family/portal")
def family_portal():
    return render_template("family_portal.html")

@app.route("/api/family/register", methods=["POST"])
def family_register():
    data = request.json
    if not data.get("email") or not data.get("password") or not data.get("name") or not data.get("resident_code"):
        return jsonify({"error": "All fields required"}), 400
    code = ResidentCode.query.filter_by(code=data["resident_code"].upper(), is_active=True).first()
    if not code:
        return jsonify({"error": "Invalid resident code. Please check with the facility."}), 400
    if FamilyUser.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 400
    from werkzeug.security import generate_password_hash
    user = FamilyUser(
        email=data["email"],
        password=generate_password_hash(data["password"]),
        name=data["name"],
        resident_code=data["resident_code"].upper()
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"success": True, "resident_name": code.resident_name})

@app.route("/api/family/login", methods=["POST"])
def family_login():
    data = request.json
    from werkzeug.security import check_password_hash
    user = FamilyUser.query.filter_by(email=data.get("email")).first()
    if not user or not check_password_hash(user.password, data.get("password", "")):
        return jsonify({"error": "Invalid email or password"}), 401
    code = ResidentCode.query.filter_by(code=user.resident_code).first()
    resident_name = code.resident_name if code else "Your loved one"
    return jsonify({"success": True, "name": user.name, "resident_name": resident_name, "resident_code": user.resident_code})

@app.route("/api/family/updates/<resident_code>", methods=["GET"])
def family_updates(resident_code):
    updates = FamilyUpdate.query.filter_by(resident_code=resident_code.upper()).order_by(FamilyUpdate.created_at.desc()).limit(30).all()
    return jsonify([u.to_dict() for u in updates])

@app.route("/api/generate-resident-code", methods=["POST"])
@login_required
def generate_resident_code():
    data = request.json
    if not data.get("resident_name"):
        return jsonify({"error": "Resident name required"}), 400
    import random
    import string
    name_part = data["resident_name"].split()[0][:4].upper()
    num_part = ''.join(random.choices(string.digits, k=4))
    code = f"{name_part}-{num_part}"
    resident_code = ResidentCode(
        code=code,
        resident_name=data["resident_name"],
        facility_name=data.get("facility_name", ""),
        created_by=current_user.email
    )
    db.session.add(resident_code)
    db.session.commit()
    return jsonify({"success": True, "code": code, "resident_name": data["resident_name"]})

@app.route("/api/publish-family-update", methods=["POST"])
@login_required
def publish_family_update():
    data = request.json
    if not data.get("resident_code") or not data.get("content"):
        return jsonify({"error": "Missing required fields"}), 400
    code = ResidentCode.query.filter_by(code=data["resident_code"].upper()).first()
    if not code:
        return jsonify({"error": "Invalid resident code"}), 400
    update = FamilyUpdate(
        resident_code=data["resident_code"].upper(),
        resident_name=code.resident_name,
        content=data["content"],
        published_by=current_user.email
    )
    db.session.add(update)
    db.session.commit()
    log_action("family_update_published", resource=data["resident_code"], details=f"Resident: {code.resident_name}")
    return jsonify({"success": True})

@app.route("/api/survey-prep", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def survey_prep():
    data = request.json
    valid, error = validate(data, ["facility_name", "survey_type", "concerns"])
    if not valid:
        return jsonify({"error": error}), 400
    prompt = f"""You are a senior living regulatory compliance expert with 20 years of experience preparing facilities for state surveys.

Facility: {data['facility_name']}
Survey type: {data['survey_type']}
Areas of concern or recent issues: {data['concerns']}
Additional context: {data.get('notes', 'None')}

Generate a comprehensive survey preparation report:

EXECUTIVE SUMMARY
Overall readiness assessment and top 3 priority areas to address before the survey.

HIGH-RISK F-TAGS TO REVIEW
List the 10 most commonly cited F-tags for this type of facility/survey.
For each: F-tag number, what it covers, what surveyors look for, and what to fix now.

DOCUMENTATION AUDIT CHECKLIST
Specific documents surveyors will request on day one.
For each document: what it is, where it should be, what makes it compliant.

MOCK SURVEY QUESTIONS
10 questions surveyors are likely to ask staff.
For each: the question, what they're really looking for, and the ideal response.

IMMEDIATE ACTION ITEMS
Things that must be fixed before surveyors arrive.
Prioritized by risk level: Critical (fix today), High (fix this week), Medium (fix this month).

STAFF TALKING POINTS
What to tell staff before the survey arrives.
What to say, what not to say, how to respond if asked about recent incidents.

Format as a professional compliance report the Administrator can share with department heads."""

    return jsonify({"result": ask_claude(prompt)})

@app.route("/api/risk-assessment", methods=["POST"])
@login_required
@limiter.limit("5 per minute")
def risk_assessment():
    data = request.json
    valid, error = validate(data, ["resident_name", "notes"])
    if not valid:
        return jsonify({"error": error}), 400

    def call_claude_internal(prompt):
        url = "https://api.anthropic.com/v1/messages"
        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        }).encode()
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01"
        })
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            return result["content"][0]["text"]

    resident_name = data["resident_name"]
    notes = data["notes"]
    facility = data.get("facility_name", "Senior Living Facility")

    try:
        # Step 1: Identify risks
        risk_factors = call_claude_internal(f"""You are a senior living clinical expert.
Caregiver notes for {resident_name}: {notes}
Extract and list ALL risk factors. Format as numbered list.
Include: clinical, fall, medication, social/behavioral, environmental risks.""")

        # Step 2: Rate risks
        risk_ratings = call_claude_internal(f"""You are a senior living clinical risk specialist.
Resident: {resident_name}. Notes: {notes}
Risk factors identified: {risk_factors}
For each risk: rate severity (Critical/High/Medium/Low), explain why, state immediate action needed.""")

        # Step 3: Recommendations
        recommendations = call_claude_internal(f"""You are a Director of Nursing.
Resident: {resident_name}. Facility: {facility}
Risk analysis: {risk_ratings}
Generate: 1) Immediate interventions 2) Care plan modifications 3) Monitoring protocols 4) Family notification needs 5) Physician notification needed?""")

        # Step 4: Final report
        final_report = call_claude_internal(f"""You are a clinical documentation specialist.
Compile a formal Resident Risk Assessment Report:
RESIDENT: {resident_name} | FACILITY: {facility}
RISKS: {risk_factors}
RATINGS: {risk_ratings}
RECOMMENDATIONS: {recommendations}
Write a professional clinical report with executive summary, prioritized risks, action items with responsible parties. Under 400 words.""")

        result = f"""RESIDENT RISK ASSESSMENT REPORT
{'='*50}

{final_report}

{'='*50}
DETAILED RISK ANALYSIS

RISK FACTORS IDENTIFIED:
{risk_factors}

SEVERITY RATINGS:
{risk_ratings}

CARE RECOMMENDATIONS:
{recommendations}"""

        log_action("risk_assessment", resource=resident_name, details=f"Facility: {facility}")
        return jsonify({"result": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/dashboard-stats", methods=["GET"])
@login_required
def dashboard_stats():
    try:
        from sqlalchemy import func
        
        # Total documents
        total_docs = Document.query.count()
        
        # Documents this week
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        docs_this_week = Document.query.filter(Document.created_at >= week_ago).count()
        
        # Most used tools
        tool_counts = db.session.query(
            Document.tool,
            func.count(Document.tool).label('count')
        ).group_by(Document.tool).order_by(func.count(Document.tool).desc()).all()
        
        # Active users this week
        active_users = db.session.query(
            func.count(func.distinct(Document.user_email))
        ).filter(Document.created_at >= week_ago).scalar()
        
        # Recent activity
        recent = Document.query.order_by(Document.created_at.desc()).limit(10).all()
        
        # Audit log count
        total_actions = AuditLog.query.count()
        
        # Family updates published
        family_updates = FamilyUpdate.query.count()
        
        # Resident codes generated
        resident_codes = ResidentCode.query.count()
        
        # Estimated time saved (avg 15 mins per document)
        time_saved_hours = round((total_docs * 15) / 60, 1)
        
        return jsonify({
            "total_docs": total_docs,
            "docs_this_week": docs_this_week,
            "active_users": active_users or 0,
            "total_actions": total_actions,
            "family_updates": family_updates,
            "resident_codes": resident_codes,
            "time_saved_hours": time_saved_hours,
            "tool_counts": [{"tool": t, "count": c} for t, c in tool_counts],
            "recent_activity": [{
                "tool": d.tool,
                "resident": d.resident_name or d.facility_name or "—",
                "user": d.user_email,
                "time": d.created_at.strftime("%b %d, %I:%M %p")
            } for d in recent]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/profile")
@login_required
def profile_page():
    return render_template("profile.html")

@app.route("/api/profile/update", methods=["POST"])
@login_required
def update_profile():
    data = request.json
    user = User.query.get(current_user.id)
    if data.get("name"):
        user.name = data["name"]
    user.credentials = data.get("credentials", "")
    user.license_number = data.get("license_number", "")
    user.title = data.get("title", "")
    db.session.commit()
    return jsonify({"success": True})

@app.route("/api/profile/signature", methods=["GET"])
@login_required
def get_signature():
    user = User.query.get(current_user.id)
    sig = f"\n\n---\nElectronically signed by: {user.name or 'Staff Member'}"
    title = getattr(user, 'title', '')
    credentials = getattr(user, 'credentials', '')
    license_number = getattr(user, 'license_number', '')
    if title:
        sig += f", {title}"
    if credentials:
        sig += f", {credentials}"
    if license_number:
        sig += f" | License #{license_number}"
    sig += f"\nDate: {datetime.now().strftime('%B %d, %Y %I:%M %p')}"
    return jsonify({"signature": sig, "name": user.name})

@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({"error": "Too many requests. Please wait a moment and try again."}), 429

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Something went wrong. Please try again."}), 500

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)