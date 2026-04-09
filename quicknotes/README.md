# QuickNotes - 隨時筆記

> Your AI-Powered Personal Note Organizer

## Overview

QuickNotes is a simple but smart personal note-taking tool where you can jot down anything anytime, anywhere (on mobile or desktop), and AI (Laura) automatically organizes everything for you.

## Features

- ⚡ **Quick Capture** - Type or voice a note in Signal, hit send
- 🤖 **AI Auto-Organization** - Laura categorizes, tags, summarizes, and links notes
- 🔍 **Searchable** - Find any note instantly with clean timeline view
- 🔒 **Private & Secure** - Notes stay on your server
- ⏰ **Smart Reminders** - Automatic date/time detection

## How It Works

1. Send a message in Signal to Laura
2. Laura processes and organizes the note
3. View all notes at the dashboard

### Example

**You:** "buy milk tomorrow"

**Laura:**
```
✅ Note saved!
━━━━━━━━━━━━━━━━━━
📝 Summary: Buy milk
📂 Category: Shopping
🏷️ Tags: #groceries #urgent
⏰ Reminder: Tomorrow
🔗 Related: None
━━━━━━━━━━━━━━━━━━
```

## Tech Stack

- **Backend:** Python Flask API
- **Frontend:** HTML/CSS/JavaScript
- **Storage:** JSON file-based (simple, portable)
- **Integration:** Signal messaging via OpenClaw

## Setup

1. Clone this repo
2. Install dependencies: `pip3 install flask`
3. Start dashboard: `cd backend && python3 app.py`
4. Access at `http://localhost:5678`

## Project Structure

```
quicknotes/
├── backend/
│   ├── app.py              # Flask API server
│   └── laura_process.py    # Note processing script
├── templates/
│   └── index.html          # Dashboard template
├── memory/
│   └── notes.json          # Notes storage
├── IDENTITY.md             # Laura's identity
├── SOUL.md                 # Laura's persona
└── AGENT.md                # Agent instructions
```

## License

Personal use only. Part of the On9Claw ecosystem.

---

Built with 🦞 by Parklanclaw
