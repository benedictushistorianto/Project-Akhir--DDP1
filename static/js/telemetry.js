/**
 * static/js/telemetry.js — Plotly Token Budget Chart
 *
 * Menampilkan chart XY sederhana:
 * - X axis: nomor giliran
 * - Y axis: prompt_tokens per giliran
 * - Garis referensi horizontal di 2200 token (batas O(1))
 *
 * Desain: charcoal gelap, aksen teal, sans grid berlebihan.
 */

export class TelemetryView {
  /**
   * @param {string} containerId - ID elemen DOM untuk div Plotly.
   */
  constructor(containerId) {
    this._containerId = containerId;
    this._turns = [];   // { turn_index, prompt_tokens, latency_ms, is_fallback }
  }

  /** Tambahkan data satu giliran baru lalu re-render. */
  addTurn({ turn_index, prompt_tokens, latency_ms, is_fallback }) {
    this._turns.push({ turn_index, prompt_tokens, latency_ms, is_fallback });
    this._render();
  }

  /** Reset semua data giliran. */
  reset() {
    this._turns = [];
    if (window.Plotly) {
      Plotly.purge(this._containerId);
    }
  }

  /** Render ulang chart Plotly. */
  _render() {
    if (!window.Plotly) return;

    const turns = this._turns;
    const xs = turns.map((t) => t.turn_index);
    const ys = turns.map((t) => t.prompt_tokens);
    const colors = turns.map((t) =>
      t.is_fallback ? "#F5A623" : "#1F9D8B"
    );

    const tokenTrace = {
      x: xs,
      y: ys,
      type: "scatter",
      mode: "lines+markers",
      name: "Prompt tokens",
      line: { color: "#1F9D8B", width: 2 },
      marker: { color: colors, size: 7, symbol: "circle" },
      hovertemplate: "Giliran %{x}<br>Tokens: %{y}<extra></extra>",
    };

    const capLine = {
      x: xs.length ? [xs[0], xs[xs.length - 1]] : [0, 1],
      y: [2200, 2200],
      type: "scatter",
      mode: "lines",
      name: "Batas O(1) = 2200",
      line: { color: "#E05C5C", width: 1, dash: "dot" },
      hoverinfo: "none",
    };

    const layout = {
      paper_bgcolor: "#14161A",
      plot_bgcolor: "#1B1E24",
      font: { family: "IBM Plex Sans, sans-serif", color: "#9BA3B5", size: 11 },
      margin: { l: 48, r: 16, t: 32, b: 40 },
      xaxis: {
        title: "Giliran",
        gridcolor: "#2A2F3A",
        zeroline: false,
        tickfont: { size: 10 },
      },
      yaxis: {
        title: "Prompt tokens",
        gridcolor: "#2A2F3A",
        zeroline: false,
        tickfont: { size: 10 },
        range: [0, 2600],
      },
      legend: {
        x: 0.02,
        y: 0.98,
        bgcolor: "rgba(0,0,0,0)",
        font: { size: 10 },
      },
      title: {
        text: "Budget Token O(1)",
        font: { size: 13, color: "#E8EAF0" },
        x: 0.02,
      },
    };

    const config = {
      displayModeBar: false,
      responsive: true,
    };

    Plotly.react(this._containerId, [tokenTrace, capLine], layout, config);
  }
}
