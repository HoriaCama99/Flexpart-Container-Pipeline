"""Typed configuration objects for FLEXPART application workflows."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field, PositiveFloat, PositiveInt, field_validator, model_validator


class TimeWindow(BaseModel):
    """Simulation start/end timestamps with validation."""

    start: datetime = Field(..., description="Simulation start timestamp (UTC)")
    end: datetime = Field(..., description="Simulation end timestamp (UTC)")

    @model_validator(mode="after")
    def _check_order(self) -> "TimeWindow":
        if self.end <= self.start:
            msg = "end must be after start"
            raise ValueError(msg)
        return self


class ReleaseGeometry(BaseModel):
    """Spatial description of the source term."""

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    height_bottom_m: float = Field(0.0, ge=0.0)
    height_top_m: float = Field(100.0, ge=0.0)
    duration_hours: PositiveFloat = Field(6.0)

    @model_validator(mode="after")
    def _check_heights(self) -> "ReleaseGeometry":
        if self.height_top_m < self.height_bottom_m:
            msg = "height_top_m must be greater or equal to height_bottom_m"
            raise ValueError(msg)
        return self


class SpeciesDefinition(BaseModel):
    """FLEXPART species slot parameters."""

    name: str = Field(..., min_length=1)
    molecular_weight: PositiveFloat = Field(28.0)
    half_life_days: Optional[PositiveFloat] = Field(
        None, description="Optional radioactive decay half-life in days"
    )


class SimulationNumerics(BaseModel):
    """Numerical controls for FLEXPART."""

    particles: PositiveInt = Field(20_000, description="Number of computational particles")
    output_interval_sec: PositiveInt = Field(3600)
    sampling_interval_sec: PositiveInt = Field(900)
    turbulence: Literal[0, 1] = Field(1)
    netcdf_output: Literal[0, 1] = Field(1)


class CredPaths(BaseModel):
    """Credential locations for flex_extract."""

    cdsapi_path: Optional[Path] = Field(
        default=None,
        description="Path to .cdsapirc file (will be mounted read-only)",
    )
    ecmwfapi_path: Optional[Path] = Field(
        default=None,
        description="Optional .ecmwfapirc path for member-only datasets",
    )

    @field_validator("cdsapi_path", "ecmwfapi_path")
    @classmethod
    def _expand_path(cls, value: Optional[Path]) -> Optional[Path]:
        return value.expanduser() if value else value


class PathsConfig(BaseModel):
    """Filesystem layout for a simulation run."""

    workspace: Path = Field(..., description="Root work directory")

    @property
    def meteo_dir(self) -> Path:
        return self.workspace / "meteo"

    @property
    def meteo_preprocessed_dir(self) -> Path:
        return self.meteo_dir / "preprocessed"

    @property
    def flex_extract_workspace(self) -> Path:
        return self.meteo_dir / "flex_extract_workspace"

    @property
    def output_dir(self) -> Path:
        return self.workspace / "output"

    @property
    def species_dir(self) -> Path:
        return self.workspace / "SPECIES"


class SimulationConfig(BaseModel):
    """Full set of knobs for orchestrating a FLEXPART run."""

    window: TimeWindow
    release: ReleaseGeometry
    species: SpeciesDefinition
    numerics: SimulationNumerics = Field(default_factory=SimulationNumerics)
    release_mass_kg: PositiveFloat = Field(1.0)
    use_era5: bool = True
    grid_deg: float = Field(0.5, gt=0.0, le=1.0, description="ERA5 target grid spacing")


class RuntimeConfig(BaseModel):
    """Combined configuration and environment options."""

    simulation: SimulationConfig
    paths: PathsConfig
    credentials: CredPaths
    flexpart_image: str = Field("flexpart-v10.4-arm64:latest")
    flex_extract_image: str = Field("convert2:latest")
    docker_timeout_sec: int = Field(3600, gt=0)
    log_level: Literal["INFO", "DEBUG"] = Field("INFO")

