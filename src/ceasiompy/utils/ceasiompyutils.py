"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions utils to run ceasiompy workflows
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import re
import os
import math
import shutil
import importlib
import subprocess
import streamlit as st

from pydantic import validate_call
from contextlib import contextmanager
from ceasiompy.utils.moduleinterfaces import get_module_list
from ceasiompy.utils.moduleinterfaces import (
    get_toolinput_file_path,
    get_tooloutput_file_path,
    check_cpacs_input_requirements,
)
from cpacspy.cpacsfunctions import (
    get_value,
    open_tixi,
    create_branch,
    add_string_vector,
    get_string_vector,
    get_value_or_default,
)

from pathlib import Path
from numpy import ndarray
from pandas import DataFrame
from unittest.mock import MagicMock
from tixi3.tixi3wrapper import Tixi3
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)
from typing import (
    List,
    Tuple,
    TextIO,
    Optional,
    Callable,
)

from ceasiompy import (
    log,
    ceasiompy_cfg,
)
from ceasiompy import (
    WKDIR_PATH,
    CPACS_FILES_PATH,
)
from ceasiompy.utils.moduleinterfaces import (
    MODNAME_INIT,
    MODNAME_SPECS,
)

from ceasiompy.utils.cpacsxpaths import AIRCRAFT_NAME_XPATH
from ceasiompy.utils.guixpaths import (
    RANGE_CRUISE_ALT_XPATH,
    RANGE_CRUISE_MACH_XPATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def write_inouts(
    tixi: Tixi3,
    df: DataFrame,
    inout: ndarray,
) -> None:
    """
    Write the specified input or the predicted output of the model
    to the CPACS file.

    Use case of this function is for surrogate modules.
    """

    df.fillna("-", inplace=True)
    for i, name in enumerate(df.index):
        value = inout[0][i]
        if df.loc[name, "setcmd"] != "-":
            # Only allow assignment to tixi elements via XPath
            xpath = df.loc[name, "setcmd"]
            create_branch(tixi, xpath)
            tixi.updateDoubleElement(xpath, value, "%g")
        elif df.loc[name, "getcmd"] != "-":
            xpath = df.loc[name, "getcmd"]
            create_branch(tixi, xpath)
            tixi.updateDoubleElement(xpath, value, "%g")


@contextmanager
def change_working_dir(working_dir):
    """Context manager to change the working directory just before the execution of a function."""

    cwd = None
    try:
        cwd = os.getcwd()
        os.chdir(working_dir)
        yield
    finally:
        if cwd is not None:
            os.chdir(cwd)


def ensure_and_append_text_element(
    tixi: Tixi3, parent_xpath: str, element_name: str, text: str
) -> None:
    """
    Ensures element (element_name) exists at xpath (parent_xpath),
    and appends data (text) to this element.

    Args:
        tixi (Tixi3): Tixi HANDLE of CPACS file.
        parent_xpath (str): xPath to the element.
        element_name (str): Name of element.
        text (str): Data to append.

    """

    element_xpath = f"{parent_xpath}/{element_name}"
    if not tixi.checkElement(element_xpath):
        tixi.addTextElement(parent_xpath, element_name, text)
        tixi.addTextAttribute(element_xpath, "mapType", "vector")
    else:
        existing_text = tixi.getTextElement(element_xpath)
        new_text = existing_text + ";" + text
        tixi.updateTextElement(element_xpath, new_text)


def get_aeromap_list_from_xpath(cpacs, aeromap_to_analyze_xpath, empty_if_not_found=False):
    """Get a list of aeromap from the xpath where it is stored, if not define, return all aeromaps
    and save them at the given xpath.

    Args:
        cpacs (obj): CPACS object (from cpacspy).
        aeromap_to_analyze_xpath (str): Xpath where the list of aeromap to analyze is stored.
        empty_if_not_found (bool): If true, return an empty list if the xpath did not exist.

    """
    tixi = cpacs.tixi

    aeromap_uid_list = []
    try:
        aeromap_uid_list = get_string_vector(tixi, aeromap_to_analyze_xpath)
    except ValueError:  # if aeroMapToPlot is not defined, select all aeromaps
        if not empty_if_not_found:
            aeromap_uid_list = cpacs.get_aeromap_uid_list()
            create_branch(tixi, aeromap_to_analyze_xpath)
            add_string_vector(tixi, aeromap_to_analyze_xpath, aeromap_uid_list)

    return aeromap_uid_list


def get_results_directory(module_name: str, create: bool = True, wkflow_dir: Path = None) -> Path:
    """
    Returns the results directory of a module.

    Args:
        module_name (str): Name of the module's result directory.
        create (bool): If you need to create it.
        wkflow_dir (Path): Path to the workflow of the module.

    """

    if module_name not in get_module_list(only_active=False):
        raise ValueError(f"Module '{module_name}' does not exist.")

    init = importlib.import_module(f"ceasiompy.{module_name}.{MODNAME_INIT}")
    if wkflow_dir is None:
        wkflow_dir = Path.cwd()
    results_dir = Path(wkflow_dir, "Results", init.MODULE_NAME)

    if create and not results_dir.is_dir():
        results_dir.mkdir(parents=True)

    return results_dir


def get_wkdir_status(module_name: str) -> bool:
    init = importlib.import_module(f"ceasiompy.{module_name}.{MODNAME_INIT}")
    return init.RES_DIR


def get_workflow_idx(wkflow_idx: int) -> str:
    return f"Workflow_{str(wkflow_idx).rjust(3, '0')}"


def current_workflow_dir() -> Path:
    """
    Get the current workflow directory.
    """

    # collect numeric suffixes only (defensive against unexpected folder names)
    idx_list: List[int] = []

    pattern = re.compile(r"Workflow_(\d+)$")
    for p in WKDIR_PATH.iterdir():
        if not p.is_dir():
            log.warning(f"There should be only Directories in {WKDIR_PATH=}")
            continue

        m = pattern.match(p.name)
        if m:
            try:
                idx_list.append(int(m.group(1)))
            except ValueError as e:
                log.error(f"Could not process pattern of workflows {e=}")

    if idx_list:
        max_idx = max(idx_list)
        last_wkflow_dir = WKDIR_PATH / get_workflow_idx(max_idx)

        # If the last workflow contains the toolinput file, we increment index
        if (
            (last_wkflow_dir / "ceasiompy.cfg").exists()
        ):
            new_idx = max_idx + 1
        else:
            new_idx = max_idx
    else:
        new_idx = 1

    current_wkflow_dir = WKDIR_PATH / get_workflow_idx(new_idx)
    current_wkflow_dir.mkdir(parents=True, exist_ok=True)

    return current_wkflow_dir


def initialize_cpacs(module_name: str) -> Tuple[CPACS, Path]:
    cpacs_in = get_toolinput_file_path(module_name)
    cpacs_out = get_tooloutput_file_path(module_name)
    check_cpacs_input_requirements(cpacs_in)
    cpacs = CPACS(cpacs_in)
    return cpacs, cpacs_out


def get_install_path(software_name: str, raise_error: bool = False) -> Path:
    """Return the installation path of a software.

    Args:
        software_name (str): Name of the software.
        raise_error (bool, optional): If True, raise an error if the software is not installed.

    """

    install_path = shutil.which(software_name)

    if install_path is not None:
        log.info(f"{software_name} is installed at: {install_path}")
        return Path(install_path)

    log.warning(f"{software_name} is not installed on your computer!")

    if raise_error:
        log.warning(f"{software_name} is not installed on your computer!")
    else:
        return None


def check_version(software_name: str, required_version: str) -> Tuple[bool, str]:
    """
    Check if the version is greater than or equal to the required version.
    """

    version = get_version(software_name)
    if version is None:
        return False, ""

    version_tuple = tuple(map(int, version.split(".")))
    required_version_tuple = tuple(map(int, required_version.split(".")))

    return version_tuple >= required_version_tuple, version


def get_version(software_name: str) -> str:
    """
    Return the installed version of a software.
    Looks at X.X.X pattern in installation path.
    """

    version_file = get_install_path(software_name)

    if not version_file.exists():
        log.warning(f"The version file for {software_name} does not exist!")
        return ""

    version_pattern = re.compile(r"\d+\.\d+\.\d+")
    match = version_pattern.search(str(version_file))

    if match:
        return match.group(0)
    else:
        log.warning(f"Version information not found in the path: {version_file}.")
        return ""


def run_software(
    software_name: str,
    arguments: List[str],
    wkdir: Path,
    with_mpi: bool = False,
    nb_cpu: int = 1,
    stdin: Optional[TextIO] = None,
    log_bool: bool = True,
    xvfb: bool = False,
) -> None:
    """Run a software with the given arguments in a specific wkdir. If the software is compatible
    with MPI, 'with_mpi' can be set to True and the number of processors can be specified. A
    logfile will be created in the wkdir.

    Args:
        software_name (str): Name of the software to run.
        arguments (str): Arguments to pass to the software.
        wkdir (Path, optional): Working directory where the software will be run.
        with_mpi (bool = False): If True, run the software with MPI. Defaults to False.
        nb_cpu (int = 1): Number of processors to use. Defaults to 1. If with_mpi is True,
        #TODO: Add rest of documentation
    """

    # Check nb_cpus
    nb_cpu = nb_cpu if with_mpi else 1

    if nb_cpu > 1:
        check_nb_cpu(nb_cpu)

    log.info(
        f"{int(nb_cpu)} cpu{'s' if nb_cpu > 1 else ''} "
        f"over {os.cpu_count()} will be used for this calculation."
    )

    if software_name == "pentagrow" or software_name == "Pentagrow":
        ceasiompy_root = Path(__file__).resolve().parents[3]
        install_path = ceasiompy_root / "installation" / "Pentagrow" / "bin" / "pentagrow"
    else:
        install_path = get_install_path(software_name)

    command_line = []
    if with_mpi:
        mpi_install_path = get_install_path("mpirun")  # "mpirun.mpich"
        # If runs with open mpi add --allow-run-as-root
        if mpi_install_path is not None:
            command_line += [mpi_install_path, "-np", str(int(nb_cpu))]

    command_line += [install_path]
    command_line += arguments

    if xvfb:
        command_line = ["xvfb-run", "--auto-servernum"] + command_line
    else:
        log.warning("xvfb-run not found. Proceeding without it.")

    log.info(f">>> Running {software_name} on {int(nb_cpu)} cpu(s)")
    log.info(f"Working directory: {wkdir}")
    log.info("Command line that will be run is:")
    log.info(" ".join(map(str, command_line)))

    with change_working_dir(wkdir):
        if log_bool:
            logfile = Path(wkdir, f"logfile_{software_name}.log")
            with open(logfile, "w") as logfile:
                if stdin is None:
                    subprocess.run(command_line, stdout=logfile, cwd=wkdir)
                else:
                    subprocess.run(command_line, stdin=stdin, stdout=logfile, cwd=wkdir)
        else:
            if stdin is None:
                subprocess.run(command_line, cwd=wkdir)
            else:
                subprocess.run(command_line, stdin=stdin, cwd=wkdir)

    log.info(f">>> {software_name} End")


def get_reasonable_nb_cpu() -> int:
    """
    Get a reasonable number of processors depending on the total number of processors on
    the host machine. Approximately 1/4 of the total number of processors will be used.
    This function is generally used to set up a default value for the number of processors,
    the user can then override this value with the settings.
    """

    cpu_count = os.cpu_count()

    if cpu_count is None:
        log.warning(
            "Could not figure out the number of CPU(s) on your machine. "
            "This might be an issue with the OS you use."
        )
        return 1

    return math.ceil(cpu_count / 4)


def check_nb_cpu(nb_proc: int) -> None:
    """
    Check if input nb_cpu from GUI is reasonable.
    """
    if not os.cpu_count() > nb_proc:
        log.warning(f"{nb_proc} CPUs is too much for your engine.")
        nb_proc = get_reasonable_nb_cpu()
        log.info(f"Using by default {nb_proc} CPUs.")


def get_conditions_from_aeromap(aeromap: AeroMap) -> Tuple[List, List, List, List]:
    alt_list = aeromap.get("altitude").tolist()
    mach_list = aeromap.get("machNumber").tolist()
    aoa_list = aeromap.get("angleOfAttack").tolist()
    aos_list = aeromap.get("angleOfSideslip").tolist()
    return alt_list, mach_list, aoa_list, aos_list


def get_aeromap_conditions(cpacs: CPACS, uid_xpath: str) -> Tuple[List, List, List, List]:
    """
    Reads the flight conditions from the aeromap.
    """
    tixi = cpacs.tixi

    # Get the first aeroMap as default one or create automatically one
    aeromap_list = cpacs.get_aeromap_uid_list()

    if aeromap_list:
        aeromap_default = aeromap_list[0]

        aeromap_uid = get_value_or_default(tixi, uid_xpath, aeromap_default)
        log.info(f"Used aeromap: {aeromap_uid}.")
        aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)
        alt_list, mach_list, aoa_list, aos_list = get_conditions_from_aeromap(aeromap)
    else:
        default_aeromap = cpacs.create_aeromap("DefaultAeromap")
        default_aeromap.description = "Automatically created AeroMap."

        mach = get_value(tixi, RANGE_CRUISE_MACH_XPATH)
        alt = get_value(tixi, RANGE_CRUISE_ALT_XPATH)

        default_aeromap.add_row(alt=alt, mach=mach, aos=0.0, aoa=0.0)
        default_aeromap.save()

        alt_list = [alt]
        mach_list = [mach]
        aoa_list = [0.0]
        aos_list = [0.0]

        aeromap_uid = get_value_or_default(tixi, uid_xpath, "DefaultAeromap")
        log.info(f"{aeromap_uid} has been created.")

    return alt_list, mach_list, aoa_list, aos_list


def aircraft_name(tixi_or_cpacs) -> str:
    """The function get the name of the aircraft from the cpacs file or add a
        default one if non-existant.

    Args:
        cpacs_path (str): Path to the CPACS file

    Returns:
        name (str): Name of the aircraft.
    """

    # TODO: MODIFY this function, temporary it could accept a cpacs path or tixi handle
    # check xpath
    # *modify corresponding test

    if isinstance(tixi_or_cpacs, Path):
        tixi = open_tixi(tixi_or_cpacs)
    else:
        tixi = tixi_or_cpacs

    name = get_value_or_default(tixi, AIRCRAFT_NAME_XPATH, "Aircraft")

    name = name.replace(" ", "_")
    log.info(f"The name of the aircraft is : {name}")

    return str(name)


def get_part_type(
    cpacs: CPACS,
    part_uid: str,
    print_info: bool = True,
) -> str:
    """The function get the type of the aircraft from the cpacs file.

    Args:
        cpacs_path (Path): Path to the CPACS file
        part_uid (str): UID of the part
        print_info (bool): True if we print the part description

    Returns:
        part_type (str): Type of the part.

    """

    # split uid if mirrored part
    part_uid = part_uid.split("_mirrored")[0]
    part_xpath = cpacs.tixi.uIDGetXPath(part_uid)

    path_part = {
        "wings/wing": "wing",
        "fuselages/fuselage": "fuselage",
        "enginePylons/enginePylon": "pylon",
        "engine/nacelle/fanCowl": "fanCowl",
        "engine/nacelle/centerCowl": "centerCowl",
        "engine/nacelle/coreCowl": "coreCowl",
        "vehicles/engines/engine": "engine",
        "vehicles/rotorcraft/model/rotors/rotor": "rotor",
    }

    for path_name, part_name in path_part.items():
        if path_name in part_xpath:
            if print_info:
                log.info(f"'{part_uid}' is a {part_name}")
            return part_name

    if print_info:
        log.warning(f"'{part_uid}' cannot be categorized!")
    return None


def remove_file_type_in_dir(directory: Path, file_type_list: List[str]) -> None:
    """Remove all files of a given type in a directory.

    Args:
        directory (Path): Path to the directory
        file_type_list (List[str]): List of file types to remove.

    """

    if not directory.exists():
        raise FileNotFoundError(f"The directory {directory} does not exist!")

    for file in directory.iterdir():
        if not file.is_file():
            continue
        if file.suffix in file_type_list:
            file.unlink()
