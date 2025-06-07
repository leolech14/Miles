"""Generate monthly promotion heatmap from history CSV data."""

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


def load_data() -> dict[str, list[int]]:
    """Load CSV files and accumulate counts per month."""
    counts: dict[str, list[int]] = defaultdict(lambda: [0] * 12)
    hist_dir = Path("history")
    for csv_file in hist_dir.glob("*.csv"):
        with open(csv_file, newline="") as f:
            for program, date, pct in csv.reader(f):
                try:
                    month = int(date.split("-")[1])
                except (IndexError, ValueError):
                    continue
                counts[program][month - 1] += 1
    return counts


def plot_heatmap(counts: dict[str, list[int]]) -> None:
    """Plot heatmap and save to stats/heatmap.png."""
    if not counts:
        print("No data to plot")
        return
    programs = sorted(counts)
    data = [counts[p] for p in programs]
    fig, ax = plt.subplots(figsize=(10, 0.5 * len(programs)))
    im = ax.imshow(data, cmap="Blues")
    ax.set_xticks(range(12), [str(i) for i in range(1, 13)])
    ax.set_yticks(range(len(programs)), programs)
    ax.set_xlabel("Month")
    ax.set_ylabel("Program")
    fig.colorbar(im, ax=ax, label="Promo frequency")
    Path("stats").mkdir(exist_ok=True)
    plt.tight_layout()
    plt.savefig("stats/heatmap.png")

def main() -> None:
    counts: dict[str, list[int]] = load_data()
    plot_heatmap(counts)


if __name__ == "__main__":
    main()
