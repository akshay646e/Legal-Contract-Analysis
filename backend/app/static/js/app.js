// LexAI Dashboard Client Logic
let activeContractId = null;
let currentContracts = [];

document.addEventListener("DOMContentLoaded", () => {
  initUpload();
  initTabs();
  initChat();
  loadContracts();
  loadStats();
});

// --- Tab Management ---
function initTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

      tab.classList.add("active");
      const target = tab.getAttribute("data-tab");
      const pane = document.getElementById(target);
      if (pane) pane.classList.add("active");
    });
  });
}

// --- Upload & Dropzone ---
function initUpload() {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const progressBox = document.getElementById("uploadProgress");
  const btnRefresh = document.getElementById("btnRefreshList");

  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      handleFileUpload(fileInput.files[0]);
    }
  });

  btnRefresh.addEventListener("click", () => {
    loadContracts();
    loadStats();
  });

  document.getElementById("btnRunPipeline").addEventListener("click", runAnalysisPipeline);
}

async function handleFileUpload(file) {
  const progressBox = document.getElementById("uploadProgress");
  const statusText = document.getElementById("uploadStatusText");
  progressBox.classList.remove("hidden");
  statusText.textContent = `Uploading & parsing ${file.name}...`;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/contracts/upload", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Upload failed");
    }

    const data = await res.json();
    progressBox.classList.add("hidden");
    await loadContracts();
    await loadStats();
    selectContract(data.id);
  } catch (err) {
    alert(`Upload Error: ${err.message}`);
    progressBox.classList.add("hidden");
  }
}

// --- Contract Loading & Selection ---
async function loadContracts() {
  try {
    const res = await fetch("/api/contracts");
    currentContracts = await res.json();
    const listContainer = document.getElementById("contractList");

    if (!currentContracts || currentContracts.length === 0) {
      listContainer.innerHTML = `<div class="empty-state-small">No contracts uploaded yet.</div>`;
      return;
    }

    listContainer.innerHTML = currentContracts.map(c => `
      <div class="contract-item ${c.id === activeContractId ? 'active' : ''}" onclick="selectContract('${c.id}')">
        <div class="contract-item-header">
          <span class="contract-item-title" title="${c.filename}">${c.filename}</span>
          <span class="status-badge status-${c.status.toLowerCase()}">${c.status}</span>
        </div>
        <div class="contract-item-meta">
          <span>${c.file_type.toUpperCase()}</span>
          <span>&bull;</span>
          <span>${(c.file_size_bytes / 1024).toFixed(1)} KB</span>
          <span>&bull;</span>
          <span>${new Date(c.created_at).toLocaleDateString()}</span>
        </div>
      </div>
    `).join("");

    // Auto-select first if none active
    if (!activeContractId && currentContracts.length > 0) {
      selectContract(currentContracts[0].id);
    }
  } catch (err) {
    console.error("Failed to load contracts:", err);
  }
}

async function selectContract(id) {
  activeContractId = id;
  const contract = currentContracts.find(c => c.id === id);

  // Update selection UI highlight
  document.querySelectorAll(".contract-item").forEach(item => {
    item.classList.toggle("active", item.innerHTML.includes(id));
  });

  // Update Ribbon
  const ribbonTitle = document.getElementById("activeContractTitle");
  const ribbonMeta = document.getElementById("activeContractMeta");
  const ribbonActions = document.getElementById("ribbonActions");

  ribbonTitle.textContent = contract ? contract.filename : "Select a contract";
  ribbonMeta.innerHTML = contract ? `
    <span>Status: <strong class="text-green">${contract.status}</strong></span>
    <span>Pages: <strong>${contract.total_pages}</strong></span>
    <span>ID: <code>${contract.id.substring(0, 8)}...</code></span>
  ` : "";
  ribbonActions.style.display = contract ? "block" : "none";

  // Load Contract Content & existing analysis
  loadContractDetails(id);
  loadAnalysisResults(id);
}

async function loadContractDetails(id) {
  try {
    const res = await fetch(`/api/contracts/${id}`);
    const data = await res.json();
    document.getElementById("rawDocumentText").textContent = data.full_text || "No preview text available.";
  } catch (err) {
    console.error("Failed to load contract details:", err);
  }
}

async function loadAnalysisResults(id) {
  try {
    const res = await fetch(`/api/analysis/${id}/results`);
    const data = await res.json();

    if (data.summary) {
      renderSummary(data.summary);
    } else {
      document.getElementById("summaryContent").innerHTML = `
        <div class="empty-tab-state">
          <i class="fa-solid fa-newspaper state-icon"></i>
          <p>Click <strong>"Run AI Analysis"</strong> to generate executive summary and key obligations.</p>
        </div>`;
    }

    if (data.clauses && data.clauses.length > 0) {
      renderClauses(data.clauses);
    } else {
      document.getElementById("clausesContent").innerHTML = `
        <div class="empty-tab-state">
          <i class="fa-solid fa-file-shield state-icon"></i>
          <p>Click <strong>"Run AI Analysis"</strong> to extract key clauses.</p>
        </div>`;
    }

    if (data.risks && data.risks.length > 0) {
      renderRisks(data.risks);
    } else {
      document.getElementById("risksContent").innerHTML = `
        <div class="empty-tab-state">
          <i class="fa-solid fa-shield-halved state-icon"></i>
          <p>Click <strong>"Run AI Analysis"</strong> to perform risk detection and redlining.</p>
        </div>`;
    }
  } catch (err) {
    console.error("Failed to load analysis results:", err);
  }
}

// --- Run Full Analysis Pipeline ---
async function runAnalysisPipeline() {
  if (!activeContractId) return;

  const btn = document.getElementById("btnRunPipeline");
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...`;

  try {
    const res = await fetch(`/api/analysis/${activeContractId}/full-pipeline`, {
      method: "POST"
    });

    if (!res.ok) throw new Error("Analysis failed");

    const data = await res.json();
    renderSummary(data.summary);
    renderClauses(data.clauses);
    renderRisks(data.risks.risks, data.risks.overall_risk_score, data.risks.executive_risk_note);

    await loadContracts();
    await loadStats();
  } catch (err) {
    alert(`Analysis error: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHtml;
  }
}

// --- Renderers ---
function renderSummary(summary) {
  const container = document.getElementById("summaryContent");
  const obligationsHtml = summary.key_obligations && summary.key_obligations.length > 0 ? `
    <table class="obligation-table">
      <thead>
        <tr><th>Party</th><th>Obligation / Covenant</th></tr>
      </thead>
      <tbody>
        ${summary.key_obligations.map(o => `<tr><td><strong>${o.party}</strong></td><td>${o.obligation}</td></tr>`).join("")}
      </tbody>
    </table>
  ` : `<p class="text-dim">No specific obligations cataloged.</p>`;

  container.innerHTML = `
    <div class="summary-container">
      <div class="meta-grid">
        <div class="meta-card">
          <div class="meta-card-label">Contract Type</div>
          <div class="meta-card-val">${summary.contract_type || "Commercial"}</div>
        </div>
        <div class="meta-card">
          <div class="meta-card-label">Effective Date</div>
          <div class="meta-card-val">${summary.effective_date || "Not Specified"}</div>
        </div>
        <div class="meta-card">
          <div class="meta-card-label">Governing Law</div>
          <div class="meta-card-val">${summary.governing_law || "Not Specified"}</div>
        </div>
        <div class="meta-card">
          <div class="meta-card-label">Parties</div>
          <div class="meta-card-val">${summary.parties && summary.parties.length ? summary.parties.join(" & ") : "Identified Parties"}</div>
        </div>
      </div>

      <div class="content-card">
        <h4><i class="fa-solid fa-align-left"></i> Executive Summary</h4>
        <div class="summary-text">${summary.executive_summary.replace(/\n\n/g, '<br><br>')}</div>
      </div>

      <div class="content-card">
        <h4><i class="fa-solid fa-handshake"></i> Key Party Obligations</h4>
        ${obligationsHtml}
      </div>
    </div>
  `;
}

function renderClauses(clauses) {
  const container = document.getElementById("clausesContent");
  container.innerHTML = `
    <div class="clauses-container">
      ${clauses.map(c => `
        <div class="clause-card">
          <div class="clause-card-header">
            <span class="clause-badge">${c.clause_type}</span>
            <span class="text-dim" style="font-size:0.75rem;">Confidence: ${(c.confidence_score * 100).toFixed(0)}%</span>
          </div>
          <div class="clause-quote-box">${c.clause_text}</div>
          <div class="clause-explanation"><strong>Legal Significance:</strong> ${c.explanation || "Governs standard commercial conditions."}</div>
        </div>
      `).join("")}
    </div>
  `;
}

function renderRisks(risks, overallScore = "MEDIUM", note = "") {
  const container = document.getElementById("risksContent");
  const overall = overallScore ? overallScore.toLowerCase() : "med";
  const bannerClass = overall === "high" ? "risk-banner-high" : (overall === "low" ? "risk-banner-low" : "risk-banner-med");

  container.innerHTML = `
    <div class="risks-container">
      <div class="risk-banner ${bannerClass}">
        <i class="fa-solid fa-triangle-exclamation" style="font-size:20px;"></i>
        <div>
          <strong>Overall Contract Risk Posture: ${overallScore}</strong>
          <p style="font-size:0.82rem; margin-top:2px;">${note || 'High financial or legal exposure items require redlining.'}</p>
        </div>
      </div>

      ${risks.map(r => `
        <div class="risk-card risk-level-${r.risk_level.toLowerCase()}">
          <div class="risk-card-header">
            <strong>${r.clause_type}</strong>
            <span class="risk-pill risk-pill-${r.risk_level.toLowerCase()}">${r.risk_level} RISK</span>
          </div>
          <div class="risk-issue-text">${r.issue_description}</div>
          ${r.impact ? `<div class="risk-meta-row"><strong>Business Impact:</strong> ${r.impact}</div>` : ''}
          <div class="risk-meta-row"><strong>Recommendation:</strong> ${r.recommendation}</div>
          ${r.redline_suggestion ? `
            <div class="redline-box">
              <div class="redline-title"><i class="fa-solid fa-pen-nib"></i> Proposed Redline Amendment:</div>
              <div class="redline-content">${r.redline_suggestion}</div>
            </div>
          ` : ''}
        </div>
      `).join("")}
    </div>
  `;
}

// --- RAG Chat Interaction ---
function initChat() {
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const chips = document.querySelectorAll(".prompt-chips .chip");

  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;
    sendMessage(query);
    chatInput.value = "";
  });

  chips.forEach(chip => {
    chip.addEventListener("click", () => {
      const prompt = chip.getAttribute("data-prompt");
      sendMessage(prompt);
    });
  });
}

async function sendMessage(text) {
  if (!activeContractId) {
    alert("Please select or upload a contract first.");
    return;
  }

  const messagesContainer = document.getElementById("chatMessages");

  // Append User message bubble
  appendBubble("user", text);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  // Append Thinking placeholder
  const thinkingId = "thinking-" + Date.now();
  appendThinkingBubble(thinkingId);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contract_id: activeContractId,
        message: text,
        include_citations: true
      })
    });

    if (!res.ok) throw new Error("Chat request failed");
    const data = await res.json();

    // Remove thinking bubble and append Bot response
    document.getElementById(thinkingId)?.remove();
    appendBubble("bot", data.reply, data.citations);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  } catch (err) {
    document.getElementById(thinkingId)?.remove();
    appendBubble("bot", `Error answering query: ${err.message}`);
  }
}

function appendBubble(sender, text, citations = []) {
  const container = document.getElementById("chatMessages");
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${sender}-bubble`;

  const citationsHtml = citations && citations.length > 0 ? `
    <div class="citations-container">
      <div class="citations-label"><i class="fa-solid fa-quote-left"></i> Verified Ground Truth Citations:</div>
      ${citations.map(c => `
        <div class="citation-pill">
          <div class="citation-header">${c.section_title || 'Section Excerpt'} ${c.section_number ? `(${c.section_number})` : ''}</div>
          <div class="citation-quote">"${c.verbatim_quote}"</div>
        </div>
      `).join("")}
    </div>
  ` : '';

  bubble.innerHTML = `
    <div class="bubble-avatar"><i class="fa-solid ${sender === 'user' ? 'fa-user' : 'fa-robot'}"></i></div>
    <div class="bubble-content">
      <p>${text}</p>
      ${citationsHtml}
    </div>
  `;
  container.appendChild(bubble);
}

function appendThinkingBubble(id) {
  const container = document.getElementById("chatMessages");
  const bubble = document.createElement("div");
  bubble.id = id;
  bubble.className = "chat-bubble bot-bubble";
  bubble.innerHTML = `
    <div class="bubble-avatar"><i class="fa-solid fa-robot"></i></div>
    <div class="bubble-content">
      <div class="spinner"></div>
    </div>
  `;
  container.appendChild(bubble);
}

// --- Stats Loading ---
async function loadStats() {
  try {
    const res = await fetch("/api/contracts/stats/overview");
    const stats = await res.json();
    document.getElementById("statTotalContracts").textContent = stats.total_contracts;
    document.getElementById("statAnalyzedContracts").textContent = stats.analyzed_contracts;
    document.getElementById("statHighRisks").textContent = stats.high_risks_detected;
  } catch (err) {
    console.error("Failed to load stats:", err);
  }
}
