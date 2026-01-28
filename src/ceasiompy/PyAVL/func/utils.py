"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Utils for PyAVL module.
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import numpy as np

from pydantic import validate_call
from ceasiompy.utils.mathsfunctions import non_dimensionalize_rate

from pathlib import Path
from numpy import ndarray
from itertools import product
from ambiance import Atmosphere
from tixi3.tixi3wrapper import Tixi3
from ceasiompy.utils.generalclasses import Point
from typing import (
    List,
    Tuple,
    TextIO,
)

from ceasiompy.utils.commonxpaths import (
    REF_XPATH,
    AREA_XPATH,
    LENGTH_XPATH,
)
from ceasiompy import (
    log,
    ceasiompy_cfg,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def practical_limit_rate_check(
    tixi: Tixi3,
    alt_list: list,
    mach_list: list,
    rotation_rates_list: list,
) -> None:
    '''
    See: https://web.mit.edu/drela/Public/web/avl/AVL_User_Primer.pdf
    '''
    rotation_rates = list(set(rotation_rates_list))

    # Get the reference dimensions
    s = tixi.getDoubleElement(AREA_XPATH)
    c = tixi.getDoubleElement(LENGTH_XPATH)
    b = s / c

    # Speed of sound is lower at higher altitude
    Atm = Atmosphere(max(alt_list))

    # With a lower mach we have a lower reference velocity
    velocity = Atm.speed_of_sound[0] * min(mach_list)

    # See https://web.mit.edu/drela/Public/web/avl/AVL_User_Primer.pdf
    # for how he non-dimensionalize the rates
    for _, rotation_rate in enumerate(rotation_rates):
        roll_rate_star, pitch_rate_star, yaw_rate_star = non_dimensionalize_rate(
            p=rotation_rate,
            q=rotation_rate,
            r=rotation_rate,
            v=velocity,
            b=b,
            c=c,
        )

        # AVL practical checks
        if not (-0.10 < roll_rate_star < 0.10):
            raise ValueError(f"pb/2V={roll_rate_star:.3f} out of range (-0.10, 0.10)")
        if not (-0.03 < pitch_rate_star < 0.03):
            raise ValueError(f"qc/2V={pitch_rate_star:.3f} out of range (-0.03, 0.03)")
        if not (-0.25 < yaw_rate_star < 0.25):
            raise ValueError(f"rb/2V={yaw_rate_star:.3f} out of range (-0.25, 0.25)")


def get_points_ref(tixi: Tixi3) -> ndarray:
    return np.array([
        tixi.getDoubleElement(REF_XPATH + "/point/x"),
        tixi.getDoubleElement(REF_XPATH + "/point/y"),
        tixi.getDoubleElement(REF_XPATH + "/point/z"),
    ])


def write_control(
    avl_file: TextIO,
    control_type: str,
    hinge_xsi: float,
    axis: str,
    control_bool: float,
) -> None:
    """Helper function to write CONTROL section."""
    avl_file.write("CONTROL\n")
    avl_file.write(f"{control_type} 1.0 {hinge_xsi} {axis} {control_bool}\n\n")


def split_dir(dir_name: str, index: int, param: str) -> float:
    part = dir_name.split("_")[index]
    if param not in part:
        raise ValueError(f"Parameter '{param}' not found in '{part}' (from '{dir_name}')")
    return float(part.split(param)[1])


def split_line(line: str, index: int) -> float:
    return float(line.split("=")[index].strip().split()[0])


def get_atmospheric_cond(alt: float, mach: float) -> Tuple[float, float, float]:
    Atm = Atmosphere(alt)
    density = Atm.density[0]
    g = Atm.grav_accel[0]
    velocity = Atm.speed_of_sound[0] * mach

    return density, g, velocity


def create_case_dir(results_dir: Path, i_case: int, alt: float, **params: float) -> Path:
    # Log the parameters
    param_log = ", ".join(f"{key}: {value}" for key, value in params.items())
    log.info(f"--- alt: {alt}, {param_log} ---")

    # Create the case directory name dynamically
    case_dir_name = f"Case{str(i_case).zfill(2)}_alt{alt}" + "".join(
        f"_{key}{round(value, 2) if isinstance(value, float) else value}"
        for key, value in params.items()
    )

    # Create the directory
    case_dir_path = Path(results_dir, case_dir_name)
    case_dir_path.mkdir(exist_ok=True)

    return case_dir_path


def convert_dist_to_avl_format(vortex_dist: str) -> int:
    if vortex_dist == "cosine":
        return 1
    elif vortex_dist == "sine":
        return 2
    else:
        return 3


def to_cpacs_format(point: Point) -> str:
    return str(point.x) + "\t" + str(point.y) + "\t" + str(point.z)


@validate_call(config=ceasiompy_cfg)
def duplicate_elements(expand: bool, *lists: List) -> Tuple[List, ...]:
    """
    Duplicates lists such that there is a unique combination of them
    and the last three lists are zero-independent.

    zero-independent: For a unique combination of elements, you will have,
        (elem1, ..., elemn) (value, 0.0, 0.0)
        (elem1, ..., elemn) (0.0, value, 0.0)
        (elem1, ..., elemn) (0.0, 0.0, value)

    Objective:
        SDSA requires data of the specified type.

    Returns:
        (Tuple[List, ...]): Number of *lists + 2, where the 3 last lists are zero-independent.

    """

    # Ensure each elements in the list are unique
    if expand:
        lists = tuple([list(set(list_)) for list_ in lists])

    *initial_lists, last_list = lists

    if expand:
        # Keep existing pairing between initial lists (no Cartesian product)
        combinations = list(product(*initial_lists))
    else:
        combinations = list(zip(*initial_lists))

    n = len(initial_lists)
    new_lists = [[] for _ in initial_lists] + [[] for _ in range(3)]

    def append_combination(combination: List, values: List) -> None:
        """Appends a combination with specific values."""
        for i, entry in enumerate(combination):
            new_lists[i].append(entry)
        for j, value in enumerate(values):
            new_lists[n + j].append(value)

    for value in last_list:
        if value == 0.0:
            for combination in combinations:
                append_combination(combination, [0.0, 0.0, 0.0])
        else:
            for combination in combinations:
                append_combination(combination, [value, 0.0, 0.0])
            for combination in combinations:
                append_combination(combination, [0.0, value, 0.0])
            for combination in combinations:
                append_combination(combination, [0.0, 0.0, value])

    return tuple(new_lists)
