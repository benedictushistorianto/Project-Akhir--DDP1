/**
 * static/js/api.js — Fetch wrapper + X-LLM-API-Key dari sessionStorage
 *
 * Aturan keamanan:
 * - Kunci API hanya disimpan di sessionStorage (hilang saat tab tutup).
 * - Kunci tidak pernah dikirim ke endpoint non-/api/llm/* untuk mencegah
 *   kebocoran ke endpoint yang tidak memerlukannya.
 * - Kunci tidak pernah dilog ke console atau body request.
 */

const API_KEY_STORAGE = "whenyhh_llm_api_key";
const LLM_PROVIDER_STORAGE = "whenyhh_llm_provider";
const LLM_BASE_URL_STORAGE = "whenyhh_llm_base_url";
const LLM_MODEL_STORAGE = "whenyhh_llm_model";

/** Ambil kunci API dari sessionStorage (ephemeral). */
function getApiKey() {
  return sessionStorage.getItem(API_KEY_STORAGE) || "";
}

/** Simpan kunci API ke sessionStorage. */
function setApiKey(key) {
  if (key) {
    sessionStorage.setItem(API_KEY_STORAGE, key);
  } else {
    sessionStorage.removeItem(API_KEY_STORAGE);
  }
}

/** Bangun header standar untuk request ke backend. */
function buildHeaders(includeLlmKey = false) {
  const headers = { "Content-Type": "application/json" };
  if (includeLlmKey) {
    const key = getApiKey();
    if (key) headers["X-LLM-API-Key"] = key;
    const provider = sessionStorage.getItem(LLM_PROVIDER_STORAGE) || "ollama";
    headers["X-LLM-Provider"] = provider;
    const baseUrl = sessionStorage.getItem(LLM_BASE_URL_STORAGE) || "";
    if (baseUrl) headers["X-LLM-Base-Url"] = baseUrl;
  }
  return headers;
}

/** Baca LLMConfig dari sessionStorage untuk dikirim di body request. */
function getLlmConfig() {
  return {
    provider: sessionStorage.getItem(LLM_PROVIDER_STORAGE) || "mock",
    base_url: sessionStorage.getItem(LLM_BASE_URL_STORAGE) || null,
    model_name: sessionStorage.getItem(LLM_MODEL_STORAGE) || null,
    temperature: 0.7,
    max_tokens: 512,
  };
}

/**
 * Fetch helper utama dengan error handling terpusat.
 * Semua kegagalan dikembalikan sebagai { ok: false, error: string }.
 */
async function apiFetch(path, options = {}) {
  try {
    const resp = await fetch(path, options);
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      return {
        ok: false,
        status: resp.status,
        error: data.detail || data.error || `HTTP ${resp.status}`,
        data,
      };
    }
    return { ok: true, status: resp.status, data };
  } catch (err) {
    return { ok: false, status: 0, error: err.message || "Network error", data: null };
  }
}

// ── Endpoint wrappers ─────────────────────────────────────────

export const Api = {
  /** Daftar semua skenario. */
  async listScenarios() {
    return apiFetch("/api/scenarios", { headers: buildHeaders() });
  },

  /** Detail satu skenario. */
  async getScenario(scenarioId) {
    return apiFetch(`/api/scenarios/${scenarioId}`, { headers: buildHeaders() });
  },

  /** Graf DAG simpul + cabang sebuah skenario. */
  async getGraph(scenarioId) {
    return apiFetch(`/api/scenarios/${scenarioId}/graph`, { headers: buildHeaders() });
  },

  /** Ekspor skenario (format: "json" atau "markdown"). */
  async exportScenario(scenarioId, format = "json") {
    return apiFetch(`/api/scenarios/${scenarioId}/export?format=${format}`, {
      headers: buildHeaders(),
    });
  },

  /**
   * Eksekusi satu giliran simulasi.
   * @param {string} scenarioId
   * @param {string} branchId
   * @param {string} parentNodeId
   * @param {string} userAction
   */
  async executeTurn(scenarioId, branchId, parentNodeId, userAction) {
    return apiFetch("/api/turns", {
      method: "POST",
      headers: buildHeaders(true),  // kirim X-LLM-API-Key
      body: JSON.stringify({
        scenario_id: scenarioId,
        branch_id: branchId,
        parent_node_id: parentNodeId,
        user_action: userAction,
        llm_config: getLlmConfig(),
      }),
    });
  },

  /**
   * Fork cabang baru dari simpul tertentu.
   * @param {string} scenarioId
   * @param {string} fromNodeId
   * @param {string} newBranchName
   */
  async forkBranch(scenarioId, fromNodeId, newBranchName) {
    return apiFetch("/api/branches/fork", {
      method: "POST",
      headers: buildHeaders(),
      body: JSON.stringify({
        scenario_id: scenarioId,
        from_node_id: fromNodeId,
        new_branch_name: newBranchName,
      }),
    });
  },

  /**
   * Checkout simpul/cabang.
   * @param {string} branchId
   * @param {string} targetNodeId
   */
  async checkout(branchId, targetNodeId) {
    return apiFetch("/api/branches/checkout", {
      method: "POST",
      headers: buildHeaders(),
      body: JSON.stringify({ branch_id: branchId, target_node_id: targetNodeId }),
    });
  },

  /** Daftar model dari provider aktif (opsional). */
  async listModels() {
    return apiFetch("/api/llm/models", { headers: buildHeaders(true) });
  },

  /** Uji konektivitas LLM. */
  async testLlm() {
    return apiFetch("/api/llm/test", {
      method: "POST",
      headers: buildHeaders(true),
      body: JSON.stringify(getLlmConfig()),
    });
  },

  /** Simpan konfigurasi LLM ke sessionStorage. */
  saveLlmConfig({ provider, baseUrl, model, apiKey }) {
    sessionStorage.setItem(LLM_PROVIDER_STORAGE, provider || "mock");
    sessionStorage.setItem(LLM_BASE_URL_STORAGE, baseUrl || "");
    sessionStorage.setItem(LLM_MODEL_STORAGE, model || "");
    setApiKey(apiKey || "");
  },

  /** Baca konfigurasi LLM dari sessionStorage. */
  readLlmConfig() {
    return {
      provider: sessionStorage.getItem(LLM_PROVIDER_STORAGE) || "mock",
      baseUrl: sessionStorage.getItem(LLM_BASE_URL_STORAGE) || "",
      model: sessionStorage.getItem(LLM_MODEL_STORAGE) || "",
      hasKey: !!getApiKey(),
    };
  },
};
