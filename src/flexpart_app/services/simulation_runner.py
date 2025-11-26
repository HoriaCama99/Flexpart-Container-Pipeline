"""Run FLEXPART simulations inside Docker."""
from __future__ import annotations

from pathlib import Path

from rich.console import Console

from ..config import RuntimeConfig
from .docker_runner import DockerRunner, DockerError

console = Console()


class FlexpartSimulationRunner:
    """Launches FLEXPART container with prepared inputs."""

    def __init__(self, docker: DockerRunner) -> None:
        self._docker = docker

    def run(self, cfg: RuntimeConfig) -> Path:
        if not self._docker.images(cfg.flexpart_image):
            raise DockerError(
                f"Docker image {cfg.flexpart_image} missing. Build Dockerfile.arm64 first."
            )

        workspace = cfg.paths.workspace
        output_dir = cfg.paths.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        pathnames_file = workspace / "pathnames"
        if not pathnames_file.exists():
            raise FileNotFoundError(f"pathnames not found at {pathnames_file}")

        inputs_host = cfg.paths.meteo_dir
        if not inputs_host.exists():
            inputs_host = workspace / "inputs"
            inputs_host.mkdir(exist_ok=True)

        volumes = [
            (workspace, "/options", "rw"),
            (output_dir, "/output", "rw"),
            (inputs_host, "/inputs", "rw"),
            (pathnames_file, "/pathnames", "ro"),
        ]

        console.log("Running FLEXPART container...")
        self._docker.run([cfg.flexpart_image], volumes=volumes)
        return output_dir

