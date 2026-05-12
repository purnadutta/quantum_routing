"""SURFnet (pruned) topology — Dutch research network.

Pruned to 17 core nodes following the approach of Vardoyan et al.,
"On the Bipartite Entanglement Capacity of Quantum Networks" (IEEE TQE
2024, Fig. 13).  Co-located PoPs are merged into single city nodes and
degree-2 pass-through sites are removed, preserving the core ring-and-
spur structure.

Fiber distances (km) are taken from the SURFnet Core fibre-route data
published by Pouryousef et al. in the companion repository
  https://github.com/pooryousefshahrooz/q_net_planning
(file ``data/SurfnetCore.gml``).

Node coordinates are real geographic positions from the same dataset.

References:
  - Vardoyan et al., "On the Bipartite Entanglement Capacity of Quantum
    Networks," IEEE TQE 2024 (arXiv:2307.04477).
  - Pouryousef et al., "Resource Placement for Rate and Fidelity
    Maximization in Quantum Networks," IEEE TQE 2024 (arXiv:2308.16264).
  - Internet Topology Zoo — SURFnet (topology-zoo.org).
"""

from quantum_routing.network import QuantumNetwork
from quantum_routing.utils.config import SimConfig

# Node positions (city, latitude, longitude)
# Coordinates from SURFnet fibre-route dataset.
SURFNET_NODES = {
    "ALM": ("Almere", 52.3745, 5.2123),
    "AMF": ("Amersfoort", 52.1537, 5.3842),
    "AMS": ("Amsterdam", 52.3710, 4.9001),
    "APD": ("Apeldoorn", 52.2157, 5.9639),
    "ARN": ("Arnhem", 51.9847, 5.9117),
    "DEL": ("Delft", 52.0114, 4.3584),
    "DEV": ("Deventer", 52.2602, 6.1555),
    "ENS": ("Enschede", 52.2179, 6.8936),
    "HIL": ("Hilversum", 52.2179, 5.1831),
    "LEI": ("Leiden", 52.1600, 4.4822),
    "LEL": ("Lelystad", 52.5151, 5.4769),
    "NIJ": ("Nijmegen", 51.8420, 5.8613),
    "RTM": ("Rotterdam", 51.9227, 4.4628),
    "UTR": ("Utrecht", 52.0959, 5.1104),
    "WAG": ("Wageningen", 51.9751, 5.6632),
    "ZUT": ("Zutphen", 52.1434, 6.2061),
    "ZWO": ("Zwolle", 52.5090, 6.0944),
}

# Edges with real fiber distances in km from SurfnetCore.gml.
# Each entry is (node_a, node_b, fibre_distance_km).
# These are the direct core-fibre connections between the 17 pruned
# cities; intermediate pass-through sites have been collapsed.
SURFNET_EDGES = [
    # West / Amsterdam cluster
    ("AMS", "ALM", 38.9),
    ("AMS", "HIL", 30.2),
    ("AMS", "LEI", 53.7),
    ("AMS", "LEL", 64.5),
    ("AMS", "UTR", 45.6),
    ("ALM", "HIL", 35.4),
    ("ALM", "LEL", 44.2),
    # Leiden / Delft / Rotterdam
    ("LEI", "DEL", 30.6),
    ("DEL", "RTM", 14.6),
    ("RTM", "UTR", 68.2),
    # Central
    ("HIL", "UTR", 36.7),
    ("UTR", "AMF", 33.8),
    ("AMF", "WAG", 61.5),
    # North-south spine
    ("LEL", "ZWO", 47.4),
    ("ZWO", "DEV", 44.7),
    ("ZWO", "ENS", 77.7),
    # East cluster
    ("DEV", "APD", 24.4),
    ("APD", "ARN", 45.3),
    ("ARN", "NIJ", 25.7),
    ("NIJ", "ZUT", 58.1),
    ("NIJ", "WAG", 66.1),
    ("ZUT", "ENS", 60.0),
]


def build_surfnet(config: SimConfig) -> QuantumNetwork:
    """Construct the pruned SURFnet topology (17 nodes, 22 edges)."""
    net = QuantumNetwork(config)
    for node_id, (city, lat, lon) in SURFNET_NODES.items():
        net.add_node(node_id, city=city, lat=lat, lon=lon)
    for u, v, dist in SURFNET_EDGES:
        net.add_edge(u, v, length_km=dist)
    return net
