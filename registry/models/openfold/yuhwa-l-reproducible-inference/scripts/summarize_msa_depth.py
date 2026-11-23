#!/usr/bin/env python3
"""Combine the MSA-depth runs with the full-MSA baseline into one table and plot.

Reads msa-depth/results/depth-<N>/measurements.csv and the committed baseline
results/measurements/measurements.csv ("full"), and writes
msa-depth/summary.csv, msa-depth/summary.md, and msa-depth/msa_depth.png
(the plot needs matplotlib; it is skipped if matplotlib is missing).
"""

import csv
from pathlib import Path

RECIPE = Path(__file__).resolve().parent.parent
OUT = RECIPE / "msa-depth"
COLS = ["target", "length", "depth", "status", "time_s_median", "mean_plddt", "ptm",
        "tm_score", "lddt_ca", "rmsd_ca"]


def read(path, depth):
    if not path.exists():
        return []
    with open(path) as f:
        return [dict(r, depth=depth) for r in csv.DictReader(f)]


rows = []
for d in sorted(OUT.glob("results/depth-*"), key=lambda p: int(p.name.split("-")[1])):
    rows += read(d / "measurements.csv", d.name.split("-")[1])
done = {r["target"] for r in rows}
rows += [r for r in read(RECIPE / "results/measurements/measurements.csv", "full")
         if r["target"] in done]
order = {"1": 0, "8": 1, "32": 2, "128": 3, "full": 4}
rows.sort(key=lambda r: (int(r["length"]), order.get(r["depth"], 9)))

with open(OUT / "summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, COLS, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)


def fmt(v, nd):
    try:
        return f"{float(v):.{nd}f}"
    except ValueError:
        return v or "-"


lines = ["| Protein | Residues | MSA depth | Time (s) | Mean pLDDT | pTM | TM-score | lDDT | RMSD (Å) |",
         "|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    lines.append(f"| {r['target']} | {r['length']} | {r['depth']} | {fmt(r['time_s_median'], 1)} | "
                 f"{fmt(r['mean_plddt'], 1)} | {fmt(r['ptm'], 2)} | {fmt(r['tm_score'], 2)} | "
                 f"{fmt(r['lddt_ca'], 2)} | {fmt(r['rmsd_ca'], 2)} |")
(OUT / "summary.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    raise SystemExit("matplotlib not installed; plot skipped")

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for target in sorted({r["target"] for r in rows}, key=lambda t: int(next(r["length"] for r in rows if r["target"] == t))):
    rs = [r for r in rows if r["target"] == target and r["tm_score"]]
    x = [order[r["depth"]] for r in rs]
    label = f"{target} ({rs[0]['length']} aa)" if rs else target
    axes[0].plot(x, [float(r["tm_score"]) for r in rs], marker="o", label=label)
    axes[1].plot(x, [float(r["mean_plddt"]) for r in rs], marker="o", label=label)
for ax, title in zip(axes, ["TM-score vs experimental structure", "Mean pLDDT (model confidence)"]):
    ax.set_xticks(range(5), ["1", "8", "32", "128", "full"])
    ax.set_xlabel("Sequences kept per alignment file")
    ax.set_title(title)
    ax.grid(alpha=0.3)
axes[0].set_ylim(0, 1)
axes[1].set_ylim(0, 100)
axes[1].legend(fontsize=8)
fig.tight_layout()
fig.savefig(OUT / "msa_depth.png", dpi=150)
print(f"wrote {OUT / 'msa_depth.png'}")
