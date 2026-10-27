#!/usr/bin/env python3
"""
plot.py - Visualizes training and validation curves per epoch for JointNLU.

Plots:
  1. Loss Curves: Train Loss vs Validation Loss
  2. Intent Classification: Validation Intent Macro-F1 and Intent Accuracy
  3. Slot Filling: Validation Slot F1
  4. Best Epoch & Performance Metrics Summary
Saves the figure to models/indicfinvoice_v1/training_curves.png
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional

import matplotlib
# Use Agg backend for safe, headless saving by default
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

DEFAULT_HISTORY_PATH = "models/indicfinvoice_v1/training_history.json"
DEFAULT_OUTPUT_PATH = "models/indicfinvoice_v1/training_curves.png"


def plot_training_curves(
    history: Dict[str, List],
    output_path: str = DEFAULT_OUTPUT_PATH,
    show: bool = False,
) -> str:
    """
    Plots training and validation metrics across epochs and saves the figure.

    Args:
        history: Dictionary containing keys:
            - 'epochs': List[int]
            - 'train_loss': List[float]
            - 'val_loss': List[float]
            - 'val_intent_acc': List[float]
            - 'val_intent_macro_f1': List[float]
            - 'val_slot_f1': List[float]
        output_path: Target PNG filepath
        show: Whether to display interactive window
    Returns:
        output_path
    """
    epochs = history.get("epochs", [])
    if not epochs:
        print("WARNING: No epoch data in history to plot.")
        return ""

    train_loss = history.get("train_loss", [])
    val_loss = history.get("val_loss", [])
    val_intent_acc = history.get("val_intent_acc", [])
    val_intent_f1 = history.get("val_intent_macro_f1", [])
    val_slot_f1 = history.get("val_slot_f1", [])

    # Find best epoch based on validation intent macro-F1
    best_idx = 0
    if val_intent_f1:
        best_idx = int(max(range(len(val_intent_f1)), key=lambda i: val_intent_f1[i]))
    best_epoch = epochs[best_idx]
    best_f1 = val_intent_f1[best_idx] if val_intent_f1 else 0.0

    # Ensure output directory exists
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        f"IndicFinVoice JointNLU Training Progress (Epoch {epochs[-1]}/{max(epochs[-1], 8)})",
        fontsize=16,
        fontweight="bold",
        y=0.98,
    )

    # ----------------------------------------------------
    # Subplot 1: Train & Validation Loss
    # ----------------------------------------------------
    ax1 = axes[0, 0]
    ax1.plot(epochs, train_loss, label="Train Loss", color="#2563EB", marker="o", linewidth=2.2)
    ax1.plot(epochs, val_loss, label="Validation Loss", color="#DC2626", marker="s", linewidth=2.2)
    ax1.set_title("Cross-Entropy Loss (Intent + Slots)", fontsize=13, fontweight="bold")
    ax1.set_xlabel("Epoch", fontsize=11)
    ax1.set_ylabel("Total Loss", fontsize=11)
    ax1.grid(True, linestyle="--", alpha=0.4)
    ax1.legend(loc="upper right", framealpha=0.9)
    if len(epochs) > 0:
        ax1.set_xticks(epochs)

    # ----------------------------------------------------
    # Subplot 2: Intent Classification Metrics
    # ----------------------------------------------------
    ax2 = axes[0, 1]
    ax2.plot(epochs, val_intent_f1, label="Val Intent Macro-F1", color="#059669", marker="^", linewidth=2.2)
    ax2.plot(epochs, val_intent_acc, label="Val Intent Accuracy", color="#7C3AED", marker="D", linewidth=2.2, linestyle="--")
    # Highlight best checkpoint
    ax2.scatter(
        [best_epoch],
        [best_f1],
        color="#F59E0B",
        s=160,
        zorder=5,
        edgecolors="#B45309",
        linewidths=1.5,
        label=f"Best Checkpoint (Ep {best_epoch}: {best_f1:.4f})",
    )
    ax2.set_title("Intent Classification Performance", fontsize=13, fontweight="bold")
    ax2.set_xlabel("Epoch", fontsize=11)
    ax2.set_ylabel("Score (0.0 to 1.0)", fontsize=11)
    ax2.set_ylim(-0.05, 1.05)
    ax2.grid(True, linestyle="--", alpha=0.4)
    ax2.legend(loc="lower right", framealpha=0.9)
    if len(epochs) > 0:
        ax2.set_xticks(epochs)

    # ----------------------------------------------------
    # Subplot 3: Slot Filling Metrics
    # ----------------------------------------------------
    ax3 = axes[1, 0]
    ax3.plot(epochs, val_slot_f1, label="Val Slot F1", color="#D97706", marker="v", linewidth=2.2)
    ax3.set_title("Slot Filling Performance (BIO Entity F1)", fontsize=13, fontweight="bold")
    ax3.set_xlabel("Epoch", fontsize=11)
    ax3.set_ylabel("F1 Score", fontsize=11)
    ax3.set_ylim(-0.05, 1.05)
    ax3.grid(True, linestyle="--", alpha=0.4)
    ax3.legend(loc="lower right", framealpha=0.9)
    if len(epochs) > 0:
        ax3.set_xticks(epochs)

    # ----------------------------------------------------
    # Subplot 4: Summary Card / Training Statistics
    # ----------------------------------------------------
    ax4 = axes[1, 1]
    ax4.axis("off")

    latest_ep = epochs[-1]
    summary_text = (
        f"TRAINING SUMMARY & CHECKPOINT STATUS\n"
        f"-----------------------------------------\n"
        f"• Base Model:          ai4bharat/indic-bert\n"
        f"• Total Epochs Run:    {latest_ep}\n"
        f"• Current Train Loss:  {train_loss[-1]:.4f}\n"
        f"• Current Val Loss:    {val_loss[-1]:.4f}\n"
        f"• Current Intent F1:   {val_intent_f1[-1]:.4f}\n"
        f"• Current Intent Acc:  {val_intent_acc[-1]:.4f}\n"
        f"• Current Slot F1:     {val_slot_f1[-1]:.4f}\n"
        f"-----------------------------------------\n"
        f"★ BEST CHECKPOINT (Epoch {best_epoch}):\n"
        f"  - Intent Macro-F1:   {best_f1:.4f}\n"
        f"  - Intent Accuracy:   {val_intent_acc[best_idx]:.4f}\n"
        f"  - Slot F1 Score:     {val_slot_f1[best_idx]:.4f}\n"
        f"  - Validation Loss:   {val_loss[best_idx]:.4f}\n"
        f"-----------------------------------------\n"
        f"Saved Model Directory:\n"
        f"  models/indicfinvoice_v1/"
    )

    ax4.text(
        0.05,
        0.5,
        summary_text,
        fontsize=11,
        family="monospace",
        verticalalignment="center",
        bbox=dict(boxstyle="round,pad=1.0", facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=1.5),
    )

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(output_path, dpi=200)
    plt.close(fig)

    if show:
        try:
            # If interactive GUI is requested and available
            import matplotlib as mp
            mp.use("TkAgg")
            plt.figure(fig.number)
            plt.show()
        except Exception:
            pass

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Plot JointNLU training curves per epoch.")
    parser.add_argument(
        "--history",
        type=str,
        default=DEFAULT_HISTORY_PATH,
        help=f"Path to training history JSON file (default: {DEFAULT_HISTORY_PATH})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Path to output PNG image (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the plot window interactively",
    )

    args = parser.parse_args()

    if not os.path.exists(args.history):
        print(f"ERROR: History file not found: {args.history}")
        print("Run nlu/train.py to generate training history.")
        sys.exit(1)

    with open(args.history, "r", encoding="utf-8") as f:
        history = json.load(f)

    out_path = plot_training_curves(history, output_path=args.output, show=args.show)
    print(f"Training curves plot saved to: {out_path}")


if __name__ == "__main__":
    main()
