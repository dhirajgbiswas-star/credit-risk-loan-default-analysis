#!/usr/bin/env python3
"""Run data-quality checks on the accepted-loan file."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import configure_logging, ensure_directories
from src.data.load import load_accepted_loans, write_schema_report
from src.data.validate import run_quality_checks, write_quality_report


def main() -> None:
    configure_logging()
    ensure_directories()
    frame = load_accepted_loans()
    write_schema_report(frame)
    report = run_quality_checks(frame)
    write_quality_report(report)
    print(report.to_string(index=False))


if __name__ == "__main__":
    main()
