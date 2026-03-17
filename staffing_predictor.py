from dotenv import load_dotenv
load_dotenv()
import urllib.request
import json
import os

API_KEY = os.environ.get("ANTHROPIC_API_KEY")

def ask_claude(prompt):
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
    except Exception as e:
        return f"Error: {str(e)}"

def predict_staffing(facility_name, historical_data):
    print(f"\n🔮 Analyzing staffing patterns for {facility_name}...\n")
    
    prompt = f"""You are an expert in senior living facility operations and workforce analytics.

A facility manager at {facility_name} has provided this staffing history:

{historical_data}

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
- Seasonal patterns
- Individual staff patterns

IMMEDIATE ACTIONS
3 specific things the manager should do TODAY to prevent shortages.
Be concrete — who to call, what to offer, what policy to implement.

STAFF TO CONTACT NOW
Based on the patterns, which types of staff should be contacted proactively?
What should they be offered to ensure availability?

30-DAY RECOMMENDATION
One structural change to prevent this pattern from recurring.

Format this as a clear operational report a facility manager can act on immediately."""

    response = ask_claude(prompt)
    print(response)
    return response

# Sample historical data for testing
sample_data = """
Last 30 days call-out log:
- Monday nights: 4 call-outs (CNAs)
- Tuesday days: 1 call-out
- Wednesday nights: 3 call-outs (CNAs)  
- Thursday days: 2 call-outs
- Friday nights: 6 call-outs (highest risk)
- Saturday all shifts: 5 call-outs
- Sunday days: 3 call-outs

Staff with multiple call-outs:
- Sarah M: 4 call-outs (all Friday nights)
- James T: 3 call-outs (Monday/Wednesday nights)
- Two agency staff used last weekend

Current staffing levels:
- Day shift: 8 CNAs (need minimum 6)
- Night shift: 5 CNAs (need minimum 4)
- Weekend coverage historically 20% below weekday

Upcoming known absences:
- 2 CNAs on vacation next week
- 1 RN on medical leave
"""

if __name__ == "__main__":
    facility = input("Facility name (or press Enter for demo): ").strip()
    if not facility:
        facility = "Sunrise Gardens"
        data = sample_data
        print("Running with sample data...")
    else:
        print("Enter staffing history (press Enter twice when done):")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        data = "\n".join(lines)
    
    predict_staffing(facility, data)