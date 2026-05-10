"""Quantum network: physical topology + dynamic entanglement link state."""

import random
from dataclasses import dataclass, field
from typing import Optional

import networkx as nx

from quantum_routing.utils.config import SimConfig
from quantum_routing.utils.fidelity import transmissivity


@dataclass
class EntangledLink:
    """An elementary entangled pair on a physical edge."""
    fidelity: float
    age: int = 0  # time steps since creation


class QuantumNetwork:
    """Manages the physical graph and the dynamic entanglement state."""

    def __init__(self, config: SimConfig):
        self.config = config
        # Physical topology: nodes + edges with attribute 'length_km'
        self.graph = nx.Graph()
        # Entanglement state: edge (u,v) -> list of EntangledLink
        # Using frozenset keys so (u,v) and (v,u) map to the same entry
        self.link_state: dict[frozenset, list[EntangledLink]] = {}

    # ---- Topology setup ----

    def add_node(self, node_id: str, **attrs):
        self.graph.add_node(node_id, **attrs)

    def add_edge(self, u: str, v: str, length_km: float):
        # Apply distance scaling (e.g., distance_scale=10 makes 1000 km -> 100 km)
        scaled_length = length_km / self.config.distance_scale
        self.graph.add_edge(u, v, length_km=scaled_length,
                            length_km_original=length_km)
        key = frozenset((u, v))
        if key not in self.link_state:
            self.link_state[key] = []

    # ---- Per-time-step operations ----

    def generate_links(self):
        """Step 1: Each physical edge independently generates an entangled pair."""
        for u, v, data in self.graph.edges(data=True):
            length_km = data["length_km"]
            p = self.config.p_gen_base * transmissivity(length_km, self.config.L_att)
            if random.random() < p:
                key = frozenset((u, v))
                self.link_state[key].append(
                    EntangledLink(fidelity=self.config.f_init, age=0)
                )

    def decohere_links(self):
        """Step 2: Age links and remove those lost to decoherence."""
        for key in list(self.link_state.keys()):
            surviving = []
            for link in self.link_state[key]:
                link.age += 1
                if self.config.decoherence_mode == "cutoff":
                    if link.age <= self.config.t_cutoff:
                        surviving.append(link)
                else:  # probabilistic
                    if random.random() < self.config.q_memory:
                        surviving.append(link)
            self.link_state[key] = surviving

    def consume_link(self, u: str, v: str) -> Optional[EntangledLink]:
        """Remove and return the highest-fidelity link on edge (u, v), or None."""
        key = frozenset((u, v))
        links = self.link_state.get(key, [])
        if not links:
            return None
        # Pick highest fidelity
        best = max(links, key=lambda lnk: lnk.fidelity)
        links.remove(best)
        return best

    def has_link(self, u: str, v: str) -> bool:
        key = frozenset((u, v))
        return len(self.link_state.get(key, [])) > 0

    def best_fidelity(self, u: str, v: str) -> float:
        """Return the highest fidelity available on edge (u, v), or 0."""
        key = frozenset((u, v))
        links = self.link_state.get(key, [])
        if not links:
            return 0.0
        return max(lnk.fidelity for lnk in links)

    def get_active_subgraph(self) -> nx.Graph:
        """Return a graph containing only edges that currently hold entanglement,
        weighted by -log(fidelity) for shortest-path computations."""
        g = nx.Graph()
        g.add_nodes_from(self.graph.nodes(data=True))
        for key, links in self.link_state.items():
            if links:
                u, v = tuple(key)
                best_f = max(lnk.fidelity for lnk in links)
                weight = -1.0 * __import__("math").log(best_f) if best_f > 0 else float("inf")
                g.add_edge(u, v, weight=weight, fidelity=best_f)
        return g

    def clear_all_links(self):
        """Reset all entanglement state."""
        for key in self.link_state:
            self.link_state[key] = []