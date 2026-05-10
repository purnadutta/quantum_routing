from quantum_routing.topologies.nsfnet import build_nsfnet
from quantum_routing.topologies.surfnet import build_surfnet
from quantum_routing.topologies.abilene import build_abilene

TOPOLOGIES = {
    "nsfnet": build_nsfnet,
    "surfnet": build_surfnet,
    "abilene": build_abilene,
}
