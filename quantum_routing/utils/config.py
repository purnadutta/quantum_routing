"""Default simulation parameters."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SimConfig:
    # Time
    num_time_steps: int = 100

    # Link generation
    L_att: float = 22.0  # attenuation length in km
    p_gen_base: float = 1.0  # base generation probability (scaled by transmissivity)

    # Decoherence mode: "probabilistic" or "cutoff"
    decoherence_mode: str = "cutoff"
    q_memory: float = 0.95  # survival prob per time step (probabilistic mode)
    t_cutoff: int = 10  # max age in time steps before link is discarded (cutoff mode)

    # Swapping
    q_swap: float = 1.0  # swap success probability (1.0 = deterministic)

    # Fidelity
    f_init: float = 1.0  # fidelity of freshly generated Bell pair
    f_min: float = 0.80  # minimum acceptable fidelity for delivery

    # User pairs (list of (src, dst) tuples, set at runtime)
    user_pairs: list = field(default_factory=list)

    # Routing algorithm: "greedy" or "mcf"
    algorithm: str = "greedy"