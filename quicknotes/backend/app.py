#!/usr/bin/env python3
"""
QuickNotes Backend API & Dashboard
Serves a web interface to view, search, and manage notes stored in memory.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime
import json
import os
import glob
import re

app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')

# Paths
NOTES_DIR = os.path.expanduser("~/.openclaw/workspace/quicknotes/memory")
NOTES_FILE = os.path.join(NOTES_DIR, "notes.json")

def load_notes():
    """Load all notes from JSON file"""
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_notes(notes):
    """Save notes to JSON file"""
    os.makedirs(NOTES_DIR, exist_ok=True)
    with open(NOTES_FILE, 'w') as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)

def add_note(summary, category, tags, reminder, related, raw_text):
    """Add a new note"""
    notes = load_notes()
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
    save_notes(notes)
    return note

@app.route('/')
def dashboard():
    """Main dashboard"""
    notes = load_notes()
    # Sort by newest first
    notes = sorted(notes, key=lambda x: x['timestamp'], reverse=True)
    
    # Get categories
    categories = {}
    for note in notes:
        cat = note.get('category', 'Uncategorized')
        categories[cat] = categories.get(cat, 0) + 1
    
    return render_template('index.html', 
                         notes=notes, 
                         categories=categories,
                         total=len(notes))

@app.route('/api/notes', methods=['GET'])
def api_notes():
    """API: Get all notes"""
    notes = load_notes()
    notes = sorted(notes, key=lambda x: x['timestamp'], reverse=True)
    return jsonify(notes)

@app.route('/api/notes', methods=['POST'])
def api_add_note():
    """API: Add a new note"""
    data = request.json
    note = add_note(
        summary=data.get('summary', ''),
        category=data.get('category', 'Personal'),
        tags=data.get('tags', []),
        reminder=data.get('reminder', 'None'),
        related=data.get('related', 'None'),
        raw_text=data.get('raw_text', '')
    )
    return jsonify(note), 201

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def api_delete_note(note_id):
    """API: Delete a note"""
    notes = load_notes()
    notes = [n for n in notes if n['id'] != note_id]
    save_notes(notes)
    return jsonify({"status": "deleted"})

@app.route('/api/search')
def api_search():
    """API: Search notes"""
    query = request.args.get('q', '').lower()
    category = request.args.get('category', '')
    notes = load_notes()
    
    results = []
    for note in notes:
        # Search in raw text, summary, tags
        text = f"{note.get('raw_text', '')} {note.get('summary', '')} {' '.join(note.get('tags', []))}".lower()
        
        if query and query not in text:
            continue
        if category and note.get('category') != category:
            continue
        
        results.append(note)
    
    results = sorted(results, key=lambda x: x['timestamp'], reverse=True)
    return jsonify(results)

@app.route('/api/categories')
def api_categories():
    """API: Get category breakdown"""
    notes = load_notes()
    categories = {}
    for note in notes:
        cat = note.get('category', 'Uncategorized')
        categories[cat] = categories.get(cat, 0) + 1
    return jsonify(categories)

if __name__ == '__main__':
    os.makedirs(NOTES_DIR, exist_ok=True)
    # Create notes.json if it doesn't exist
    if not os.path.exists(NOTES_FILE):
        save_notes([])
    
    print("📝 QuickNotes Dashboard starting on http://0.0.0.0:5678")
    app.run(host='0.0.0.0', port=5678, debug=False)
