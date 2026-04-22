from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "AI_Crisis_Orchestrator_Project_Brief.pdf"


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleCenter",
            parent=styles["Title"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#122033"),
            fontSize=24,
            leading=28,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubTitleCenter",
            parent=styles["BodyText"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#506176"),
            fontSize=11,
            leading=15,
            spaceAfter=18,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#0F355A"),
            fontSize=15,
            leading=19,
            spaceBefore=12,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallMuted",
            parent=styles["BodyText"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#66778A"),
        )
    )
    styles["BodyText"].fontSize = 10.5
    styles["BodyText"].leading = 15
    return styles


def bullet_list(items, styles):
    return ListFlowable(
        [
            ListItem(Paragraph(item, styles["BodyText"]), leftIndent=10)
            for item in items
        ],
        bulletType="bullet",
        start="circle",
        leftIndent=18,
        bulletFontName="Helvetica",
        bulletFontSize=8,
        bulletColor=colors.HexColor("#244B74"),
    )


def info_table(data):
    table = Table(data, colWidths=[1.85 * inch, 4.95 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173B63")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7FAFD")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F7FAFD"), colors.HexColor("#EDF3F8")]),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#BFD0E0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D2DDEA")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def build_story():
    styles = build_styles()
    story = []

    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph("AI Crisis Orchestrator", styles["TitleCenter"]))
    story.append(
        Paragraph(
            "Project Brief, Prototype Documentation, and Future Enhancement Roadmap",
            styles["SubTitleCenter"],
        )
    )
    story.append(
        Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            styles["SmallMuted"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("1. Executive Summary", styles["SectionHeading"]))
    story.append(
        Paragraph(
            "AI Crisis Orchestrator is a hotel and resort emergency coordination prototype built as a real-time command-center experience. "
            "The application accepts crisis reports, identifies the incident type and severity with AI assistance, then converts that result into "
            "deterministic staff assignments, live timeline updates, operational checklists, one-click escalations, analytics, and voice-supported reporting.",
            styles["BodyText"],
        )
    )
    story.append(Spacer(1, 0.08 * inch))
    story.append(
        bullet_list(
            [
                "Primary goal: enable rapid response and coordinated action during hotel emergencies.",
                "Current maturity: high-quality interactive prototype suitable for screening rounds and demo presentations.",
                "Strategic direction: evolve from a crisis-response console into a broader hotel staff operations and emergency management platform.",
            ],
            styles,
        )
    )

    story.append(Paragraph("2. Project Overview", styles["SectionHeading"]))
    story.append(
        info_table(
            [
                ["Category", "AI-enabled hotel emergency response and staff coordination prototype"],
                ["Core users today", "Demo evaluator, hotel operations lead, incident coordinator"],
                ["Problem solved", "Slow, unstructured, and manual crisis communication during hotel incidents"],
                ["Project type", "Web-based command center application"],
                ["Current architecture", "Flask backend with HTML/CSS/JavaScript frontend and OpenRouter-powered AI classification"],
                ["Prototype emphasis", "Fast coordination, visual clarity, believable workflows, and demo impact"],
            ]
        )
    )

    story.append(Paragraph("3. Current Feature Set", styles["SectionHeading"]))
    story.append(
        bullet_list(
            [
                "AI crisis intake: accepts a free-text emergency report and floor selection.",
                "AI-generated classification: predicts crisis type, severity, summary, and immediate actions.",
                "Deterministic responder assignment: staff floor, status, ETA, and task routing come from backend logic instead of untrusted model output.",
                "Live incident timeline: records reported, triaged, dispatched, escalation, and undo events.",
                "Emergency checklist: maps incident categories such as fire, medical, security, evacuation, and general response to structured action lists.",
                "One-click escalation controls: lock floor, evacuate, call ambulance, notify manager, trigger fire protocol, and mark all clear.",
                "Undo and lock behavior: escalation actions become active and locked after use, with rollback support.",
                "Staff availability states: available, off-duty, responding, on-site, and busy.",
                "Analytics dashboard: incident count, active count, high-severity count, average response distance, dominant crisis type, and staff utilization.",
                "Voice input: browser-based speech recognition can populate incident details rapidly.",
                "Crisis history: previous incidents remain visible during the app session.",
            ],
            styles,
        )
    )

    story.append(Paragraph("4. User Flow", styles["SectionHeading"]))
    story.append(
        bullet_list(
            [
                "Step 1: user enters or speaks a crisis description and selects the affected floor.",
                "Step 2: backend calls the AI model for classification and immediate action suggestions.",
                "Step 3: backend computes staff assignments, checklist, timeline, analytics, and escalation metadata.",
                "Step 4: frontend renders a command-center dashboard with summary, timeline, assignments, and controls.",
                "Step 5: user can apply escalation actions, which update timeline entries, staff statuses, severity, and resolution state.",
                "Step 6: history and analytics reflect the current incident state and any follow-up incidents created during the demo.",
            ],
            styles,
        )
    )

    story.append(Paragraph("5. Technical Architecture", styles["SectionHeading"]))
    story.append(
        info_table(
            [
                ["Backend", "Python Flask application"],
                ["Frontend", "Server-rendered HTML with custom CSS and vanilla JavaScript"],
                ["AI provider", "OpenRouter chat completion endpoint"],
                ["Model used", "Configurable via environment variable, defaulting to google/gemini-2.0-flash-lite-001"],
                ["Configuration", ".env-based setup using python-dotenv"],
                ["Persistence", "In-memory incident history for prototype speed and simplicity"],
            ]
        )
    )

    story.append(Paragraph("6. Backend Responsibilities", styles["SectionHeading"]))
    story.append(
        bullet_list(
            [
                "Validate incoming requests and required fields.",
                "Send crisis prompts to the AI provider with timeout and response checks.",
                "Normalize model output into a strict JSON shape.",
                "Generate deterministic staff assignments from hotel role and floor data.",
                "Create role-specific tasks, response statuses, ETAs, and availability labels.",
                "Build checklists, timeline events, analytics summaries, and escalation metadata.",
                "Apply escalation changes and support undo by rebuilding the incident state from a base snapshot.",
            ],
            styles,
        )
    )

    story.append(Paragraph("7. Frontend Responsibilities", styles["SectionHeading"]))
    story.append(
        bullet_list(
            [
                "Provide a polished command-center UI for intake, operations, and review.",
                "Render hero incident summary, responder cards, timeline, checklist, actions, analytics, and history.",
                "Handle escalation requests asynchronously without full-page refresh.",
                "Surface severity visually across the page.",
                "Support voice capture through the browser speech-recognition API where available.",
            ],
            styles,
        )
    )

    story.append(Paragraph("8. API Endpoints", styles["SectionHeading"]))
    story.append(
        info_table(
            [
                ["Route", "Purpose"],
                ["/", "Serves the main command-center interface"],
                ["/analyze", "Accepts a crisis report and returns a full incident payload"],
                ["/escalate", "Applies or undoes escalation actions for a given incident"],
                ["/history", "Returns current in-memory incident history"],
                ["/analytics", "Returns aggregated prototype analytics"],
            ]
        )
    )

    story.append(Paragraph("9. Strengths of the Prototype", styles["SectionHeading"]))
    story.append(
        bullet_list(
            [
                "Strong demo value: interactive, visual, and operational rather than purely textual.",
                "Clear product story: emergency command center for hospitality environments.",
                "Good UX direction: voice input, escalation controls, analytics, and timeline make the experience memorable.",
                "Safer architecture than a raw AI demo: core coordination logic is deterministic where correctness matters.",
                "Expandable foundation: the current codebase can evolve into a role-based operational platform.",
            ],
            styles,
        )
    )

    story.append(Paragraph("10. Current Limitations", styles["SectionHeading"]))
    story.append(
        bullet_list(
            [
                "Incident data is stored in memory only and does not persist across server restarts.",
                "There is no authentication, role-based authorization, or database yet.",
                "Staff roster and checklists are hardcoded for prototype speed.",
                "The prototype does not yet support multiple simultaneous users or real-time synchronization across devices.",
                "Escalation logic is simulated and not integrated with external systems such as calling, SMS, CCTV, or property management software.",
                "Voice input depends on browser support for speech recognition APIs.",
            ],
            styles,
        )
    )

    story.append(PageBreak())

    story.append(Paragraph("11. UI and Experience Summary", styles["SectionHeading"]))
    story.append(
        Paragraph(
            "The current interface has been polished into a command-center style dashboard with a top status bar, an incident intake panel, "
            "a hero incident summary, response metrics, escalation cards, dispatch board, timeline, checklist, analytics, and history audit trail. "
            "The visual language uses strong contrast, structured cards, severity-aware styling, and a custom mic control to elevate the prototype beyond a generic CRUD demo.",
            styles["BodyText"],
        )
    )

    story.append(Paragraph("12. Security and Reliability Considerations", styles["SectionHeading"]))
    story.append(
        bullet_list(
            [
                "API credentials are now environment-based rather than hardcoded in application code.",
                "Backend includes response validation and timeout handling around the external AI service.",
                "Model output is not trusted for floor-critical assignment details.",
                "Future versions should include key rotation, audit logs, role permissions, database-backed storage, and request-level authentication.",
            ],
            styles,
        )
    )

    story.append(Paragraph("13. Future Enhancement Roadmap", styles["SectionHeading"]))
    story.append(
        bullet_list(
            [
                "Persistent storage with a proper relational database for incidents, staff, shifts, and checklists.",
                "Authentication and role-based access for managers, supervisors, security, medical staff, reception, housekeeping, and maintenance.",
                "Manager dashboard for shift planning, daily assignments, staff directory, and incident oversight.",
                "Staff portal for personal tasks, shift information, emergency duties, nearby staff contacts, and real-time incident notices.",
                "Live staff location and status updates backed by a real-time service.",
                "Multi-incident handling with resource conflict resolution and dispatch prioritization.",
                "Notification integrations such as SMS, email, call triggers, and push alerts.",
                "Floor-map visualization with responder placement and crisis zone highlighting.",
                "Incident report export and compliance-ready audit summaries.",
                "Integration with property-management systems, access control, fire panels, or CCTV feeds where relevant.",
            ],
            styles,
        )
    )

    story.append(Paragraph("14. Product Vision Beyond the Prototype", styles["SectionHeading"]))
    story.append(
        Paragraph(
            "The long-term direction is not just an AI crisis analyzer. It is a hotel operations and emergency coordination platform. "
            "In that future version, the crisis orchestrator becomes one powerful module inside a broader system used daily by management and staff. "
            "Managers would oversee assignments, staffing, visibility, and incident command. Staff members would log in to view their profile, "
            "daily tasks, emergency responsibilities, contact information, and live operational updates. This product direction makes the solution "
            "more realistic, more defensible, and more valuable than a standalone AI demo.",
            styles["BodyText"],
        )
    )

    story.append(Paragraph("15. Recommended Next Build Priorities", styles["SectionHeading"]))
    story.append(
        bullet_list(
            [
                "Add persistence and authentication first.",
                "Introduce manager and staff role-based interfaces second.",
                "Add real-time updates and floor visualization third.",
                "Expand external integrations and reporting once the operational workflow is stable.",
            ],
            styles,
        )
    )

    story.append(Spacer(1, 0.2 * inch))
    story.append(
        Paragraph(
            "Prepared as a comprehensive project brief for documentation, presentation support, and future planning.",
            styles["SmallMuted"],
        )
    )

    return story


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#66778A"))
    canvas.drawRightString(doc.pagesize[0] - 40, 22, f"Page {doc.page}")
    canvas.restoreState()


def main():
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=36,
        bottomMargin=34,
    )
    doc.build(build_story(), onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"Created {OUTPUT}")


if __name__ == "__main__":
    main()
