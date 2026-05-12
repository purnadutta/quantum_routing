#!/usr/bin/env python3
"""Generate plots comparing greedy vs MCF routing.

Usage:
    python scripts/plot_results.py

Produces:
    results/cutoff_sweep_comparison.png
    results/fmin_sweep_comparison.png
    results/per_pair_comparison.png
    results/algo_summary.png
"""

import random
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

from quantum_routing.utils.config import SimConfig
from quantum_routing.topologies import TOPOLOGIES
from quantum_routing.simulation import run_simulation
from quantum_routing.algorithms.greedy_shortest_path import greedy_route
from quantum_routing.algorithms.multi_commodity_flow import mcf_route


USER_PAIRS = {
    "nsfnet": [("WA", "DC"), ("CA1", "NY"), ("TX", "MI")],
    "surfnet": [("AMS", "NIJ"), ("DEL", "ENS"), ("RTM", "ZWO")],
    "abilene": [("SEA", "NYC"), ("LAX", "CHI"), ("HOU", "WAS")],
}
SCALES = {"nsfnet": 100, "surfnet": 1, "abilene": 100}
COLORS = {"nsfnet": "#534AB7", "surfnet": "#1D9E75", "abilene": "#D85A30"}
MARKERS = {"nsfnet": "o", "surfnet": "s", "abilene": "^"}
ALGO_STYLES = {"greedy": "-", "mcf": "--"}
N_STEPS = 500
SEED = 42


def run_sweep(param_name, param_values, fixed_params, algorithm="greedy"):
    """Run simulations sweeping one parameter."""
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
                algorithm=algorithm,
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


def run_per_pair(algorithm="greedy"):
    """Run per-pair analysis for a given algorithm."""
    fixed_config = dict(
        L_att=22.0, p_gen_base=1.0, decoherence_mode="cutoff",
        t_cutoff=10, q_swap=1.0, f_init=0.95, f_min=0.80,
    )
    route_fn = greedy_route if algorithm == "greedy" else mcf_route
    all_data = {}

    for topo in ["nsfnet", "surfnet", "abilene"]:
        config = SimConfig(
            num_time_steps=N_STEPS,
            distance_scale=SCALES[topo],
            user_pairs=USER_PAIRS[topo],
            algorithm=algorithm,
            **fixed_config,
        )
        random.seed(SEED)
        net = TOPOLOGIES[topo](config)

        pair_del = {str(p): 0 for p in USER_PAIRS[topo]}
        pair_fid = {str(p): [] for p in USER_PAIRS[topo]}

        for t in range(N_STEPS):
            net.generate_links()
            net.decohere_links()
            res = route_fn(net)
            for r in res:
                k = str((r["src"], r["dst"]))
                if r["delivered"]:
                    pair_del[k] += 1
                    pair_fid[k].append(r["fidelity"])

        topo_data = []
        for src, dst in USER_PAIRS[topo]:
            hops = nx.shortest_path_length(net.graph, src, dst)
            k = str((src, dst))
            cnt = pair_del[k]
            avg_f = float(np.mean(pair_fid[k])) if pair_fid[k] else 0.0
            topo_data.append({
                "label": f"{src}-{dst}\n({hops} hop)",
                "rate": cnt / N_STEPS,
                "fidelity": avg_f,
                "hops": hops,
            })
        all_data[topo] = topo_data

    return all_data


# ── Plot 1: Cutoff sweep, greedy vs MCF ──────────────────────────────────

def plot_cutoff_sweep():
    cutoffs = [1, 3, 5, 10, 20, 50]
    fixed = dict(L_att=22.0, p_gen_base=1.0, decoherence_mode="cutoff",
                 q_swap=1.0, f_init=0.95, f_min=0.80)

    res_greedy = run_sweep("t_cutoff", cutoffs, fixed, algorithm="greedy")
    res_mcf = run_sweep("t_cutoff", cutoffs, fixed, algorithm="mcf")

    fig, ax = plt.subplots(figsize=(9, 5.5))
    for topo in ["nsfnet", "surfnet", "abilene"]:
        ax.plot(cutoffs, res_greedy[topo]["rates"],
                color=COLORS[topo], marker=MARKERS[topo],
                linewidth=2, markersize=7, linestyle="-",
                label=f"{topo.upper()} greedy")
        ax.plot(cutoffs, res_mcf[topo]["rates"],
                color=COLORS[topo], marker=MARKERS[topo], markerfacecolor="white",
                linewidth=2.5, markersize=8, linestyle=":",
                label=f"{topo.upper()} MCF")

    ax.set_xlabel("Cutoff time (time steps)", fontsize=12)
    ax.set_ylabel("Entanglement rate (pairs/step)", fontsize=12)
    ax.set_title("Entanglement rate vs memory cutoff time (greedy vs MCF)", fontsize=13)
    ax.legend(fontsize=9, ncol=2, columnspacing=1.5)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)
    fig.tight_layout()
    fig.savefig("results/cutoff_sweep_comparison.png", dpi=150)
    print("Saved results/cutoff_sweep_comparison.png")
    plt.close(fig)


# ── Plot 2: Fidelity threshold sweep, greedy vs MCF ─────────────────────

def plot_fmin_sweep():
    fmins = [0.50, 0.60, 0.70, 0.80, 0.90]
    fixed = dict(L_att=22.0, p_gen_base=1.0, decoherence_mode="cutoff",
                 t_cutoff=10, q_swap=1.0, f_init=0.95)

    res_greedy = run_sweep("f_min", fmins, fixed, algorithm="greedy")
    res_mcf = run_sweep("f_min", fmins, fixed, algorithm="mcf")

    fig, ax = plt.subplots(figsize=(9, 5.5))
    for topo in ["nsfnet", "surfnet", "abilene"]:
        ax.plot(fmins, res_greedy[topo]["rates"],
                color=COLORS[topo], marker=MARKERS[topo],
                linewidth=2, markersize=7, linestyle="-",
                label=f"{topo.upper()} greedy")
        ax.plot(fmins, res_mcf[topo]["rates"],
                color=COLORS[topo], marker=MARKERS[topo], markerfacecolor="white",
                linewidth=2.5, markersize=8, linestyle=":",
                label=f"{topo.upper()} MCF")

    ax.set_xlabel("Minimum fidelity threshold (f_min)", fontsize=12)
    ax.set_ylabel("Entanglement rate (pairs/step)", fontsize=12)
    ax.set_title("Entanglement rate vs fidelity threshold (greedy vs MCF)", fontsize=13)
    ax.legend(fontsize=9, ncol=2, columnspacing=1.5)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)
    fig.tight_layout()
    fig.savefig("results/fmin_sweep_comparison.png", dpi=150)
    print("Saved results/fmin_sweep_comparison.png")
    plt.close(fig)


# ── Plot 3: Per-pair grouped bars, greedy vs MCF ────────────────────────

def plot_per_pair_comparison():
    print("  Running greedy per-pair...")
    data_greedy = run_per_pair("greedy")
    print("  Running MCF per-pair...")
    data_mcf = run_per_pair("mcf")

    # Build labels and data arrays
    labels = []
    rates_g, rates_m = [], []
    fids_g, fids_m = [], []
    bar_colors = []

    for topo in ["nsfnet", "surfnet", "abilene"]:
        for i in range(len(USER_PAIRS[topo])):
            labels.append(data_greedy[topo][i]["label"])
            rates_g.append(data_greedy[topo][i]["rate"])
            rates_m.append(data_mcf[topo][i]["rate"])
            fids_g.append(data_greedy[topo][i]["fidelity"])
            fids_m.append(data_mcf[topo][i]["fidelity"])
            bar_colors.append(COLORS[topo])

    x = np.arange(len(labels))
    w = 0.35

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9), sharex=True)

    # Delivery rate bars
    bars_g = ax1.bar(x - w / 2, rates_g, w, color=bar_colors, alpha=0.7,
                     edgecolor="white", linewidth=0.5, label="Greedy")
    bars_m = ax1.bar(x + w / 2, rates_m, w, color=bar_colors, alpha=1.0,
                     edgecolor="white", linewidth=0.5, label="MCF", hatch="//")
    ax1.set_ylabel("Delivery rate (per step)", fontsize=12)
    ax1.set_title("Per-pair delivery rate: greedy (solid) vs MCF (hatched)", fontsize=13)
    ax1.grid(True, alpha=0.3, axis="y")
    ax1.legend(fontsize=10)

    # Fidelity bars
    ax2.bar(x - w / 2, fids_g, w, color=bar_colors, alpha=0.7,
            edgecolor="white", linewidth=0.5)
    ax2.bar(x + w / 2, fids_m, w, color=bar_colors, alpha=1.0,
            edgecolor="white", linewidth=0.5, hatch="//")
    ax2.set_ylabel("Average fidelity", fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=9)
    ax2.set_ylim(0.75, 0.95)
    ax2.grid(True, alpha=0.3, axis="y")
    ax2.axhline(y=0.80, color="red", linestyle="--", alpha=0.5, label="f_min = 0.80")
    ax2.legend(fontsize=10)

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLORS["nsfnet"], label="NSFNET"),
        Patch(facecolor=COLORS["surfnet"], label="SURFnet"),
        Patch(facecolor=COLORS["abilene"], label="Abilene"),
    ]
    ax1.legend(handles=legend_elements + [
        Patch(facecolor="gray", alpha=0.7, label="Greedy"),
        Patch(facecolor="gray", hatch="//", label="MCF"),
    ], fontsize=9, ncol=3)

    fig.tight_layout()
    fig.savefig("results/per_pair_comparison.png", dpi=150)
    print("Saved results/per_pair_comparison.png")
    plt.close(fig)


# ── Plot 4: Summary bar chart ───────────────────────────────────────────

def plot_algo_summary():
    """Simple grouped bar: total rate per topology, greedy vs MCF."""
    fixed = dict(
        L_att=22.0, p_gen_base=1.0, decoherence_mode="cutoff",
        t_cutoff=10, q_swap=1.0, f_init=0.95, f_min=0.80,
    )
    topos = ["nsfnet", "surfnet", "abilene"]
    rates_g, rates_m, fids_g, fids_m = [], [], [], []

    for topo in topos:
        for algo, r_list, f_list in [("greedy", rates_g, fids_g), ("mcf", rates_m, fids_m)]:
            config = SimConfig(
                num_time_steps=N_STEPS,
                distance_scale=SCALES[topo],
                user_pairs=USER_PAIRS[topo],
                algorithm=algo,
                **fixed,
            )
            random.seed(SEED)
            net = TOPOLOGIES[topo](config)
            m = run_simulation(net)
            s = m.summary()
            r_list.append(s["entanglement_rate"])
            f_list.append(s["average_fidelity"])

    x = np.arange(len(topos))
    w = 0.3
    topo_colors = [COLORS[t] for t in topos]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))

    ax1.bar(x - w / 2, rates_g, w, color=topo_colors, alpha=0.7, label="Greedy")
    ax1.bar(x + w / 2, rates_m, w, color=topo_colors, alpha=1.0, label="MCF", hatch="//")
    ax1.set_xticks(x)
    ax1.set_xticklabels([t.upper() for t in topos], fontsize=11)
    ax1.set_ylabel("Entanglement rate (pairs/step)", fontsize=12)
    ax1.set_title("Total delivery rate", fontsize=13)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3, axis="y")

    # Add improvement % labels
    for i in range(len(topos)):
        if rates_g[i] > 0:
            pct = (rates_m[i] - rates_g[i]) / rates_g[i] * 100
            ax1.annotate(f"+{pct:.0f}%",
                         xy=(x[i] + w / 2, rates_m[i]),
                         ha="center", va="bottom", fontsize=10,
                         fontweight="bold", color=topo_colors[i])

    ax2.bar(x - w / 2, fids_g, w, color=topo_colors, alpha=0.7, label="Greedy")
    ax2.bar(x + w / 2, fids_m, w, color=topo_colors, alpha=1.0, label="MCF", hatch="//")
    ax2.set_xticks(x)
    ax2.set_xticklabels([t.upper() for t in topos], fontsize=11)
    ax2.set_ylabel("Average fidelity", fontsize=12)
    ax2.set_title("Average delivered fidelity", fontsize=13)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3, axis="y")
    ax2.set_ylim(0.80, 0.92)

    fig.tight_layout()
    fig.savefig("results/algo_summary.png", dpi=150)
    print("Saved results/algo_summary.png")
    plt.close(fig)


if __name__ == "__main__":
    print("1/4 Cutoff sweep (greedy + MCF)...")
    plot_cutoff_sweep()
    print("2/4 Fidelity threshold sweep (greedy + MCF)...")
    plot_fmin_sweep()
    print("3/4 Per-pair comparison...")
    plot_per_pair_comparison()
    print("4/4 Algorithm summary...")
    plot_algo_summary()
    print("\nDone! All plots saved to results/")
