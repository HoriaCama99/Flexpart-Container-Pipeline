#!/usr/bin/env python3
"""Quick-look plot for FLEXPART grid_conc NetCDF outputs."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from netCDF4 import Dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot FLEXPART NetCDF output")
    parser.add_argument("nc_file", type=Path, help="Path to grid_conc_*.nc file")
    parser.add_argument(
        "--output", type=Path, default=None, help="Path to save PNG (defaults next to file)"
    )
    args = parser.parse_args()

    nc_path = args.nc_file.expanduser()
    if not nc_path.exists():
        raise SystemExit(f"NetCDF file not found: {nc_path}")

    with Dataset(nc_path) as ds:
        lon = ds.variables["longitude"][:]
        lat = ds.variables["latitude"][:]
        conc = ds.variables.get("spec001_mr")
        title = f"{nc_path.name}"
        if conc is not None and conc.shape[2] > 0:
            data = conc[0, 0, 0, 0, :, :]
            label = "spec001_mr (first time, height)"
        else:
            if "ORO" not in ds.variables:
                raise SystemExit("No concentration field or ORO variable available to plot")
            data = ds.variables["ORO"][:]
            label = "ORO (m)"
            title += " – no conc data; showing ORO"

    lon2d, lat2d = np.meshgrid(lon, lat)
    fig, ax = plt.subplots(figsize=(8, 6))
    mesh = ax.pcolormesh(lon2d, lat2d, data, shading="auto")
    cbar = fig.colorbar(mesh, ax=ax, label=label)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(title)
    ax.set_aspect('auto')

    out_path = args.output or nc_path.with_suffix(".png")
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    print(f"Saved plot to {out_path}")


if __name__ == "__main__":
    main()
