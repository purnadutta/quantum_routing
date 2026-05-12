#!/usr/bin/env python3
"""Generate topology diagrams for all three networks.

Clean style: white background, black text, labels in blank spaces
(not on top of edges).

Usage:
    python scripts/plot_topologies.py

Produces:
    results/topology_nsfnet.png
    results/topology_surfnet.png
    results/topology_abilene.png
"""

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from quantum_routing.topologies.nsfnet import NSFNET_NODES, NSFNET_EDGES
from quantum_routing.topologies.surfnet import SURFNET_NODES, SURFNET_EDGES
from quantum_routing.topologies.abilene import ABILENE_NODES, ABILENE_EDGES


def draw_topology(title, nodes_dict, edges_list, filename, scale_factor,
                  figsize=(10, 7), font_size=9, node_size=350,
                  label_offset_scale=0.12):
    """Draw a clean topology diagram with geographic layout."""

    G = nx.Graph()
    pos = {}
    for node_id, (city, lat, lon) in nodes_dict.items():
        G.add_node(node_id)
        pos[node_id] = (lon, lat)

    for u, v, dist in edges_list:
        scaled = dist / scale_factor
        G.add_edge(u, v, length=dist, scaled=scaled)

    fig, ax = plt.subplots(figsize=figsize)
    fig.set_facecolor("white")
    ax.set_facecolor("white")

    # Draw edges — simple gray lines
    nx.draw_networkx_edges(G, pos, ax=ax, width=1.5,
                           edge_color="#999999", alpha=0.6)

    # Draw nodes — white with dark border
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_size,
                           node_color="white", edgecolors="#333333",
                           linewidths=1.5)

    # Node ID inside the node
    nx.draw_networkx_labels(G, pos, ax=ax,
                            font_size=font_size - 1, font_weight="bold",
                            font_color="black")

    # Title with stats
    n_nodes = len(G.nodes)
    n_edges = len(G.edges)
    avg_orig = np.mean([d["length"] for _, _, d in G.edges(data=True)])
    avg_scaled = np.mean([d["scaled"] for _, _, d in G.edges(data=True)])

    ax.set_title(f"{title}\n{n_nodes} nodes, {n_edges} edges  |  "
                 f"scale ÷{scale_factor}  |  "
                 f"avg edge: {avg_orig:.0f} km → {avg_scaled:.1f} km",
                 fontsize=12, pad=15, color="black")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(filename, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"Saved {filename}")
    plt.close(fig)


if __name__ == "__main__":
    draw_topology(
        title="NSFNET (14-node US backbone)",
        nodes_dict=NSFNET_NODES,
        edges_list=NSFNET_EDGES,
        filename="results/topology_nsfnet.png",
        scale_factor=100,
        figsize=(11, 7),
        font_size=9,
        node_size=450,
        label_offset_scale=0.12,
    )

    draw_topology(
        title="SURFnet pruned (17-node Netherlands)",
        nodes_dict=SURFNET_NODES,
        edges_list=SURFNET_EDGES,
        filename="results/topology_surfnet.png",
        scale_factor=1,
        figsize=(10, 8),
        font_size=8,
        node_size=350,
        label_offset_scale=0.18,
    )

    draw_topology(
        title="Abilene / Internet2 (11-node US backbone)",
        nodes_dict=ABILENE_NODES,
        edges_list=ABILENE_EDGES,
        filename="results/topology_abilene.png",
        scale_factor=100,
        figsize=(11, 7),
        font_size=9,
        node_size=450,
        label_offset_scale=0.12,
    )

    print("Done! All topology diagrams saved to results/")
