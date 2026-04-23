let currentIncident = null;
let recognition = null;
let historyCache = [];

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

async function analyzeCrisis() {
  const crisis = document.getElementById("crisis-input").value.trim();
  const floor = document.getElementById("floor-select").value;

  if (!crisis) {
    alert("Please describe the crisis first.");
    return;
  }

  const btn = document.getElementById("analyze-btn");
  const loading = document.getElementById("loading");
  const dashboard = document.getElementById("dashboard");

  btn.disabled = true;
  loading.classList.remove("hidden");
  dashboard.classList.add("hidden");

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ crisis, floor })
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Unable to analyze the crisis right now.");
    }

    currentIncident = data;
    renderIncident(data);
    dashboard.classList.remove("hidden");
    showBanner(data.severity, data.response_mode);
    loadHistory();
  } catch (error) {
    alert(error.message || "Something went wrong. Check console for details.");
    console.error(error);
  } finally {
    btn.disabled = false;
    loading.classList.add("hidden");
  }
}

function renderIncident(data) {
  document.body.setAttribute("data-severity", data.severity.toLowerCase());
  document.getElementById("crisis-type").textContent = data.crisis_type;
  document.getElementById("summary").textContent = data.summary;
  document.getElementById("incident-location").textContent = data.location;
  document.getElementById("updated-at").textContent = data.updated_at;
  document.getElementById("incident-id").textContent = `Incident #${data.incident_id}`;
  document.getElementById("incident-mode").textContent = data.response_mode;
  document.getElementById("incident-mode").className = `chip ${data.response_source === "ai" ? "chip-on-site" : "chip-busy"}`;

  const severityEl = document.getElementById("severity");
  severityEl.textContent = data.severity;
  severityEl.className = `meta-value severity-${data.severity.toLowerCase()}`;

  renderAssignments(data.assignments);
  renderImmediateActions(data.immediate_actions, data.summary);
  renderTimeline(data.timeline);
  renderChecklist(data.checklist);
  renderEscalationActions(data.available_actions, data.resolved);
  renderFloorOverview(data.floor_overview);
  renderAnalytics(data.analytics);
}

function renderAssignments(assignments) {
  const assignmentsDiv = document.getElementById("assignments");
  assignmentsDiv.innerHTML = "";

  assignments.forEach(person => {
    const availabilityClass = person.availability.toLowerCase().replace(/\s+/g, "-");
    const card = document.createElement("div");
    card.className = "assignment-card";
    card.innerHTML = `
      <div class="assignment-top">
        <div class="assignment-name">${escapeHtml(person.name)} <span class="floor-badge">Floor ${escapeHtml(person.floor)}</span></div>
        <span class="chip chip-${availabilityClass}">${escapeHtml(person.availability)}</span>
      </div>
      <div class="assignment-role">${escapeHtml(person.role)} | ${escapeHtml(person.status)}</div>
      <div class="assignment-meta">Response distance: ${escapeHtml(person.distance)} floor(s) | ETA: ${escapeHtml(person.eta)}</div>
      <div class="assignment-task">Task: ${escapeHtml(person.task)}</div>
    `;
    assignmentsDiv.appendChild(card);
  });
}

function renderImmediateActions(actions, summary) {
  document.getElementById("summary").textContent = summary;
  const actionsList = document.getElementById("actions");
  actionsList.innerHTML = "";

  actions.forEach(action => {
    const li = document.createElement("li");
    li.textContent = action;
    actionsList.appendChild(li);
  });
}

function renderTimeline(events) {
  const list = document.getElementById("timeline-list");
  list.innerHTML = "";

  events.forEach((event, index) => {
    const item = document.createElement("div");
    item.className = `timeline-item ${index === events.length - 1 ? "timeline-item-latest" : ""}`;
    item.innerHTML = `
      <span class="timeline-time">${escapeHtml(event.time)}</span>
      <div class="timeline-content">
        <div class="timeline-title">${escapeHtml(event.title)}</div>
        <div class="timeline-detail">${escapeHtml(event.detail)}</div>
      </div>
    `;
    list.appendChild(item);
  });
}

function renderChecklist(items) {
  const list = document.getElementById("checklist-list");
  list.innerHTML = "";

  items.forEach(item => {
    const row = document.createElement("label");
    row.className = `checklist-item ${item.completed ? "completed" : ""}`;
    row.innerHTML = `
      <input type="checkbox" ${item.completed ? "checked" : ""} disabled />
      <span>${escapeHtml(item.label)}</span>
    `;
    list.appendChild(row);
  });
}

function renderEscalationActions(actions, resolved) {
  const container = document.getElementById("escalation-actions");
  container.innerHTML = "";

  actions.forEach(action => {
    const card = document.createElement("div");
    card.className = `action-card ${action.active ? "action-card-active" : ""}`;

    const applyBtnDisabled = action.active || (resolved && action.key !== "all_clear");
    card.innerHTML = `
      <div class="action-card-head">
        <span class="action-title">${escapeHtml(action.label)}</span>
        <span class="chip ${action.active ? "chip-busy" : "chip-neutral"}">${action.active ? "Active" : "Ready"}</span>
      </div>
      <p class="action-description">${escapeHtml(action.description)}</p>
      <div class="action-card-buttons">
        <button type="button" class="escalation-btn" ${applyBtnDisabled ? "disabled" : ""}>${action.active ? "Locked" : "Apply"}</button>
        <button type="button" class="ghost-btn undo-btn" ${action.active ? "" : "disabled"}>Undo</button>
      </div>
    `;

    const [applyBtn, undoBtn] = card.querySelectorAll("button");
    if (!applyBtnDisabled) {
      applyBtn.addEventListener("click", () => triggerEscalation(action.key, "apply"));
    }
    if (action.active) {
      undoBtn.addEventListener("click", () => triggerEscalation(action.key, "undo"));
    }

    container.appendChild(card);
  });
}

function renderFloorOverview(floors) {
  const container = document.getElementById("floor-overview");
  container.innerHTML = "";

  floors.forEach(level => {
    const row = document.createElement("div");
    row.className = `floor-row ${level.is_incident_floor ? "floor-row-incident" : ""}`;

    const respondersMarkup = level.responders.length
      ? level.responders.map(responder => {
          const availabilityClass = responder.availability.toLowerCase().replace(/\s+/g, "-");
          return `<span class="floor-responder chip chip-${availabilityClass}">${escapeHtml(responder.name)}</span>`;
        }).join("")
      : '<span class="floor-empty">No assigned staff on this floor</span>';

    row.innerHTML = `
      <div class="floor-label-wrap">
        <span class="floor-name">Floor ${escapeHtml(level.floor)}</span>
        ${level.is_incident_floor ? '<span class="floor-incident-badge">Incident Zone</span>' : ""}
      </div>
      <div class="floor-track">
        <div class="floor-metrics">
          <span>${escapeHtml(level.responder_count)} staff linked</span>
          <span>${escapeHtml(level.active_count)} active responders</span>
        </div>
        <div class="floor-responders">${respondersMarkup}</div>
      </div>
    `;
    container.appendChild(row);
  });
}

async function triggerEscalation(action, mode = "apply") {
  if (!currentIncident) {
    return;
  }

  try {
    const response = await fetch("/escalate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        incident_id: currentIncident.incident_id,
        action,
        mode
      })
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Unable to run escalation.");
    }

    currentIncident = data;
    renderIncident(data);
    showBanner(data.severity, data.response_mode);
    loadHistory();
  } catch (error) {
    alert(error.message || "Unable to run escalation.");
    console.error(error);
  }
}

function renderAnalytics(analytics) {
  document.getElementById("total-incidents").textContent = analytics.totals.incidents;
  document.getElementById("active-incidents").textContent = analytics.totals.active_incidents;
  document.getElementById("high-severity-count").textContent = analytics.totals.high_severity;
  document.getElementById("avg-distance").textContent = analytics.totals.avg_response_distance;
  document.getElementById("common-type").textContent = analytics.most_common_type;
  document.getElementById("response-trend").textContent = analytics.response_trend;

  const utilizationList = document.getElementById("utilization-list");
  utilizationList.innerHTML = "";

  if (!analytics.staff_utilization.length) {
    utilizationList.innerHTML = '<span class="utilization-empty">No active staff utilization yet.</span>';
    return;
  }

  analytics.staff_utilization.forEach(member => {
    const chip = document.createElement("span");
    chip.className = "chip chip-neutral";
    chip.textContent = `${member.name}: ${member.count}`;
    utilizationList.appendChild(chip);
  });
}

function showBanner(severity, responseMode) {
  const banner = document.getElementById("alert-banner");
  const text = document.getElementById("banner-text");

  banner.className = "";
  banner.classList.add("banner-" + severity.toLowerCase());
  text.textContent = `ACTIVE CRISIS - Severity: ${severity.toUpperCase()} - ${responseMode.toUpperCase()}`;
  banner.classList.remove("hidden");
}

async function loadHistory() {
  const res = await fetch("/history");
  const history = await res.json();
  historyCache = history;
  const list = document.getElementById("history-list");

  if (history.length === 0) {
    list.innerHTML = '<p class="no-history">No crises recorded yet.</p>';
    return;
  }

  list.innerHTML = "";
  [...history].reverse().forEach(item => {
    const card = document.createElement("div");
    card.className = "history-card";
    card.addEventListener("click", () => openHistoryModal(item.incident_id));
    card.innerHTML = `
      <div class="history-left">
        <div class="history-type">${escapeHtml(item.crisis_type)} <span class="chip chip-neutral">#${escapeHtml(item.incident_id)}</span></div>
        <div class="history-summary">${escapeHtml(item.summary)}</div>
        <div class="history-summary">Mode: ${escapeHtml(item.response_mode)} | Timeline events: ${escapeHtml(item.timeline.length)}</div>
      </div>
      <div class="history-right">
        <div class="history-time">${escapeHtml(item.timestamp)}</div>
        <div class="history-floor">${escapeHtml(item.location)}</div>
        <div class="card-value severity-${escapeHtml(item.severity.toLowerCase())}" style="font-size:13px">${escapeHtml(item.severity)}</div>
      </div>
    `;
    list.appendChild(card);
  });

  loadAnalytics();
}

async function loadAnalytics() {
  const response = await fetch("/analytics");
  const analytics = await response.json();
  renderAnalytics(analytics);
}

function initVoiceInput() {
  const voiceBtn = document.getElementById("voice-btn");
  const voiceStatus = document.getElementById("voice-status");
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    voiceBtn.disabled = true;
    voiceStatus.textContent = "Voice input not supported in this browser";
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    voiceStatus.textContent = "Listening for crisis details...";
    voiceBtn.classList.add("voice-btn-live");
  };

  recognition.onresult = event => {
    const transcript = event.results[0][0].transcript;
    const input = document.getElementById("crisis-input");
    input.value = input.value ? `${input.value} ${transcript}` : transcript;
    voiceStatus.textContent = "Voice note captured";
  };

  recognition.onerror = () => {
    voiceStatus.textContent = "Voice input failed. Try again.";
    voiceBtn.classList.remove("voice-btn-live");
  };

  recognition.onend = () => {
    voiceBtn.classList.remove("voice-btn-live");
  };

  voiceBtn.addEventListener("click", () => recognition.start());
}

function initQuickPrompts() {
  document.querySelectorAll(".prompt-chip").forEach(button => {
    button.addEventListener("click", () => {
      document.getElementById("crisis-input").value = button.dataset.prompt;
    });
  });
}

initVoiceInput();
initQuickPrompts();
loadHistory();
loadAnalytics();

function openHistoryModal(incidentId) {
  const incident = historyCache.find(i => i.incident_id === incidentId);
  if (!incident) return;

  document.getElementById("modal-crisis-type").textContent = incident.crisis_type;
  document.getElementById("modal-summary").textContent = incident.summary;
  document.getElementById("modal-location").textContent = incident.location;
  document.getElementById("modal-time").textContent = incident.timestamp;
  document.getElementById("modal-incident-id").textContent = `Incident #${incident.incident_id}`;
  document.getElementById("modal-mode").textContent = incident.response_mode;
  document.getElementById("modal-mode").className = `chip ${incident.response_source === "ai" ? "chip-on-site" : "chip-busy"}`;
  
  const statusEl = document.getElementById("modal-status");
  statusEl.textContent = incident.resolved ? "Resolved" : "Active";
  statusEl.className = `chip ${incident.resolved ? "chip-available" : "chip-responding"}`;

  const sev = document.getElementById("modal-severity");
  sev.textContent = incident.severity;
  sev.className = `chip severity-${incident.severity.toLowerCase()}`;

  // Timeline
  const tlList = document.getElementById("modal-timeline-list");
  tlList.innerHTML = "";
  incident.timeline.forEach((event, index) => {
    const item = document.createElement("div");
    item.className = `timeline-item ${index === incident.timeline.length - 1 ? "timeline-item-latest" : ""}`;
    item.innerHTML = `
      <span class="timeline-time">${escapeHtml(event.time)}</span>
      <div class="timeline-content">
        <div class="timeline-title">${escapeHtml(event.title)}</div>
        <div class="timeline-detail">${escapeHtml(event.detail)}</div>
      </div>
    `;
    tlList.appendChild(item);
  });

  // Checklist
  const ckList = document.getElementById("modal-checklist-list");
  ckList.innerHTML = "";
  incident.checklist.forEach(item => {
    const row = document.createElement("label");
    row.className = `checklist-item ${item.completed ? "completed" : ""}`;
    row.innerHTML = `
      <input type="checkbox" ${item.completed ? "checked" : ""} disabled />
      <span>${escapeHtml(item.label)}</span>
    `;
    ckList.appendChild(row);
  });

  // Assignments
  const asList = document.getElementById("modal-assignments");
  asList.innerHTML = "";
  incident.assignments.forEach(person => {
    const availabilityClass = person.availability.toLowerCase().replace(/\s+/g, "-");
    const card = document.createElement("div");
    card.className = "assignment-card";
    card.innerHTML = `
      <div class="assignment-top">
        <div class="assignment-name">${escapeHtml(person.name)} <span class="floor-badge">Floor ${escapeHtml(person.floor)}</span></div>
        <span class="chip chip-${availabilityClass}">${escapeHtml(person.availability)}</span>
      </div>
      <div class="assignment-role">${escapeHtml(person.role)} | ${escapeHtml(person.status)}</div>
      <div class="assignment-task" style="margin-top: 10px;">Task: ${escapeHtml(person.task)}</div>
    `;
    asList.appendChild(card);
  });

  const modal = document.getElementById("history-modal");
  modal.classList.remove("hidden");
  
  document.getElementById("close-modal-btn").onclick = closeHistoryModal;
  modal.addEventListener("click", (e) => {
    if(e.target === modal) closeHistoryModal();
  });
}

function closeHistoryModal() {
  document.getElementById("history-modal").classList.add("hidden");
}
