"""Performance metrics tracking."""

from dataclasses import dataclass, field


@dataclass
class SimMetrics:
    """Accumulates per-time-step results."""

    # Per time step: list of delivered fidelities
    deliveries_per_step: list[list[float]] = field(default_factory=list)

    def record_step(self, results: list[dict]):
        """Record results from one time step."""
        delivered = [r["fidelity"] for r in results if r["delivered"]]
        self.deliveries_per_step.append(delivered)

    @property
    def total_steps(self) -> int:
        return len(self.deliveries_per_step)

    def entanglement_rate(self) -> float:
        """Average EPR pairs delivered per time step (above f_min)."""
        if not self.deliveries_per_step:
            return 0.0
        total = sum(len(d) for d in self.deliveries_per_step)
        return total / len(self.deliveries_per_step)

    def average_fidelity(self) -> float:
        """Average fidelity of all delivered pairs."""
        all_f = [f for step in self.deliveries_per_step for f in step]
        if not all_f:
            return 0.0
        return sum(all_f) / len(all_f)

    def summary(self) -> dict:
        return {
            "total_steps": self.total_steps,
            "entanglement_rate": self.entanglement_rate(),
            "average_fidelity": self.average_fidelity(),
            "total_delivered": sum(len(d) for d in self.deliveries_per_step),
        }