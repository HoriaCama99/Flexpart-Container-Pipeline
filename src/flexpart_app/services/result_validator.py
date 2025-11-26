"""Basic validation for FLEXPART outputs."""
from __future__ import annotations

from pathlib import Path

from rich.console import Console

console = Console()


class ResultValidator:
    """Ensure expected files exist after FLEXPART run."""

    REQUIRED = ("totals.nc",)

    def validate(self, output_dir: Path) -> None:
        missing = [name for name in self.REQUIRED if not (output_dir / name).exists()]
        if missing:
            raise FileNotFoundError(
                f"Missing FLEXPART outputs in {output_dir}: {', '.join(missing)}"
            )
        grids = sorted(output_dir.glob("grid_*.nc"))
        if not grids:
            console.log(
                "No grid_*.nc files found; ensure LNETCDFOUT=1 if gridded output needed",
            )
        console.log(f"Validation complete. Files present: {', '.join(self.REQUIRED)}")

