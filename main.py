#!/usr/bin/env python3
"""CLI entry point for the quantum network entanglement routing simulator."""

import argparse
import json
import random
import sys
from pathlib import Path

from quantum_routing.utils.config import SimConfig
from quantum_routing.topologies import TOPOLOGIES
from quantum_routing.simulation import run_simulation


# Representative user pairs for each topology
DEFAULT_USER_PAIRS = {
    "nsfnet": [("WA", "DC"), ("CA1", "NY"), ("TX", "MI")],
    "surfnet": [("AMS", "NIJ"), ("DEL", "ENS"), ("RTM", "ZWO")],
    "abilene": [("SEA", "NYC"), ("LAX", "CHI"), ("HOU", "WAS")],
}


def parse_args():
    p = argparse.ArgumentParser(
        description="Quantum Network Entanglement Routing Simulator"
    )
    p.add_argument(
        "--topology", "-t",
        choices=list(TOPOLOGIES.keys()),
        default="nsfnet",
        help="Network topology (default: nsfnet)",
    )
    p.add_argument(
        "--algorithm", "-a",
        choices=["greedy", "mcf"],
        default="greedy",
        help="Routing algorithm (default: greedy)",
    )
    p.add_argument(
        "--time-steps", "-T",
        type=int, default=100,
        help="Number of simulation time steps (default: 100)",
    )
    p.add_argument(
        "--t-cutoff",
        type=int, default=10,
        help="Deterministic cutoff time for stored links (default: 10)",
    )
    p.add_argument(
        "--f-init",
        type=float, default=0.95,
        help="Initial fidelity of generated Bell pairs (default: 0.95)",
    )
    p.add_argument(
        "--f-min",
        type=float, default=0.80,
        help="Minimum fidelity threshold for delivery (default: 0.80)",
    )
    p.add_argument(
        "--p-gen",
        type=float, default=1.0,
        help="Base entanglement generation probability (default: 1.0)",
    )
    p.add_argument(
        "--L-att",
        type=float, default=22.0,
        help="Fiber attenuation length in km (default: 22.0)",
    )
    p.add_argument(
        "--distance-scale",
        type=float, default=1.0,
        help="Divide all edge lengths by this factor (default: 1.0)",
    )
    p.add_argument(
        "--seed",
        type=int, default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    p.add_argument(
        "--output", "-o",
        type=str, default=None,
        help="Output JSON file for results (default: print to stdout)",
    )
    return p.parse_args()


def main():
    args = parse_args()

    config = SimConfig(
        num_time_steps=args.time_steps,
        L_att=args.L_att,
        p_gen_base=args.p_gen,
        decoherence_mode="cutoff",
        t_cutoff=args.t_cutoff,
        q_swap=1.0,
        f_init=args.f_init,
        f_min=args.f_min,
        distance_scale=args.distance_scale,
        user_pairs=DEFAULT_USER_PAIRS[args.topology],
        algorithm=args.algorithm,
    )

    random.seed(args.seed)

    build_fn = TOPOLOGIES[args.topology]
    network = build_fn(config)

    print(f"Topology:    {args.topology} ({len(network.graph.nodes)} nodes, "
          f"{len(network.graph.edges)} edges)")
    print(f"Algorithm:   {args.algorithm}")
    print(f"Time steps:  {args.time_steps}")
    print(f"Cutoff:      {args.t_cutoff}")
    print(f"f_init:      {args.f_init}   f_min: {args.f_min}")
    print(f"p_gen_base:  {args.p_gen}    L_att: {args.L_att} km")
    print(f"User pairs:  {config.user_pairs}")
    print(f"Seed:        {args.seed}")
    print("-" * 60)

    metrics = run_simulation(network)
    summary = metrics.summary()

    print(f"Total delivered:      {summary['total_delivered']}")
    print(f"Entanglement rate:    {summary['entanglement_rate']:.4f} pairs/step")
    print(f"Average fidelity:     {summary['average_fidelity']:.4f}")

    # Build full results dict
    results = {
        "topology": args.topology,
        "algorithm": args.algorithm,
        "config": {
            "time_steps": args.time_steps,
            "t_cutoff": args.t_cutoff,
            "f_init": args.f_init,
            "f_min": args.f_min,
            "p_gen_base": args.p_gen,
            "L_att": args.L_att,
            "seed": args.seed,
            "user_pairs": config.user_pairs,
        },
        "summary": summary,
        "per_step_deliveries": [len(d) for d in metrics.deliveries_per_step],
        "per_step_fidelities": metrics.deliveries_per_step,
    }

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")

    return results


if __name__ == "__main__":
    main()
