#!/usr/bin/env python3
"""Generate topology diagrams for all three networks.

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

from quantum_routing.utils.config import SimConfig
from quantum_routing.topologies.nsfnet import build_nsfnet, NSFNET_NODES, NSFNET_EDGES
from quantum_routing.topologies.surfnet import build_surfnet, SURFNET_NODES, SURFNET_EDGES
from quantum_routing.topologies.abilene import build_abilene, ABILENE_NODES, ABILENE_EDGES
from quantum_routing.utils.fidelity import transmissivity


def draw_topology(title, nodes_dict, edges_list, filename, scale_factor,
                  figsize=(10, 7), font_size=9, node_size=500):
    """Draw a network topology diagram with geographic layout."""

    config = SimConfig(distance_scale=scale_factor)
    G = nx.Graph()

    # Use (lon, lat) as positions so the map looks geographically correct
    pos = {}
    for node_id, (city, lat, lon) in nodes_dict.items():
        G.add_node(node_id)
        pos[node_id] = (lon, lat)

    edge_lengths = []
    for u, v, dist in edges_list:
        scaled = dist / scale_factor
        p_gen = transmissivity(scaled, 22.0)
        G.add_edge(u, v, length=dist, scaled=scaled, p_gen=p_gen)
        edge_lengths.append(scaled)

    fig, ax = plt.subplots(figsize=figsize)

    # Edge colors by generation probability
    p_gens = [G[u][v]["p_gen"] for u, v in G.edges()]
    edge_colors = plt.cm.RdYlGn(np.array(p_gens))

    # Draw edges
    nx.draw_networkx_edges(G, pos, ax=ax, width=2.0,
                           edge_color=edge_colors, alpha=0.8)

    # Edge labels: original distance
    edge_labels = {}
    for u, v, d in G.edges(data=True):
        edge_labels[(u, v)] = f"{d['length']:.0f} km"
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,
                                 ax=ax, font_size=font_size - 2,
                                 font_color="gray", alpha=0.8)

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_size,
                           node_color="white", edgecolors="#534AB7",
                           linewidths=2.0)

    # Node labels: ID + city name
    node_labels = {}
    for node_id, (city, lat, lon) in nodes_dict.items():
        short_city = city.split(",")[0]
        node_labels[node_id] = f"{node_id}\n({short_city})"
    nx.draw_networkx_labels(G, pos, labels=node_labels, ax=ax,
                            font_size=font_size, font_weight="bold")

    # Colorbar for generation probability
    sm = plt.cm.ScalarMappable(cmap=plt.cm.RdYlGn,
                                norm=plt.Normalize(vmin=0, vmax=1))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label(f"Gen. probability (scale={scale_factor}x, L_att=22 km)",
                   fontsize=10)

    n_nodes = len(G.nodes)
    n_edges = len(G.edges)
    avg_dist = np.mean([d["length"] for _, _, d in G.edges(data=True)])
    avg_p = np.mean(p_gens)

    ax.set_title(f"{title}\n{n_nodes} nodes, {n_edges} edges, "
                 f"avg dist {avg_dist:.0f} km, avg p_gen {avg_p:.3f} "
                 f"(at {scale_factor}x scale)",
                 fontsize=12, pad=15)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(filename, dpi=150, bbox_inches="tight")
    print(f"Saved {filename}")
    plt.close(fig)


if __name__ == "__main__":
    draw_topology(
        title="NSFNET (14-node US backbone)",
        nodes_dict=NSFNET_NODES,
        edges_list=NSFNET_EDGES,
        filename="results/topology_nsfnet.png",
        scale_factor=30,
        figsize=(11, 7),
        font_size=8,
        node_size=600,
    )

    draw_topology(
        title="SURFnet pruned (8-node Netherlands)",
        nodes_dict=SURFNET_NODES,
        edges_list=SURFNET_EDGES,
        filename="results/topology_surfnet.png",
        scale_factor=3,
        figsize=(8, 7),
        font_size=9,
        node_size=600,
    )

    draw_topology(
        title="Abilene / Internet2 (11-node US backbone)",
        nodes_dict=ABILENE_NODES,
        edges_list=ABILENE_EDGES,
        filename="results/topology_abilene.png",
        scale_factor=40,
        figsize=(11, 7),
        font_size=8,
        node_size=600,
    )

    print("Done! All topology diagrams saved to results/")
