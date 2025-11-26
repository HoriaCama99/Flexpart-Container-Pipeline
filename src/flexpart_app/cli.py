"""Typer-based CLI entrypoint for the FLEXPART application."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .config import (
    CredPaths,
    PathsConfig,
    ReleaseGeometry,
    RuntimeConfig,
    SimulationConfig,
    SpeciesDefinition,
    SimulationNumerics,
    TimeWindow,
)
from .services.docker_runner import DockerRunner
from .services.flex_extract import FlexExtractService
from .services.input_builder import FlexpartInputBuilder
from .services.result_validator import ResultValidator
from .services.simulation_runner import FlexpartSimulationRunner

app = typer.Typer(help="Run FLEXPART simulations via Docker")
console = Console()


@app.command()
def run(
    workspace: Path = typer.Argument(..., help="Working directory to store inputs/outputs"),
    start: datetime = typer.Option(..., help="Simulation start (UTC, YYYY-MM-DDTHH:MM)"),
    end: datetime = typer.Option(..., help="Simulation end (UTC, YYYY-MM-DDTHH:MM)"),
    latitude: float = typer.Option(..., help="Release latitude"),
    longitude: float = typer.Option(..., help="Release longitude"),
    release_bottom: float = typer.Option(0.0, help="Release bottom height [m]"),
    release_top: float = typer.Option(500.0, help="Release top height [m]"),
    release_duration_hours: float = typer.Option(6.0, help="Release duration [h]"),
    release_mass: float = typer.Option(1.0, help="Total release mass [kg]"),
    particles: int = typer.Option(20000, help="Number of particles"),
    species: str = typer.Option("DUST", help="Species name"),
    molecular_weight: float = typer.Option(100.0, help="Species molecular weight"),
    cdsapirc: Optional[Path] = typer.Option(None, help="Path to .cdsapirc for ERA5"),
    ecmwfapirc: Optional[Path] = typer.Option(None, help="Path to .ecmwfapirc"),
    flexpart_image: str = typer.Option("flexpart-v10.4-arm64:latest", help="FLEXPART image"),
    flex_extract_image: str = typer.Option("convert2:latest", help="flex_extract image"),
    docker_timeout: int = typer.Option(3600, help="Docker command timeout [s]"),
    era5: bool = typer.Option(True, help="Download ERA5 via flex_extract"),
) -> None:
    """Run a single FLEXPART simulation end-to-end."""

    workspace = workspace.expanduser().resolve()
    window = TimeWindow(start=start, end=end)
    release = ReleaseGeometry(
        latitude=latitude,
        longitude=longitude,
        height_bottom_m=release_bottom,
        height_top_m=release_top,
        duration_hours=release_duration_hours,
    )
    species_def = SpeciesDefinition(name=species.upper(), molecular_weight=molecular_weight)
    numerics = SimulationNumerics(particles=particles)

    simulation_cfg = SimulationConfig(
        window=window,
        release=release,
        species=species_def,
        numerics=numerics,
        release_mass_kg=release_mass,
        use_era5=era5,
    )

    runtime = RuntimeConfig(
        simulation=simulation_cfg,
        paths=PathsConfig(workspace=workspace),
        credentials=CredPaths(cdsapi_path=cdsapirc, ecmwfapi_path=ecmwfapirc),
        flexpart_image=flexpart_image,
        flex_extract_image=flex_extract_image,
        docker_timeout_sec=docker_timeout,
    )

    docker = DockerRunner(timeout_sec=docker_timeout)
    input_builder = FlexpartInputBuilder()
    sim_runner = FlexpartSimulationRunner(docker)
    validator = ResultValidator()

    if era5:
        flex_extract_service = FlexExtractService(docker)
        flex_extract_service.run(runtime)

    input_builder.prepare(runtime)
    output_dir = sim_runner.run(runtime)
    validator.validate(output_dir)
    console.print(f"✅ FLEXPART run complete. Results in {output_dir}")


if __name__ == "__main__":
    app()

