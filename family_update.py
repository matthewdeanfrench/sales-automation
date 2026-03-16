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

def generate_family_update(resident_name, caregiver_notes):
    print(f"\n✍️ Generating family update for {resident_name}...\n")
    
    prompt = f"""You are a compassionate senior living care coordinator.

A caregiver wrote these rough notes about resident {resident_name} today:

{caregiver_notes}

Please turn these notes into a warm, professional family update email. Include:
1. A friendly greeting
2. How {resident_name} is doing overall
3. Highlights from their day
4. Any important health or care notes (in reassuring language)
5. A warm closing

Keep it under 200 words. Sound human and caring, not clinical."""

    response = ask_claude(prompt)
    if response:
        print(response)

if __name__ == "__main__":
    print("=== Family Update Generator ===\n")
    resident_name = input("Resident name: ")
    print("Enter caregiver notes (press Enter twice when done):")
    
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    
    caregiver_notes = "\n".join(lines)
    generate_family_update(resident_name, caregiver_notes)