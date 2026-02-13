"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to run SU2 configuration files in CEASIOMpy.

| Author: Leon Deligny
| Creation: 20 March 2025

"""

# Imports

import os
import re

from ceasiompy.utils.ceasiompyutils import run_software

from pathlib import Path
from typing import Callable

from ceasiompy.su2run import SOFTWARE_NAME
from ceasiompy.utils.commonnames import (
    CONFIG_CFD_NAME,
    CONFIG_DYNSTAB_NAME,
    SU2_FORCES_BREAKDOWN_NAME,
    SU2_DYNSTAB_FORCES_BREAKDOWN_NAME,
)

# Functions


def check_config_file_exists(config_file: list[Path], config_dir: Path) -> None:
    """
    Check that there exists exactly 1 configuration file for 1 scenario
    """
    if not config_file:
        raise ValueError(
            f"No configuration files '{CONFIG_CFD_NAME}' "
            f"and '{CONFIG_DYNSTAB_NAME}' have been found in directory {config_dir}."
        )

    if len(config_file) > 1:
        raise ValueError(
            f"More than one configuration file '{CONFIG_CFD_NAME}' "
            f"or '{CONFIG_DYNSTAB_NAME}' have been found in directory {config_dir}."
        )


def check_force_files_exists(config_dir: Path) -> None:
    forces_breakdown_file = Path(config_dir, SU2_FORCES_BREAKDOWN_NAME)
    dynstab_forces_breakdown_file = Path(config_dir, SU2_DYNSTAB_FORCES_BREAKDOWN_NAME)

    if (not forces_breakdown_file.exists()) and (not dynstab_forces_breakdown_file.exists()):
        raise ValueError(
            "The SU2_CFD calculations have not ended correctly, "
            f"{SU2_FORCES_BREAKDOWN_NAME} and {SU2_DYNSTAB_FORCES_BREAKDOWN_NAME} "
            f"are missing in {config_dir}."
        )


def _tail_text(log_path: Path, max_bytes: int = 8192) -> str:
    try:
        with open(log_path, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(size - max_bytes, 0))
            data = fh.read()
        return data.decode(errors="replace")
    except FileNotFoundError:
        return ""


def _parse_total_iterations(config_path: Path) -> int | None:
    pattern = re.compile(r"^\s*(INNER_ITER|ITER)\s*=\s*(\d+)", re.IGNORECASE)
    inner_iter = None
    iter_count = None
    for line in config_path.read_text(errors="replace").splitlines():
        match = pattern.match(line)
        if not match:
            continue
        key = match.group(1).upper()
        value = int(match.group(2))
        if key == "INNER_ITER":
            inner_iter = value
        elif key == "ITER":
            iter_count = value
    return inner_iter if inner_iter is not None else iter_count


def _parse_current_iteration(log_text: str) -> int | None:
    current = None
    for line in log_text.splitlines():
        match = re.match(r"^\|\s*(\d+)\s*\|", line)
        if match:
            value = int(match.group(1))
            if current is None or value > current:
                current = value
    return current


def _parse_current_iteration_from_history(history_path: Path) -> int | None:
    if not history_path.exists():
        return None

    try:
        lines = history_path.read_text(errors="replace").splitlines()
    except Exception:
        return None

    # Find last non-empty data line and parse first column as INNER_ITER.
    for line in reversed(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("%"):
            continue
        first_col = stripped.split(",")[0].strip().strip('"')
        if first_col.isdigit():
            return int(first_col)

    return None


def run_SU2_multi(
    wkdir: Path,
    nb_proc: int = 1,
    *,
    progress_callback: Callable[..., None] | None = None,
) -> None:
    """
    Run in the given working directory SU2 calculations.
    The working directory must have a folder structure created by 'SU2Config' module.

    Args:
        wkdir (Path): Path to the working directory.
        nb_proc (int): Number of processor that should be used to run the calculation in parallel.

    """

    case_dir_list = sorted(
        [
            dir
            for dir in wkdir.iterdir()
            if "Case" in dir.name
        ],
        key=lambda p: p.name,
    )

    if not case_dir_list:
        raise FileNotFoundError(
            f"No Case directory has been found in the working directory: {wkdir}."
        )

    # Iterate through different cases.
    for case_dir in case_dir_list:
        config_dirs = sorted([d for d in case_dir.iterdir() if d.is_dir()], key=lambda p: p.name)
        if not config_dirs:
            # Support flat case directory (ConfigCFD.cfg directly inside case_dir).
            config_dirs = [case_dir]

        # Iterate through [no_deformation, aileron, elevator, rudder].
        for config_dir in config_dirs:
            config_file = [
                c
                for c in config_dir.iterdir()
                if (c.name == CONFIG_CFD_NAME or c.name == CONFIG_DYNSTAB_NAME)
            ]

            check_config_file_exists(config_file, config_dir)

            total_iter = _parse_total_iterations(config_file[0])
            label = (
                case_dir.name
                if config_dir == case_dir
                else f"{case_dir.name}/{config_dir.name}"
            )
            history_path = Path(config_dir, "history.csv")

            def _progress_parser(log_path: Path):
                # Prefer history.csv (updated every INNER_ITER), fallback to logfile tail parsing.
                current_iter = _parse_current_iteration_from_history(history_path)
                if current_iter is None:
                    log_text = _tail_text(log_path)
                    current_iter = _parse_current_iteration(log_text)

                if total_iter and total_iter > 0 and current_iter is not None:
                    ratio = min(max(current_iter / total_iter, 0.0), 1.0)
                    progress = ratio
                    detail = (
                        f"{label} · SU2 iterations: "
                        f"{current_iter}/{total_iter} ({ratio * 100:.1f}%)"
                    )
                else:
                    progress = None
                    detail = f"{label} · SU2 running..."
                return progress, detail, None

            cloud = os.environ.get("CEASIOMPY_CLOUD", "False").lower() in {"1", "true", "yes"}
            nb_proc = 1 if cloud else nb_proc
            run_software(
                software_name=SOFTWARE_NAME,
                arguments=[config_file[0]],
                wkdir=config_dir,
                with_mpi=True,
                nb_cpu=1,
                log_bool=True,
                progress_callback=progress_callback,
                progress_parser=_progress_parser if progress_callback is not None else None,
            )

            if progress_callback is not None:
                progress_callback(
                    detail=f"{label} · SU2 completed.",
                    progress=1.0,
                )

            check_force_files_exists(config_dir)
