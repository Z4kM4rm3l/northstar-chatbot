# North Star Support Bot
### AI Chatbot Developer — Upwork Talent Accelerator Submission
**Developed by:** Zakary Marmel  
**Date:** June 2026

---

## Overview

North Star is a customer support chatbot for an outdoor apparel and camping gear e-commerce brand. Built with Python, Flask, and Google Gemini, it handles the four core support use cases with natural conversation flows, intent recognition, and graceful fallback handling.

---

## Core Use Cases

| Use Case | Trigger Examples |
|---|---|
| Order Tracking | "Where is my order?", "Track my package", "Order #222" |
| Returns & Exchanges | "I want to return something", "What's your return policy?" |
| Product Recommendations | "Help me find gear", "I need a hiking jacket" |
| Human Handoff | "Talk to a person", "I need a real agent" |

---

## Mock Order Data

| Order # | Status | Response |
|---|---|---|
| #111 | Shipped | Arriving tomorrow |
| #222 | Processing | Ships within 24 hours |
| #333 | Delivered | Follow-up prompt |
| Any other | Invalid | Not found message + escalation offer |

---

## Intent Recognition

The chatbot uses a **two-layer intent detection system:**

1. **Keyword matching** — fast, reliable detection for common phrases
2. **Gemini LLM fallback** — handles ambiguous or varied phrasing

This ensures robust handling of natural language variations like:
- "Where is my order?" → order_tracking
- "Track my package" → order_tracking  
- "Has my stuff shipped?" → order_tracking

---

## Tech Stack

- **Backend:** Python 3.11, Flask
- **AI:** Google Gemini 1.5 Flash
- **Frontend:** Vanilla HTML/CSS/JS
- **Session Management:** Flask sessions (per-user conversation state)

---

## Project Structure

```
northstar-chatbot/
├── app.py              # Flask server & routes
├── chatbot.py          # Core chatbot logic, intent detection, flows
├── templates/
│   └── index.html      # Chat UI
├── requirements.txt    # Dependencies
└── README.md
```

---

## Setup & Running

### Prerequisites
- Python 3.9+
- Google Gemini API key (free tier works)

### Installation

```bash
# Clone or unzip the project
cd northstar-chatbot

# Install dependencies
pip install -r requirements.txt

# Set your Gemini API key
export GEMINI_API_KEY=your_api_key_here   # Mac/Linux
set GEMINI_API_KEY=your_api_key_here      # Windows

# Run the app
python app.py
```

### Access
Open your browser to: **http://localhost:5000**

---

## Conversation Flow Design

```
User Message
     │
     ▼
Awaiting State? (order number, follow-up)
     │ Yes → Handle directly
     │ No  ↓
Intent Detection (keywords → Gemini fallback)
     │
     ├── order_tracking    → Ask for order # → Return mock status
     ├── returns           → Return policy + link
     ├── shipping          → Shipping options + times
     ├── product_rec       → Gemini-powered clarifying Q + recommendation
     ├── human_handoff     → Transfer message + context saved
     └── unknown           → Friendly fallback + menu options
```

---

## Key Design Decisions

- **No database required** — session state held in memory, mock data hardcoded per spec
- **Stateful conversations** — chatbot remembers context within a session (e.g. awaiting order number)
- **Post-delivery follow-up** — order #333 (delivered) triggers a follow-up to check satisfaction
- **Graceful fallback** — unknown intents return a helpful menu rather than a dead end
- **Quick reply buttons** — UI shortcuts for all 4 core use cases improve usability

---

## Submission Contents

- `app.py` — Flask application
- `chatbot.py` — Chatbot logic
- `templates/index.html` — Frontend UI
- `requirements.txt` — Dependencies
- `README.md` — This file
- `demo_video.mp4` — 2-3 minute walkthrough of all use cases
