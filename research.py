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

def research_prospect(company_name):
    print(f"\n🔍 Researching {company_name}...\n")
    
    prompt = f"""I have a sales call with {company_name} today. I sell AI automation tools to senior living facilities.

Give me:
1. What {company_name} likely does and their biggest challenges
2. 3 specific talking points connecting their challenges to AI automation
3. 3 smart questions to ask on the call

Be specific and practical. I have 2 minutes to prep."""

    response = ask_claude(prompt)
    if response:
        print(response)

if __name__ == "__main__":
    company = input("Enter company name: ")
    research_prospect(company)