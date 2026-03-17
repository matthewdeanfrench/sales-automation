from dotenv import load_dotenv
load_dotenv()
import urllib.request
import json
import os

API_KEY = os.environ.get("ANTHROPIC_API_KEY")

def call_claude(prompt, system=None):
    url = "https://api.anthropic.com/v1/messages"
    
    messages = [{"role": "user", "content": prompt}]
    
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1024,
        "messages": messages
    }
    
    if system:
        payload["system"] = system
    
    data = json.dumps(payload).encode()
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

def resident_risk_agent(resident_name, resident_notes, facility_name=""):
    print(f"\n🤖 Starting Risk Assessment Agent for {resident_name}...")
    print("=" * 60)
    
    # STEP 1: Identify risk factors
    print("\n📋 Step 1: Identifying risk factors...")
    step1_prompt = f"""You are a senior living clinical expert.

A caregiver has provided these notes about resident {resident_name}:
{resident_notes}

Extract and list ALL risk factors present. Be thorough.
Format as a numbered list. Include: clinical risks, fall risks, 
medication risks, social/behavioral risks, environmental risks.
Only list the risks, no explanations yet."""

    risk_factors = call_claude(step1_prompt)
    print(risk_factors)
    
    # STEP 2: Rate each risk
    print("\n⚠️ Step 2: Rating severity of each risk...")
    step2_prompt = f"""You are a senior living clinical risk specialist.

Resident: {resident_name}
Original notes: {resident_notes}

Risk factors identified:
{risk_factors}

For each risk factor, provide:
- Severity: Critical / High / Medium / Low
- Why it's that severity level
- Immediate action needed (if any)

Format clearly with each risk on its own section."""

    risk_ratings = call_claude(step2_prompt)
    print(risk_ratings)
    
    # STEP 3: Generate care recommendations
    print("\n💊 Step 3: Generating care recommendations...")
    step3_prompt = f"""You are a Director of Nursing creating care recommendations.

Resident: {resident_name}
Facility: {facility_name or 'Senior Living Facility'}

Based on this risk analysis:
{risk_ratings}

Generate specific, actionable care recommendations:
1. Immediate interventions (today)
2. Care plan modifications needed
3. Monitoring protocols
4. Family notification recommendations
5. Physician notification needed? (yes/no and why)

Be specific and clinical."""

    recommendations = call_claude(step3_prompt)
    print(recommendations)
    
    # STEP 4: Write final report
    print("\n📄 Step 4: Compiling final report...")
    step4_prompt = f"""You are a clinical documentation specialist.

Compile a formal Resident Risk Assessment Report using this information:

RESIDENT: {resident_name}
FACILITY: {facility_name or 'Senior Living Facility'}

RISK FACTORS IDENTIFIED:
{risk_factors}

RISK SEVERITY RATINGS:
{risk_ratings}

CARE RECOMMENDATIONS:
{recommendations}

Write a professional, concise clinical report that:
- Has a clear executive summary
- Lists risks by priority
- Includes specific action items with responsible parties
- Is suitable for inclusion in the medical record
- Is under 400 words"""

    final_report = call_claude(step4_prompt)
    
    print("\n" + "=" * 60)
    print("📄 FINAL RISK ASSESSMENT REPORT")
    print("=" * 60)
    print(final_report)
    
    return {
        "risk_factors": risk_factors,
        "risk_ratings": risk_ratings,
        "recommendations": recommendations,
        "final_report": final_report
    }

if __name__ == "__main__":
    print("=== Resident Risk Assessment Agent ===")
    print("This agent makes 4 AI calls to build a comprehensive risk report.\n")
    
    resident_name = input("Resident name: ")
    facility = input("Facility name (optional): ")
    print("Enter resident notes (press Enter twice when done):")
    
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    
    notes = "\n".join(lines)
    resident_risk_agent(resident_name, notes, facility)