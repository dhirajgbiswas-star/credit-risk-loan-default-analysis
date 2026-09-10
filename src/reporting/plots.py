"""Standard chart helpers for portfolio and risk analysis."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.config import FIGURE_DIR

sns.set_theme(style="whitegrid", context="talk")
PALETTE = ["#1F4E79", "#C45911", "#548235", "#7030A0", "#833C0C", "#2F5496"]


def _save(fig, name: str) -> Path:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURE_DIR / name
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path


def bar_rate(table: pd.DataFrame, category: str, title: str, filename: str, rate_col: str = "default_rate"):
    plot_df = table.dropna(subset=[category]).copy()
    fig, ax = plt.subplots(figsize=(10, 5.5))
    sns.barplot(data=plot_df, x=category, y=rate_col, color=PALETTE[0], ax=ax)
    ax.set_title(title)
    ax.set_ylabel("Default rate")
    ax.set_xlabel(category.replace("_", " ").title())
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
    if plot_df[category].nunique() > 8:
        ax.tick_params(axis="x", rotation=45)
    return _save(fig, filename)


def trend_dual(table: pd.DataFrame, x: str, y1: str, y2: str, title: str, filename: str):
    fig, ax1 = plt.subplots(figsize=(10, 5.5))
    ax2 = ax1.twinx()
    ax1.plot(table[x], table[y1], color=PALETTE[0], marker="o", label=y1)
    ax2.plot(table[x], table[y2], color=PALETTE[1], marker="o", label=y2)
    ax1.set_title(title)
    ax1.set_xlabel(x.replace("_", " ").title())
    fig.legend(loc="upper left", bbox_to_anchor=(0.12, 0.88))
    return _save(fig, filename)


def vintage_lines(curve: pd.DataFrame, filename: str = "vintage_curves.png"):
    fig, ax = plt.subplots(figsize=(11, 6))
    for vintage, part in curve.groupby("vintage"):
        ax.plot(part["loan_age_months"], part["cumulative_default_rate"], label=str(vintage))
    ax.set_title("Cumulative default rate by loan age and vintage")
    ax.set_xlabel("Loan age (months)")
    ax.set_ylabel("Cumulative default rate")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
    ax.legend(title="Vintage", ncol=3, fontsize=9)
    return _save(fig, filename)


def vintage_heatmap_plot(heatmap: pd.DataFrame, filename: str = "vintage_heatmap.png"):
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(heatmap, cmap="YlOrRd", ax=ax)
    ax.set_title("Vintage heatmap: cumulative default rate")
    ax.set_xlabel("Loan age (months)")
    ax.set_ylabel("Vintage")
    return _save(fig, filename)


def distribution(series: pd.Series, title: str, filename: str, bins: int = 40):
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(series.dropna(), bins=bins, color=PALETTE[0], ax=ax)
    ax.set_title(title)
    return _save(fig, filename)
