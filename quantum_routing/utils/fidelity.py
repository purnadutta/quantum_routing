"""Fidelity helpers for entanglement swapping and decoherence."""

import math


def transmissivity(length_km: float, L_att: float = 22.0) -> float:
    """Link generation probability from fiber length: eta = exp(-L / L_att)."""
    return math.exp(-length_km / L_att)


def swap_fidelity(f1: float, f2: float) -> float:
    """Fidelity after entanglement swapping two links with fidelities f1, f2.

    Standard depolarizing model:
        F_out = f1 * f2 + (1 - f1)(1 - f2) / 3
    """
    return f1 * f2 + (1 - f1) * (1 - f2) / 3


def path_fidelity(fidelities: list[float]) -> float:
    """End-to-end fidelity after swapping along a chain of links."""
    if not fidelities:
        return 0.0
    result = fidelities[0]
    for f in fidelities[1:]:
        result = swap_fidelity(result, f)
    return result


def fidelity_weight(f: float) -> float:
    """Edge weight for shortest-path: -log(f). Lower is better."""
    if f <= 0:
        return float("inf")
    return -math.log(f)