/**
 * static/js/relation_view.js — Cytoscape Relasi Aktor (Bezier Asimetris)
 *
 * Fitur:
 * - Graf relasi A->B dan B->A yang terpisah (bezier dua arah).
 * - Ketebalan edge proporsional dengan |trust| atau |affinity|.
 * - Warna edge: teal (#1F9D8B) untuk positif, oranye (#F5A623) untuk negatif.
 * - Label edge: "trust:+2 tension:1".
 * - Klik node -> highlight semua relasi aktor tersebut.
 */

export class RelationView {
  /**
   * @param {string} containerId - ID elemen DOM container.
   */
  constructor(containerId) {
    this._container = document.getElementById(containerId);
    this._cy = null;
  }

  /** Inisialisasi Cytoscape pada container. */
  init() {
    if (!window.cytoscape) return;
    this._cy = cytoscape({
      container: this._container,
      style: this._buildStyle(),
      layout: { name: "cose", animate: false },
      wheelSensitivity: 0.3,
    });
  }

  /**
   * Render ulang graf relasi dari data checkout/node.
   * @param {Array} actorStates  - [{ actor_id, name, ... }]
   * @param {Array} relationEdges - [{ source_actor_id, target_actor_id, trust, affinity, tension }]
   */
  render(actorStates, relationEdges) {
    if (!this._cy) return;
    this._cy.elements().remove();

    const cyNodes = actorStates.map((a) => ({
      data: {
        id: a.actor_id,
        label: a.name || a.actor_id,
        mood: a.mood ?? 2,
      },
    }));

    const cyEdges = (relationEdges || []).map((e) => {
      const trust = e.trust ?? 0;
      const tension = e.tension ?? 0;
      const sentiment = trust >= 0 ? "pos" : "neg";
      const width = Math.max(1, Math.abs(trust));
      return {
        data: {
          id: `${e.source_actor_id}_${e.target_actor_id}`,
          source: e.source_actor_id,
          target: e.target_actor_id,
          label: `trust:${trust > 0 ? "+" : ""}${trust} ten:${tension}`,
          sentiment,
          edgeWidth: width,
        },
      };
    });

    this._cy.add([...cyNodes, ...cyEdges]);
    this._cy
      .layout({
        name: "cose",
        animate: true,
        animationDuration: 400,
        nodeRepulsion: 8000,
        idealEdgeLength: 120,
      })
      .run();
  }

  _buildStyle() {
    return [
      {
        selector: "node",
        style: {
          shape: "ellipse",
          width: 60,
          height: 60,
          label: "data(label)",
          "font-family": "IBM Plex Sans, sans-serif",
          "font-size": 10,
          color: "#E8EAF0",
          "text-valign": "center",
          "text-halign": "center",
          "background-color": "#2A2F3A",
          "border-width": 2,
          "border-color": "#1F9D8B",
        },
      },
      {
        // Mood rendah (1) = border merah
        selector: "node[mood = 1]",
        style: { "border-color": "#E05C5C" },
      },
      {
        // Mood tinggi (3) = border teal
        selector: "node[mood = 3]",
        style: { "border-color": "#1F9D8B" },
      },
      {
        selector: "edge",
        style: {
          width: "data(edgeWidth)",
          label: "data(label)",
          "font-family": "JetBrains Mono, monospace",
          "font-size": 9,
          color: "#9BA3B5",
          "text-rotation": "autorotate",
          "text-margin-y": -8,
          "curve-style": "bezier",
          "target-arrow-shape": "triangle",
          "line-color": "#1F9D8B",
          "target-arrow-color": "#1F9D8B",
          opacity: 0.8,
        },
      },
      {
        selector: "edge[sentiment = 'neg']",
        style: {
          "line-color": "#F5A623",
          "target-arrow-color": "#F5A623",
        },
      },
    ];
  }
}
