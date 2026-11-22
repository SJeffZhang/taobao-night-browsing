"""EDA: data-distribution plots with a professional academic palette.

Generates four figures under figures/eda/:
  1. event volume by hour of day
  2. user activity distribution (episodes per user)
  3. item popularity distribution (episodes per item)
  4. purchase-delay distribution (among 24 h buyers)

Run from inside src/.
"""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import fig_style_paper as fs
fs.apply()

EXT = Path(__file__).resolve().parents[1]
DATA = EXT / "data"; PROC = DATA / "processed"; FIG = EXT / "figures" / "eda"
FIG.mkdir(parents=True, exist_ok=True)

START, DAY, HOUR = 1511539200, 86400, 3600

# ---------------------------------------------------------------- 1. hourly volume
ev = pd.read_parquet(PROC / "events_clean.parquet", columns=["ts"])
hour = ((ev.ts.to_numpy() - START) % DAY) // HOUR
vol = np.bincount(hour, minlength=24) / 1e6
fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(np.arange(24), vol, color=fs.BLUE, alpha=0.88, edgecolor="white", linewidth=0.4)
ax.set_xticks(range(24))
ax.set_xlabel("Hour of day (Asia/Shanghai)")
ax.set_ylabel("Events (millions)")
ax.set_title("Event volume by hour of day")
ax.grid(axis="y", alpha=0.35)
fig.tight_layout(); fig.savefig(FIG / "eda_01_hourly_volume.png", dpi=150, bbox_inches="tight"); plt.close(fig)
print("1/4 hourly volume done")
del ev

# ---------------------------------------------------------------- episodes for 2-4
ep = pd.read_parquet(DATA / "episodes_hour.parquet", columns=["user_id", "item_id", "buy_delay_s"])

# 2. user activity distribution
uc = ep.user_id.value_counts().to_numpy()
fig, ax = plt.subplots(figsize=(8, 4))
ax.hist(uc, bins=np.logspace(0, np.log10(uc.max()), 50), color=fs.GREEN, alpha=0.88,
        edgecolor="white", linewidth=0.4)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("First-view episodes per user")
ax.set_ylabel("Number of users")
ax.set_title("User activity distribution")
ax.grid(alpha=0.35)
fig.tight_layout(); fig.savefig(FIG / "eda_02_user_activity.png", dpi=150, bbox_inches="tight"); plt.close(fig)
print("2/4 user activity done")

# 3. item popularity distribution
ic = ep.item_id.value_counts().to_numpy()
fig, ax = plt.subplots(figsize=(8, 4))
ax.hist(ic, bins=np.logspace(0, np.log10(ic.max()), 50), color=fs.ORANGE, alpha=0.88,
        edgecolor="white", linewidth=0.4)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("First-view episodes per item (popularity)")
ax.set_ylabel("Number of items")
ax.set_title("Item popularity distribution")
ax.grid(alpha=0.35)
fig.tight_layout(); fig.savefig(FIG / "eda_03_item_popularity.png", dpi=150, bbox_inches="tight"); plt.close(fig)
print("3/4 item popularity done")

# 4. purchase delay distribution (24 h buyers)
dl = ep.buy_delay_s.to_numpy()
buy = dl[(dl >= 0) & (dl < DAY)] / 60.0  # minutes
fig, ax = plt.subplots(figsize=(8, 4))
ax.hist(buy, bins=np.logspace(-1, np.log10(24 * 60), 60), color=fs.RED, alpha=0.88,
        edgecolor="white", linewidth=0.4)
ax.set_xscale("log")
ax.set_xlabel("Minutes from first view to purchase")
ax.set_ylabel("Number of episodes")
ax.set_title("Purchase delay distribution (24 h buyers)")
ax.grid(alpha=0.35)
fig.tight_layout(); fig.savefig(FIG / "eda_04_purchase_delay.png", dpi=150, bbox_inches="tight"); plt.close(fig)
print("4/4 purchase delay done")
print("EDA figures written to", FIG)
