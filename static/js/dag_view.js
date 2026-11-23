/**
 * static/js/dag_view.js — Cytoscape Git-DAG Swimlane
 *
 * Fitur:
 * - Visualisasi pohon simpul (node) + cabang (branch) sebagai DAG.
 * - Swimlane per-cabang dengan warna berbeda (dari field `color` di DB).
 * - Klik simpul -> event "dag:nodeSelected" berisi data simpul.
 * - Klik kanan / tombol fork -> event "dag:forkRequested".
 * - Layout: cytoscape-dagre (top-to-bottom, swimlane).
 * - Panah asimetris: bezier + target-arrow triangle.
 */

export class DagView {
  /**
   * @param {string} containerId - ID elemen DOM container.
   */
  constructor(containerId) {
    this._container = document.getElementById(containerId);
    this._cy = null;
    this._selectedNodeId = null;
  }

  /** Inisialisasi Cytoscape pada container. */
  init() {
    if (!window.cytoscape) {
      console.error("[DagView] cytoscape tidak tersedia.");
      return;
    }
    if (!window.cytoscapeDagre) {
      console.error("[DagView] cytoscape-dagre tidak tersedia.");
      return;
    }
    cytoscape.use(cytoscapeDagre);

    this._cy = cytoscape({
      container: this._container,
      style: this._buildStyle(),
      layout: { name: "dagre", rankDir: "TB", nodeSep: 40, rankSep: 60 },
      wheelSensitivity: 0.3,
    });

    this._cy.on("tap", "node", (evt) => {
      const node = evt.target;
      this._selectedNodeId = node.id();
      // Highlight
      this._cy.nodes().removeClass("selected");
      node.addClass("selected");
      this._container.dispatchEvent(
        new CustomEvent("dag:nodeSelected", { detail: node.data(), bubbles: true })
      );
    });

    this._cy.on("cxttap", "node", (evt) => {
      const node = evt.target;
      this._container.dispatchEvent(
        new CustomEvent("dag:forkRequested", { detail: node.data(), bubbles: true })
      );
    });
  }

  /**
   * Render ulang DAG dari data graf API.
   * @param {Object} graphData - { nodes: [...], edges: [...], branches: [...] }
   */
  render(graphData) {
    if (!this._cy) return;
    this._cy.elements().remove();

    const branchColorMap = {};
    (graphData.branches || []).forEach((b) => {
      branchColorMap[b.branch_id] = b.color || "#1F9D8B";
    });

    // Tambahkan nodes
    const cyNodes = (graphData.nodes || []).map((n) => ({
      data: {
        id: n.node_id,
        label: `T${n.turn_index}\n${(n.user_action || "root").slice(0, 24)}`,
        turn_index: n.turn_index,
        branch_id: n.branch_id,
        is_fallback: n.is_fallback,
        narrative: n.narrative || "",
        arc_summary: n.arc_summary || "",
        suggested_choices: n.suggested_choices || [],
        color: branchColorMap[n.branch_id] || "#1F9D8B",
        parent_id: n.parent_id,
        user_action: n.user_action || "",
      },
    }));

    // Tambahkan edges (parent -> child)
    const cyEdges = (graphData.nodes || [])
      .filter((n) => n.parent_id)
      .map((n) => ({
        data: {
          id: `e_${n.parent_id}_${n.node_id}`,
          source: n.parent_id,
          target: n.node_id,
          branch_id: n.branch_id,
          color: branchColorMap[n.branch_id] || "#1F9D8B",
        },
      }));

    this._cy.add([...cyNodes, ...cyEdges]);
    this._relayout();

    // Pulihkan seleksi
    if (this._selectedNodeId) {
      const sel = this._cy.getElementById(this._selectedNodeId);
      if (sel.length) sel.addClass("selected");
    }
  }

  /** Pilih simpul secara programatik (misal setelah turn baru dibuat). */
  selectNode(nodeId) {
    if (!this._cy) return;
    this._cy.nodes().removeClass("selected");
    const node = this._cy.getElementById(nodeId);
    if (node.length) {
      node.addClass("selected");
      this._selectedNodeId = nodeId;
      this._cy.animate({ center: { eles: node }, zoom: 1.4 }, { duration: 300 });
    }
  }

  /** Jalankan ulang layout dagre. */
  _relayout() {
    if (!this._cy) return;
    this._cy
      .layout({
        name: "dagre",
        rankDir: "TB",
        nodeSep: 50,
        rankSep: 70,
        animate: true,
        animationDuration: 350,
      })
      .run();
  }

  _buildStyle() {
    return [
      {
        selector: "node",
        style: {
          shape: "round-rectangle",
          width: 110,
          height: 48,
          label: "data(label)",
          "text-wrap": "wrap",
          "text-max-width": 100,
          "font-family": "IBM Plex Sans, sans-serif",
          "font-size": 10,
          color: "#E8EAF0",
          "text-valign": "center",
          "text-halign": "center",
          "background-color": "data(color)",
          "border-width": 0,
          "padding": 6,
        },
      },
      {
        selector: "node[is_fallback=true]",
        style: {
          "border-width": 2,
          "border-color": "#F5A623",
          "border-style": "dashed",
        },
      },
      {
        selector: "node.selected",
        style: {
          "border-width": 3,
          "border-color": "#FFFFFF",
          "border-opacity": 0.9,
        },
      },
      {
        selector: "edge",
        style: {
          width: 2,
          "line-color": "data(color)",
          "target-arrow-color": "data(color)",
          "target-arrow-shape": "triangle",
          "curve-style": "bezier",
          opacity: 0.75,
        },
      },
    ];
  }
}
