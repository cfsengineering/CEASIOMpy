"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Utils for PyAVL module.

Python version: >=3.8

| Author: Leon Deligny
| Creation: 2025-Feb-28

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pydantic import validate_call
from cpacspy.cpacsfunctions import get_value
from ceasiompy.PyAVL.func.config import get_option_settings
from ceasiompy.PyAVL.func.cpacs2avl import convert_cpacs_to_avl
from ceasiompy.utils.ceasiompyutils import get_aeromap_conditions

from pathlib import Path
from itertools import product
from cpacspy.cpacspy import CPACS

from typing import (
    List,
    Tuple,
)

from ceasiompy import (
    log,
    ceasiompy_cfg,
)

from ceasiompy.utils.commonxpath import (
    AVL_NB_CPU_XPATH,
    AVL_AEROMAP_UID_XPATH,
    AVL_CTRLSURF_ANGLES_XPATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


@validate_call(config=ceasiompy_cfg)
def retrieve_gui_values(cpacs: CPACS) -> Tuple[
    List, List, List, List,
    List, List,
    Path, bool,
    int,
]:
    tixi = cpacs.tixi
    alt_list, mach_list, aoa_list, aos_list = get_aeromap_conditions(cpacs, AVL_AEROMAP_UID_XPATH)
    save_fig, _, _, _, _, rotation_rates_float = get_option_settings(tixi)
    control_surface_float = get_value(tixi, AVL_CTRLSURF_ANGLES_XPATH)

    # Convert to lists
    rotation_rate_list = [float(x) for x in str(rotation_rates_float).split(';')]
    control_surface_list = [float(x) for x in str(control_surface_float).split(';')]

    avl_path = convert_cpacs_to_avl(tixi)

    nb_cpu = int(get_value(tixi, AVL_NB_CPU_XPATH))

    return (
        alt_list, mach_list, aoa_list, aos_list,
        rotation_rate_list, control_surface_list,
        avl_path,
        save_fig,
        nb_cpu,
    )


@validate_call(config=ceasiompy_cfg)
def duplicate_elements(*lists: List) -> Tuple[List, ...]:
    """
    Duplicates lists such that there is a unique combination of them
    and the last three lists are zero-independent.

    zero-independent: For a unique combination of elements, you will have,
        (elem1, ..., elemn) (value, 0.0, 0.0)
        (elem1, ..., elemn) (0.0, value, 0.0)
        (elem1, ..., elemn) (0.0, 0.0, value)

    Returns:
        new_lists (Tuple[List, ...]): Number of *lists + 2, where the 3 last lists are zero-independent.

    """
    if len(lists) < 2:
        return tuple(lists)

    *initial_lists, last_list = lists
    combinations = list(product(*initial_lists))

    n = len(initial_lists)
    new_lists = [[] for _ in initial_lists] + [[] for _ in range(3)]

    for value in last_list:
        if value == 0.0:
            for combination in combinations:
                for i, entry in enumerate(combination):
                    new_lists[i].append(entry)

                new_lists[n].append(0.0)
                new_lists[n + 1].append(0.0)
                new_lists[n + 2].append(0.0)

        else:
            for combination in combinations:
                for i, entry in enumerate(combination):
                    new_lists[i].append(entry)

                new_lists[n].append(value)
                new_lists[n + 1].append(0.0)
                new_lists[n + 2].append(0.0)

            for combination in combinations:
                for i, entry in enumerate(combination):
                    new_lists[i].append(entry)

                new_lists[n].append(0.0)
                new_lists[n + 1].append(value)
                new_lists[n + 2].append(0.0)

            for combination in combinations:
                for i, entry in enumerate(combination):
                    new_lists[i].append(entry)

                new_lists[n].append(0.0)
                new_lists[n + 1].append(0.0)
                new_lists[n + 2].append(value)

    return tuple(new_lists)

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute.")
