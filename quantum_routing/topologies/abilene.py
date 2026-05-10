"""Abilene (Internet2) topology — 11-node US research backbone.

The Abilene network was the Internet2 backbone connecting major US cities.
Standard 11-node, 14-edge topology widely used in networking research.

References:
  - Internet2 / Abilene Observatory
  - Internet Topology Zoo
"""

from quantum_routing.network import QuantumNetwork
from quantum_routing.utils.config import SimConfig

# Node positions (city, latitude, longitude)
ABILENE_NODES = {
    "SEA": ("Seattle, WA", 47.61, -122.33),
    "SNV": ("Sunnyvale, CA", 37.39, -122.03),
    "LAX": ("Los Angeles, CA", 34.05, -118.24),
    "DEN": ("Denver, CO", 39.74, -104.98),
    "KSC": ("Kansas City, MO", 39.10, -94.58),
    "HOU": ("Houston, TX", 29.76, -95.37),
    "CHI": ("Chicago, IL", 41.88, -87.63),
    "IPL": ("Indianapolis, IN", 39.77, -86.16),
    "ATL": ("Atlanta, GA", 33.75, -84.39),
    "WAS": ("Washington, DC", 38.91, -77.04),
    "NYC": ("New York, NY", 40.71, -74.01),
}

# Edges with approximate fiber distances in km
ABILENE_EDGES = [
    ("SEA", "SNV", 1300),
    ("SNV", "LAX", 570),
    ("SNV", "DEN", 1600),
    ("LAX", "HOU", 2300),
    ("DEN", "KSC", 900),
    ("KSC", "HOU", 1060),
    ("KSC", "IPL", 720),
    ("HOU", "ATL", 1150),
    ("CHI", "IPL", 290),
    ("CHI", "NYC", 1150),
    ("IPL", "ATL", 690),
    ("ATL", "WAS", 870),
    ("WAS", "NYC", 340),
    ("SEA", "DEN", 2100),
]


def build_abilene(config: SimConfig) -> QuantumNetwork:
    """Construct the Abilene (Internet2) topology."""
    net = QuantumNetwork(config)
    for node_id, (city, lat, lon) in ABILENE_NODES.items():
        net.add_node(node_id, city=city, lat=lat, lon=lon)
    for u, v, dist in ABILENE_EDGES:
        net.add_edge(u, v, length_km=dist)
    return net
