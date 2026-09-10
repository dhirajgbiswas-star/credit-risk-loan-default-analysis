#!/usr/bin/env python3
"""Stage local Lending Club files or download them from Kaggle."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import configure_logging, ensure_directories
from src.data.download import prepare_raw_data


def main() -> None:
    configure_logging()
    ensure_directories()
    staged = prepare_raw_data(allow_download=True)
    for name, path in staged.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
