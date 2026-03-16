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
        print(f"Error code: {e.code}")
        print(f"Error detail: {error_body}")
        return None

def generate_move_in_package(facility_name, resident_name, room_number, 
                              move_in_date, care_level, family_contact, notes):
    print(f"\n🏠 Generating move-in package for {resident_name}...\n")
    
    prompt = f"""You are a warm, professional senior living coordinator at {facility_name}.

A new resident is moving in with these details:
- Resident name: {resident_name}
- Room number: {room_number}
- Move-in date: {move_in_date}
- Care level: {care_level}
- Primary family contact: {family_contact}
- Additional notes: {notes}

Please generate a complete move-in package with these 3 documents:

---DOCUMENT 1: WELCOME LETTER---
A warm, personal welcome letter to {resident_name} and their family.
Mention their room number, move-in date, and what to expect on day one.
Signed by the Executive Director. Keep it under 200 words. Warm and reassuring.

---DOCUMENT 2: FAMILY CHECKLIST---
A practical checklist for the family covering:
- What to bring on move-in day
- What NOT to bring (valuables, certain medications)
- Who to contact for different needs
- First week expectations
- How to stay connected with their loved one

---DOCUMENT 3: DAY ONE SCHEDULE---
A personalized schedule for {resident_name}'s first day including:
- Arrival and room setup time
- Meet the care team
- First meal in the dining room
- Orientation tour
- Evening wind-down

Make everything warm, specific, and professional."""

    response = ask_claude(prompt)
    if response:
        print(response)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"move_in_{resident_name.replace(' ', '_')}_{timestamp}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"MOVE-IN PACKAGE\n")
            f.write(f"Facility: {facility_name}\n")
            f.write(f"Resident: {resident_name}\n")
            f.write(f"Generated: {datetime.now().strftime('%B %d, %Y')}\n")
            f.write("=" * 50 + "\n\n")
            f.write(response)
        print(f"\n✅ Complete move-in package saved to: {filename}")

if __name__ == "__main__":
    print("=== Move-In Package Generator ===\n")
    facility_name = input("Facility name: ")
    resident_name = input("Resident name: ")
    room_number = input("Room number: ")
    move_in_date = input("Move-in date (e.g. March 20, 2026): ")
    care_level = input("Care level (e.g. assisted living, memory care): ")
    family_contact = input("Primary family contact name: ")
    print("Any special notes about this resident (press Enter twice when done):")
    
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    
    notes = "\n".join(lines) if lines else "None"
    
    generate_move_in_package(facility_name, resident_name, room_number,
                             move_in_date, care_level, family_contact, notes)