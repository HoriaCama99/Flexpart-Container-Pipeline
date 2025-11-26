"""flex_extract container orchestration."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.console import Console

from ..config import RuntimeConfig
from .docker_runner import DockerRunner, DockerError
from .meteo import create_available_file

console = Console()


class FlexExtractService:
    """Handles ERA5 downloads via convert2 container."""

    def __init__(self, docker: DockerRunner) -> None:
        self._docker = docker

    def run(self, cfg: RuntimeConfig) -> Path:
        if not cfg.simulation.use_era5:
            raise ValueError("FlexExtractService should only run when use_era5=True")
        if not self._docker.images(cfg.flex_extract_image):
            raise DockerError(
                f"Docker image {cfg.flex_extract_image} missing. Build Dockerfile.convert2 first."
            )

        paths = cfg.paths
        paths.meteo_dir.mkdir(parents=True, exist_ok=True)
        input_dir = paths.flex_extract_workspace / "input"
        output_dir = paths.meteo_preprocessed_dir
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        credential_volumes, credential_env = self._credential_env(cfg)
        volumes = [
            (input_dir, "/workspace/input", "rw"),
            (output_dir, "/workspace/output", "rw"),
        ] + credential_volumes

        release = cfg.simulation.release
        margin = 10.0
        north = min(90.0, release.latitude + margin)
        south = max(-90.0, release.latitude - margin)
        east = min(180.0, release.longitude + margin)
        west = max(-180.0, release.longitude - margin)

        window = cfg.simulation.window
        args = [
            cfg.flex_extract_image,
            f"--start-date={window.start.strftime('%Y%m%d')}",
            f"--end-date={window.end.strftime('%Y%m%d')}",
            f"--area={north}/{west}/{south}/{east}",
            f"--grid={cfg.simulation.grid_deg}",
            "--levelist=1/to/137",
            "--basetime=0",
            "--dtime=1",
            "--prefix=EC",
            "--input-dir=/workspace/input",
            "--output-dir=/workspace/output",
            "--request=0",
            "--rrint=1",
            "--date-chunk=3",
        ]

        console.log("Running flex_extract container...")
        self._docker.run(args, volumes=volumes, env=credential_env)

        produced = list(output_dir.glob("EC*"))
        if not produced:
            raise RuntimeError(
                f"flex_extract completed but produced no EC files in {output_dir}"
            )

        count = create_available_file(
            output_dir, start_time=window.start, end_time=window.end
        )
        console.log(f"Generated AVAILABLE with {count} entries")
        return output_dir

    def _credential_env(
        self, cfg: RuntimeConfig
    ) -> tuple[list[tuple[Path, str, str]], list[tuple[str, str]]]:
        volumes: list[tuple[Path, str, str]] = []
        env: list[tuple[str, str]] = []
        creds = cfg.credentials

        def _mount(path: Optional[Path], env_name: str, target: str) -> None:
            if not path:
                return
            expanded = path.expanduser()
            if not expanded.exists():
                raise FileNotFoundError(f"Credential file {expanded} not found")
            volumes.append((expanded, target, "ro"))
            env.append((env_name, target))

        _mount(creds.cdsapi_path, "FLEXEXTRACT_CDSAPI_PATH", "/keys/cdsapirc")
        _mount(creds.ecmwfapi_path, "FLEXEXTRACT_APIKEY_PATH", "/keys/ecmwfapirc")

        if not env:
            raise RuntimeError(
                "No flex_extract credentials provided. Set cdsapi_path or ecmwfapi_path"
            )

        return volumes, env

