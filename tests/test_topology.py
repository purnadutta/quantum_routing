"""Tests for quantum_routing.topologies module."""

import pytest
from quantum_routing.utils.config import SimConfig
from quantum_routing.topologies.nsfnet import build_nsfnet, NSFNET_NODES, NSFNET_EDGES
from quantum_routing.topologies.surfnet import build_surfnet, SURFNET_NODES, SURFNET_EDGES


@pytest.fixture
def config():
    return SimConfig()


class TestNSFNET:
    """Tests for the NSFNET topology builder."""

    def test_node_count(self, config):
        net = build_nsfnet(config)
        assert len(net.graph.nodes) == 14

    def test_edge_count(self, config):
        net = build_nsfnet(config)
        assert len(net.graph.edges) == len(NSFNET_EDGES)

    def test_all_nodes_present(self, config):
        net = build_nsfnet(config)
        for node_id in NSFNET_NODES:
            assert node_id in net.graph.nodes

    def test_edges_have_length(self, config):
        net = build_nsfnet(config)
        for u, v, data in net.graph.edges(data=True):
            assert "length_km" in data
            assert data["length_km"] > 0

    def test_node_attributes(self, config):
        net = build_nsfnet(config)
        for node_id, attrs in net.graph.nodes(data=True):
            assert "city" in attrs
            assert "lat" in attrs
            assert "lon" in attrs

    def test_link_state_initialized(self, config):
        """Every edge should have an empty link state list."""
        net = build_nsfnet(config)
        assert len(net.link_state) == len(NSFNET_EDGES)
        for links in net.link_state.values():
            assert links == []

    def test_graph_connected(self, config):
        """NSFNET should be a connected graph."""
        import networkx as nx
        net = build_nsfnet(config)
        assert nx.is_connected(net.graph)

    def test_realistic_distances(self, config):
        """Edge distances should be in a realistic range (100-2000 km for US)."""
        net = build_nsfnet(config)
        for u, v, data in net.graph.edges(data=True):
            assert 100 <= data["length_km"] <= 2000, (
                f"Edge {u}-{v} has unrealistic distance {data['length_km']} km"
            )


class TestSURFnet:
    """Tests for the pruned SURFnet topology (17-node)."""

    def test_node_count(self, config):
        net = build_surfnet(config)
        assert len(net.graph.nodes) == 17

    def test_edge_count(self, config):
        net = build_surfnet(config)
        assert len(net.graph.edges) == len(SURFNET_EDGES)

    def test_all_nodes_present(self, config):
        net = build_surfnet(config)
        for node_id in SURFNET_NODES:
            assert node_id in net.graph.nodes

    def test_edges_have_length(self, config):
        net = build_surfnet(config)
        for u, v, data in net.graph.edges(data=True):
            assert "length_km" in data
            assert data["length_km"] > 0

    def test_graph_connected(self, config):
        """SURFnet should be a connected graph."""
        import networkx as nx
        net = build_surfnet(config)
        assert nx.is_connected(net.graph)

    def test_realistic_distances(self, config):
        """Edge distances should be in Netherlands range (10-80 km)."""
        net = build_surfnet(config)
        for u, v, data in net.graph.edges(data=True):
            assert 10 <= data["length_km"] <= 80, (
                f"Edge {u}-{v} has distance {data['length_km']} km"
            )
