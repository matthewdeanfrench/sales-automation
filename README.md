# AI Tools for Senior Living

A collection of AI-powered automation tools built to eliminate administrative 
burden for senior living facility staff — freeing them to focus on resident care.

Built by Matt French — Sales professional turned AI automation builder.
Specializing in senior living operations.

---

## Tools

### 🔍 Prospect Research (`research.py`)
Before any sales call, type a company name and instantly get a company 
overview, their biggest challenges, tailored talking points, and smart 
discovery questions.

### 💌 Family Update Generator (`family_update.py`)
Paste rough caregiver notes and get a warm, professional family update 
email in seconds — instead of 15 minutes.

### 📋 Incident Report Generator (`incident_report.py`)
Paste rough notes about an incident and get a fully compliant, 
professional incident report ready for regulatory review. Auto-saves 
to file.

### 📅 Staff Scheduling Assistant (`staff_scheduling.py`)
Describe a scheduling crisis and get an immediate action plan — who to 
call, what to say, overtime warnings, and a word-for-word phone script.

### 🏠 Move-In Package Generator (`move_in.py`)
Enter a new resident's details and instantly generate a complete move-in 
package: personalized welcome letter, family checklist, and day one 
schedule.

### 🔮 Predictive Staffing AI (`staffing_predictor.py`)
Analyzes historical call-out patterns and predicts staffing shortages before 
they happen. Provides risk assessment, probability scores for each shift, 
immediate action plans, and 30-day structural recommendations.

---

## Why I Built This

Senior living facilities are critically understaffed. Caregivers and 
administrators spend hours on documentation, communication, and paperwork 
instead of caring for residents. These tools use AI to handle the 
repetitive writing and decision-making tasks so staff can focus on 
what matters most — the people in their care.

---

## Setup

1. Clone this repo
2. Create a `.env` file with your Anthropic API key:
```
ANTHROPIC_API_KEY=your-key-here
```
3. Install dependencies:
```
py -m pip install python-dotenv
```
4. Run any tool:
```
py research.py
py family_update.py
py incident_report.py
py staff_scheduling.py
py move_in.py
```

---

## What's Next

- Medication log summarizer
- Billing and occupancy tracker  
- Care plan documentation
- Web interface for non-technical staff
- Workato integration for full automation