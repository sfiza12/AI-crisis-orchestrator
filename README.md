# AI Crisis Orchestrator

AI Crisis Orchestrator is a hotel and resort emergency response prototype built as a live command-center web app. It combines AI-assisted crisis classification with deterministic staff coordination, escalation controls, emergency checklists, analytics, and voice-supported incident intake.

## Overview

This project is designed to demonstrate how hospitality teams can respond faster and more clearly during emergencies such as fire incidents, medical events, security threats, or evacuation scenarios.

The app accepts a crisis description and floor location, classifies the situation with AI, then turns that output into a structured response workflow:

- crisis type and severity
- responder assignments by role and floor
- live incident timeline
- emergency checklist
- one-click escalation controls
- analytics and history tracking

## Current Highlights

- AI-powered incident classification using OpenRouter
- Deterministic staff assignment logic based on floor proximity and staff roles
- Live incident timeline with escalation and undo support
- Role-aware staff states such as `Available`, `Responding`, `On-site`, `Busy`, and `Off-duty`
- Emergency checklist generation by crisis type
- One-click actions like `Lock Floor`, `Evacuate`, `Call Ambulance`, `Notify Manager`, `Trigger Fire Protocol`, and `Mark All Clear`
- Built-in analytics dashboard
- Browser voice input for crisis reporting
- Polished command-center style interface
- Project brief PDF included in the repo

## Tech Stack

- Python
- Flask
- HTML
- CSS
- Vanilla JavaScript
- OpenRouter API
- `python-dotenv`
- `requests`

## Project Structure

```text
ai-crisis-orchestrator/
├── app.py
├── requirements.txt
├── .gitignore
├── AI_Crisis_Orchestrator_Project_Brief.pdf
├── templates/
│   └── index.html
├── static/
│   ├── script.js
│   └── style.css
└── tools/
    └── generate_project_brief_pdf.py
```

## How It Works

### 1. Incident Intake

The user enters or speaks a crisis description and selects the affected floor.

### 2. AI Triage

The backend sends the report to OpenRouter and asks for:

- crisis type
- severity
- short summary
- immediate actions

### 3. Operational Logic

Once the AI returns its classification, the backend computes:

- nearest responder order
- staff availability state
- role-specific response tasks
- floor-aware status labels
- timeline events
- emergency checklist
- escalation metadata
- analytics summary

### 4. Live Dashboard

The frontend renders a command-center interface showing:

- incident overview
- live timeline
- staff assignments
- emergency checklist
- escalation controls
- priority actions
- analytics
- crisis history

## API Routes

| Route | Method | Purpose |
|---|---|---|
| `/` | `GET` | Loads the main dashboard |
| `/analyze` | `POST` | Creates a new incident from crisis input |
| `/escalate` | `POST` | Applies or undoes escalation actions |
| `/history` | `GET` | Returns in-memory incident history |
| `/analytics` | `GET` | Returns aggregated prototype analytics |

## Running Locally

### 1. Clone the repo

```bash
git clone https://github.com/sfiza12/AI-crisis-orchestrator.git
cd AI-crisis-orchestrator
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file

Add your OpenRouter credentials:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=google/gemini-2.0-flash-lite-001
FLASK_DEBUG=true
```

### 5. Run the app

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Notes

- `.env` is ignored by git and should not be committed.
- Incident history is currently stored in memory only.
- Voice input depends on browser support for the Web Speech API.
- Escalation behavior is simulated for prototype/demo use.

## Included Documentation

This repo includes:

- [AI_Crisis_Orchestrator_Project_Brief.pdf](./AI_Crisis_Orchestrator_Project_Brief.pdf)
- [tools/generate_project_brief_pdf.py](./tools/generate_project_brief_pdf.py)

You can regenerate the PDF if needed using the provided script and a Python environment with `reportlab`.

## Future Enhancements

Planned evolution beyond the current prototype:

- database-backed persistence
- authentication and role-based access
- separate manager and staff dashboards
- daily task assignment and shift planning
- live staff directory and internal contact system
- multi-incident handling
- floor-map visualization
- external alerting integrations
- exportable incident reports
- property-management and building-system integrations

## Product Direction

The long-term vision is larger than a crisis demo.

This can evolve into a full hospitality operations platform where:

- managers assign daily tasks, oversee staff, and coordinate incidents
- staff log in to view responsibilities, contacts, tasks, and crisis instructions
- emergency response becomes one powerful module inside a broader hotel operations system

## Why This Project Stands Out

- It is not just an AI chatbot wrapped in a UI.
- It combines AI with deterministic operational logic.
- It focuses on a real use case with clear value in hospitality.
- It demonstrates product thinking, workflow design, and UI polish.

## License

This project currently has no license specified.

