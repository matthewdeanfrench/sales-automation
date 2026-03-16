# AI Tools for Senior Living

A collection of AI-powered automation tools built to reduce administrative burden 
for senior living facility staff — freeing them up to focus on resident care.

Built by Matt French — Sales professional turned AI automation builder.

---

## Tools

### 🔍 Prospect Research Tool (`research.py`)
Before any sales call, type in a company name and instantly get:
- Company overview and biggest challenges
- 3 tailored talking points
- 3 smart discovery questions

**Run it:**
```
py research.py
```

### 💌 Family Update Generator (`family_update.py`)
Paste in rough caregiver notes and instantly get a warm, professional 
family update email — in seconds instead of 15 minutes.

**Run it:**
```
py family_update.py
```

---

## Why I Built This

Senior living facilities are understaffed and overwhelmed with administrative work. 
Caregivers spend hours writing emails, reports, and documentation instead of 
caring for residents. These tools use AI to handle the repetitive writing tasks 
so staff can focus on what matters.

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
4. Run any tool with `py filename.py`

---

## What's Next

- Incident report generator
- Medication log summarizer  
- Move-in welcome letter automation
- Web interface for non-technical staff