"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Extract results from AVL calculations and save them in a CPACS file.
"""

# Imports

import math

from cpacspy.aeromap import get_filter
from cpacspy.cpacsfunctions import get_value
from ceasiompy.pyavl.func.utils import split_line
from ceasiompy.utils.ceasiompyutils import ensure_and_append_text_element

from pathlib import Path
from pandas import DataFrame
from tixi3.tixi3wrapper import Tixi3
from ceasiompy.pyavl.func.data import AVLData
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)

from ceasiompy import log
from ceasiompy.pyavl.func import AVL_COEFS
from ceasiompy.utils.commonxpaths import SELECTED_AEROMAP_XPATH
from ceasiompy.pyavl import (
    AVL_XPATH,
    AVL_TABLE_XPATH,
    AVL_CTRLTABLE_XPATH,
)

# Functions


def get_avl_aerocoefs(force_file: Path) -> tuple[
    float, float, float,
    float, float, float,
    float,
    float,
    float,
]:
    """
    Get aerodynamic coefficients and velocity from AVL total forces file (st.txt).

    Args:
        force_file_ft (Path): Path to the AVL total forces file.

    Returns:
        cl (float): Lift coefficient.
        cd (float): Drag coefficient.
        cs (float): Side force coefficient.
        cmd (float): Rolling moment.
        cml (float): Yawing moment.
        cms (float): Pitching moment.
        cms_a (float): Derivative of Pitching moment with respect to the angle of attack [deg].
        cml_b (float): Derivative of Yawing moment with respect to the sidesplip angle [deg].
        cmd_b (float): Derivative of Rolling moment with respect to the sidesplip angle [deg].

    """

    results = {key: None for key in AVL_COEFS.values()}

    with open(force_file) as f:
        for line in f.readlines():
            for key, (index, var_name) in AVL_COEFS.items():
                if key in line:
                    # Exception as they appear twice in .txt file
                    if key in ["Clb", "Cnb"]:
                        parts = line.split("=")
                        if len(parts) > 2:
                            results[var_name] = split_line(line, index)
                    else:
                        results[var_name] = split_line(line, index)
    return (
        results["cd"], results["cs"], results["cl"],
        results["cmd"], results["cms"], results["cml"],
        math.radians(results["cmd_b"]),
        math.radians(results["cms_a"]),
        math.radians(results["cml_b"]),
    )


def add_coefficients_in_aeromap(
    cpacs: CPACS,
    avl_data: AVLData,
    st_file_path: Path,
) -> None:
    """
    Add aerodynamic coefficients from PyAVL in selected aeromap.
    """

    tixi = cpacs.tixi
    cd, cs, cl, cmd, cms, cml, cmd_b, cms_a, cml_b = get_avl_aerocoefs(st_file_path)

    aeromap_uid = get_value(tixi, SELECTED_AEROMAP_XPATH)
    log.info(f"Loading coefficients in {aeromap_uid=}")
    aeromap: AeroMap = cpacs.get_aeromap_by_uid(aeromap_uid)

    (
        altitude, mach, alpha, beta
    ) = avl_data.altitude, avl_data.mach, avl_data.alpha, avl_data.beta

    filt = get_filter(
        df=aeromap.df,
        alt_list=[altitude],
        mach_list=[mach],
        aos_list=[beta],
        aoa_list=[avl_data.alpha],
    )
    if aeromap.df.loc[filt].empty:
        aeromap.add_row(
            alt=altitude,
            mach=mach,
            aos=beta,
            aoa=alpha,
        )

    # Add coefficients to the aeromap
    aeromap.add_coefficients(
        alt=altitude,
        mach=mach,
        aos=beta,
        aoa=alpha,
        cd=cd,
        cl=cl,
        cs=cs,
        cmd=cmd,
        cml=cml,
        cms=cms,
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
        "aoa": aoa,
        "aos": aos,
        "p": p,
        "q": q,
        "r": r,
        "cd": cd,
        "cs": cs,
        "cl": cl,
        "cmd": cmd,
        "cms": cms,
        "cml": cml,
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
        "aileron": aileron,
        "elevator": elevator,
        "rudder": rudder,
        "cd": cd,
        "cs": cs,
        "cl": cl,
        "cmd": cmd,
        "cms": cms,
        "cml": cml,
    }

    add_coefficients(tixi, AVL_CTRLTABLE_XPATH, "CtrlTable", coefficients)


def get_force_files(config_dir: Path) -> Path:
    st_file_path = Path(config_dir, "st.txt")
    if not st_file_path.exists():
        raise FileNotFoundError(
            f"No result total forces 'st.txt' file have been found at {st_file_path}"
        )

    return st_file_path


def get_avl_results(
    cpacs: CPACS,
    results_dir: Path,
) -> None:
    """
    Write AVL results in a CPACS file at xPath:
    '/cpacs/vehicles/aircraft/model/analyses/aeroPerformance/aeroMap[n]/aeroPerformanceMap'
    """

    tixi = cpacs.tixi
    case_dir_list = [
        case_dir
        for case_dir in results_dir.iterdir()
        if ("case" in case_dir.name) and (case_dir.is_dir())
    ]

    total_avl_results = []
    eps = 1e-12

    for config_dir in sorted(case_dir_list):
        st_file_path = get_force_files(config_dir)
        avl_data = AVLData.load_json(Path(config_dir, "avldata.json"))

        if (
            (abs(avl_data.p) <= eps) and (abs(avl_data.q) <= eps) and (abs(avl_data.r) <= eps)
            and (abs(avl_data.aileron) <= eps)
            and (abs(avl_data.rudder) <= eps)
            and (abs(avl_data.elevator) <= eps)
        ):
            add_coefficients_in_aeromap(
                cpacs=cpacs,
                avl_data=avl_data,
                st_file_path=st_file_path,
            )
        elif (
            (abs(avl_data.p) > eps) or (abs(avl_data.q) > eps) or (abs(avl_data.r) > eps)
        ):
            add_coefficients_in_table(
                tixi=tixi,
                mach=avl_data.mach,
                aos=avl_data.beta,
                aoa=avl_data.alpha,
                p=avl_data.p,
                q=avl_data.q,
                r=avl_data.r,
                st_file_path=st_file_path,
            )
        else:
            add_coefficients_in_ctrltable(
                tixi=tixi,
                mach=avl_data.mach,
                aoa=avl_data.alpha,
                aileron=avl_data.aileron,
                elevator=avl_data.elevator,
                rudder=avl_data.rudder,
                st_file_path=st_file_path,
            )

        cd, cs, cl, cmd, cms, cml, _, _, _ = get_avl_aerocoefs(st_file_path)
        total_avl_results.append(
            {
                **avl_data.case_key(),
                "cd": cd,
                "cs": cs,
                "cl": cl,
                "cmd": cmd,
                "cms": cms,
                "cml": cml,
            }
        )

    # Remove columns with (p, q, r or aileron rudder elevator)
    # if they have only 0.0 entries everywhere
    if not total_avl_results:
        log.warning(f"No AVL case results found in {results_dir}")
        return None

    df = DataFrame(total_avl_results)
    cols_maybe_zero = ["p", "q", "r", "aileron", "rudder", "elevator"]
    cols_to_drop = []
    for col in cols_maybe_zero:
        if col in df.columns and (df[col].abs() <= eps).all():
            cols_to_drop.append(col)
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)

    # Store in CSV format of total results configuration inside results_dir
    csv_path = Path(results_dir, "avl_simulations_results.csv")
    df.to_csv(csv_path, index=False)
    log.info(f"Saved AVL aggregated results to {csv_path}")
