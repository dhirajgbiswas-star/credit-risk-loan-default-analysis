#!/usr/bin/env python3
"""Train origination-time default-probability models."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src.config import PROCESSED_DIR, configure_logging, ensure_directories
from src.data.load import load_accepted_loans
from src.data.transform import build_analytical_dataset
from src.modeling.train import train_and_evaluate


def main() -> None:
    configure_logging()
    ensure_directories()
    parquet_path = PROCESSED_DIR / "analytical_loans.parquet"
    if parquet_path.exists():
        analytical = pd.read_parquet(parquet_path)
    else:
        analytical = build_analytical_dataset(load_accepted_loans())
    summary = train_and_evaluate(analytical)
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
