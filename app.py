import json
import os
from collections import Counter
from copy import deepcopy
from datetime import datetime

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-lite-001")
DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
MAX_FLOORS = 5

STAFF = [
    {"name": "Arjun", "role": "Security", "floor": 1},
    {"name": "Priya", "role": "Housekeeping", "floor": 2},
    {"name": "Ravi", "role": "Reception", "floor": 1},
    {"name": "Meena", "role": "Medical", "floor": 3},
    {"name": "Suresh", "role": "Manager", "floor": 2},
]

CHECKLISTS = {
    "fire": [
        "Trigger the nearest fire alarm and confirm the source area.",
        "Begin floor evacuation and secure smoke spread routes.",
        "Deploy security to isolate the zone and guide responders.",
        "Confirm guest headcount for the impacted floor.",
    ],
    "medical": [
        "Dispatch medical support with first-aid equipment immediately.",
        "Clear surrounding area and create responder access path.",
        "Contact emergency services if symptoms are severe or unclear.",
        "Log patient details and escalation decisions for handover.",
    ],
    "security": [
        "Secure the affected zone and control entry points.",
        "Separate guests from the threat area and protect evidence.",
        "Notify management and prepare external authority escalation.",
        "Track witness notes and movement around the incident location.",
    ],
    "evacuation": [
        "Initiate evacuation guidance for the impacted floor.",
        "Assign stairwell and exit support roles immediately.",
        "Confirm mobility assistance coverage for vulnerable guests.",
        "Report floor-by-floor clearance to the incident lead.",
    ],
    "general": [
        "Validate the incident source and exact floor location.",
        "Dispatch the closest qualified responders.",
        "Create a communication lead and escalation path.",
        "Monitor guest safety until the area is stabilized.",
    ],
}

CRISIS_KEYWORDS = {
    "Fire": ["fire", "smoke", "burn", "sparks", "flame", "gas leak", "explosion"],
    "Medical": ["medical", "injury", "collapsed", "unresponsive", "bleeding", "patient", "ambulance", "faint"],
    "Security": ["security", "threat", "fight", "suspicious", "intruder", "weapon", "violence", "theft"],
    "Evacuation": ["evacuate", "evacuation", "stampede", "crowd", "leakage", "flood", "earthquake"],
}

ESCALATION_ACTIONS = {
    "lock_floor": {
        "label": "Lock Floor",
        "timeline": "Security lockdown initiated for the impacted floor.",
        "description": "Moves security into lockdown mode and secures access on the affected floor.",
    },
    "evacuate": {
        "label": "Evacuate",
        "timeline": "Evacuation protocol activated and guest movement guidance started.",
        "description": "Switches the response into evacuation support and marks the checklist as urgent.",
    },
    "call_ambulance": {
        "label": "Call Ambulance",
        "timeline": "External medical support requested and ETA tracking started.",
        "description": "Escalates to external medical support and shifts reception and medical into response mode.",
    },
    "notify_manager": {
        "label": "Notify Manager",
        "timeline": "Incident commander notified with current floor and staffing details.",
        "description": "Flags the manager as actively coordinating the incident response.",
    },
    "trigger_fire_protocol": {
        "label": "Trigger Fire Protocol",
        "timeline": "Fire response checklist escalated to full protocol mode.",
        "description": "Raises severity to high and pushes the core response team into emergency mode.",
    },
    "all_clear": {
        "label": "Mark All Clear",
        "timeline": "Incident marked stable and active crisis response wound down.",
        "description": "Closes the active incident and returns assigned staff to available status.",
    },
}

crisis_history = []
incident_counter = 0


def current_time_label():
    return datetime.now().strftime("%I:%M %p")


def parse_model_json(raw_text):
    cleaned = raw_text.strip()

    if cleaned.startswith("```"):
        parts = cleaned.split("```")
        if len(parts) > 1:
            cleaned = parts[1].strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

    return json.loads(cleaned)


def normalize_severity(value):
    normalized = str(value).strip().lower()
    if normalized == "high":
        return "High"
    if normalized == "low":
        return "Low"
    return "Medium"


def validate_crisis_payload(result):
    required_keys = {"crisis_type", "severity", "summary", "assignments", "immediate_actions"}

    if not isinstance(result, dict) or not required_keys.issubset(result):
        raise ValueError("Model response did not include the expected crisis fields.")

    if not isinstance(result["immediate_actions"], list):
        raise ValueError("Model response used an invalid immediate_actions format.")

    result["crisis_type"] = str(result["crisis_type"]).strip() or "General Incident"
    result["severity"] = normalize_severity(result["severity"])
    result["summary"] = str(result["summary"]).strip() or "An incident has been detected and requires attention."
    result["immediate_actions"] = [str(item).strip() for item in result["immediate_actions"] if str(item).strip()][:3]
    if not result["immediate_actions"]:
        result["immediate_actions"] = CHECKLISTS["general"][:3]
    return result


def infer_crisis_type_from_text(text):
    lowered = text.lower()
    for crisis_type, keywords in CRISIS_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return crisis_type
    return "General Incident"


def infer_severity_from_text(text, crisis_type):
    lowered = text.lower()
    high_keywords = ["spreading", "severe", "unresponsive", "bleeding", "weapon", "explosion", "panic", "trapped"]
    low_keywords = ["small", "minor", "contained", "slow", "isolated"]

    if any(keyword in lowered for keyword in high_keywords):
        return "High"
    if any(keyword in lowered for keyword in low_keywords):
        return "Low"
    if crisis_type in {"Fire", "Medical", "Security"}:
        return "High" if crisis_type == "Medical" and "collapsed" in lowered else "Medium"
    return "Medium"


def infer_checklist_type(crisis_type):
    lowered = crisis_type.lower()
    for key in ("fire", "medical", "security", "evacuation"):
        if key in lowered:
            return key
    return "general"


def build_fallback_result(crisis_input):
    crisis_type = infer_crisis_type_from_text(crisis_input)
    severity = infer_severity_from_text(crisis_input, crisis_type)
    checklist_key = infer_checklist_type(crisis_type)
    immediate_actions = CHECKLISTS[checklist_key][:3]

    return {
        "crisis_type": crisis_type,
        "severity": severity,
        "summary": f"{crisis_type} incident detected. Continuity mode created a structured response while AI classification was unavailable.",
        "assignments": [],
        "immediate_actions": immediate_actions,
    }


def get_floor_status(staff_floor, crisis_floor):
    distance = abs(staff_floor - crisis_floor)

    if distance == 0:
        return f"On-site response - Floor {staff_floor}"
    if distance == 1:
        return f"Nearby support - Floor {staff_floor}"
    return f"Extended support - Floor {staff_floor}"


def get_availability(role, staff_floor, crisis_floor):
    distance = abs(staff_floor - crisis_floor)

    if role == "Medical" and distance <= 1:
        return "On-site" if distance == 0 else "Responding"
    if role == "Security" and distance <= 1:
        return "Responding"
    if role == "Manager":
        return "Busy"
    if distance >= 3:
        return "Off-duty"
    if distance == 0:
        return "Responding"
    return "Available"


def build_role_task(role, crisis_type, staff_floor, crisis_floor):
    floor_note = f"from Floor {staff_floor} to Floor {crisis_floor}" if staff_floor != crisis_floor else f"on Floor {crisis_floor}"
    crisis_label = crisis_type.lower()

    role_tasks = {
        "Security": f"Secure the affected area {floor_note}, control access, and guide emergency responders for the {crisis_label} incident.",
        "Housekeeping": f"Clear corridors {floor_note}, remove nearby hazards, and support evacuation logistics around the {crisis_label} incident.",
        "Reception": f"Coordinate guest communication, call external responders if needed, and direct support teams to Floor {crisis_floor}.",
        "Medical": f"Provide immediate medical assessment {floor_note}, stabilize anyone affected, and brief responders on patient condition.",
        "Manager": f"Coordinate the response command flow, confirm escalation steps, and keep teams aligned around Floor {crisis_floor}.",
    }

    return role_tasks.get(
        role,
        f"Support the {crisis_label} response {floor_note} and coordinate with the nearest available team."
    )


def build_assignments(crisis_type, crisis_floor, staff_members):
    assignments = []

    for member in staff_members:
        distance = abs(member["floor"] - crisis_floor)
        assignments.append(
            {
                "name": member["name"],
                "role": member["role"],
                "floor": member["floor"],
                "status": get_floor_status(member["floor"], crisis_floor),
                "availability": get_availability(member["role"], member["floor"], crisis_floor),
                "distance": distance,
                "eta": "Immediate" if distance == 0 else f"{distance * 2} min",
                "task": build_role_task(member["role"], crisis_type, member["floor"], crisis_floor),
            }
        )

    return assignments


def build_checklist(crisis_type):
    checklist_key = infer_checklist_type(crisis_type)
    return [
        {"label": item, "completed": index == 0}
        for index, item in enumerate(CHECKLISTS[checklist_key])
    ]


def build_timeline(crisis_type, crisis_floor, assignments):
    return [
        {
            "time": current_time_label(),
            "title": "Incident reported",
            "detail": f"{crisis_type} incident logged for Floor {crisis_floor}.",
        },
        {
            "time": current_time_label(),
            "title": "Response plan generated",
            "detail": "Severity, summary, and immediate response plan were generated.",
        },
        {
            "time": current_time_label(),
            "title": "Closest team dispatched",
            "detail": ", ".join(
                f"{member['name']} ({member['availability']})"
                for member in assignments[:3]
            ),
        },
    ]


def build_floor_overview(assignments, crisis_floor):
    floors = []
    for floor_number in range(MAX_FLOORS, 0, -1):
        responders = [
            {
                "name": member["name"],
                "role": member["role"],
                "availability": member["availability"],
            }
            for member in assignments
            if member["floor"] == floor_number
        ]
        active_count = sum(
            1
            for member in responders
            if member["availability"] in {"Busy", "Responding", "On-site"}
        )
        floors.append(
            {
                "floor": floor_number,
                "is_incident_floor": floor_number == crisis_floor,
                "responder_count": len(responders),
                "active_count": active_count,
                "responders": responders,
            }
        )
    return floors


def build_available_actions(incident):
    applied_actions = set(incident.get("applied_actions", []))
    return [
        {
            "key": key,
            "label": value["label"],
            "description": value["description"],
            "active": key in applied_actions,
        }
        for key, value in ESCALATION_ACTIONS.items()
    ]


def apply_escalation(incident, action_key):
    now = current_time_label()
    crisis_floor = incident["crisis_floor"]

    if action_key == "lock_floor":
        for member in incident["assignments"]:
            if member["role"] == "Security":
                member["availability"] = "Busy"
                member["task"] = f"Enforce floor lockdown on Floor {crisis_floor}, secure access points, and support controlled movement."
    elif action_key == "evacuate":
        for member in incident["assignments"]:
            if member["role"] in {"Housekeeping", "Reception"}:
                member["availability"] = "Busy"
        incident["checklist"] = [{"label": item["label"], "completed": True} for item in incident["checklist"]]
    elif action_key == "call_ambulance":
        for member in incident["assignments"]:
            if member["role"] == "Medical":
                member["availability"] = "On-site"
            if member["role"] == "Reception":
                member["availability"] = "Busy"
    elif action_key == "notify_manager":
        for member in incident["assignments"]:
            if member["role"] == "Manager":
                member["availability"] = "Busy"
    elif action_key == "trigger_fire_protocol":
        incident["severity"] = "High"
        for member in incident["assignments"]:
            if member["role"] in {"Security", "Housekeeping", "Manager"}:
                member["availability"] = "Busy"
    elif action_key == "all_clear":
        incident["resolved"] = True
        for member in incident["assignments"]:
            member["availability"] = "Available"

    incident["floor_overview"] = build_floor_overview(incident["assignments"], crisis_floor)
    incident["timeline"].append(
        {
            "time": now,
            "title": ESCALATION_ACTIONS[action_key]["label"],
            "detail": ESCALATION_ACTIONS[action_key]["timeline"],
        }
    )
    incident["updated_at"] = now


def rebuild_incident_state(incident):
    incident["severity"] = incident["base_severity"]
    incident["resolved"] = False
    incident["assignments"] = deepcopy(incident["base_assignments"])
    incident["checklist"] = deepcopy(incident["base_checklist"])
    incident["timeline"] = deepcopy(incident["base_timeline"])
    incident["floor_overview"] = deepcopy(incident["base_floor_overview"])

    for action_key in incident.get("applied_actions", []):
        apply_escalation(incident, action_key)


def build_analytics(history):
    if not history:
        return {
            "totals": {
                "incidents": 0,
                "high_severity": 0,
                "active_incidents": 0,
                "avg_response_distance": "0.0 floors",
            },
            "most_common_type": "No incidents yet",
            "response_trend": "No response trend available yet.",
            "staff_utilization": [],
        }

    crisis_types = Counter(item["crisis_type"] for item in history)
    total_distance = 0
    total_assignments = 0
    utilization = Counter()
    active_incidents = 0
    high_severity = 0

    for incident in history:
        if incident["severity"].lower() == "high":
            high_severity += 1
        if not incident.get("resolved"):
            active_incidents += 1

        for member in incident["assignments"]:
            total_distance += member.get("distance", 0)
            total_assignments += 1
            if member.get("availability") in {"Busy", "Responding", "On-site"}:
                utilization[member["name"]] += 1

    average_distance = total_distance / total_assignments if total_assignments else 0
    staff_utilization = [
        {"name": name, "count": count}
        for name, count in utilization.most_common()
    ]

    return {
        "totals": {
            "incidents": len(history),
            "high_severity": high_severity,
            "active_incidents": active_incidents,
            "avg_response_distance": f"{average_distance:.1f} floors",
        },
        "most_common_type": crisis_types.most_common(1)[0][0],
        "response_trend": f"{active_incidents} active incident(s) with average responder distance of {average_distance:.1f} floors.",
        "staff_utilization": staff_utilization,
    }


def build_incident_payload(result, crisis_input, crisis_floor, sorted_staff, response_source):
    global incident_counter

    assignments = build_assignments(result["crisis_type"], crisis_floor, sorted_staff)
    timeline = build_timeline(result["crisis_type"], crisis_floor, assignments)

    if response_source == "fallback":
        timeline.insert(
            1,
            {
                "time": current_time_label(),
                "title": "Continuity mode activated",
                "detail": "The AI service was unavailable, so the app switched to rule-based fallback triage.",
            },
        )

    checklist = build_checklist(result["crisis_type"])
    floor_overview = build_floor_overview(assignments, crisis_floor)
    incident_counter += 1

    return {
        "incident_id": incident_counter,
        "crisis_input": crisis_input,
        "crisis_type": result["crisis_type"],
        "severity": result["severity"],
        "summary": result["summary"],
        "crisis_floor": crisis_floor,
        "location": f"Floor {crisis_floor}",
        "timestamp": current_time_label(),
        "updated_at": current_time_label(),
        "resolved": False,
        "response_source": response_source,
        "response_mode": "AI Assisted" if response_source == "ai" else "Continuity Mode",
        "assignments": assignments,
        "timeline": timeline,
        "checklist": checklist,
        "floor_overview": floor_overview,
        "immediate_actions": result["immediate_actions"],
        "applied_actions": [],
        "base_severity": result["severity"],
        "base_assignments": deepcopy(assignments),
        "base_checklist": deepcopy(checklist),
        "base_timeline": deepcopy(timeline),
        "base_floor_overview": deepcopy(floor_overview),
    }


def public_incident_payload(incident):
    return {
        "incident_id": incident["incident_id"],
        "crisis_input": incident["crisis_input"],
        "crisis_type": incident["crisis_type"],
        "severity": incident["severity"],
        "summary": incident["summary"],
        "crisis_floor": incident["crisis_floor"],
        "location": incident["location"],
        "timestamp": incident["timestamp"],
        "updated_at": incident["updated_at"],
        "resolved": incident["resolved"],
        "response_source": incident["response_source"],
        "response_mode": incident["response_mode"],
        "assignments": incident["assignments"],
        "timeline": incident["timeline"],
        "checklist": incident["checklist"],
        "floor_overview": incident["floor_overview"],
        "immediate_actions": incident["immediate_actions"],
        "available_actions": build_available_actions(incident),
        "analytics": build_analytics(crisis_history),
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    crisis_input = data.get("crisis", "").strip()

    if not crisis_input:
        return jsonify({"error": "Please describe the crisis before analyzing."}), 400

    try:
        crisis_floor = int(data.get("floor", 1))
    except (TypeError, ValueError):
        return jsonify({"error": "Floor must be a valid number."}), 400

    sorted_staff = sorted(STAFF, key=lambda member: abs(member["floor"] - crisis_floor))
    staff_context = "\n".join(
        [f"- {member['name']} ({member['role']}, Floor {member['floor']})" for member in sorted_staff]
    )

    prompt = f"""
You are an AI crisis coordinator for a hotel.

Crisis reported: "{crisis_input}"
Crisis location: Floor {crisis_floor}

Available staff (sorted by proximity to crisis floor):
{staff_context}

Classify the crisis, estimate severity, write a one-line summary, and list the three most important immediate actions.

Respond only in this exact JSON format, with no extra text:
{{
  "crisis_type": "short type like Fire / Medical / Security",
  "severity": "High / Medium / Low",
  "summary": "one sentence describing the situation",
  "assignments": [],
  "immediate_actions": ["action 1", "action 2", "action 3"]
}}
"""

    result = None
    response_source = "fallback"

    if OPENROUTER_API_KEY:
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=25,
            )
            response.raise_for_status()
            response_json = response.json()
            result_text = response_json["choices"][0]["message"]["content"]
            result = validate_crisis_payload(parse_model_json(result_text))
            response_source = "ai"
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
            result = build_fallback_result(crisis_input)
    else:
        result = build_fallback_result(crisis_input)

    incident = build_incident_payload(result, crisis_input, crisis_floor, sorted_staff, response_source)
    crisis_history.append(incident)

    return jsonify(public_incident_payload(incident))


@app.route("/escalate", methods=["POST"])
def escalate():
    data = request.get_json(silent=True) or {}
    incident_id = data.get("incident_id")
    action_key = data.get("action")
    mode = data.get("mode", "apply")

    if not incident_id or action_key not in ESCALATION_ACTIONS:
        return jsonify({"error": "A valid incident and escalation action are required."}), 400

    incident = next((item for item in crisis_history if item["incident_id"] == incident_id), None)
    if not incident:
        return jsonify({"error": "Incident not found."}), 404

    applied_actions = incident.setdefault("applied_actions", [])

    if mode == "undo":
        if action_key not in applied_actions:
            return jsonify({"error": "That action is not currently active."}), 400
        applied_actions.remove(action_key)
        rebuild_incident_state(incident)
        incident["timeline"].append(
            {
                "time": current_time_label(),
                "title": f"{ESCALATION_ACTIONS[action_key]['label']} undone",
                "detail": "Manual rollback applied to return the incident to its previous state.",
            }
        )
        incident["updated_at"] = current_time_label()
    else:
        if action_key in applied_actions:
            return jsonify({"error": "That action has already been applied."}), 400
        applied_actions.append(action_key)
        rebuild_incident_state(incident)

    return jsonify(public_incident_payload(incident))


@app.route("/history")
def history():
    return jsonify([public_incident_payload(incident) for incident in crisis_history])


@app.route("/analytics")
def analytics():
    return jsonify(build_analytics(crisis_history))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=DEBUG)