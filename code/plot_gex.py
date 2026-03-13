"""
plot_gex.py

Plots the GEX profile by strike as a bar chart.
Positive GEX (green) = dealers long gamma at that strike (stabilizing).
Negative GEX (red)   = dealers short gamma at that strike (amplifying).

Key levels marked with vertical lines:
  - Gamma flip (dashed black)
  - Call wall  (dashed green)
  - Put wall   (dashed red)

Usage:
    python code/plot_gex.py
"""

import os
import sys
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Allow importing from the code directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from compute_gex import load_chain, compute_gex_profile


def plot_gex(result: dict, title: str = "GEX Profile by Strike (SPY Sample)") -> None:
    gex_by_strike = result["gex_by_strike"]
    total_gex = result["total_gex"]
    gamma_flip = result["gamma_flip"]
    call_wall = result["call_wall"]
    put_wall = result["put_wall"]

    strikes = sorted(gex_by_strike.keys())
    values_m = [gex_by_strike[k] / 1e6 for k in strikes]  # in $M

    colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in values_m]

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(strikes, values_m, width=2.5, color=colors, edgecolor="white", linewidth=0.5)

    # Zero line
    ax.axhline(0, color="white", linewidth=0.8, alpha=0.5)

    # Gamma flip
    if gamma_flip is not None:
        ax.axvline(
            gamma_flip,
            color="white",
            linestyle="--",
            linewidth=1.4,
            label=f"Gamma flip: {gamma_flip:.1f}",
        )

    # Call wall
    ax.axvline(
        call_wall,
        color="#2ecc71",
        linestyle="--",
        linewidth=1.4,
        label=f"Call wall: {call_wall:.0f}",
    )

    # Put wall
    ax.axvline(
        put_wall,
        color="#e74c3c",
        linestyle="--",
        linewidth=1.4,
        label=f"Put wall: {put_wall:.0f}",
    )

    # Axis labels and formatting
    ax.set_xlabel("Strike", fontsize=12, color="#cccccc")
    ax.set_ylabel("Net GEX ($M)", fontsize=12, color="#cccccc")
    ax.set_title(title, fontsize=14, fontweight="bold", color="white", pad=14)

    total_sign = "+" if total_gex >= 0 else ""
    regime_label = "Positive (mean-reversion)" if total_gex >= 0 else "Negative (momentum)"
    ax.set_title(
        f"{title}\nTotal GEX: {total_sign}{total_gex/1e9:.2f}B  |  Regime: {regime_label}",
        fontsize=13,
        color="white",
        pad=14,
    )

    ax.tick_params(colors="#aaaaaa")
    ax.spines["bottom"].set_color("#555555")
    ax.spines["left"].set_color("#555555")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")

    # Legend
    legend_patches = [
        mpatches.Patch(color="#2ecc71", label="Positive GEX (dealers long gamma)"),
        mpatches.Patch(color="#e74c3c", label="Negative GEX (dealers short gamma)"),
    ]
    if gamma_flip is not None:
        legend_patches.append(
            plt.Line2D([0], [0], color="white", linestyle="--", label=f"Gamma flip: {gamma_flip:.1f}")
        )
    legend_patches.append(
        plt.Line2D([0], [0], color="#2ecc71", linestyle="--", label=f"Call wall: {call_wall:.0f}")
    )
    legend_patches.append(
        plt.Line2D([0], [0], color="#e74c3c", linestyle="--", label=f"Put wall: {put_wall:.0f}")
    )

    ax.legend(
        handles=legend_patches,
        loc="upper left",
        framealpha=0.3,
        facecolor="#2a2a3e",
        labelcolor="#cccccc",
        fontsize=9,
    )

    plt.tight_layout()
    plt.show()


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "..", "data", "sample_chain.csv")

    chain = load_chain(csv_path)
    result = compute_gex_profile(chain)
    plot_gex(result)


if __name__ == "__main__":
    main()

# FlashAlpha API gives you the same data in one call:
#   import flashalpha as fa
#   fa.gex("SPY")  ->  returns gex_by_strike, gamma_flip, call_wall, put_wall
#   API base: https://lab.flashalpha.com   Auth: X-Api-Key header
