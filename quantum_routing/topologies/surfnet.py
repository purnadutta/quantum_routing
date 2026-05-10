"""SURFnet (pruned) topology — Dutch research network.

Based on the SURFnet core network topology used in quantum networking
literature (Pouryousef et al., Vardoyan et al.).  Pruned to 8 core nodes
with approximate geographic fiber distances in km.

References:
  - Internet Topology Zoo (SURFnet)
  - Pouryousef et al., "Resource Placement for Rate and Fidelity
    Maximization in Quantum Networks," IEEE TQE 2024.
"""

from quantum_routing.network import QuantumNetwork
from quantum_routing.utils.config import SimConfig

# Node positions (city, latitude, longitude)
SURFNET_NODES = {
    "AMS": ("Amsterdam", 52.37, 4.90),
    "HAG": ("The Hague", 52.08, 4.31),
    "DEL": ("Delft", 52.01, 4.36),
    "LEI": ("Leiden", 52.16, 4.49),
    "UTR": ("Utrecht", 52.09, 5.12),
    "EIN": ("Eindhoven", 51.44, 5.47),
    "GRO": ("Groningen", 53.22, 6.57),
    "ENS": ("Enschede", 52.22, 6.90),
}

# Edges with approximate fiber distances in km
# Fiber paths follow roads/rail, so distances are ~1.3-1.5x straight-line.
SURFNET_EDGES = [
    ("AMS", "LEI", 45),
    ("AMS", "UTR", 50),
    ("AMS", "GRO", 200),
    ("LEI", "HAG", 25),
    ("LEI", "DEL", 20),
    ("HAG", "DEL", 15),
    ("UTR", "EIN", 100),
    ("UTR", "ENS", 160),
    ("GRO", "ENS", 150),
    ("EIN", "ENS", 170),
]


def build_surfnet(config: SimConfig) -> QuantumNetwork:
    """Construct the pruned SURFnet topology."""
    net = QuantumNetwork(config)
    for node_id, (city, lat, lon) in SURFNET_NODES.items():
        net.add_node(node_id, city=city, lat=lat, lon=lon)
    for u, v, dist in SURFNET_EDGES:
        net.add_edge(u, v, length_km=dist)
    return net
