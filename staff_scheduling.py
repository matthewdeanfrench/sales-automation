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

def analyze_scheduling_problem(facility_name, problem_description):
    print(f"\n📅 Analyzing scheduling issue at {facility_name}...\n")
    
    prompt = f"""You are an expert in senior living facility operations and staff scheduling.

The facility manager at {facility_name} has this scheduling problem:

{problem_description}

Please provide:
1. IMMEDIATE FIX — what to do right now to solve the coverage gap
2. STAFF TO CALL — who to contact first and what to say
3. OVERTIME RISK — flag any overtime concerns and how to avoid them
4. PREVENT IT NEXT TIME — one specific process change to prevent this from happening again
5. SCRIPT — give them an exact script to use when calling staff to cover the shift

Be direct and practical. This manager is stressed and needs fast answers."""

    response = ask_claude(prompt)
    if response:
        print(response)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"schedule_issue_{facility_name.replace(' ', '_')}_{timestamp}.txt"
        with open(filename, 'w') as f:
            f.write(f"SCHEDULING ISSUE REPORT\n")
            f.write(f"Facility: {facility_name}\n")
            f.write(f"Date: {datetime.now().strftime('%B %d, %Y %I:%M %p')}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"PROBLEM:\n{problem_description}\n\n")
            f.write("AI RECOMMENDATIONS:\n\n")
            f.write(response)
        print(f"\n✅ Saved to: {filename}")

if __name__ == "__main__":
    print("=== Staff Scheduling Assistant ===\n")
    facility_name = input("Facility name: ")
    print("Describe the scheduling problem (press Enter twice when done):")
    
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    
    problem = "\n".join(lines)
    analyze_scheduling_problem(facility_name, problem)