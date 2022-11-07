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


def write_actuator_disk():

    cpacs = CPACS(cpacs_path)
    tixi = cpacs.tixi

    results_dir = get_results_directory("AD")
    brep_dir = Path(results_dir, "brep_files")
    brep_dir.mkdir()

    # XPath definition
    cruise_alt_xpath = RANGE_XPATH + "/cruiseAltitude"
    cruise_mach_xpath = RANGE_XPATH + "/cruiseMach"
    stations_xpath = PROP_XPATH + "/propeller/blade/discretization"
    radius_xpath = PROP_XPATH + "/propeller/blade/discretization"
    thrust_xpath = PROP_XPATH + "propeller/thrust"
    n_xpath = PROP_XPATH + "propeller/rotational_velocity"
    no_prandtl_correction_xpath = PROP_XPATH + "propeller/blade/loss"
    prandtl_correction_xpath = PROP_XPATH + "propeller/blade/loss"
    blades_number_xpath = PROP_XPATH + "propeller/blade"

    # Required input data from CPACS
    cruise_alt = get_value_or_default(tixi, cruise_alt_xpath, 10000)
    cruise_mach = get_value_or_default(tixi, cruise_mach_xpath, 0.67)
    stations = get_value_or_default(tixi, stations_xpath, 10)
    radius = get_value_or_default(tixi, radius_xpath, 1.5)
    thrust = get_value_or_default(tixi, thrust_xpath, 108824.367)
    n = get_value_or_default(tixi, n_xpath, 2000)
    prandtl = get_value_or_default(tixi, prandtl_correction_xpath, True)
    blades_number = get_value_or_default(tixi, blades_number_xpath, 2)

    Atm = Atmosphere(cruise_alt)
    rho = Atm.density
    sound_speed = Atm.speed_of_sound

    free_stream_velocity = cruise_mach * sound_speed
    diameter = 2 * radius
    total_thrust_coefficient = thrust / (rho * n**2 * diameter**4)
    hub_radius = 0.1 * radius
    advanced_ratio = free_stream_velocity / (n * diameter)

    thrust_calculator(
        stations,
        total_thrust_coefficient,
        radius,
        hub_radius,
        advanced_ratio,
        free_stream_velocity,
        prandtl,
        blades_number,
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
