#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Main module of CEASIOMpy to launch workflow by different way.

| Author: Aidan Jungo
| Creation: 2022-03-29

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import sys
import signal
import argparse
import subprocess

from ceasiompy.utils.ceasiompyutils import current_workflow_dir

from pathlib import Path
from argparse import Namespace
from ceasiompy.utils.workflowclasses import Workflow

from ceasiompy import log
from unittest.mock import patch
from ceasiompy.utils.commonpaths import (
    WKDIR_PATH,
    STREAMLIT_PATH,
    TEST_CASES_PATH,
    CPACS_FILES_PATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def _get_cpu_count() -> int:
    cpus = os.cpu_count()
    if cpus is not None:
        return int(cpus // 2 + 1)

    return 1


def _parse_bool(value: str) -> bool:
    """Parse a CLI boolean value."""

    normalized = value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value!r}")


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


def testcase_message(testcase_nb: int) -> None:
    """Top message to show when a test case is run."""

    log.info(f"CEASIOMpy as been started from test case {testcase_nb}")

    log.info("")
    log.info("#" * 30)
    log.info(f"### CEASIOMpy: Test case {testcase_nb} ###")
    log.info("#" * 30)
    log.info("More information about this test case at:")
    log.info(
        "https://github.com/cfsengineering/CEASIOMpy/blob/main/"
        f"test_cases/test_case_{testcase_nb}/README.md"
    )
    log.info("")


def run_testcase(testcase_nb):
    """Run a test case."""

    if testcase_nb == 1:

        testcase_message(1)

        test_case_1_path = Path(TEST_CASES_PATH, "test_case_1")
        test_case_1_cfg = Path(test_case_1_path, "testcase1.cfg")

        workflow = Workflow()
        workflow.from_config_file(test_case_1_cfg)
        workflow.working_dir = current_workflow_dir()
        workflow.cpacs_in = Path(CPACS_FILES_PATH, "D150_simple.xml")

        workflow.set_workflow()
        workflow.run_workflow(test=True)

        log.info("Congratulations, this Test case is now finished!")
        log.info(f"You can now check your results in: {workflow.current_wkflow_dir}/Results")

    elif testcase_nb == 2:
        testcase_message(2)
        log.info("Use the GUI to create your workflow.")
        run_gui()
        log.info("Congratulations, this Test case is now finished!")

    elif testcase_nb == 3:
        testcase_message(3)
        log.info("Use the GUI to create your workflow.")
        run_gui()
        log.info("Congratulations, this Test case is now finished!")

    elif testcase_nb == 4:
        testcase_message(4)
        log.info(
            "To run this test case, you will need to open a terminal "
            "and run the following command:"
        )
        log.info(">> conda activate ceasiompy")
        log.info(
            ">> ceasiompy_run -m ../test_files/CPACSfiles/D150_simple.xml "
            "PyAVL SkinFriction SaveAeroCoefficients"
        )

    elif testcase_nb == 5:
        testcase_message(5)

    else:
        log.info("Test case number must be 1,2,3,4 or 5.")


def run_modules_list(args_list) -> None:
    """Run a workflow from a CPACS file and a list of modules."""

    if len(args_list) < 2:
        log.warning(
            "At least 2 arguments are required to run a CEASIOMpy, the first onw must be the "
            "CPACS file and the modules to run. You can add as many modules as you want."
        )
        return None

    cpacs_path = Path(args_list[0])
    if cpacs_path.suffix != ".xml":
        log.warning(
            'The first argument of "-m/--modules" option must be the path to a CPACS file.',
        )
        return None

    cwd = os.getcwd()
    new_cpacs_path = Path(Path(cwd), cpacs_path)

    if not new_cpacs_path.exists():
        log.warning(f"The CPACS file {new_cpacs_path} does not exist.")
        return None

    modules_list = args_list[1:]

    log.info("CEASIOMpy has been started from a command line.")
    with patch("streamlit.runtime.scriptrunner_utils.script_run_context"):
        with patch("streamlit.runtime.state.session_state_proxy"):
            workflow = Workflow()
            workflow.cpacs_in = new_cpacs_path
            workflow.modules_list = modules_list
            workflow.module_optim = ["NO"] * len(modules_list)
            workflow.write_config_file()
            workflow.set_workflow()
            workflow.run_workflow(test=True)


def run_config_file(config_file) -> None:
    """Run a workflow from a config file"""

    log.info("CEASIOMpy has been started from a config file.")
    config_file_path = Path(config_file)

    cwd = os.getcwd()
    new_cfg_path = Path(Path(cwd), config_file_path)

    if not new_cfg_path.exists():
        log.warning(f"The config file {new_cfg_path} does not exist.")
        return

    workflow = Workflow()
    workflow.from_config_file(new_cfg_path)
    workflow.working_dir = current_workflow_dir()
    workflow.set_workflow()
    workflow.run_workflow(test=True)


def run_gui(
    cpus: int | None = None,
    wkdir: Path | None = None,
    headless: bool = False,
    port: int | None = None,
) -> None:
    """Create and run a workflow from the GUI."""

    if cpus is None:
        cpus = _get_cpu_count()

    if wkdir is None:
        wkdir = WKDIR_PATH

    if not headless and not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
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
    # Add CEASIOMpy src directory first (for helper modules like `utilities`),
    # then OpenVSP Python roots (for degen_geom, openvsp, etc.) to PYTHONPATH.
    project_root = Path(__file__).resolve().parents[2]
    src_dir = project_root / "src"
    vsp_python_root = project_root / "INSTALLDIR/OpenVSP/python"
    vsp_openvsp_pkg = vsp_python_root / "openvsp"
    degen_geom_pkg = vsp_python_root / "degen_geom"
    vsp_config_pkg = vsp_python_root / "openvsp_config"
    utilities_pkg = vsp_python_root / "utilities"
    env["PYTHONPATH"] = (
        str(src_dir)
        + os.pathsep
        # + str(vsp_python_root)
        # + os.pathsep
        + str(vsp_openvsp_pkg)
        + os.pathsep
        + str(vsp_config_pkg)
        + os.pathsep
        + str(degen_geom_pkg)
        + os.pathsep
        + str(utilities_pkg)
        + os.pathsep
        + env.get("PYTHONPATH", "")
    )

    # Environment variables must be strings
    env["MAX_CPUS"] = str(cpus)

    # Expose working directory to the Streamlit app
    env["CEASIOMPY_WKDIR"] = str(wkdir)

    args = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "✈️_Geometry.py",
        "--server.headless", f"{str(headless).lower()}",
    ]
    if port is not None:
        args += [
            "--server.port", f"{port}"
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

    def workflow_number(path: Path) -> int:
        parts = path.name.split("_")
        if parts and parts[-1].isdigit():
            return int(parts[-1])
        return -1

    last_workflow = max(workflow_dirs, key=workflow_number)
    status_file = last_workflow / "workflow_status.json"

    if status_file.exists():
        try:
            status_file.unlink()
        except OSError:
            pass


# =================================================================================================
#    MAIN
# =================================================================================================


def main() -> None:
    _ensure_conda_prefix_bin_first()
    _ensure_usr_bin_in_path()
    parser = argparse.ArgumentParser(
        description="CEASIOMpy: Conceptual Aircraft Design Environment",
        usage=argparse.SUPPRESS,
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=80, width=99),
    )

    parser.add_argument(
        "-c",
        "--cfg",
        type=str,
        metavar="PATH",
        help="create a CEASIOMpy workflow from a configuration file [PATH to the config file]",
    )
    parser.add_argument(
        "-g",
        "--gui",
        action="store_true",
        help="create a CEASIOMpy workflow with the Graphical user interface",
    )
    parser.add_argument(
        "-p",
        "--port",
        required=False,
        help="Select specific Port.",
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
        type=_parse_bool,
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
    parser.add_argument(
        "-m",
        "--modules",
        nargs="+",
        metavar="",
        default=[],
        help="create a CEASIOMpy workflow by giving the CPACS file and the list of module to run"
        " [Path to the CPACS] [Module list]",
    )
    parser.add_argument(
        "--testcase",
        type=int,
        metavar="NB",
        help="run a test case [1, 2, or 3]",
    )

    args: Namespace = parser.parse_args()

    if args.testcase:
        run_testcase(args.testcase)
        return

    if args.modules:
        run_modules_list(args.modules)
        return

    if args.cfg:
        run_config_file(args.cfg)
        return

    if args.gui:
        port = int(args.port) if args.port is not None else None
        wkdir = Path(args.wkdir) if args.wkdir is not None else None
        cleanup_previous_workflow_status(wkdir)
        run_gui(
            port=port,
            cpus=int(args.cpus),
            wkdir=wkdir,
            headless=args.headless,
        )
        return

    # If no argument is given, print the help
    parser.print_help()


if __name__ == "__main__":
    main()
