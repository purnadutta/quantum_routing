"""Tests for quantum_routing.metrics module."""

import pytest
from quantum_routing.metrics import SimMetrics


class TestSimMetrics:
    """Tests for the SimMetrics accumulator."""

    def test_empty_metrics(self):
        m = SimMetrics()
        assert m.total_steps == 0
        assert m.entanglement_rate() == 0.0
        assert m.average_fidelity() == 0.0

    def test_record_single_step_with_deliveries(self):
        m = SimMetrics()
        results = [
            {"fidelity": 0.90, "delivered": True},
            {"fidelity": 0.85, "delivered": True},
            {"fidelity": 0.0, "delivered": False},
        ]
        m.record_step(results)
        assert m.total_steps == 1
        assert len(m.deliveries_per_step[0]) == 2  # only delivered ones

    def test_entanglement_rate(self):
        m = SimMetrics()
        # Step 1: 2 deliveries
        m.record_step([
            {"fidelity": 0.90, "delivered": True},
            {"fidelity": 0.85, "delivered": True},
        ])
        # Step 2: 1 delivery
        m.record_step([
            {"fidelity": 0.92, "delivered": True},
            {"fidelity": 0.0, "delivered": False},
        ])
        # Rate = (2 + 1) / 2 = 1.5
        assert m.entanglement_rate() == pytest.approx(1.5)

    def test_average_fidelity(self):
        m = SimMetrics()
        m.record_step([
            {"fidelity": 0.90, "delivered": True},
            {"fidelity": 0.80, "delivered": True},
        ])
        assert m.average_fidelity() == pytest.approx(0.85)

    def test_average_fidelity_excludes_undelivered(self):
        m = SimMetrics()
        m.record_step([
            {"fidelity": 0.90, "delivered": True},
            {"fidelity": 0.0, "delivered": False},
        ])
        # Only the delivered pair counts
        assert m.average_fidelity() == pytest.approx(0.90)

    def test_summary_dict(self):
        m = SimMetrics()
        m.record_step([{"fidelity": 0.90, "delivered": True}])
        m.record_step([{"fidelity": 0.85, "delivered": True}])
        s = m.summary()
        assert s["total_steps"] == 2
        assert s["total_delivered"] == 2
        assert s["entanglement_rate"] == pytest.approx(1.0)
        assert s["average_fidelity"] == pytest.approx(0.875)

    def test_no_deliveries_at_all(self):
        m = SimMetrics()
        m.record_step([{"fidelity": 0.0, "delivered": False}])
        m.record_step([{"fidelity": 0.0, "delivered": False}])
        assert m.entanglement_rate() == 0.0
        assert m.average_fidelity() == 0.0
