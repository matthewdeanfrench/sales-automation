from dotenv import load_dotenv
load_dotenv()
import urllib.request
import json
import os
from datetime import datetime

API_KEY = os.environ.get("ANTHROPIC_API_KEY")

def ask_claude(prompt):
    url = "https://api.anthropic.com/v1/messages"
    
    data = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1024,
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
        print(f"Error code: {e.code}")
        print(f"Error detail: {error_body}")
        return None

def generate_incident_report(resident_name, staff_name, rough_notes):
    print(f"\n📋 Generating incident report for {resident_name}...\n")
    
    today = datetime.now().strftime("%B %d, %Y %I:%M %p")
    
    prompt = f"""You are a senior living facility administrator helping staff write 
professional incident reports for compliance and documentation purposes.

Staff member {staff_name} reported this incident involving resident {resident_name}:

{rough_notes}

Please generate a formal incident report with these sections:
1. INCIDENT SUMMARY - one clear sentence describing what happened
2. DATE & TIME - use {today}
3. RESIDENT - {resident_name}
4. STAFF PRESENT - {staff_name}
5. DETAILED DESCRIPTION - professional, factual account of the incident
6. IMMEDIATE ACTIONS TAKEN - what staff did in response
7. RESIDENT CONDITION AFTER INCIDENT - current status
8. FOLLOW UP REQUIRED - recommended next steps

Use professional, clinical language suitable for regulatory review. 
Be factual and specific. Do not speculate."""

    response = ask_claude(prompt)
    if response:
        print(response)
        
        # Save to a file
        filename = f"incident_{resident_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        with open(filename, 'w') as f:
            f.write(f"INCIDENT REPORT\n")
            f.write(f"Generated: {today}\n")
            f.write("=" * 50 + "\n\n")
            f.write(response)
        print(f"\n✅ Report saved to: {filename}")

if __name__ == "__main__":
    print("=== Incident Report Generator ===\n")
    resident_name = input("Resident name: ")
    staff_name = input("Your name: ")
    print("Describe what happened (press Enter twice when done):")
    
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    
    rough_notes = "\n".join(lines)
    generate_incident_report(resident_name, staff_name, rough_notes)