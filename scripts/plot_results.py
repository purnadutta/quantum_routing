#!/usr/bin/env python3
"""Generate plots from simulation results.

Usage:
    python scripts/plot_results.py

Produces:
    results/cutoff_sweep.png
    results/fmin_sweep.png
    results/per_pair_rates.png
"""

import random
import matplotlib.pyplot as plt
import numpy as np

from quantum_routing.utils.config import SimConfig
from quantum_routing.topologies import TOPOLOGIES
from quantum_routing.simulation import run_simulation
from quantum_routing.algorithms.greedy_shortest_path import greedy_route


USER_PAIRS = {
    "nsfnet": [("WA", "DC"), ("CA1", "NY"), ("TX", "MI")],
    "surfnet": [("AMS", "EIN"), ("DEL", "GRO"), ("HAG", "ENS")],
    "abilene": [("SEA", "NYC"), ("LAX", "CHI"), ("HOU", "WAS")],
}
SCALES = {"nsfnet": 30, "surfnet": 3, "abilene": 40}
COLORS = {"nsfnet": "#534AB7", "surfnet": "#1D9E75", "abilene": "#D85A30"}
MARKERS = {"nsfnet": "o", "surfnet": "s", "abilene": "^"}
N_STEPS = 500
SEED = 42


def run_sweep(param_name, param_values, fixed_params):
    """Run simulations sweeping one parameter, return {topo: [rates], [fids]}."""
    results = {}
    for topo in ["nsfnet", "surfnet", "abilene"]:
        rates, fids = [], []
        for val in param_values:
            kwargs = dict(fixed_params)
            kwargs[param_name] = val
            config = SimConfig(
                num_time_steps=N_STEPS,
                distance_scale=SCALES[topo],
                user_pairs=USER_PAIRS[topo],
                algorithm="greedy",
                **kwargs,
            )
            random.seed(SEED)
            net = TOPOLOGIES[topo](config)
            m = run_simulation(net)
            s = m.summary()
            rates.append(s["entanglement_rate"])
            fids.append(s["average_fidelity"])
        results[topo] = {"rates": rates, "fids": fids}
    return results


def plot_cutoff_sweep():
    """Plot entanglement rate vs cutoff time."""
    cutoffs = [1, 3, 5, 10, 20, 50]
    fixed = dict(L_att=22.0, p_gen_base=1.0, decoherence_mode="cutoff",
                 q_swap=1.0, f_init=0.95, f_min=0.80)
    results = run_sweep("t_cutoff", cutoffs, fixed)

    fig, ax = plt.subplots(figsize=(8, 5))
    for topo in ["nsfnet", "surfnet", "abilene"]:
        ax.plot(cutoffs, results[topo]["rates"],
                color=COLORS[topo], marker=MARKERS[topo],
                linewidth=2, markersize=7, label=topo.upper())
    ax.set_xlabel("Cutoff time (time steps)", fontsize=12)
    ax.set_ylabel("Entanglement rate (pairs/step)", fontsize=12)
    ax.set_title("Entanglement rate vs memory cutoff time", fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)
    fig.tight_layout()
    fig.savefig("results/cutoff_sweep.png", dpi=150)
    print("Saved results/cutoff_sweep.png")
    plt.close(fig)


def plot_fmin_sweep():
    """Plot entanglement rate vs fidelity threshold."""
    fmins = [0.50, 0.60, 0.70, 0.80, 0.90]
    fixed = dict(L_att=22.0, p_gen_base=1.0, decoherence_mode="cutoff",
                 t_cutoff=10, q_swap=1.0, f_init=0.95)
    results = run_sweep("f_min", fmins, fixed)

    fig, ax = plt.subplots(figsize=(8, 5))
    for topo in ["nsfnet", "surfnet", "abilene"]:
        ax.plot(fmins, results[topo]["rates"],
                color=COLORS[topo], marker=MARKERS[topo],
                linewidth=2, markersize=7, label=topo.upper())
    ax.set_xlabel("Minimum fidelity threshold (f_min)", fontsize=12)
    ax.set_ylabel("Entanglement rate (pairs/step)", fontsize=12)
    ax.set_title("Entanglement rate vs fidelity threshold", fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)
    fig.tight_layout()
    fig.savefig("results/fmin_sweep.png", dpi=150)
    print("Saved results/fmin_sweep.png")
    plt.close(fig)


def plot_per_pair_rates():
    """Bar chart of per-pair delivery rates."""
    fixed_config = dict(
        L_att=22.0, p_gen_base=1.0, decoherence_mode="cutoff",
        t_cutoff=10, q_swap=1.0, f_init=0.95, f_min=0.80,
    )
    labels = []
    rates = []
    colors = []
    fidelities = []

    for topo in ["nsfnet", "surfnet", "abilene"]:
        config = SimConfig(
            num_time_steps=N_STEPS,
            distance_scale=SCALES[topo],
            user_pairs=USER_PAIRS[topo],
            algorithm="greedy",
            **fixed_config,
        )
        random.seed(SEED)
        net = TOPOLOGIES[topo](config)

        # Track per-pair results
        import networkx as nx
        pair_del = {str(p): 0 for p in USER_PAIRS[topo]}
        pair_fid = {str(p): [] for p in USER_PAIRS[topo]}

        for t in range(N_STEPS):
            net.generate_links()
            net.decohere_links()
            res = greedy_route(net)
            for r in res:
                k = str((r["src"], r["dst"]))
                if r["delivered"]:
                    pair_del[k] += 1
                    pair_fid[k].append(r["fidelity"])

        for src, dst in USER_PAIRS[topo]:
            hops = nx.shortest_path_length(net.graph, src, dst)
            k = str((src, dst))
            cnt = pair_del[k]
            avg_f = np.mean(pair_fid[k]) if pair_fid[k] else 0
            labels.append(f"{src}-{dst}\n({hops} hop)")
            rates.append(cnt / N_STEPS)
            colors.append(COLORS[topo])
            fidelities.append(avg_f)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    x = np.arange(len(labels))
    ax1.bar(x, rates, color=colors, width=0.6, edgecolor="white", linewidth=0.5)
    ax1.set_ylabel("Delivery rate (per step)", fontsize=12)
    ax1.set_title("Per-pair delivery rate and fidelity", fontsize=14)
    ax1.grid(True, alpha=0.3, axis="y")

    ax2.bar(x, fidelities, color=colors, width=0.6, edgecolor="white", linewidth=0.5)
    ax2.set_ylabel("Average fidelity", fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=9)
    ax2.set_ylim(0.75, 0.95)
    ax2.grid(True, alpha=0.3, axis="y")
    ax2.axhline(y=0.80, color="red", linestyle="--", alpha=0.5, label="f_min = 0.80")
    ax2.legend(fontsize=10)

    # Add topology legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLORS["nsfnet"], label="NSFNET"),
        Patch(facecolor=COLORS["surfnet"], label="SURFnet"),
        Patch(facecolor=COLORS["abilene"], label="Abilene"),
    ]
    ax1.legend(handles=legend_elements, fontsize=10)

    fig.tight_layout()
    fig.savefig("results/per_pair_rates.png", dpi=150)
    print("Saved results/per_pair_rates.png")
    plt.close(fig)


if __name__ == "__main__":
    print("Running cutoff sweep...")
    plot_cutoff_sweep()
    print("Running fidelity threshold sweep...")
    plot_fmin_sweep()
    print("Running per-pair analysis...")
    plot_per_pair_rates()
    print("Done! All plots saved to results/")
