"""Dark summary charts for the README, drawn from the characterization data.

Reads reports/{campus,tiny_medipol}/data/*.json (deterministic seeds) and
writes docs/media/chart-*.png. Run from anywhere:

    uv run --with matplotlib python reports/make_readme_charts.py
"""
import json
import random
import statistics as st

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
R = REPO / "reports"
OUT = REPO / "docs" / "media"

SURF, INK, INK2, MUTED = "#121211", "#ffffff", "#c3c2b7", "#898781"
GRID, BASE = "#2c2c2a", "#383835"
S1, S2 = "#3987e5", "#d95926"  # categorical slots 1-2, dark steps

plt.rcParams.update({
    "font.family": "DejaVu Sans Mono",
    "font.size": 11,
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": BASE, "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8,
    "xtick.major.size": 0, "ytick.major.size": 0,
    "axes.labelpad": 8,
})
LINE = dict(lw=2.2, marker="o", ms=8, mec=SURF, mew=1.5, zorder=3)


def frame(title, subtitle):
    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=160)
    fig.subplots_adjust(left=0.09, right=0.86, top=0.76, bottom=0.14)
    fig.text(0.09, 0.93, title, color=INK, fontsize=15, fontweight="bold", ha="left", va="top")
    fig.text(0.09, 0.865, subtitle, color=INK2, fontsize=10.5, ha="left", va="top", linespacing=1.5)
    ax.spines["bottom"].set_color(BASE)
    return fig, ax


def save(fig, name):
    path = f"{OUT}/{name}"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    print("wrote", path)


# A. Retrieval latency by burial depth (campus) -------------------------------------
rows = json.load(open(f"{R}/campus/data/exp_a_depth_fullness.json"))["rows"]
assert not any(r["stuck"] for r in rows)
rng = random.Random(7)
fig, ax = frame(
    "Retrieval time grows with burial depth, not with fill level",
    "Campus layout: 87 single retrievals at 30 to 95% full.\n"
    "Each dot is one run; the time includes the 45 s customer exit.",
)
depths = [0, 1, 2]
ax.scatter([r["depth"] + rng.uniform(-0.13, 0.13) for r in rows], [r["latency"] for r in rows],
           s=26, color=S1, alpha=0.35, linewidths=0, zorder=2)
med = [st.median(r["latency"] for r in rows if r["depth"] == d) for d in depths]
ax.plot(depths, med, color=S1, **LINE)
for d, m in zip(depths, med):
    ax.annotate(f"{m:.0f} s median", (d, m), xytext=(34, 0), textcoords="offset points",
                color=INK2, fontsize=10.5, va="center")
ax.set_xticks(depths, ["on top", "1 car above it", "2 cars above it"])
ax.set_xlim(-0.4, 2.75)
ax.set_ylim(0, 160)
ax.set_ylabel("seconds until the car is delivered")
ax.set_xlabel("where the requested car sits in its stack")
save(fig, "chart-latency-depth.png")
print("medians by depth:", [round(m, 1) for m in med])


# B. Throughput under concurrent requests (campus vs tiny_medipol) -------------------
def by_k(fac):
    rows = json.load(open(f"{R}/{fac}/data/exp_b_drain_scaling.json"))["rows"]
    assert not any(r["stuck"] for r in rows)
    ks = sorted({r["k"] for r in rows})
    return ks, [st.median(r["throughput_per_h"] for r in rows if r["k"] == k) for k in ks]


kc, tc = by_k("campus")
kt, tt = by_k("tiny_medipol")
print("campus:", list(zip(kc, [round(v, 1) for v in tc])))
print("tiny  :", list(zip(kt, [round(v, 1) for v in tt])))
fig, ax = frame(
    "The small layout saturates near 50 cars/h; campus keeps climbing",
    "Cars delivered per hour when k requests arrive at once (median of 5 seeds, 70% full).\n"
    "Campus routes are longer, but its five lift regions keep absorbing work: ~105 cars/h at k = 164.",
)
ax.plot(kc, tc, color=S1, label="campus: 5 lifts, 5 shuttles, 420 slots", **LINE)
ax.plot(kt, tt, color=S2, label="tiny_medipol: 2 lifts, 2 shuttles", **LINE)
ax.annotate("campus", (kc[-1], tc[-1]), xytext=(12, 0), textcoords="offset points", color=INK2, va="center")
ax.annotate("tiny_medipol", (kt[-1], tt[-1]), xytext=(12, 0), textcoords="offset points", color=INK2, va="center")
ax.set_xticks(sorted(set(kc) | set(kt)))
ax.set_xlim(0, 17.5)
ax.set_ylim(0, max(tc + tt) * 1.2)
ax.set_xlabel("requests issued at the same moment (k)")
ax.set_ylabel("cars delivered per hour")
ax.legend(loc="upper left", frameon=False, labelcolor=INK2, fontsize=10)
save(fig, "chart-concurrency.png")


# C. 30-day endurance (campus) --------------------------------------------------------
m = json.load(open(f"{R}/campus/data/exp_month.json"))
days = [d["day"] + 1 for d in m["days"]]
stores = [d["stores"] for d in m["days"]]
deliv = [d["deliveries"] for d in m["days"]]
assert not any(d["stuck"] for d in m["days"])
fig, ax = frame(
    "30 simulated days of commuter traffic, no stuck day",
    f"Campus layout, 80% target fill, 25% SUVs: {sum(stores):,} cars stored, {sum(deliv):,} delivered.\n"
    "Evening demand is set to 1.7x the drain ceiling on purpose, so some nights roll over to the morning.",
)
ax.plot(days, stores, color=S1, lw=2.2, label="stored", zorder=3)
ax.plot(days, deliv, color=S2, lw=2.2, label="delivered", zorder=3)
ax.annotate("stored", (days[-1], stores[-1]), xytext=(12, 6), textcoords="offset points", color=INK2, va="center")
ax.annotate("delivered", (days[-1], deliv[-1]), xytext=(12, -8), textcoords="offset points", color=INK2, va="center")
ax.set_xlim(0.5, 32.5)
ax.set_xticks([1, 5, 10, 15, 20, 25, 30])
ax.set_ylim(0, 700)
ax.set_xlabel("simulated day")
ax.set_ylabel("cars per day")
ax.legend(loc="upper left", frameon=False, labelcolor=INK2, fontsize=10, ncols=2)
save(fig, "chart-month.png")
