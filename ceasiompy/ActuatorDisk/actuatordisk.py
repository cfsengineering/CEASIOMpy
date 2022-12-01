"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This is a script to generate a file with thrust distribution along the blade

Python version: >=3.8

| Author: Giacomo Benedetti
| Creation: 2022-11-03

TODO:

    * Things to improve ...
    * Things to add ...

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ambiance import Atmosphere
from ceasiompy.ActuatorDisk.func.optimalprop import thrust_calculator
from ceasiompy.ActuatorDisk.func.plot_func import function_plot
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.utils.commonxpath import PROP_XPATH, RANGE_XPATH
from ceasiompy.utils.moduleinterfaces import (
    check_cpacs_input_requirements,
    get_toolinput_file_path,
    get_tooloutput_file_path,
)
from cpacspy.cpacsfunctions import get_value_or_default
from cpacspy.cpacspy import CPACS

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def write_actuator_disk(cpacs_path, cpacs_out_path):
    """Function to call every functions in order to obtain the file with thrust and power
    coefficients distribution in order to perform a CFD calculation with SU2

    Args:
        cpacs_path (str): Path to CPACS file
        cpacs_out_path (str):Path to CPACS output file

    """

    cpacs = CPACS(cpacs_path)
    tixi = cpacs.tixi

    results_dir = get_results_directory("ActuatorDisk")
    actuator_disk_dir = Path(results_dir, "ActuatorDisk")
    actuator_disk_dir.mkdir()

    # XPath definition
    cruise_alt_xpath = RANGE_XPATH + "/cruiseAltitude"
    cruise_mach_xpath = RANGE_XPATH + "/cruiseMach"
    stations_xpath = PROP_XPATH + "/propeller/blade/discretization"
    radius_xpath = PROP_XPATH + "/propeller/blade/radius"
    hub_radius_xpath = PROP_XPATH + "/propeller/blade/hub_radius"
    thrust_xpath = PROP_XPATH + "propeller/thrust"
    n_xpath = PROP_XPATH + "propeller/rotational_velocity"
    prandtl_correction_xpath = PROP_XPATH + "propeller/blade/loss"
    blades_number_xpath = PROP_XPATH + "propeller/blade"

    # Required input data from CPACS
    cruise_alt = get_value_or_default(tixi, cruise_alt_xpath, 9000)
    cruise_mach = get_value_or_default(tixi, cruise_mach_xpath, 0.45)
    stations = int(get_value_or_default(tixi, stations_xpath, 40))
    radius = get_value_or_default(tixi, radius_xpath, 0.935)
    hub_radius = get_value_or_default(tixi, hub_radius_xpath, 0.2)
    thrust = get_value_or_default(tixi, thrust_xpath, 3000)
    rotational_velocity = get_value_or_default(tixi, n_xpath, 33)
    prandtl_correction = get_value_or_default(tixi, prandtl_correction_xpath, True)
    blades_nb = get_value_or_default(tixi, blades_number_xpath, 3)

    Atm = Atmosphere(cruise_alt)

    free_stream_velocity = float(cruise_mach * Atm.speed_of_sound)
    total_thrust_coefficient = float(
        thrust / (Atm.density * rotational_velocity**2 * (radius * 2) ** 4)
    )
    advanced_ratio = float(free_stream_velocity / (rotational_velocity * (radius * 2)))

    (
        _,
        _,
        _,
        _,
        r,
        dCt_optimal,
        dCp,
        non_dimensional_radius,
        optimal_axial_interference_factor,
        optimal_rotational_interference_factor,
        prandtl,
        correction_function,
    ) = thrust_calculator(
        stations,
        total_thrust_coefficient,
        radius,
        hub_radius,
        advanced_ratio,
        free_stream_velocity,
        prandtl_correction,
        blades_nb,
        rotational_velocity,
    )

    function_plot(
        r,
        dCt_optimal,
        dCp,
        non_dimensional_radius,
        optimal_axial_interference_factor,
        optimal_rotational_interference_factor,
        prandtl,
        correction_function,
    )

    # Save CPACS
    cpacs.save_cpacs(cpacs_out_path, overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + MODULE_NAME + " -----")

    check_cpacs_input_requirements(cpacs_path)
    write_actuator_disk(cpacs_path, cpacs_out_path)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":

    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
