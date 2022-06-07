"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Weight conventional module for preliminary design of conventional aircraft

Python version: >=3.7

| Author : Stefano Piccini
| Date of creation: 2018-09-27

TODO:
    * Simplify classes, use only one or use subclasses
    * Make tings compatible also with the others W&B Modules
    * Use Pathlib and absolute path when refactor this module

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================


from pathlib import Path

import numpy as np
from ceasiompy.WeightConventional.func.cabin import Cabin
from ceasiompy.WeightConventional.func.masses import AircfaftMasses

from ceasiompy.utils.InputClasses.Conventional.weightconvclass import InsideDimensions
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.utils.commonxpath import TURBOPROP_XPATH, WB_DOUBLE_FLOOR_XPATH

from ceasiompy.utils.moduleinterfaces import (
    check_cpacs_input_requirements,
    get_toolinput_file_path,
    get_tooloutput_file_path,
)
from ceasiompy.utils.WB.ConvGeometry import geometry
from ceasiompy.WeightConventional.func.AoutFunc import cpacsweightupdate, outputweightgen

from ceasiompy.WeightConventional.func.mtom import estimate_mtom
from ceasiompy.WeightConventional.func.oem import estimate_oem

from ceasiompy.WeightConventional.func.weightutils import PILOT_NB

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


def get_weight_estimations(cpacs_path, cpacs_out_path):
    """Function to estimate the all weights for a conventional aircraft.

    Function 'get_weight_estimations' use available information in the CPACS file to estimate the
    masses of the aircraft. It also estimates some cabin dimensions and number of people.

    Source:
        * Reference paper or book, with author and date, see ...

    Args:
        cpacs_path (Path): Path to CPACS file
        cpacs_out_path (Path):Path to CPACS output file

    """

    cpacs = CPACS(cpacs_path)
    result_dir = get_results_directory("WeightConventional")

    turboprop = get_value_or_default(cpacs.tixi, TURBOPROP_XPATH, False)
    is_double_floor = get_value_or_default(cpacs.tixi, WB_DOUBLE_FLOOR_XPATH, 0)

    # Classes

    # Aircraft geometry
    ag = geometry.AircraftGeometry()
    ag.fuse_geom_eval(cpacs)
    ag.wing_geom_eval(cpacs)
    ag.produce_output_txt()

    inside_dim = InsideDimensions(ag)
    inside_dim.get_inside_dim(cpacs)

    # Masses
    ac_masses = AircfaftMasses(cpacs)
    ac_masses.get_mtom(
        fuselage_length=ag.fuse_length[0],
        fuselage_width=ag.fuse_width,
        wing_area=ag.wing_area,
        wing_span=ag.wing_span[0],
        results_dir=result_dir,
    )
    ac_masses.get_oem(
        fuselage_length=ag.fuse_length[0], wing_span=ag.wing_span[0], turboprop=turboprop
    )
    ac_masses.get_wing_loading(wings_area=np.sum(ag.wing_plt_area))
    ac_masses.get_mass_fuel_max(ag.wing_area, ag.fuse_length[0], turboprop)

    # ---------------- (TODO)
    # Adding extra length in case of aircraft with second floor [m].
    if is_double_floor == 1:
        cabin_length_tot = inside_dim.cabin_length * 1.91
    elif is_double_floor == 2:
        cabin_length_tot = inside_dim.cabin_length * 1.20
    elif is_double_floor == 0:
        cabin_length_tot = inside_dim.cabin_length
    else:
        log.warning(
            "Warning, double floor index can be only 0 (1 floor),\
                    2 (B747-2nd floor type) or 3 (A380-2nd floor type).\
                    Set Default value (0)"
        )
        cabin_length_tot = inside_dim.cabin_length
    # ----------------

    # Cabin
    cabin_width = ag.fuse_width / (1 + (inside_dim.fuse_thick / 100))
    cabin = Cabin(cpacs, cabin_length_tot, cabin_width, ac_masses.max_payload_mass)
    cabin.save_to_cpacs()
    cabin.write_seat_config(Path(result_dir, "Cabin.out"))

    ac_masses.get_payload_mass(cabin.passenger_mass)
    ac_masses.write_masses_output(Path(result_dir, "Masses.out"))

    log.info("---- Geometry evaluation from CPACS file ----")
    log.info(f"Fuselage length: {round(ag.fuse_length[0], 3)}  [m]")
    log.info(f"Fuselage width: {round(ag.fuse_width, 3)}  [m]")
    log.info(f"Fuselage mean width: {round(ag.fuse_mean_width, 3)}  [m]")
    log.info(f"Wing Span: {round(ag.wing_span[0], 3)}  [m]")

    log.info("--------- Masses evaluated: -----------")
    log.info(f"Maximum Take Off Mass: {int(round(ac_masses.mtom))} [kg]")
    log.info(f"Operating Empty Mass: {int(round(ac_masses.oem))} [kg]")
    log.info(f"Zero Fuel Mass: {int(round(ac_masses.zfm))} [kg]")
    log.info(f"Wing loading : {int(round(ac_masses.wing_loading))} [kg/m^2]")
    log.info("Maximum amount of fuel allowed with no passengers:")
    log.info(f" -> {int(ac_masses.mass_fuel_max)} [kg]")
    log.info(f" -> {int(ac_masses.mass_fuel_max / ac_masses.fuel_density * 1000)} [l]")
    log.info("--------- Passengers evaluated: ---------")
    log.info(f"Passengers: {cabin.passenger_nb}")
    log.info(f"Lavatory: {cabin.toilet_nb}")
    log.info(f"Payload mass: {ac_masses.payload_mass} [kg]")
    log.info("------- Crew members evaluated: --------")
    log.info(f"Pilots: {PILOT_NB}")
    log.info(f"Cabin crew members: {cabin.cabin_crew_nb}")
    log.info("Weight estimation completed.")

    # Output writing
    log.info("Generating output text file")
    # TODO: should be do completely differently
    # outputweightgen.output_txt(
    #     out, masses, inside_dim, is_double_floor, max_payload, max_fuel_vol, fuel_density
    # )

    # cpacsweightupdate.cpacs_update(masses, out, cpacs)

    cpacs.save_cpacs(cpacs_out_path, overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + MODULE_NAME + " -----")

    check_cpacs_input_requirements(cpacs_path)

    get_weight_estimations(cpacs_path, cpacs_out_path)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":

    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
