"""Tests for quantum_routing.algorithms.multi_commodity_flow module."""

import random
import pytest
from quantum_routing.network import QuantumNetwork, EntangledLink
from quantum_routing.utils.config import SimConfig
from quantum_routing.algorithms.multi_commodity_flow import mcf_route


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
        algorithm="mcf",
    )


def _build_line(config, fids=None):
    """A--B--C with pre-loaded links."""
    if fids is None:
        fids = {"AB": 0.95, "BC": 0.95}
    net = QuantumNetwork(config)
    for n in ["A", "B", "C"]:
        net.add_node(n)
    net.add_edge("A", "B", length_km=1.0)
    net.add_edge("B", "C", length_km=1.0)
    if fids.get("AB"):
        net.link_state[frozenset(("A", "B"))] = [EntangledLink(fidelity=fids["AB"], age=0)]
    if fids.get("BC"):
        net.link_state[frozenset(("B", "C"))] = [EntangledLink(fidelity=fids["BC"], age=0)]
    return net


def _build_diamond(config):
    """Diamond: A--B--D and A--C--D, all edges with links."""
    net = QuantumNetwork(config)
    for n in ["A", "B", "C", "D"]:
        net.add_node(n)
    net.add_edge("A", "B", length_km=1.0)
    net.add_edge("A", "C", length_km=1.0)
    net.add_edge("B", "D", length_km=1.0)
    net.add_edge("C", "D", length_km=1.0)
    for key in net.link_state:
        net.link_state[key] = [EntangledLink(fidelity=0.95, age=0)]
    return net


class TestMCFBasicRouting:

    def test_successful_delivery(self, config):
        net = _build_line(config)
        results = mcf_route(net)
        assert len(results) == 1
        assert results[0]["delivered"] is True
        assert results[0]["fidelity"] > 0

    def test_no_links_no_delivery(self, config):
        net = QuantumNetwork(config)
        for n in ["A", "B", "C"]:
            net.add_node(n)
        net.add_edge("A", "B", length_km=1.0)
        net.add_edge("B", "C", length_km=1.0)
        results = mcf_route(net)
        assert results[0]["delivered"] is False

    def test_fidelity_below_threshold(self, config):
        config.f_min = 0.99
        net = _build_line(config, fids={"AB": 0.90, "BC": 0.85})
        results = mcf_route(net)
        assert results[0]["delivered"] is False

    def test_consumes_links(self, config):
        net = _build_line(config)
        mcf_route(net)
        assert not net.has_link("A", "B")
        assert not net.has_link("B", "C")


class TestMCFMultiplePairs:

    def test_two_pairs_disjoint_paths(self, config):
        """Diamond topology: two pairs can use disjoint paths."""
        config.user_pairs = [("A", "D"), ("A", "D")]
        net = _build_diamond(config)
        # Two disjoint paths exist: A-B-D and A-C-D
        results = mcf_route(net)
        assert len(results) == 2
        # MCF should find both disjoint paths
        delivered = [r for r in results if r["delivered"]]
        assert len(delivered) == 2

    def test_competing_pairs_shared_edge(self, config):
        """Line A--B--C: two pairs wanting A->C can only get one."""
        config.user_pairs = [("A", "C"), ("A", "C")]
        net = _build_line(config)
        results = mcf_route(net)
        delivered = [r for r in results if r["delivered"]]
        assert len(delivered) == 1

    def test_mcf_beats_greedy_on_diamond(self, config):
        """MCF should find 2 disjoint paths where greedy might not."""
        from quantum_routing.algorithms.greedy_shortest_path import greedy_route

        config.user_pairs = [("A", "D"), ("A", "D")]

        # Greedy run
        net_g = _build_diamond(config)
        res_g = greedy_route(net_g)
        greedy_delivered = sum(1 for r in res_g if r["delivered"])

        # MCF run
        net_m = _build_diamond(config)
        res_m = mcf_route(net_m)
        mcf_delivered = sum(1 for r in res_m if r["delivered"])

        # MCF should do at least as well as greedy
        assert mcf_delivered >= greedy_delivered


class TestMCFWithSwapFailure:

    def test_deterministic_swap(self, config):
        config.q_swap = 1.0
        net = _build_line(config)
        results = mcf_route(net)
        assert results[0]["delivered"] is True

    def test_zero_swap_prob(self, config):
        config.q_swap = 0.0
        net = _build_line(config)
        results = mcf_route(net)
        assert results[0]["delivered"] is False


class TestMCFIntegration:

    def test_runs_in_simulation_loop(self):
        """MCF works end-to-end inside run_simulation."""
        from quantum_routing.topologies.nsfnet import build_nsfnet
        from quantum_routing.simulation import run_simulation

        config = SimConfig(
            num_time_steps=5,
            p_gen_base=1.0,
            decoherence_mode="cutoff",
            t_cutoff=5,
            q_swap=1.0,
            f_init=0.95,
            f_min=0.80,
            distance_scale=30,
            user_pairs=[("TX", "MI")],
            algorithm="mcf",
        )
        random.seed(42)
        net = build_nsfnet(config)
        metrics = run_simulation(net)
        assert metrics.total_steps == 5
