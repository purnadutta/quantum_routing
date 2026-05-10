"""Tests for quantum_routing.algorithms.greedy_shortest_path module."""

import random
import pytest
from quantum_routing.network import QuantumNetwork, EntangledLink
from quantum_routing.utils.config import SimConfig
from quantum_routing.algorithms.greedy_shortest_path import greedy_route


@pytest.fixture
def config():
    return SimConfig(
        num_time_steps=10,
        L_att=22.0,
        p_gen_base=1.0,
        decoherence_mode="cutoff",
        t_cutoff=10,
        q_swap=1.0,
        f_init=0.95,
        f_min=0.80,
        user_pairs=[("A", "C")],
    )


def _build_line_network(config, fidelities=None):
    """Build A--B--C linear network with pre-loaded entangled links."""
    if fidelities is None:
        fidelities = {"AB": 0.95, "BC": 0.95}

    net = QuantumNetwork(config)
    for node in ["A", "B", "C"]:
        net.add_node(node)
    net.add_edge("A", "B", length_km=1.0)
    net.add_edge("B", "C", length_km=1.0)

    # Pre-load entangled links
    if fidelities.get("AB"):
        net.link_state[frozenset(("A", "B"))] = [
            EntangledLink(fidelity=fidelities["AB"], age=0)
        ]
    if fidelities.get("BC"):
        net.link_state[frozenset(("B", "C"))] = [
            EntangledLink(fidelity=fidelities["BC"], age=0)
        ]
    return net


class TestGreedyBasicRouting:
    """Basic routing scenarios."""

    def test_successful_delivery(self, config):
        """A--B--C with good links should deliver."""
        net = _build_line_network(config)
        results = greedy_route(net)
        assert len(results) == 1
        r = results[0]
        assert r["delivered"] is True
        assert r["path"] == ["A", "B", "C"]
        assert r["fidelity"] > 0

    def test_no_path_available(self, config):
        """If no links exist, delivery should fail."""
        net = _build_line_network(config, fidelities={"AB": None, "BC": None})
        # Clear the pre-loaded links
        for key in net.link_state:
            net.link_state[key] = []
        results = greedy_route(net)
        assert len(results) == 1
        assert results[0]["delivered"] is False

    def test_partial_path_fails(self, config):
        """If only one hop has a link, the path can't be completed."""
        net = _build_line_network(config, fidelities={"AB": 0.95, "BC": None})
        net.link_state[frozenset(("B", "C"))] = []
        results = greedy_route(net)
        assert results[0]["delivered"] is False

    def test_fidelity_below_threshold(self, config):
        """Delivery fails if end-to-end fidelity < f_min."""
        config.f_min = 0.99  # Very strict threshold
        net = _build_line_network(config, fidelities={"AB": 0.90, "BC": 0.85})
        results = greedy_route(net)
        # End-to-end fidelity will be < 0.99
        assert results[0]["delivered"] is False


class TestGreedyMultipleUsers:
    """Tests with multiple user pairs competing for links."""

    def test_two_pairs_enough_links(self, config):
        """Two pairs with independent paths should both succeed."""
        config.user_pairs = [("A", "B"), ("B", "C")]

        net = QuantumNetwork(config)
        for node in ["A", "B", "C"]:
            net.add_node(node)
        net.add_edge("A", "B", length_km=1.0)
        net.add_edge("B", "C", length_km=1.0)

        net.link_state[frozenset(("A", "B"))] = [
            EntangledLink(fidelity=0.95, age=0)
        ]
        net.link_state[frozenset(("B", "C"))] = [
            EntangledLink(fidelity=0.95, age=0)
        ]

        results = greedy_route(net)
        assert len(results) == 2
        assert all(r["delivered"] for r in results)

    def test_competing_pairs_first_wins(self, config):
        """Two pairs sharing an edge: first pair gets priority."""
        config.user_pairs = [("A", "C"), ("A", "C")]

        net = _build_line_network(config)
        results = greedy_route(net)

        assert len(results) == 2
        # First pair should succeed, second should fail (links consumed)
        assert results[0]["delivered"] is True
        assert results[1]["delivered"] is False

    def test_link_consumption_prevents_reuse(self, config):
        """Once links are consumed by pair 1, pair 2 can't use them."""
        config.user_pairs = [("A", "C"), ("A", "C")]

        net = _build_line_network(config)
        greedy_route(net)

        # After routing, links on A-B and B-C should be consumed
        assert not net.has_link("A", "B")
        assert not net.has_link("B", "C")


class TestGreedyFidelityComputation:
    """Tests that fidelity is correctly computed along paths."""

    def test_single_hop_fidelity(self, config):
        """Single-hop path: end-to-end fidelity = link fidelity."""
        config.user_pairs = [("A", "B")]
        net = _build_line_network(config, fidelities={"AB": 0.92, "BC": 0.95})
        results = greedy_route(net)
        assert results[0]["fidelity"] == pytest.approx(0.92)

    def test_two_hop_fidelity(self, config):
        """Two-hop path: fidelity should follow the swap formula."""
        from quantum_routing.utils.fidelity import swap_fidelity

        net = _build_line_network(config, fidelities={"AB": 0.95, "BC": 0.90})
        results = greedy_route(net)
        expected = swap_fidelity(0.95, 0.90)
        assert results[0]["fidelity"] == pytest.approx(expected)

    def test_picks_highest_fidelity_link(self, config):
        """When multiple links exist on an edge, the best one is used."""
        config.user_pairs = [("A", "B")]

        net = QuantumNetwork(config)
        net.add_node("A")
        net.add_node("B")
        net.add_edge("A", "B", length_km=1.0)

        net.link_state[frozenset(("A", "B"))] = [
            EntangledLink(fidelity=0.80, age=2),
            EntangledLink(fidelity=0.95, age=0),
            EntangledLink(fidelity=0.85, age=1),
        ]

        results = greedy_route(net)
        assert results[0]["fidelity"] == pytest.approx(0.95)


class TestGreedyWithSwapFailure:
    """Tests with probabilistic swapping (qswap < 1)."""

    def test_deterministic_swap_always_succeeds(self, config):
        """With q_swap=1.0, swaps always succeed."""
        config.q_swap = 1.0
        net = _build_line_network(config)
        random.seed(42)
        results = greedy_route(net)
        assert results[0]["delivered"] is True

    def test_zero_swap_prob_always_fails(self, config):
        """With q_swap=0.0, multi-hop paths always fail."""
        config.q_swap = 0.0
        net = _build_line_network(config)
        random.seed(42)
        results = greedy_route(net)
        # A->C is 2 hops, needs 1 swap at B, which fails
        assert results[0]["delivered"] is False
        assert results[0]["fidelity"] == 0.0
