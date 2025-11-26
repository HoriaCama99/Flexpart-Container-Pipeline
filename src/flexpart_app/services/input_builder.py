"""Write FLEXPART input/control files for a simulation."""
from __future__ import annotations

import subprocess
from datetime import timedelta
from pathlib import Path

from rich.console import Console

from ..config import RuntimeConfig

console = Console()


class FlexpartInputBuilder:
    """Generates COMMAND/RELEASES/etc. based on the runtime config."""

    STATIC_FILES = ("IGBP_int1.dat", "sfcdata.t", "sfcdepo.t")

    def prepare(self, cfg: RuntimeConfig) -> None:
        workspace = cfg.paths.workspace
        workspace.mkdir(parents=True, exist_ok=True)
        cfg.paths.output_dir.mkdir(parents=True, exist_ok=True)
        cfg.paths.species_dir.mkdir(parents=True, exist_ok=True)
        self._extract_static_files(cfg)
        self._write_pathnames(cfg)
        self._write_command(cfg)
        self._write_releases(cfg)
        self._write_species(cfg)
        self._write_outgrid(cfg)
        self._write_ageclasses(cfg)

    def _extract_static_files(self, cfg: RuntimeConfig) -> None:
        for fname in self.STATIC_FILES:
            target = cfg.paths.workspace / fname
            command = [
                "docker",
                "run",
                "--rm",
                "--entrypoint",
                "/bin/cat",
                cfg.flexpart_image,
                f"/options/{fname}",
            ]
            console.log(f"Extracting {fname} from {cfg.flexpart_image}")
            with open(target, "wb") as handle:
                subprocess.run(command, check=True, stdout=handle)

    def _write_pathnames(self, cfg: RuntimeConfig) -> None:
        if cfg.simulation.use_era5:
            preprocessed = cfg.paths.meteo_preprocessed_dir
            if preprocessed.exists() and any(preprocessed.iterdir()):
                inputs = "/inputs/preprocessed"
                avail = f"{inputs}/AVAILABLE"
            else:
                inputs = "/inputs"
                avail = "/inputs/AVAILABLE"
        else:
            inputs = "/inputs"
            avail = "/inputs/AVAILABLE"

        content = f"""/options/
/output/
{inputs}/
{avail}
"""
        (cfg.paths.workspace / "pathnames").write_text(content)

    def _write_command(self, cfg: RuntimeConfig) -> None:
        sim = cfg.simulation
        window = sim.window
        duration = int((window.end - window.start).total_seconds())
        loutrestart = max(86400, duration)
        command = f"""&COMMAND
LDIRECT=               1,
IBDATE=         {window.start.strftime('%Y%m%d')},
IBTIME=           {window.start.strftime('%H%M%S')},
IEDATE=         {window.end.strftime('%Y%m%d')},
IETIME=           {window.end.strftime('%H%M%S')},
LOUTSTEP=           {sim.numerics.output_interval_sec},
LOUTAVER=           {sim.numerics.output_interval_sec},
LOUTSAMPLE=          {sim.numerics.sampling_interval_sec},
LOUTRESTART=       {loutrestart},
LRECOUTSTEP=        {sim.numerics.output_interval_sec},
LRECOUTAVER=        {sim.numerics.output_interval_sec},
LRECOUTSAMPLE=       {sim.numerics.sampling_interval_sec},
LSYNCTIME=           {sim.numerics.sampling_interval_sec},
CTL=          -5.0000000,
IFINE=                 4,
IOUT=                  1,
IPOUT=                 0,
LSUBGRID=              0,
LCONVECTION=           0,
LTURBULENCE=           {sim.numerics.turbulence},
LTURBULENCE_MESO=      0,
LAGESPECTRA=           0,
IPIN=                  0,
IOUTPUTFOREACHRELEASE= 0,
IFLUX=                 0,
MDOMAINFILL=           0,
IND_SOURCE=            1,
IND_RECEPTOR=          0,
MQUASILAG=             0,
NESTED_OUTPUT=         0,
LNETCDFOUT=            {sim.numerics.netcdf_output},
LINIT_COND=            0,
SFC_ONLY=              0,
CBLFLAG=               0,
OHFIELDS_PATH= "../../flexin/",
NXSHIFT=               0,
MAXTHREADGRID=         4,
MAXFILESIZE=       10000,
LOGVERTINTERP=         0,
&END
"""
        (cfg.paths.workspace / "COMMAND").write_text(command)

    def _write_releases(self, cfg: RuntimeConfig) -> None:
        sim = cfg.simulation
        release = sim.release
        window = sim.window
        release_end = min(window.end, window.start + timedelta(hours=release.duration_hours))
        num = sim.numerics.particles
        content = f"""&RELEASES_CTRL
 NSPEC      =           1,
 SPECNUM_REL=           1,
 /
&RELEASE
 IDATE1  =       {window.start.strftime('%Y%m%d')},
 ITIME1  =         {window.start.strftime('%H%M%S')},
 IDATE2  =       {release_end.strftime('%Y%m%d')},
 ITIME2  =         {release_end.strftime('%H%M%S')},
 LON1    =         {release.longitude:8.3f},
 LON2    =         {release.longitude:8.3f},
 LAT1    =         {release.latitude:8.3f},
 LAT2    =         {release.latitude:8.3f},
 Z1      =         {release.height_bottom_m:8.3f},
 Z2      =         {release.height_top_m:8.3f},
 ZKIND   =              1,
 MASS    =       {sim.release_mass_kg:10.4E},
 PARTS   =          {num:8d},
 COMMENT =    "RELEASE 1",
 /
"""
        (cfg.paths.workspace / "RELEASES").write_text(content)

    def _write_species(self, cfg: RuntimeConfig) -> None:
        species = cfg.simulation.species
        content = f"""&SPECIES_PARAMS
 PSPECIES="{species.name}",
 PWEIGHTMOLAR={species.molecular_weight:.2f},
 PDECAY={species.half_life_days or -9.9},
 /
"""
        (cfg.paths.species_dir / "SPECIES_001").write_text(content)

    def _write_outgrid(self, cfg: RuntimeConfig) -> None:
        release = cfg.simulation.release
        content = f"""&OUTGRID
 OUTLON0=        {release.longitude - 5:.1f},
 OUTLAT0=        {release.latitude - 5:.1f},
 NUMXGRID=             60,
 NUMYGRID=             60,
 DXOUT=               0.2,
 DYOUT=               0.2,
 OUTHEIGHTS=   500.0, 1500.0, 5000.0, 50000.0,
 /
"""
        (cfg.paths.workspace / "OUTGRID").write_text(content)

    def _write_ageclasses(self, cfg: RuntimeConfig) -> None:
        content = """&AGECLASSES
NCLASS=                 1,
LAGE=                   0,
&END
"""
        (cfg.paths.workspace / "AGECLASSES").write_text(content)
