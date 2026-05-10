"""NSFNET 14-node topology with approximate geographic distances (km)."""

from quantum_routing.network import QuantumNetwork
from quantum_routing.utils.config import SimConfig

# Node positions (approximate US city coordinates)
NSFNET_NODES = {
    "WA": ("Seattle, WA", 47.61, -122.33),
    "CA1": ("Palo Alto, CA", 37.44, -122.14),
    "CA2": ("San Diego, CA", 32.72, -117.16),
    "UT": ("Salt Lake City, UT", 40.76, -111.89),
    "CO": ("Boulder, CO", 40.01, -105.27),
    "TX": ("Houston, TX", 29.76, -95.37),
    "NE": ("Lincoln, NE", 40.81, -96.70),
    "IL": ("Champaign, IL", 40.12, -88.24),
    "MI": ("Ann Arbor, MI", 42.28, -83.74),
    "PA": ("Pittsburgh, PA", 40.44, -79.99),
    "GA": ("Atlanta, GA", 33.75, -84.39),
    "NY": ("Ithaca, NY", 42.44, -76.50),
    "NJ": ("Princeton, NJ", 40.35, -74.66),
    "DC": ("College Park, MD", 38.99, -76.94),
}

# Edges with approximate distances in km
NSFNET_EDGES = [
    ("WA", "CA1", 1100),
    ("WA", "UT", 1150),
    ("CA1", "CA2", 800),
    ("CA1", "UT", 1000),
    ("CA2", "CO", 1350),
    ("UT", "CO", 600),
    ("CO", "NE", 900),
    ("CO", "TX", 1500),
    ("NE", "IL", 750),
    ("TX", "GA", 1150),
    ("IL", "MI", 400),
    ("IL", "PA", 700),
    ("MI", "NY", 800),
    ("PA", "NJ", 450),
    ("PA", "DC", 350),
    ("GA", "DC", 900),
    ("NY", "NJ", 350),
    ("NJ", "DC", 250),
    ("NE", "TX", 1100),
    ("MI", "PA", 500),
    ("GA", "PA", 950),
]


def build_nsfnet(config: SimConfig) -> QuantumNetwork:
    """Construct the NSFNET topology."""
    net = QuantumNetwork(config)
    for node_id, (city, lat, lon) in NSFNET_NODES.items():
        net.add_node(node_id, city=city, lat=lat, lon=lon)
    for u, v, dist in NSFNET_EDGES:
        net.add_edge(u, v, length_km=dist)
    return net