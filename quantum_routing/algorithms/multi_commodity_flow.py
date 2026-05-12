"""Multi-commodity flow routing via path-based ILP.

For each user pair we enumerate candidate paths on the current active
subgraph, then solve an integer linear program that maximises the total
number of delivered EPR pairs subject to:

  1.  Each physical edge's available link count is not exceeded.
  2.  At most one path is selected per user pair per time step.
      (Multi-path per pair is a natural extension; keeping it to one
       makes the comparison with greedy fair.)

The ILP is solved with scipy.optimize.milp (scipy >= 1.7).
"""

import random
from itertools import islice

import networkx as nx
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

from quantum_routing.network import QuantumNetwork
from quantum_routing.utils.fidelity import path_fidelity


# Maximum number of candidate paths to enumerate per user pair.
MAX_PATHS_PER_PAIR = 10


def _enumerate_candidate_paths(network: QuantumNetwork, active: nx.Graph):
    """For each user pair, find candidate paths and their fidelities.

    Returns a list of dicts:
        {"pair_idx", "src", "dst", "path", "fidelity", "edges"}
    Only paths whose end-to-end fidelity >= f_min are included.
    """
    config = network.config
    candidates = []

    for pair_idx, (src, dst) in enumerate(config.user_pairs):
        if src not in active or dst not in active:
            continue
        try:
            raw_paths = list(islice(
                nx.shortest_simple_paths(active, src, dst, weight="weight"),
                MAX_PATHS_PER_PAIR,
            ))
        except nx.NetworkXNoPath:
            continue

        for path in raw_paths:
            # Collect the best fidelity on each hop
            fids = []
            valid = True
            for i in range(len(path) - 1):
                f = network.best_fidelity(path[i], path[i + 1])
                if f <= 0:
                    valid = False
                    break
                fids.append(f)
            if not valid:
                continue

            e2e = path_fidelity(fids)
            if e2e < config.f_min:
                continue

            edges = set()
            for i in range(len(path) - 1):
                edges.add(frozenset((path[i], path[i + 1])))

            candidates.append({
                "pair_idx": pair_idx,
                "src": src,
                "dst": dst,
                "path": path,
                "fidelity": e2e,
                "edges": edges,
            })

    return candidates


def _solve_ilp(candidates, network: QuantumNetwork):
    """Solve the path-selection ILP.

    Returns a list of indices into *candidates* for the selected paths.
    """
    n_paths = len(candidates)
    if n_paths == 0:
        return []

    config = network.config
    n_pairs = len(config.user_pairs)

    # --- Collect all edges used by any candidate path ---
    all_edges_set = set()
    for c in candidates:
        all_edges_set.update(c["edges"])
    all_edges = sorted(all_edges_set, key=lambda e: tuple(sorted(e)))
    edge_to_idx = {e: i for i, e in enumerate(all_edges)}
    n_edges = len(all_edges)

    # --- Edge capacities ---
    edge_caps = np.zeros(n_edges)
    for i, e in enumerate(all_edges):
        links = network.link_state.get(e, [])
        edge_caps[i] = len(links)

    # --- Build constraint matrix ---
    # Row block 1: edge capacity  (n_edges rows)
    # Row block 2: at-most-one path per pair  (n_pairs rows)
    n_constraints = n_edges + n_pairs
    A = np.zeros((n_constraints, n_paths))

    # Edge capacity rows
    for j, c in enumerate(candidates):
        for e in c["edges"]:
            A[edge_to_idx[e], j] = 1.0

    # One-path-per-pair rows
    for j, c in enumerate(candidates):
        A[n_edges + c["pair_idx"], j] = 1.0

    b_upper = np.concatenate([edge_caps, np.ones(n_pairs)])

    # --- Objective: maximise total delivered = minimise -sum(x) ---
    # Tie-break by fidelity so the solver prefers higher-quality paths
    obj = np.array([-1.0 - 1e-4 * c["fidelity"] for c in candidates])

    constraints = LinearConstraint(A, ub=b_upper)
    integrality = np.ones(n_paths)
    bounds = Bounds(lb=0, ub=1)

    result = milp(
        c=obj,
        constraints=constraints,
        integrality=integrality,
        bounds=bounds,
    )

    if not result.success:
        return []

    selected = [j for j in range(n_paths) if result.x[j] > 0.5]
    return selected


def mcf_route(network: QuantumNetwork) -> list[dict]:
    """Route all user pairs via multi-commodity flow optimisation.

    Returns a list of results, one per user pair:
        {"src", "dst", "path", "fidelity", "delivered"}
    """
    config = network.config
    active = network.get_active_subgraph()

    # --- Enumerate candidate paths ---
    candidates = _enumerate_candidate_paths(network, active)

    # --- Solve ILP ---
    selected_indices = _solve_ilp(candidates, network)

    # --- Build per-pair results ---
    pair_result = {}
    for idx in selected_indices:
        c = candidates[idx]
        pair_result[c["pair_idx"]] = c

    results = []
    for pair_idx, (src, dst) in enumerate(config.user_pairs):
        if pair_idx not in pair_result:
            results.append({
                "src": src, "dst": dst, "path": None,
                "fidelity": 0.0, "delivered": False,
            })
            continue

        chosen = pair_result[pair_idx]
        path = chosen["path"]

        # Consume links along the chosen path
        link_fidelities = []
        success = True
        for i in range(len(path) - 1):
            link = network.consume_link(path[i], path[i + 1])
            if link is None:
                success = False
                break
            link_fidelities.append(link.fidelity)

        if not success:
            results.append({
                "src": src, "dst": dst, "path": path,
                "fidelity": 0.0, "delivered": False,
            })
            continue

        # Swapping (q_swap)
        num_swaps = len(path) - 2
        swap_ok = all(
            random.random() < config.q_swap for _ in range(num_swaps)
        )

        e2e_fidelity = path_fidelity(link_fidelities) if swap_ok else 0.0
        delivered = swap_ok and e2e_fidelity >= config.f_min

        results.append({
            "src": src, "dst": dst, "path": path,
            "fidelity": e2e_fidelity, "delivered": delivered,
        })

    return results
