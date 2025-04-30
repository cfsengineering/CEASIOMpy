"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Extract results from AVL calculations and save them in a CPACS file.

| Author: Leon Deligny
| Creation: 2025-Feb-14

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from cpacspy.aeromap import get_filter
from cpacspy.cpacsfunctions import get_value
from ceasiompy.PyAVL.func.plot import plot_lift_distribution
from ceasiompy.PyAVL.func.utils import (
    split_dir,
    split_line,
)
from ceasiompy.utils.ceasiompyutils import (
    bool_,
    ensure_and_append_text_element,
)

from typing import Tuple
from pathlib import Path
from cpacspy.cpacspy import CPACS, AeroMap
from tixi3.tixi3wrapper import Tixi3

from ceasiompy import log
from ceasiompy.PyAVL.func import AVL_COEFS
from ceasiompy.PyAVL import (
    AVL_XPATH,
    AVL_TABLE_XPATH,
    AVL_PLOTLIFT_XPATH,
    AVL_CTRLTABLE_XPATH,
    AVL_AEROMAP_UID_XPATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_avl_aerocoefs(force_file: Path) -> Tuple[
    float, float, float,
    float, float, float,
    float, float, float,
]:
    """
    Get aerodynamic coefficients and velocity from AVL total forces file (sb.txt).

    Args:
        force_file_ft (Path): Path to the AVL total forces file.

    Returns:
        cl (float): Lift coefficient.
        cd (float): Drag coefficient.
        cs (float): Side force coefficient.
        cmd (float): Rolling moment.
        cml (float): Yawing moment.
        cms (float): Pitching moment.
        cms_a (float): Derivative of Pitching moment with respect to the angle of attack.
        cml_b (float): Derivative of Yawing moment with respect to the sidesplip angle.
        cmd_b (float): Derivative of Rolling moment with respect to the sidesplip angle.

    """

    results = {key: None for key in AVL_COEFS.values()}

    with open(force_file) as f:
        for line in f.readlines():
            for key, (index, var_name) in AVL_COEFS.items():
                if key in line:
                    # Exception as they appear twice in .txt file
                    if key in ["Clb", "Cnb"]:
                        parts = line.split('=')
                        if len(parts) > 2:
                            results[var_name] = split_line(line, index)
                    else:
                        results[var_name] = split_line(line, index)

    return (
        results["cd"], results["cs"], results["cl"],
        results["cmd"], results["cms"], results["cml"],
        results["cmd_b"], results["cms_a"], results["cml_b"],
    )


def add_coefficients_in_aeromap(
    cpacs: CPACS,
    alt: float,
    mach: float,
    aos: float,
    aoa: float,
    fs_file_path: Path,
    st_file_path: Path,
    config_dir: Path,
) -> None:
    """
    Add aerodynamic coefficients from PyAVL in chosen aeromap.

    Args:
        cpacs (CPACS): CPACS file.
        alt (float): Altitude.
        mach (float): Mach Number.
        aos (float): SideSlip angle.
        aoa (float): Angle of attack.
        fs_file_path (Path): Path to force coefficients for plot.
        st_file_path (Path): Path to moment coefficients.
        config_dir (Path): Configuration Directory for plot.

    """

    tixi = cpacs.tixi

    cl, cd, cs, cmd, cml, cms, cms_a, cml_b, cmd_b = get_avl_aerocoefs(st_file_path)

    plot = bool_(get_value(tixi, AVL_PLOTLIFT_XPATH))

    if plot:
        plot_lift_distribution(fs_file_path, aoa, aos, mach, alt, wkdir=config_dir)

    aeromap_uid = get_value(tixi, AVL_AEROMAP_UID_XPATH)
    log.info(f"Loading coefficients in {aeromap_uid=}")
    aeromap: AeroMap = cpacs.get_aeromap_by_uid(aeromap_uid)

    filt = get_filter(aeromap.df, [alt], [mach], [aos], [aoa])
    if aeromap.df.loc[filt].empty:
        aeromap.add_row(
            alt=alt,
            mach=mach,
            aos=aos,
            aoa=aoa,
        )

    # Add coefficients to the aeromap
    aeromap.add_coefficients(
        alt=alt,
        mach=mach,
        aos=aos,
        aoa=aoa,
        cd=cd,
        cl=cl,
        cs=cs,
        cmd=cmd,
        cml=cml,
        cms=cms
    )

    increment_maps_xpath = f"{aeromap.xpath}/incrementMaps"
    increment_map_xpath = f"{increment_maps_xpath}/incrementMap"

    # Ensure the incrementMaps and incrementMap elements exist
    if not tixi.checkElement(increment_maps_xpath):
        tixi.createElement(aeromap.xpath, "incrementMaps")
    if not tixi.checkElement(increment_map_xpath):
        tixi.createElement(increment_maps_xpath, "incrementMap")

    # Add text elements for the coefficients
    ensure_and_append_text_element(tixi, increment_map_xpath, "dcmd", str(cmd_b))
    ensure_and_append_text_element(tixi, increment_map_xpath, "dcms", str(cms_a))
    ensure_and_append_text_element(tixi, increment_map_xpath, "dcml", str(cml_b))

    aeromap.save()


def add_coefficients(
    tixi: Tixi3,
    xpath: str,
    table_name: str,
    coefficients: dict,
) -> None:
    """
    Adds aerodynamic coefficients to a specified table.
    """

    if not tixi.checkElement(xpath):
        tixi.createElement(AVL_XPATH, table_name)

    # Add text elements for the coefficients
    for name, value in coefficients.items():
        ensure_and_append_text_element(tixi, xpath, name, str(value))


def add_coefficients_in_table(
    tixi: Tixi3,
    mach: float,
    aos: float,
    aoa: float,
    p: float,
    q: float,
    r: float,
    st_file_path: Path,
) -> None:
    """
    Add aerodynamic coefficients from PyAVL in specific table.
    xPath of Table: AVL_TABLE_XPATH.

    Args:
        cpacs (CPACS): CPACS file.
        mach (float): Mach Number.
        aos (float): SideSlip angle.
        aoa (float): Angle of attack.
        p (float): Roll rate.
        q (float): Pitch rate.
        r (float): Yaw rate.
        st_file_path (Path): Path to moment coefficients.

    """

    cd, cs, cl, cmd, cms, cml, _, _, _ = get_avl_aerocoefs(st_file_path)

    coefficients = {
        "mach": mach,
        "aoa": aoa, "aos": aos,
        "p": p, "q": q, "r": r,
        "cd": cd, "cs": cs, "cl": cl,
        "cmd": cmd, "cms": cms, "cml": cml,
    }

    add_coefficients(tixi, AVL_TABLE_XPATH, "Table", coefficients)


def add_coefficients_in_ctrltable(
    tixi: Tixi3,
    mach: float,
    aoa: float,
    aileron: float,
    elevator: float,
    rudder: float,
    st_file_path: Path,
) -> None:
    """
    Add aerodynamic coefficients from PyAVL in specific ctrltable.
    xPath of Table: AVL_CTRLTABLE_XPATH.

    Args:
        cpacs (CPACS): CPACS file.
        mach (float): Mach Number.
        aos (float): SideSlip angle.
        aoa (float): Angle of attack.
        aileron (float): Aileron rate.
        elevator (float): Elevator rate.
        rudder (float): Rudder rate.
        st_file_path (Path): Path to moment coefficients.

    """

    cd, cs, cl, cmd, cms, cml, _, _, _ = get_avl_aerocoefs(st_file_path)

    coefficients = {
        "mach": mach,
        "aoa": aoa,
        "aileron": aileron, "elevator": elevator, "rudder": rudder,
        "cd": cd, "cs": cs, "cl": cl,
        "cmd": cmd, "cms": cms, "cml": cml,
    }

    add_coefficients(tixi, AVL_CTRLTABLE_XPATH, "CtrlTable", coefficients)


def get_force_files(config_dir: Path) -> Tuple[Path, Path]:
    st_file_path = Path(config_dir, "st.txt")
    if not st_file_path.exists():
        raise FileNotFoundError(
            f"No result total forces 'st.txt' file have been found at {st_file_path}. "
        )

    fs_file_path = Path(config_dir, "fs.txt")
    if not fs_file_path.exists():
        raise FileNotFoundError(
            f"No result strip forces 'fs.txt' file have been found {fs_file_path}"
        )

    return st_file_path, fs_file_path


def get_avl_results(cpacs: CPACS, results_dir: Path) -> None:
    """
    Write AVL results in a CPACS file at xPath:
    '/cpacs/vehicles/aircraft/model/analyses/aeroPerformance/aeroMap[n]/aeroPerformanceMap'
    """

    tixi = cpacs.tixi
    case_dir_list = [
        case_dir
        for case_dir in results_dir.iterdir()
        if ("Case" in case_dir.name) and (case_dir.is_dir())
    ]

    for config_dir in sorted(case_dir_list):
        dir_name = config_dir.name
        st_file_path, fs_file_path = get_force_files(config_dir)

        # Extract common parameters
        alt = split_dir(dir_name, 1, "alt")
        mach = split_dir(dir_name, 2, "mach")
        aoa = split_dir(dir_name, 3, "aoa" if "p" in dir_name else "alt")

        if "p" in dir_name:  # Standard aeromap or dynamic stability
            aos = split_dir(dir_name, 4, "aos")
            q = split_dir(dir_name, 5, "q")
            p = split_dir(dir_name, 6, "p")
            r = split_dir(dir_name, 7, "r")

            if (p == 0.0) and (q == 0.0) and (r == 0.0):
                add_coefficients_in_aeromap(
                    cpacs,
                    alt,
                    mach,
                    aos,
                    aoa,
                    fs_file_path,
                    st_file_path,
                    config_dir,
                )

            # Add coefficients for dynamic stability
            add_coefficients_in_table(
                tixi,
                mach,
                aos,
                aoa,
                p,
                q,
                r,
                st_file_path,
            )
        else:  # Control surface deflections for dynamic stability
            aileron = split_dir(dir_name, 4, "aileron")
            elevator = split_dir(dir_name, 5, "elevator")
            rudder = split_dir(dir_name, 6, "rudder")

            # Add coefficients for control surface deflections
            add_coefficients_in_ctrltable(
                tixi,
                mach,
                aoa,
                aileron,
                elevator,
                rudder,
                st_file_path,
            )

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
