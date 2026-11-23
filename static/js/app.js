/**
 * static/js/app.js — Orchestrator Utama Whenyhh.ai Cockpit
 *
 * Alur utama:
 * 1. Cek T&C gate (localStorage). Jika belum setuju, tampilkan modal T&C.
 * 2. Load daftar skenario dari API; isi sidebar #scenario-list.
 * 3. Saat skenario dipilih: load graph DAG, render DagView + RelationView.
 * 4. Saat simpul di-klik: tampilkan detail + pilihan aksi di pane tengah.
 * 5. Submit aksi -> POST /api/turns -> update semua panel.
 * 6. Tombol fork -> POST /api/branches/fork -> refresh DAG.
 * 7. Modal konfigurasi LLM: simpan ke sessionStorage.
 *
 * Anti-AI-Slop guardrails:
 * - Tidak ada emoji fungsional (hanya Lucide outline di ikon).
 * - Tidak ada em-dash di copy UI; gunakan tanda baca BI biasa.
 * - prefers-reduced-motion dihormati (animasi dinonaktifkan jika disetel).
 * - Semua teks naratif di-sanitasi dengan DOMPurify sebelum innerHTML.
 */

import { Api } from "./api.js";
import { DagView } from "./dag_view.js";
import { RelationView } from "./relation_view.js";
import { TelemetryView } from "./telemetry.js";

// ── Konstanta ─────────────────────────────────────────────────
const TNC_ACCEPTED_KEY = "whenyhh_tnc_accepted_v1";
const BRANCH_COLORS = [
  "#1F9D8B", "#2E7DD1", "#8B5CF6", "#D97706",
  "#DC2626", "#059669", "#7C3AED", "#0EA5E9",
];

// ── State UI ──────────────────────────────────────────────────
let currentScenario = null;   // { scenario_id, name, ... }
let currentBranch = null;     // { branch_id, name, head_node_id, color }
let currentNode = null;       // data dari dag:nodeSelected
let scenarioGraph = null;     // { nodes, edges, branches }

// ── View instances ────────────────────────────────────────────
const dagView = new DagView("dag-container");
const relationView = new RelationView("relation-container");
const telemetryView = new TelemetryView("telemetry-container");

// ── Inisialisasi ──────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  // Render ikon Lucide
  if (window.lucide) lucide.createIcons();

  // T&C Gate
  if (!localStorage.getItem(TNC_ACCEPTED_KEY)) {
    showTncModal();
  } else {
    bootApp();
  }
});

function bootApp() {
  dagView.init();
  relationView.init();
  loadScenarioList();
  setupEventListeners();
}

// ── T&C Modal ────────────────────────────────────────────────

function showTncModal() {
  const modal = document.getElementById("tnc-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  document.getElementById("tnc-accept-btn")?.addEventListener("click", () => {
    localStorage.setItem(TNC_ACCEPTED_KEY, "1");
    modal.classList.add("hidden");
    bootApp();
  });
}

// ── Skenario ──────────────────────────────────────────────────

async function loadScenarioList() {
  const list = document.getElementById("scenario-list");
  if (!list) return;
  list.innerHTML = `<li class="text-muted text-sm px-2 py-1">Memuat...</li>`;

  const result = await Api.listScenarios();
  if (!result.ok) {
    list.innerHTML = `<li class="text-danger text-sm px-2 py-1">Gagal memuat skenario.</li>`;
    return;
  }

  const scenarios = result.data.scenarios || [];
  list.innerHTML = "";
  scenarios.forEach((s) => {
    const li = document.createElement("li");
    li.className = "scenario-item cursor-pointer px-3 py-2 rounded hover-highlight text-sm";
    li.textContent = s.name || s.scenario_id;
    li.dataset.id = s.scenario_id;
    li.addEventListener("click", () => selectScenario(s));
    list.appendChild(li);
  });

  // Pilih skenario pertama otomatis
  if (scenarios.length > 0) selectScenario(scenarios[0]);
}

async function selectScenario(scenario) {
  currentScenario = scenario;
  currentNode = null;

  // Update UI judul
  const title = document.getElementById("scenario-title");
  if (title) title.textContent = scenario.name || scenario.scenario_id;

  // Highlight item
  document.querySelectorAll(".scenario-item").forEach((el) => {
    el.classList.toggle("active", el.dataset.id === scenario.scenario_id);
  });

  // Load graph
  await refreshGraph();
  clearDetailPane();
}

async function refreshGraph() {
  if (!currentScenario) return;
  const result = await Api.getGraph(currentScenario.scenario_id);
  if (!result.ok) return;

  scenarioGraph = result.data;

  // Set branch utama (pertama atau branch yang sedang aktif)
  if (scenarioGraph.branches?.length > 0) {
    if (!currentBranch) {
      currentBranch = scenarioGraph.branches[0];
    } else {
      // Refresh objek branch
      currentBranch =
        scenarioGraph.branches.find((b) => b.branch_id === currentBranch.branch_id) ||
        scenarioGraph.branches[0];
    }
  }

  dagView.render(scenarioGraph);
  renderBranchList(scenarioGraph.branches || []);

  // Jika ada node yang sebelumnya dipilih, pertahankan
  if (currentNode) {
    dagView.selectNode(currentNode.id);
  }
}

function renderBranchList(branches) {
  const container = document.getElementById("branch-list");
  if (!container) return;
  container.innerHTML = "";
  branches.forEach((b) => {
    const btn = document.createElement("button");
    btn.className = "branch-btn text-xs px-2 py-1 rounded mr-1 mb-1";
    btn.style.backgroundColor = b.color || "#1F9D8B";
    btn.style.color = "#E8EAF0";
    btn.textContent = b.name || b.branch_id.slice(0, 8);
    btn.title = `Branch: ${b.branch_id}`;
    btn.addEventListener("click", () => {
      currentBranch = b;
      document.querySelectorAll(".branch-btn").forEach((el) =>
        el.classList.toggle("ring-2", el === btn)
      );
    });
    container.appendChild(btn);
  });
}

// ── Event Listeners ───────────────────────────────────────────

function setupEventListeners() {
  // DAG: simpul diklik
  document.getElementById("dag-container")?.addEventListener("dag:nodeSelected", (e) => {
    currentNode = e.detail;
    renderDetailPane(e.detail);
  });

  // DAG: fork diminta (klik kanan)
  document.getElementById("dag-container")?.addEventListener("dag:forkRequested", (e) => {
    openForkModal(e.detail);
  });

  // Tombol submit aksi
  document.getElementById("action-submit-btn")?.addEventListener("click", handleSubmitAction);

  // Tombol fork di pane detail
  document.getElementById("fork-btn")?.addEventListener("click", () => {
    if (currentNode) openForkModal(currentNode);
  });

  // Modal fork: konfirmasi
  document.getElementById("fork-confirm-btn")?.addEventListener("click", handleForkConfirm);

  // Modal fork: batal
  document.getElementById("fork-cancel-btn")?.addEventListener("click", () => {
    document.getElementById("fork-modal")?.classList.add("hidden");
  });

  // Modal LLM config
  document.getElementById("llm-config-btn")?.addEventListener("click", openLlmConfigModal);
  document.getElementById("llm-config-save-btn")?.addEventListener("click", saveLlmConfig);
  document.getElementById("llm-config-cancel-btn")?.addEventListener("click", () => {
    document.getElementById("llm-config-modal")?.classList.add("hidden");
  });
  document.getElementById("llm-test-btn")?.addEventListener("click", handleLlmTest);

  // Tombol ekspor
  document.getElementById("export-json-btn")?.addEventListener("click", () =>
    handleExport("json")
  );
  document.getElementById("export-md-btn")?.addEventListener("click", () =>
    handleExport("markdown")
  );

  // Tabs telemetri/relasi
  document.querySelectorAll("[data-tab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tab = btn.dataset.tab;
      switchTab(tab);
    });
  });
}

// ── Detail Pane ───────────────────────────────────────────────

function clearDetailPane() {
  const narrative = document.getElementById("narrative-text");
  const choices = document.getElementById("choices-container");
  const actionInput = document.getElementById("action-input");
  if (narrative) narrative.innerHTML = "";
  if (choices) choices.innerHTML = "";
  if (actionInput) actionInput.value = "";
}

function renderDetailPane(nodeData) {
  // Narasi (di-sanitasi DOMPurify + render Markdown)
  const narrative = document.getElementById("narrative-text");
  if (narrative && window.DOMPurify && window.marked) {
    const raw = nodeData.narrative || "";
    narrative.innerHTML = DOMPurify.sanitize(marked.parse(raw));
  }

  // Pilihan aksi
  const choices = document.getElementById("choices-container");
  if (choices) {
    choices.innerHTML = "";
    const suggested = nodeData.suggested_choices || [];
    suggested.forEach((choice) => {
      const btn = document.createElement("button");
      btn.className = "choice-btn text-sm px-3 py-1 rounded mr-2 mb-2";
      btn.textContent = choice;
      btn.addEventListener("click", () => {
        const input = document.getElementById("action-input");
        if (input) input.value = choice;
      });
      choices.appendChild(btn);
    });
  }

  // Fallback badge
  const fallbackBadge = document.getElementById("fallback-badge");
  if (fallbackBadge) {
    fallbackBadge.classList.toggle("hidden", !nodeData.is_fallback);
  }

  // Load state relasi
  if (currentScenario && nodeData.id) {
    loadRelationState(nodeData.id);
  }
}

async function loadRelationState(nodeId) {
  const result = await Api.checkout(
    currentBranch?.branch_id || "",
    nodeId
  );
  if (result.ok) {
    relationView.render(
      result.data.actor_states || [],
      result.data.relation_edges || []
    );
  }
}

// ── Submit Aksi ───────────────────────────────────────────────

async function handleSubmitAction() {
  if (!currentScenario || !currentBranch || !currentNode) {
    showBanner("Pilih skenario, cabang, dan simpul terlebih dahulu.", "warn");
    return;
  }

  const input = document.getElementById("action-input");
  const userAction = input?.value?.trim();
  if (!userAction) {
    showBanner("Masukkan aksi terlebih dahulu.", "warn");
    return;
  }

  setSubmitLoading(true);
  const result = await Api.executeTurn(
    currentScenario.scenario_id,
    currentBranch.branch_id,
    currentNode.id,
    userAction
  );
  setSubmitLoading(false);

  if (!result.ok) {
    showBanner(`Gagal: ${result.error}`, "error");
    return;
  }

  const node = result.data;
  if (node.is_fallback) {
    showBanner("Model tidak merespons. Status skenario dipertahankan (fallback).", "warn");
  }

  // Tambah data ke telemetri
  telemetryView.addTurn({
    turn_index: node.turn_index,
    prompt_tokens: node.prompt_tokens,
    latency_ms: node.latency_ms,
    is_fallback: node.is_fallback,
  });

  // Update node aktif dan refresh DAG
  currentNode = { id: node.node_id, ...node };
  await refreshGraph();
  dagView.selectNode(node.node_id);
  renderDetailPane(currentNode);

  if (input) input.value = "";
}

function setSubmitLoading(loading) {
  const btn = document.getElementById("action-submit-btn");
  if (!btn) return;
  btn.disabled = loading;
  btn.textContent = loading ? "Memproses..." : "Jalankan aksi";
}

// ── Fork ──────────────────────────────────────────────────────

function openForkModal(nodeData) {
  const modal = document.getElementById("fork-modal");
  if (!modal) return;
  const label = document.getElementById("fork-node-label");
  if (label) {
    label.textContent = `Dari simpul T${nodeData.turn_index || "?"}`;
  }
  const nameInput = document.getElementById("fork-branch-name");
  if (nameInput) {
    nameInput.value = `cabang-${Date.now().toString(36)}`;
  }
  modal.dataset.nodeId = nodeData.id;
  modal.classList.remove("hidden");
}

async function handleForkConfirm() {
  const modal = document.getElementById("fork-modal");
  const nodeId = modal?.dataset.nodeId;
  const nameInput = document.getElementById("fork-branch-name");
  const branchName = nameInput?.value?.trim() || "cabang-baru";

  if (!currentScenario || !nodeId) return;

  const result = await Api.forkBranch(currentScenario.scenario_id, nodeId, branchName);
  modal?.classList.add("hidden");

  if (!result.ok) {
    showBanner(`Fork gagal: ${result.error}`, "error");
    return;
  }

  currentBranch = result.data;
  await refreshGraph();
  showBanner(`Cabang "${branchName}" berhasil dibuat.`, "ok");
}

// ── LLM Config Modal ──────────────────────────────────────────

function openLlmConfigModal() {
  const modal = document.getElementById("llm-config-modal");
  if (!modal) return;
  const cfg = Api.readLlmConfig();
  document.getElementById("llm-provider-select").value = cfg.provider;
  document.getElementById("llm-base-url-input").value = cfg.baseUrl;
  document.getElementById("llm-model-input").value = cfg.model;
  document.getElementById("llm-api-key-input").value = "";
  modal.classList.remove("hidden");
  updateApiKeyHint(cfg.provider);
}

function saveLlmConfig() {
  const provider = document.getElementById("llm-provider-select")?.value || "mock";
  const baseUrl = document.getElementById("llm-base-url-input")?.value || "";
  const model = document.getElementById("llm-model-input")?.value || "";
  const apiKey = document.getElementById("llm-api-key-input")?.value || "";

  Api.saveLlmConfig({ provider, baseUrl, model, apiKey });
  document.getElementById("llm-config-modal")?.classList.add("hidden");
  showBanner("Konfigurasi LLM disimpan.", "ok");
}

async function handleLlmTest() {
  const statusEl = document.getElementById("llm-test-status");
  if (statusEl) statusEl.textContent = "Menguji...";
  const result = await Api.testLlm();
  if (statusEl) {
    statusEl.textContent = result.ok
      ? `Terhubung (${result.data?.latency_ms ?? "?"}ms)`
      : `Gagal: ${result.data?.error || result.error}`;
  }
}

function updateApiKeyHint(provider) {
  const hint = document.getElementById("llm-api-key-hint");
  if (!hint) return;
  const needsKey = ["groq", "openrouter", "gemini", "byom"].includes(provider);
  hint.textContent = needsKey
    ? "Kunci API diperlukan untuk provider cloud ini."
    : "Provider lokal tidak memerlukan kunci API.";
}

// ── Ekspor ────────────────────────────────────────────────────

async function handleExport(format) {
  if (!currentScenario) return;
  const result = await Api.exportScenario(currentScenario.scenario_id, format);
  if (!result.ok) {
    showBanner(`Ekspor gagal: ${result.error}`, "error");
    return;
  }
  const content = format === "json"
    ? JSON.stringify(result.data, null, 2)
    : result.data?.content || JSON.stringify(result.data, null, 2);
  const mime = format === "json" ? "application/json" : "text/markdown";
  const ext = format === "json" ? "json" : "md";
  const filename = `${currentScenario.scenario_id}.${ext}`;
  downloadBlob(content, filename, mime);
}

function downloadBlob(content, filename, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ── Tabs ──────────────────────────────────────────────────────

function switchTab(tab) {
  const panes = document.querySelectorAll("[data-pane]");
  panes.forEach((p) => p.classList.toggle("hidden", p.dataset.pane !== tab));
  document.querySelectorAll("[data-tab]").forEach((btn) =>
    btn.classList.toggle("tab-active", btn.dataset.tab === tab)
  );
}

// ── Banner notifikasi ─────────────────────────────────────────

function showBanner(message, type = "ok") {
  const banner = document.getElementById("notif-banner");
  if (!banner) return;
  banner.textContent = message;
  banner.className = `notif-banner notif-${type}`;
  banner.classList.remove("hidden");
  clearTimeout(banner._timeout);
  banner._timeout = setTimeout(() => banner.classList.add("hidden"), 4000);
}
