"""Utilities for managing meteorological inputs."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable


class MeteoError(RuntimeError):
    """Raised when meteorological products are missing or malformed."""


def create_available_file(
    product_dir: Path,
    start_time: datetime,
    end_time: datetime,
    prefix: str = "EC",
) -> int:
    """Generate a FLEXPART AVAILABLE file from EC* GRIB products."""
    products = sorted(product_dir.glob(f"{prefix}*"))
    if not products:
        raise MeteoError(f"No {prefix} files found in {product_dir}")

    def _parse(name: str) -> datetime | None:
        suffix = name[len(prefix) :]
        for fmt in ("%Y%m%d%H", "%Y%m%d", "%Y%m%d%H%M"):
            try:
                return datetime.strptime(suffix, fmt)
            except ValueError:
                continue
        for fmt in ("%y%m%d%H", "%y%m%d", "%y%m%d%H%M"):
            try:
                ts = datetime.strptime(suffix, fmt)
                if ts.year < 1950:
                    ts = ts.replace(year=ts.year + 2000)
                elif ts.year < 2000:
                    ts = ts.replace(year=ts.year + 1900)
                return ts
            except ValueError:
                continue
        return None

    filtered: list[tuple[datetime, str]] = []
    unparseable: list[str] = []
    for item in products:
        if not item.is_file():
            continue
        ts = _parse(item.name)
        if ts is None:
            unparseable.append(item.name)
            continue
        if start_time <= ts <= end_time:
            filtered.append((ts, item.name))

    if not filtered:
        for item in products:
            ts = _parse(item.name)
            if ts is not None:
                filtered.append((ts, item.name))
        filtered.sort(key=lambda row: row[0])

    if not filtered:
        raise MeteoError(
            "Unable to parse timestamps for AVAILABLE file from: "
            + ", ".join(unparseable)
        )

    header = [
        "XXXXXX EMPTY LINES XXXXXXXXX",
        "XXXXXX EMPTY LINES XXXXXXXX",
        "YYYYMMDD HHMMSS   name of the file(up to 80 characters)",
    ]
    entries: Iterable[str] = (
        f"{ts.strftime('%Y%m%d')} {ts.strftime('%H%M%S')}      {name:<30}      ON DISK"
        for ts, name in filtered
    )
    (product_dir / "AVAILABLE").write_text("\n".join([*header, *entries]) + "\n")
    return len(filtered)

