"""Main simulation loop."""

from quantum_routing.network import QuantumNetwork
from quantum_routing.metrics import SimMetrics
from quantum_routing.algorithms.greedy_shortest_path import greedy_route
from quantum_routing.algorithms.multi_commodity_flow import mcf_route

ALGORITHMS = {
    "greedy": greedy_route,
    "mcf": mcf_route,
}


def run_simulation(network: QuantumNetwork) -> SimMetrics:
    """Run the full simulation for config.num_time_steps."""
    config = network.config
    metrics = SimMetrics()

    route_fn = ALGORITHMS.get(config.algorithm)
    if route_fn is None:
        raise NotImplementedError(f"Algorithm '{config.algorithm}' not yet implemented")

    for t in range(config.num_time_steps):
        # Step 1: Generate new entangled links
        network.generate_links()

        # Step 2: Decohere / age existing links
        network.decohere_links()

        # Step 3-4: Route and swap
        results = route_fn(network)

        # Record metrics
        metrics.record_step(results)

    return metrics