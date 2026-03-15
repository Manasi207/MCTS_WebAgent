// popup.js
const API_URL = "http://localhost:8000";

// ─────────────────────────────────────────────
// State
// ─────────────────────────────────────────────
let selectedVariant   = "basic-mcts";
let attachmentData    = null;   // base64 string
let attachmentName    = null;   // filename

const VARIANT_INFO = {
  "basic-mcts": {
    desc:  "Standard MCTS — UCB1 selection, random rollout, heuristic scoring. Baseline variant — no retrieval or LLM.",
    color: "#f7c94f",
  },
  "r-mcts": {
    desc:  "Retrieval MCTS — live web retrieval per node during expansion. Action selection grounded in freshly fetched content.",
    color: "#4f8ef7",
  },
  "wm-mcts": {
    desc:  "World-Model MCTS — LLM predicts action quality before expansion. Most accurate variant.",
    color: "#7c5cfc",
  },
  "rag-mcts": {
    desc:  "MCTS-RAG — retrieves live context once before search starts. Context-aware planning.",
    color: "#00d4aa",
  },
};

const VARIANT_CSS = {
  "Basic-MCTS": "basic-mcts",
  "R-MCTS":     "r-mcts",
  "WM-MCTS":    "wm-mcts",
  "MCTS-RAG":   "rag-mcts",
};

const VARIANT_NAME_CSS = {
  "Basic-MCTS": "v-basic",
  "R-MCTS":     "v-r",
  "WM-MCTS":    "v-wm",
  "MCTS-RAG":   "v-rag",
};

// ─────────────────────────────────────────────
// Variant pills
// ─────────────────────────────────────────────
document.querySelectorAll(".variant-pill").forEach((pill) => {
  pill.addEventListener("click", () => {
    document.querySelectorAll(".variant-pill").forEach((p) => p.classList.remove("active"));
    pill.classList.add("active");
    selectedVariant = pill.dataset.variant;
    const info   = VARIANT_INFO[selectedVariant];
    const descEl = document.getElementById("variant-desc");
    descEl.textContent           = info.desc;
    descEl.style.borderLeftColor = info.color;
  });
});

// ─────────────────────────────────────────────
// Simulations slider
// ─────────────────────────────────────────────
const simSlider  = document.getElementById("simulations");
const simDisplay = document.getElementById("sim-display");
simSlider.addEventListener("input", () => { simDisplay.textContent = simSlider.value; });

// ─────────────────────────────────────────────
// File attachment handler
// ─────────────────────────────────────────────
const attachInput    = document.getElementById("attachment-input");
const fileInfoDiv    = document.getElementById("file-selected-info");
const fileNameSpan   = document.getElementById("file-selected-name");
const fileClearBtn   = document.getElementById("file-clear-btn");
const uploadPrompt   = document.getElementById("upload-prompt");

if (attachInput) {
  attachInput.addEventListener("change", () => {
    const file = attachInput.files[0];
    if (!file) return;

    // Size guard — 10 MB max (base64 stays under FastAPI default 16MB limit)
    if (file.size > 10 * 1024 * 1024) {
      alert("File too large. Maximum attachment size is 10 MB.");
      attachInput.value = "";
      return;
    }

    attachmentName = file.name;

    const reader = new FileReader();
    reader.onload = (e) => {
      // e.target.result is "data:<mime>;base64,<data>" — strip the prefix
      const base64Full = e.target.result;
      attachmentData   = base64Full.split(",")[1];

      // Update UI
      fileNameSpan.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      fileInfoDiv.classList.add("visible");
      uploadPrompt.textContent = "File attached";
    };
    reader.readAsDataURL(file);
  });

  fileClearBtn.addEventListener("click", () => {
    attachmentData = null;
    attachmentName = null;
    attachInput.value = "";
    fileInfoDiv.classList.remove("visible");
    uploadPrompt.textContent = "Click to attach a file (PDF, image, doc, zip...)";
  });
}

// ─────────────────────────────────────────────
// Action selector
// ─────────────────────────────────────────────
document.getElementById("action-type").addEventListener("change", (e) => {
  document.querySelectorAll(".action-section").forEach((s) => s.classList.remove("active"));
  const map = {
    "chat":        "chat-section",
    "scrape-data": "scrape-data-section",
    "send-email":  "send-email-section",
    "fetch-email": "fetch-email-section",
  };
  const sid = map[e.target.value];
  if (sid) document.getElementById(sid).classList.add("active");
  hideResultPanel();
});

// ─────────────────────────────────────────────
// Result panel tabs
// ─────────────────────────────────────────────
document.querySelectorAll(".result-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".result-tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".result-pane").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(`pane-${tab.dataset.tab}`).classList.add("active");
  });
});

function showResultPanel(tab = "output") {
  document.getElementById("result-panel").style.display = "block";
  document.querySelectorAll(".result-tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.tab === tab);
  });
  document.querySelectorAll(".result-pane").forEach((p) => {
    p.classList.toggle("active", p.id === `pane-${tab}`);
  });
}

function hideResultPanel() {
  document.getElementById("result-panel").style.display = "none";
}

// ─────────────────────────────────────────────
// Connection check
// ─────────────────────────────────────────────
async function checkConnection() {
  const el = document.getElementById("status");
  try {
    const res = await fetch(`${API_URL}/health`);
    if (res.ok) {
      el.textContent = "Connected";
      el.className   = "status-badge connected";
    } else {
      el.textContent = "Backend Error";
      el.className   = "status-badge disconnected";
    }
  } catch {
    el.textContent = "Offline";
    el.className   = "status-badge disconnected";
  }
}
checkConnection();
setInterval(checkConnection, 10000);

// ─────────────────────────────────────────────
// Execute button
// ─────────────────────────────────────────────
document.getElementById("execute-btn").addEventListener("click", async () => {
  const actionType = document.getElementById("action-type").value;
  const resultDiv  = document.getElementById("result");
  const execBtn    = document.getElementById("execute-btn");
  const analBtn    = document.getElementById("analyse-btn");

  execBtn.disabled    = true;
  execBtn.textContent = "Processing...";
  analBtn.disabled    = true;

  resultDiv.textContent = "Working...";
  showResultPanel("output");

  try {
    if      (actionType === "chat")        await handleChatQuery(resultDiv);
    else if (actionType === "scrape-data") await handleScrapeData(resultDiv);
    else if (actionType === "send-email")  await handleSendEmail(resultDiv);
    else if (actionType === "fetch-email") await handleFetchEmails(resultDiv);
  } catch (err) {
    resultDiv.textContent = `Error: ${err.message}`;
  } finally {
    execBtn.disabled    = false;
    execBtn.textContent = "Execute";
    analBtn.disabled    = false;
  }
});

// ─────────────────────────────────────────────
// Analyse button — runs all 4 variants on the
// current query, then shows a full analysis table
// with Speed, Plan Quality Score, TSR Accuracy,
// Step Efficiency, and Improvement vs Baseline.
//
// Accuracy metric: Task Success Rate (TSR)
//   TSR (%) = (plan_score / 10.0) × 100
//   Standard metric used in AgentBench / WebArena /
//   ALFWorld agentic task evaluation benchmarks.
// ─────────────────────────────────────────────
document.getElementById("analyse-btn").addEventListener("click", async () => {
  const task = document.getElementById("task").value.trim();
  if (!task) {
    alert("Please enter a query in the chat box first, then click Analyse.");
    return;
  }

  const analBtn  = document.getElementById("analyse-btn");
  const execBtn  = document.getElementById("execute-btn");
  const analDiv  = document.getElementById("analysis-result");

  analBtn.disabled    = true;
  analBtn.textContent = "Analysing...";
  execBtn.disabled    = true;

  analDiv.innerHTML = `<div style="color:var(--text-muted);font-family:'JetBrains Mono',monospace;font-size:11px;padding:10px;">Running all 4 MCTS variants on your query...</div>`;
  showResultPanel("analysis");

  try {
    const sims = parseInt(simSlider.value);
    const res  = await fetch(`${API_URL}/mcts/benchmark`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ query: task, simulations: sims }),
    });
    const data = await res.json();
    renderAnalysisTable(data, analDiv);
  } catch (err) {
    analDiv.innerHTML = `<div style="color:var(--danger);font-size:11px;">Analysis failed: ${err.message}</div>`;
  } finally {
    analBtn.disabled    = false;
    analBtn.textContent = "Analyse All 4";
    execBtn.disabled    = false;
  }
});

// ─────────────────────────────────────────────
// Render Analysis Table
// ─────────────────────────────────────────────
function getCSSClass(name) { return VARIANT_CSS[name]      || "basic-mcts"; }
function getNameCSS(name)  { return VARIANT_NAME_CSS[name] || "v-basic"; }

function renderAnalysisTable(data, container) {
  const results  = data.results  || [];
  const summary  = data.summary  || {};
  const metaInfo = data.metric_info || {};

  if (!results.length) {
    container.innerHTML = `<div style="color:var(--danger)">No results returned.</div>`;
    return;
  }

  const maxTime = Math.max(...results.map(r => r.time_ms || 0), 1);
  const maxTSR  = Math.max(...results.map(r => r.tsr_accuracy || 0), 1);

  // ── Metric explanation box ───────────────────────────────────
  let html = `
  <div class="analysis-meta">
    <b style="color:var(--accent)">Accuracy Formula:</b> TSR (%) = (Plan Score / 10) × 100 &nbsp;|&nbsp;
    <b style="color:var(--accent)">Standard:</b> AgentBench / WebArena Task Success Rate<br>
    <b style="color:var(--accent)">Step Efficiency:</b> Score per planning step &nbsp;|&nbsp;
    <b style="color:var(--accent)">Baseline:</b> Basic-MCTS (TSR = ${summary.baseline_tsr ?? "—"}%)
  </div>`;

  // ── Main analysis table ──────────────────────────────────────
  html += `
  <table class="analysis-table">
    <thead>
      <tr>
        <th>Rank</th>
        <th>Variant</th>
        <th>Speed (ms)</th>
        <th>PQS /10</th>
        <th>TSR Accuracy</th>
        <th>Step Eff.</th>
        <th>vs Baseline</th>
        <th>Steps</th>
      </tr>
    </thead>
    <tbody>`;

  results.forEach((r) => {
    const css      = getCSSClass(r.variant);
    const nameCss  = getNameCSS(r.variant);
    const rank     = r.rank || 4;

    // Speed colour: fastest = green, slowest = red
    const isFastest = r.variant === summary.fastest;
    const isSlowest = r.time_ms === Math.max(...results.map(x => x.time_ms || 0));
    const speedCss  = isFastest ? "speed-fast" : isSlowest ? "speed-slow" : "";

    // TSR bar
    const tsrPct = ((r.tsr_accuracy || 0) / maxTSR * 100).toFixed(0);

    // Improvement pill
    let impHtml = `<span class="imp-pill imp-base">Baseline</span>`;
    if (r.variant !== "Basic-MCTS" && r.improvement_vs_baseline != null) {
      const v   = r.improvement_vs_baseline;
      const cls = v >= 0 ? "imp-pos" : "imp-neg";
      impHtml   = `<span class="imp-pill ${cls}">${v >= 0 ? "+" : ""}${v}%</span>`;
    }

    // Plan steps (short)
    const planSteps = (r.plan || []).length > 0
      ? r.plan.map(s => `<span>${s}</span>`).join(" ")
      : `<span style="color:var(--text-muted)">—</span>`;

    html += `
    <tr>
      <td><span class="rank-badge rank-${rank}">${rank}</span></td>
      <td><span class="${nameCss}">${r.variant}</span></td>
      <td class="speed-cell ${speedCss}">${(r.time_ms || 0).toFixed(0)}ms</td>
      <td>${r.plan_score != null ? r.plan_score.toFixed(1) : "—"}</td>
      <td class="tsr-cell">
        <div class="tsr-bar-wrap">
          <div class="tsr-bar-track">
            <div class="tsr-bar-fill ${css}" style="width:${tsrPct}%"></div>
          </div>
          <span class="tsr-val">${r.tsr_accuracy != null ? r.tsr_accuracy : "—"}%</span>
        </div>
      </td>
      <td>${r.step_efficiency != null ? r.step_efficiency.toFixed(2) : "—"}</td>
      <td>${impHtml}</td>
      <td class="plan-steps">${planSteps}</td>
    </tr>`;
  });

  html += `</tbody></table>`;

  // ── Summary row ──────────────────────────────────────────────
  html += `
  <div class="analysis-summary">
    <b>Fastest:</b> ${summary.fastest || "N/A"} &nbsp;
    <b>Most Accurate (TSR):</b> ${summary.most_accurate || "N/A"} &nbsp;
    <b>Most Efficient:</b> ${summary.most_efficient || "N/A"} &nbsp;
    <b>Best Overall:</b> ${summary.best_overall || "N/A"}
  </div>`;

  container.innerHTML = html;
}

// ─────────────────────────────────────────────
// Action handlers (existing logic preserved)
// ─────────────────────────────────────────────
async function handleChatQuery(resultDiv) {
  const task = document.getElementById("task").value.trim();
  if (!task) { resultDiv.textContent = "Please enter a query"; return; }

  resultDiv.textContent = `Processing with ${selectedVariant.toUpperCase()}...`;

  const sims = parseInt(simSlider.value);
  const res  = await fetch(`${API_URL}/ask`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ query: task, variant: selectedVariant, simulations: sims }),
  });

  const data = await res.json();

  let output = "";
  if (data.mcts_variant)         output += `[${data.mcts_variant}] `;
  if (data.mcts_score != null)   output += `Score: ${data.mcts_score}/10 | `;
  if (data.mcts_time_ms != null) output += `Time: ${data.mcts_time_ms.toFixed(0)}ms\n\n`;
  if (data.plan && data.plan.length > 0 && data.plan[0] !== "Direct LLM Response") {
    output += `Plan: ${data.plan.join(" → ")}\n\n`;
  }
  output += data.answer || JSON.stringify(data);
  resultDiv.textContent = output;
}

async function handleScrapeData(resultDiv) {
  const url = document.getElementById("scrape-url").value.trim();
  if (!url) { resultDiv.textContent = "Please enter a URL"; return; }
  resultDiv.textContent = "Scraping...";
  const res  = await fetch(`${API_URL}/ask`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ query: `scrape ${url}` }),
  });
  const data = await res.json();
  resultDiv.textContent = data.answer || JSON.stringify(data);
}

async function handleSendEmail(resultDiv) {
  const recipient = document.getElementById("recipient").value.trim();
  const subject   = document.getElementById("subject").value.trim();
  const body      = document.getElementById("body").value.trim();

  if (!recipient || !subject) {
    resultDiv.textContent = "Recipient and subject are required";
    return;
  }

  const statusMsg = attachmentName
    ? `Sending email with attachment: ${attachmentName}...`
    : "Sending email...";
  resultDiv.textContent = statusMsg;

  const payload = {
    recipient,
    subject,
    body,
    attachment_data: attachmentData || null,
    attachment_name: attachmentName || null,
  };

  const res  = await fetch(`${API_URL}/send-email`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(payload),
  });
  const data = await res.json();
  resultDiv.textContent = data.message;

  // Clear attachment after successful send
  if (data.message && data.message.includes("sent successfully✅")) {
    attachmentData = null;
    attachmentName = null;
    if (attachInput)   attachInput.value = "";
    if (fileInfoDiv)   fileInfoDiv.classList.remove("visible");
    if (uploadPrompt)  uploadPrompt.textContent = "Click to attach a file (PDF, image, doc, zip...)";
  }
}

async function handleFetchEmails(resultDiv) {
  resultDiv.textContent = "Fetching emails...";
  const res  = await fetch(`${API_URL}/fetch-emails`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
  });
  const data = await res.json();
  resultDiv.textContent = data.message;
}
/////////////////////////////////////////////////////////////////////////////////////////////////////////
