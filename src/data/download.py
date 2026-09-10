"""Locate or download the Lending Club dataset without embedding credentials."""

from __future__ import annotations

import logging
import os
import shutil
import zipfile
from pathlib import Path

from src.config import (
    ACCEPTED_FILENAME,
    ARCHIVE_DIR,
    KAGGLE_DATASET,
    RAW_DIR,
    REJECTED_FILENAME,
    ensure_directories,
)

logger = logging.getLogger(__name__)


def _candidate_paths(filename: str) -> list[Path]:
    stem = filename.replace(".csv", "")
    return [
        RAW_DIR / filename,
        RAW_DIR / f"{filename}.gz",
        ARCHIVE_DIR / filename,
        ARCHIVE_DIR / f"{stem.lower()}.csv" / filename,
        ARCHIVE_DIR / f"{stem}.csv" / filename,
        PROJECT_ARCHIVE_ACCEPTED if "accepted" in filename.lower() else PROJECT_ARCHIVE_REJECTED,
    ]


PROJECT_ARCHIVE_ACCEPTED = (
    ARCHIVE_DIR / "accepted_2007_to_2018q4.csv" / "accepted_2007_to_2018Q4.csv"
)
PROJECT_ARCHIVE_REJECTED = (
    ARCHIVE_DIR / "rejected_2007_to_2018q4.csv" / "rejected_2007_to_2018Q4.csv"
)


def find_local_file(filename: str) -> Path | None:
    for path in _candidate_paths(filename):
        if path.exists() and path.is_file():
            return path
    gz_name = filename.replace(".csv", ".csv.gz")
    for folder in (RAW_DIR, ARCHIVE_DIR):
        candidate = folder / gz_name
        if candidate.exists():
            return candidate
    return None


def _link_or_copy(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return destination
    try:
        destination.symlink_to(source.resolve())
        logger.info("Linked %s -> %s", destination, source)
    except OSError:
        shutil.copy2(source, destination)
        logger.info("Copied %s -> %s", source, destination)
    return destination


def stage_local_files() -> dict[str, Path]:
    ensure_directories()
    staged: dict[str, Path] = {}
    for filename in (ACCEPTED_FILENAME, REJECTED_FILENAME):
        source = find_local_file(filename)
        if source is None:
            logger.warning("Local file not found for %s", filename)
            continue
        destination = RAW_DIR / source.name
        staged[filename] = _link_or_copy(source, destination)
    return staged


def download_from_kaggle() -> Path:
    ensure_directories()
    if not (os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY")):
        kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
        if not kaggle_json.exists():
            raise FileNotFoundError(
                "Kaggle credentials were not found. Set KAGGLE_USERNAME and "
                "KAGGLE_KEY or place kaggle.json in ~/.kaggle/."
            )
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError as exc:
        raise ImportError("Install the kaggle package to download the dataset.") from exc

    api = KaggleApi()
    api.authenticate()
    logger.info("Downloading %s", KAGGLE_DATASET)
    api.dataset_download_files(KAGGLE_DATASET, path=str(RAW_DIR), unzip=False)
    archives = list(RAW_DIR.glob("*.zip"))
    if not archives:
        raise FileNotFoundError("Kaggle download completed but no zip archive was found.")
    archive = archives[0]
    with zipfile.ZipFile(archive, "r") as zf:
        zf.extractall(RAW_DIR)
    logger.info("Extracted archive to %s", RAW_DIR)
    return RAW_DIR


def prepare_raw_data(allow_download: bool = True) -> dict[str, Path]:
    staged = stage_local_files()
    if ACCEPTED_FILENAME in staged:
        return staged
    if not allow_download:
        raise FileNotFoundError(
            f"{ACCEPTED_FILENAME} was not found under data/raw/lending_club or archive/."
        )
    download_from_kaggle()
    staged = stage_local_files()
    if ACCEPTED_FILENAME not in staged:
        raise FileNotFoundError("Accepted loan file is still missing after download.")
    return staged
