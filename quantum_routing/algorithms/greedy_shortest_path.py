"""Greedy shortest-path routing: serve user pairs one at a time."""

import networkx as nx
from quantum_routing.network import QuantumNetwork
from quantum_routing.utils.fidelity import path_fidelity


def greedy_route(network: QuantumNetwork) -> list[dict]:
    """Route all user pairs greedily by priority order.

    For each pair, find the shortest path (by -log fidelity weight) in the
    current active subgraph, consume the links, then move to the next pair.

    Returns a list of results, one per user pair:
        {"src", "dst", "path", "fidelity", "delivered"}
    """
    config = network.config
    results = []
    active = network.get_active_subgraph()

    for src, dst in config.user_pairs:
        try:
            path = nx.shortest_path(active, src, dst, weight="weight")
        except nx.NetworkXNoPath:
            results.append({
                "src": src, "dst": dst, "path": None,
                "fidelity": 0.0, "delivered": False,
            })
            continue

        # Try to consume links along the path
        link_fidelities = []
        consumed_edges = []
        success = True

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            link = network.consume_link(u, v)
            if link is None:
                success = False
                break
            link_fidelities.append(link.fidelity)
            consumed_edges.append((u, v))

        if not success:
            results.append({
                "src": src, "dst": dst, "path": path,
                "fidelity": 0.0, "delivered": False,
            })
            continue

        # Swapping (q_swap = 1.0 by default, but support probabilistic)
        import random
        num_swaps = len(path) - 2  # internal nodes
        swap_success = all(
            random.random() < config.q_swap for _ in range(num_swaps)
        )

        e2e_fidelity = path_fidelity(link_fidelities) if swap_success else 0.0
        delivered = swap_success and e2e_fidelity >= config.f_min

        # Remove consumed edges from active subgraph for subsequent pairs
        for u, v in consumed_edges:
            if active.has_edge(u, v):
                active.remove_edge(u, v)

        results.append({
            "src": src, "dst": dst, "path": path,
            "fidelity": e2e_fidelity, "delivered": delivered,
        })

    return results