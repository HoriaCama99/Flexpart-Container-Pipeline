"""Utility helpers for invoking Docker with consistent logging and errors."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from rich.console import Console

console = Console()


class DockerError(RuntimeError):
    """Raised when a docker command fails."""


@dataclass
class DockerRunner:
    """Thin wrapper around the docker CLI."""

    timeout_sec: int = 3600

    def images(self, name: str) -> bool:
        """Return True if an image with the given repository exists."""
        result = subprocess.run(
            ["docker", "images", "-q", name],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise DockerError(result.stderr.strip() or result.stdout.strip())
        return bool(result.stdout.strip())

    def build(self, dockerfile: Path, tag: str, context: Path) -> None:
        command = [
            "docker",
            "build",
            "-t",
            tag,
            "-f",
            str(dockerfile),
            str(context),
        ]
        self._run(command)

    def run(
        self,
        args: Sequence[str],
        *,
        volumes: Iterable[tuple[Path, str, str]] = (),
        env: Iterable[tuple[str, str]] = (),
        remove: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        command: list[str] = ["docker", "run"]
        if remove:
            command.append("--rm")
        for host_path, container_path, mode in volumes:
            command.extend(["-v", f"{host_path}:{container_path}:{mode}"])
        for key, value in env:
            command.extend(["-e", f"{key}={value}"])
        command.extend(args)
        return self._run(command)

    def _run(self, command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        console.log(f"[bold]$ {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=self.timeout_sec,
            check=False,
        )
        if result.returncode != 0:
            snippet = result.stderr or result.stdout
            raise DockerError(snippet.strip())
        if result.stdout:
            console.log(result.stdout.strip())
        return result

