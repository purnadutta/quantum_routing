"""Tests for quantum_routing.simulation (end-to-end integration)."""

import random
import pytest
from quantum_routing.utils.config import SimConfig
from quantum_routing.topologies.nsfnet import build_nsfnet
from quantum_routing.simulation import run_simulation


class TestSimulationIntegration:
    """End-to-end simulation tests on NSFNET."""

    def test_simulation_runs_without_error(self):
        """Basic smoke test: simulation completes without crashing."""
        config = SimConfig(
            num_time_steps=5,
            p_gen_base=1.0,
            decoherence_mode="cutoff",
            t_cutoff=5,
            q_swap=1.0,
            f_init=0.95,
            f_min=0.80,
            user_pairs=[("WA", "DC")],
            algorithm="greedy",
        )
        random.seed(42)
        net = build_nsfnet(config)
        metrics = run_simulation(net)

        assert metrics.total_steps == 5
        summary = metrics.summary()
        assert summary["total_steps"] == 5

    def test_simulation_multiple_pairs(self):
        """Simulation with multiple user pairs."""
        config = SimConfig(
            num_time_steps=10,
            p_gen_base=1.0,
            decoherence_mode="cutoff",
            t_cutoff=10,
            q_swap=1.0,
            f_init=0.95,
            f_min=0.80,
            user_pairs=[("WA", "DC"), ("CA1", "NY"), ("TX", "MI")],
            algorithm="greedy",
        )
        random.seed(42)
        net = build_nsfnet(config)
        metrics = run_simulation(net)
        assert metrics.total_steps == 10

    def test_no_user_pairs_no_deliveries(self):
        """With no user pairs, nothing should be delivered."""
        config = SimConfig(
            num_time_steps=5,
            user_pairs=[],
            algorithm="greedy",
        )
        random.seed(42)
        net = build_nsfnet(config)
        metrics = run_simulation(net)
        assert metrics.entanglement_rate() == 0.0

    def test_short_edges_produce_deliveries(self):
        """Short-range pairs on NSFNET with scaled distances should produce deliveries."""
        config = SimConfig(
            num_time_steps=20,
            p_gen_base=1.0,
            decoherence_mode="cutoff",
            t_cutoff=10,
            q_swap=1.0,
            f_init=0.95,
            f_min=0.50,  # lenient threshold
            distance_scale=30,  # scale down continental distances
            user_pairs=[("NJ", "DC")],  # short path: NJ -> DC
            algorithm="greedy",
        )
        random.seed(42)
        net = build_nsfnet(config)
        metrics = run_simulation(net)
        # With 1-hop path and high gen prob, should deliver often
        assert metrics.entanglement_rate() > 0

    def test_invalid_algorithm_raises(self):
        """Unknown algorithm name should raise NotImplementedError."""
        config = SimConfig(
            num_time_steps=1,
            user_pairs=[("WA", "DC")],
            algorithm="unknown_algo",
        )
        net = build_nsfnet(config)
        with pytest.raises(NotImplementedError):
            run_simulation(net)
