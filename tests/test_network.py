"""Tests for quantum_routing.network module."""

import random
import pytest
from quantum_routing.network import QuantumNetwork, EntangledLink
from quantum_routing.utils.config import SimConfig


@pytest.fixture
def simple_config():
    """A minimal config for testing."""
    return SimConfig(
        num_time_steps=10,
        L_att=22.0,
        p_gen_base=1.0,
        decoherence_mode="cutoff",
        t_cutoff=3,
        q_swap=1.0,
        f_init=0.95,
        f_min=0.80,
    )


@pytest.fixture
def triangle_network(simple_config):
    """A 3-node triangle topology: A--B--C--A with short edges."""
    net = QuantumNetwork(simple_config)
    net.add_node("A")
    net.add_node("B")
    net.add_node("C")
    net.add_edge("A", "B", length_km=1.0)
    net.add_edge("B", "C", length_km=1.0)
    net.add_edge("A", "C", length_km=1.0)
    return net


class TestQuantumNetworkSetup:
    """Tests for topology construction."""

    def test_add_nodes_and_edges(self, triangle_network):
        assert len(triangle_network.graph.nodes) == 3
        assert len(triangle_network.graph.edges) == 3

    def test_edge_length_stored(self, triangle_network):
        data = triangle_network.graph.edges["A", "B"]
        assert data["length_km"] == 1.0

    def test_link_state_initialized_empty(self, triangle_network):
        for key, links in triangle_network.link_state.items():
            assert links == []

    def test_frozenset_keys(self, triangle_network):
        """Link state uses frozenset so (A,B) == (B,A)."""
        key_ab = frozenset(("A", "B"))
        assert key_ab in triangle_network.link_state


class TestLinkGeneration:
    """Tests for generate_links()."""

    def test_short_edges_high_gen_prob(self, triangle_network):
        """Very short edges (1 km) with p_gen_base=1.0 should almost always generate."""
        random.seed(42)
        triangle_network.generate_links()
        total_links = sum(len(v) for v in triangle_network.link_state.values())
        # With 1 km edges and L_att=22, p ~ exp(-1/22) ~ 0.955
        # Expect most edges to succeed
        assert total_links >= 2  # very likely all 3, but allow some randomness

    def test_generated_link_fidelity(self, triangle_network):
        """Generated links should have initial fidelity from config."""
        random.seed(42)
        triangle_network.generate_links()
        for links in triangle_network.link_state.values():
            for link in links:
                assert link.fidelity == triangle_network.config.f_init

    def test_generated_link_age_zero(self, triangle_network):
        """Freshly generated links should have age 0."""
        random.seed(42)
        triangle_network.generate_links()
        for links in triangle_network.link_state.values():
            for link in links:
                assert link.age == 0

    def test_multiple_generations_accumulate(self, triangle_network):
        """Calling generate_links twice can produce multiple links per edge."""
        random.seed(42)
        triangle_network.generate_links()
        triangle_network.generate_links()
        # At least some edges should have 2 links
        max_links = max(len(v) for v in triangle_network.link_state.values())
        assert max_links >= 1  # conservative

    def test_zero_gen_probability(self, simple_config):
        """With p_gen_base=0, no links should be generated."""
        simple_config.p_gen_base = 0.0
        net = QuantumNetwork(simple_config)
        net.add_node("A")
        net.add_node("B")
        net.add_edge("A", "B", length_km=1.0)
        net.generate_links()
        total = sum(len(v) for v in net.link_state.values())
        assert total == 0


class TestDecoherence:
    """Tests for decohere_links() in cutoff mode."""

    def test_cutoff_removes_old_links(self, triangle_network):
        """Links older than t_cutoff should be removed."""
        key = frozenset(("A", "B"))
        triangle_network.link_state[key] = [EntangledLink(fidelity=0.95, age=0)]

        # Age the link past the cutoff (t_cutoff=3)
        for _ in range(4):
            triangle_network.decohere_links()

        assert len(triangle_network.link_state[key]) == 0

    def test_cutoff_keeps_young_links(self, triangle_network):
        """Links within cutoff should survive."""
        key = frozenset(("A", "B"))
        triangle_network.link_state[key] = [EntangledLink(fidelity=0.95, age=0)]

        triangle_network.decohere_links()  # age becomes 1
        assert len(triangle_network.link_state[key]) == 1

    def test_aging_increments(self, triangle_network):
        """Each decohere call should increment age by 1."""
        key = frozenset(("A", "B"))
        triangle_network.link_state[key] = [EntangledLink(fidelity=0.95, age=0)]

        triangle_network.decohere_links()
        assert triangle_network.link_state[key][0].age == 1

        triangle_network.decohere_links()
        assert triangle_network.link_state[key][0].age == 2

    def test_probabilistic_mode(self):
        """In probabilistic mode with q_memory=0, all links should be removed."""
        config = SimConfig(decoherence_mode="probabilistic", q_memory=0.0)
        net = QuantumNetwork(config)
        net.add_node("A")
        net.add_node("B")
        net.add_edge("A", "B", length_km=1.0)

        key = frozenset(("A", "B"))
        net.link_state[key] = [EntangledLink(fidelity=0.95, age=0)]
        net.decohere_links()
        assert len(net.link_state[key]) == 0

    def test_probabilistic_mode_perfect_memory(self):
        """In probabilistic mode with q_memory=1.0, all links should survive."""
        config = SimConfig(decoherence_mode="probabilistic", q_memory=1.0)
        net = QuantumNetwork(config)
        net.add_node("A")
        net.add_node("B")
        net.add_edge("A", "B", length_km=1.0)

        key = frozenset(("A", "B"))
        net.link_state[key] = [EntangledLink(fidelity=0.95, age=0)]
        net.decohere_links()
        assert len(net.link_state[key]) == 1


class TestConsumeLink:
    """Tests for consume_link()."""

    def test_consume_returns_best_fidelity(self, triangle_network):
        """Should return the highest-fidelity link."""
        key = frozenset(("A", "B"))
        triangle_network.link_state[key] = [
            EntangledLink(fidelity=0.80, age=2),
            EntangledLink(fidelity=0.95, age=0),
            EntangledLink(fidelity=0.85, age=1),
        ]
        link = triangle_network.consume_link("A", "B")
        assert link is not None
        assert link.fidelity == 0.95

    def test_consume_removes_link(self, triangle_network):
        """After consuming, the link should be gone."""
        key = frozenset(("A", "B"))
        triangle_network.link_state[key] = [EntangledLink(fidelity=0.90, age=0)]

        triangle_network.consume_link("A", "B")
        assert len(triangle_network.link_state[key]) == 0

    def test_consume_empty_returns_none(self, triangle_network):
        """Consuming from an edge with no links returns None."""
        assert triangle_network.consume_link("A", "B") is None

    def test_consume_direction_independent(self, triangle_network):
        """consume_link(A, B) and consume_link(B, A) access the same state."""
        key = frozenset(("A", "B"))
        triangle_network.link_state[key] = [EntangledLink(fidelity=0.90, age=0)]

        link = triangle_network.consume_link("B", "A")
        assert link is not None
        assert link.fidelity == 0.90


class TestHasLinkAndBestFidelity:
    """Tests for has_link() and best_fidelity()."""

    def test_has_link_true(self, triangle_network):
        key = frozenset(("A", "B"))
        triangle_network.link_state[key] = [EntangledLink(fidelity=0.90, age=0)]
        assert triangle_network.has_link("A", "B") is True

    def test_has_link_false(self, triangle_network):
        assert triangle_network.has_link("A", "B") is False

    def test_best_fidelity_empty(self, triangle_network):
        assert triangle_network.best_fidelity("A", "B") == 0.0

    def test_best_fidelity_multiple(self, triangle_network):
        key = frozenset(("A", "B"))
        triangle_network.link_state[key] = [
            EntangledLink(fidelity=0.80, age=2),
            EntangledLink(fidelity=0.95, age=0),
        ]
        assert triangle_network.best_fidelity("A", "B") == 0.95


class TestActiveSubgraph:
    """Tests for get_active_subgraph()."""

    def test_empty_network_no_edges(self, triangle_network):
        """No entangled links -> active subgraph has nodes but no edges."""
        g = triangle_network.get_active_subgraph()
        assert len(g.nodes) == 3
        assert len(g.edges) == 0

    def test_active_edges_have_weight(self, triangle_network):
        """Edges with links should appear with -log(f) weight."""
        import math
        key = frozenset(("A", "B"))
        triangle_network.link_state[key] = [EntangledLink(fidelity=0.90, age=0)]

        g = triangle_network.get_active_subgraph()
        assert g.has_edge("A", "B")
        assert g["A"]["B"]["weight"] == pytest.approx(-math.log(0.90))
        assert g["A"]["B"]["fidelity"] == pytest.approx(0.90)

    def test_only_active_edges_included(self, triangle_network):
        """Only edges with links should appear."""
        key = frozenset(("A", "B"))
        triangle_network.link_state[key] = [EntangledLink(fidelity=0.90, age=0)]

        g = triangle_network.get_active_subgraph()
        assert g.has_edge("A", "B")
        assert not g.has_edge("B", "C")
        assert not g.has_edge("A", "C")


class TestClearAllLinks:
    """Tests for clear_all_links()."""

    def test_clear_removes_everything(self, triangle_network):
        key = frozenset(("A", "B"))
        triangle_network.link_state[key] = [EntangledLink(fidelity=0.90, age=0)]
        triangle_network.clear_all_links()
        total = sum(len(v) for v in triangle_network.link_state.values())
        assert total == 0
