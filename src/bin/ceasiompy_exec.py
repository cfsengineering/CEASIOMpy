#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Main module of CEASIOMpy to launch workflow by different way.
"""

# Imports

import os
import sys
import signal
import json
import argparse
import subprocess

from ceasiompy.utils.ceasiompyutils import (
    parse_bool,
    has_display,
    workflow_number,
)

from pathlib import Path
from argparse import Namespace

from ceasiompy import log
from ceasiompy.utils.commonpaths import (
    WKDIR_PATH,
    STREAMLIT_PATH,
)


# Methods
def _get_cpu_count() -> int:
    cpus = os.cpu_count()
    if cpus is not None:
        return int(cpus // 2 + 1)

    return 1


def _ensure_conda_prefix_bin_first(env: dict[str, str] | None = None) -> dict[str, str] | None:
    """Ensure `$CONDA_PREFIX/bin` is prepended to PATH when CONDA_PREFIX is set."""

    if env is None:
        conda_prefix = os.environ.get("CONDA_PREFIX")
        if not conda_prefix:
            return None
        conda_bin = str(Path(conda_prefix) / "bin")
        path_parts = [p for p in os.environ.get("PATH", "").split(os.pathsep) if p]
        path_parts = [p for p in path_parts if p != conda_bin]
        os.environ["PATH"] = os.pathsep.join([conda_bin, *path_parts])
        return None

    conda_prefix = env.get("CONDA_PREFIX")
    if not conda_prefix:
        return env
    conda_bin = str(Path(conda_prefix) / "bin")
    path_parts = [p for p in env.get("PATH", "").split(os.pathsep) if p]
    path_parts = [p for p in path_parts if p != conda_bin]
    env["PATH"] = os.pathsep.join([conda_bin, *path_parts])
    return env


def _ensure_usr_bin_in_path(env: dict[str, str] | None = None) -> dict[str, str] | None:
    """Ensure `/usr/bin` is present in PATH."""

    usr_bin = "/usr/bin"
    if env is None:
        path_parts = [p for p in os.environ.get("PATH", "").split(os.pathsep) if p]
        if usr_bin not in path_parts:
            os.environ["PATH"] = os.pathsep.join([*path_parts, usr_bin])
        return None

    path_parts = [p for p in env.get("PATH", "").split(os.pathsep) if p]
    if usr_bin not in path_parts:
        env["PATH"] = os.pathsep.join([*path_parts, usr_bin])
    return env


# Functions

def run_gui(
    # Modify default CEASIOMpy Streamlit
    modules_list: list[str] | None = None,
    geometry_path: Path | None = None,

    # Cloud Instance Parameters
    cpus: int | None = None,
    wkdir: Path | None = None,
    headless: bool = False,
    port: int | None = None,
    address: str | None = None,
    cloud: bool = False,
) -> None:
    """Create and run a workflow from the GUI."""

    if cpus is None:
        cpus = _get_cpu_count()

    if wkdir is None:
        wkdir = WKDIR_PATH

    if not headless and not has_display():
        headless = True
        log.info(
            "No DISPLAY/WAYLAND_DISPLAY detected; starting Streamlit in headless mode "
            "(open the printed URL manually)."
        )

    if wkdir.exists():
        if not wkdir.is_dir():
            raise NotADirectoryError(
                f"The working directory path '{wkdir}' exists but is not a directory."
            )
    else:
        try:
            wkdir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            raise OSError(f"Unable to create working directory '{wkdir}': {exc}") from exc

    log.info("CEASIOMpy has been started from the GUI.")
    env = os.environ.copy()
    _ensure_conda_prefix_bin_first(env)
    # Add CEASIOMpy src directory first, then OpenVSP Python root.
    # The parent directory must be used (not package subdirectories) so
    # `import openvsp` resolves the OpenVSP package correctly.
    project_root = Path(__file__).resolve().parents[2]
    src_dir = project_root / "src"
    vsp_python_root = project_root / "installdir/OpenVSP/python"
    existing_pythonpath = env.get("PYTHONPATH", "")
    py_paths = [str(src_dir), str(vsp_python_root)]
    if existing_pythonpath:
        py_paths.append(existing_pythonpath)

    env["PYTHONPATH"] = os.pathsep.join(py_paths)

    env["CEASIOMPY_CLOUD"] = str(cloud)

    # Environment variables must be strings
    env["MAX_CPUS"] = str(cpus)

    # Expose working directory to the Streamlit app
    env["CEASIOMPY_WKDIR"] = str(wkdir)
    if geometry_path is not None:
        env["CEASIOMPY_GEOMETRY"] = str(geometry_path)
    if modules_list is not None:
        env["CEASIOMPY_MODULES"] = json.dumps(modules_list)

    streamlit_entrypoint = str(STREAMLIT_PATH / "app.py")
    args = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        streamlit_entrypoint,
        "--server.headless", f"{str(headless).lower()}",
    ]

    if port is not None:
        args += [
            "--server.port", f"{port}"
        ]

    if address is not None:
        args += [
            "--server.address", f"{address}"
        ]

    if cloud:
        args += [
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=false",
        ]

    try:
        subprocess.run(
            args=args,
            cwd=STREAMLIT_PATH,
            check=True,
            env=env,
        )
    except FileNotFoundError as exc:
        log.error(
            "Unable to start the GUI because Streamlit is not installed in the current "
            "Python environment."
        )
        raise SystemExit(1) from exc
    except subprocess.CalledProcessError as exc:
        if exc.returncode < 0:
            try:
                sig_name = signal.Signals(-exc.returncode).name
            except Exception:
                sig_name = f"SIG{-exc.returncode}"
            log.error(f"Streamlit crashed ({sig_name}).")
        else:
            log.error(f"Streamlit exited with code {exc.returncode}.")
        raise SystemExit(exc.returncode or 1) from exc


def cleanup_previous_workflow_status(wkdir: Path | None = None) -> None:
    """Remove the last workflow status file without importing Streamlit."""
    if wkdir is None:
        wkdir = WKDIR_PATH

    if not wkdir.exists():
        return

    workflow_dirs = [
        wkdir_entry
        for wkdir_entry in wkdir.iterdir()
        if wkdir_entry.is_dir() and wkdir_entry.name.startswith("Workflow_")
    ]

    if not workflow_dirs:
        return

    last_workflow = max(workflow_dirs, key=workflow_number)
    status_file = last_workflow / "workflow_status.json"

    if status_file.exists():
        try:
            status_file.unlink()
        except OSError:
            pass


# Main

def main() -> None:
    _ensure_conda_prefix_bin_first()
    _ensure_usr_bin_in_path()
    parser = argparse.ArgumentParser(
        description="CEASIOMpy: Open Source Conceptual Aircraft Design Environment.",
        usage=argparse.SUPPRESS,
        add_help=False,
        formatter_class=lambda prog: argparse.RawTextHelpFormatter(
            prog, max_help_position=80, width=99
        ),
    )

    parser.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Show this help message and exit.",
    )

    # By default is GUI
    parser.add_argument(
        "-g",
        "--g",
        "-gui",
        "--gui",

        # Don't look for an argument
        action="store_true",
        help="Creates a CEASIOMpy workflow with the Graphical user interface.",
        required=False,
    )

    parser.add_argument(
        "--geometry",
        help=(
            "Specify the path to your geometry (.vsp, .xml).\n"
            "\n"
            "Examples:\n"
            "  ceasiompy_run --geometry path/to/cpacs.xml\n"
            "  ceasiompy_run --geometry path/to/geometry.vsp\n"
            "\n"
        ),
        type=Path,
        required=False,
    )

    parser.add_argument(
        "--modules",
        nargs="+",
        metavar="",
        default=None,
        type=str,
        required=False,
        help=(
            "Creates a CEASIOMpy workflow by giving the list of modules to run.\n"
            "\n"
            "Examples:\n"
            "  ceasiompy_run --modules pyavl\n"
            "  ceasiompy_run --modules cpacs2gmsh su2run\n"
            "  ceasiompy_run --modules smtrain\n"
            "\n"
        ),
    )

    # Specific to CEASIOMpy Cloud
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        required=False,
        help="Specify a preferred Port.",
    )
    parser.add_argument(
        "--cloud",
        required=False,
        nargs="?",
        const=True,
        type=parse_bool,
        default=False,
        help="If running from a cloud instance.",
    )
    parser.add_argument(
        "--address",
        type=str,
        required=False,
        help="Select server address.",
    )
    parser.add_argument(
        "--wkdir",
        type=Path,
        required=False,
        help="Select specific work directory (for the results).",
    )
    parser.add_argument(
        "--headless",
        required=False,
        nargs="?",
        const=True,
        type=parse_bool,
        default=False,
        help="Run Streamlit in headless mode (no browser auto-open).",
    )
    parser.add_argument(
        "--cpus",
        required=False,
        type=int,
        default=_get_cpu_count(),
        help="Select maximum number of authorized CPUs.",
    )

    args: Namespace = parser.parse_args()

    port = int(args.port) if args.port is not None else None
    wkdir = Path(args.wkdir) if args.wkdir is not None else None
    geometry_path = (
        Path(args.geometry).expanduser().resolve(strict=False)
        if args.geometry is not None
        else None
    )

    cleanup_previous_workflow_status(wkdir)
    run_gui(
        port=port,
        cpus=int(args.cpus),
        wkdir=wkdir,
        headless=args.headless,
        address=args.address,
        cloud=bool(args.cloud),
        modules_list=args.modules if args.modules else None,
        geometry_path=geometry_path,
    )


if __name__ == "__main__":
    main()
