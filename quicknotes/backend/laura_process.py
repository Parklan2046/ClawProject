#!/usr/bin/env python3
"""
Laura - Note Processing Script
Called by OpenClaw to process and save notes.
"""

import sys
import json
import os
from datetime import datetime
import urllib.request

NOTES_FILE = os.path.expanduser("~/.openclaw/workspace/quicknotes/memory/notes.json")

def categorize_note(text):
    """Auto-categorize based on content"""
    text_lower = text.lower()
    
    shopping_keywords = ['buy', 'purchase', 'get', 'pick up', 'shop', 'groceries', 'milk', 'bread', 'store']
    work_keywords = ['meeting', 'work', 'call', 'email', 'client', 'project', 'deadline', 'boss', 'office']
    health_keywords = ['doctor', 'gym', 'exercise', 'medication', 'appointment', 'health', 'dentist', 'hospital']
    finance_keywords = ['bill', 'pay', 'money', 'bank', 'investment', 'stock', 'budget', 'expense', 'salary']
    travel_keywords = ['trip', 'flight', 'hotel', 'booking', 'travel', 'vacation', 'airport', 'passport']
    idea_keywords = ['idea', 'thought', 'maybe', 'what if', 'suggestion', 'feature', 'creative', 'innovate']
    
    if any(kw in text_lower for kw in shopping_keywords):
        return "Shopping"
    elif any(kw in text_lower for kw in work_keywords):
        return "Work"
    elif any(kw in text_lower for kw in health_keywords):
        return "Health"
    elif any(kw in text_lower for kw in finance_keywords):
        return "Finance"
    elif any(kw in text_lower for kw in travel_keywords):
        return "Travel"
    elif any(kw in text_lower for kw in idea_keywords):
        return "Ideas"
    elif 'todo' in text_lower or 'task' in text_lower or 'need to' in text_lower:
        return "To-do"
    else:
        return "Personal"

def extract_tags(text, category):
    """Extract relevant tags"""
    text_lower = text.lower()
    tags = []
    
    # Time-based tags
    if any(w in text_lower for w in ['tomorrow', 'next week', 'today', 'urgent', 'asap']):
        tags.append("#urgent")
    if any(w in text_lower for w in ['follow up', 'follow-up', 'reminder', 'remember']):
        tags.append("#follow-up")
    
    # Category-specific tags
    if category == "Shopping":
        if any(w in text_lower for w in ['groceries', 'food', 'milk', 'bread', 'vegetables']):
            tags.append("#groceries")
        tags.append("#shopping")
    elif category == "Work":
        tags.append("#work")
        if 'meeting' in text_lower:
            tags.append("#meeting")
        if 'call' in text_lower:
            tags.append("#call")
    elif category == "Health":
        tags.append("#health")
        if 'doctor' in text_lower or 'dentist' in text_lower:
            tags.append("#appointment")
    elif category == "Finance":
        tags.append("#finance")
    elif category == "Ideas":
        tags.append("#idea")
        tags.append("#creative")
    elif category == "Personal":
        tags.append("#personal")
        if 'birthday' in text_lower:
            tags.append("#birthday")
    
    return tags if tags else ["#note"]

def detect_reminder(text):
    """Detect if there's a date/time reminder"""
    text_lower = text.lower()
    
    time_indicators = {
        'tomorrow': 'Tomorrow',
        'next week': 'Next Week',
        'next month': 'Next Month',
        'today': 'Today',
        'tonight': 'Tonight',
        'this weekend': 'This Weekend'
    }
    
    for indicator, reminder in time_indicators.items():
        if indicator in text_lower:
            return reminder
    
    return "None"

def save_note(raw_text, summary, category, tags, reminder, related="None"):
    """Save note to JSON file"""
    os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
    
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, 'r') as f:
            notes = json.load(f)
    else:
        notes = []
    
    note = {
        "id": len(notes) + 1,
        "timestamp": datetime.utcnow().isoformat(),
        "raw_text": raw_text,
        "summary": summary,
        "category": category,
        "tags": tags,
        "reminder": reminder,
        "related": related
    }
    
    notes.append(note)
    
    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)
    
    return note

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 laura_process.py <note_text>")
        sys.exit(1)
    
    raw_text = ' '.join(sys.argv[1:])
    
    # Process the note
    category = categorize_note(raw_text)
    tags = extract_tags(raw_text, category)
    reminder = detect_reminder(raw_text)
    
    # Simple summary (first sentence or truncated)
    summary = raw_text[:100] if len(raw_text) > 100 else raw_text
    
    # Save the note
    note = save_note(raw_text, summary, category, tags, reminder)
    
    # Output formatted response
    print(f"✅ Note saved!")
    print("━━━━━━━━━━━━━━━━━━")
    print(f"📝 Summary: {summary}")
    print(f"📂 Category: {category}")
    print(f"🏷️ Tags: {' '.join(tags)}")
    print(f"⏰ Reminder: {reminder}")
    print(f"🔗 Related: None")
    print("━━━━━━━━━━━━━━━━━━")
