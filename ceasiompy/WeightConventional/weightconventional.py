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

from ceasiompy.utils.InputClasses.Conventional.weightconvclass import (
    InsideDimensions,
    MassesWeights,
)
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.utils.commonxpath import (
    F_XPATH,
    MASS_CARGO_XPATH,
    TURBOPROP_XPATH,
    WB_MASS_LIMIT_XPATH,
    WB_DOUBLE_FLOOR_XPATH,
    WB_MAX_FUEL_VOL_XPATH,
    WB_MAX_PAYLOAD_XPATH,
)
from ceasiompy.utils.moduleinterfaces import (
    check_cpacs_input_requirements,
    get_toolinput_file_path,
    get_tooloutput_file_path,
)
from ceasiompy.utils.WB.ConvGeometry import geometry
from ceasiompy.WeightConventional.func.AoutFunc import cpacsweightupdate, outputweightgen

from ceasiompy.WeightConventional.func.mtom import estimate_mtom
from ceasiompy.WeightConventional.func.oem import estimate_oem


from ceasiompy.WeightConventional.func.weightutils import (
    PASSENGER_MASS,
    PILOT_NB,
    UNUSABLE_FUEL_RATIO,
)
from cpacspy.cpacsfunctions import add_uid, get_value_or_default
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

    # Get user input
    description = "Desired max fuel volume [m^3] and payload mass [kg]"
    get_value_or_default(cpacs.tixi, WB_MASS_LIMIT_XPATH + "/description", description)

    max_payload = get_value_or_default(cpacs.tixi, WB_MAX_PAYLOAD_XPATH, 0)
    max_fuel_vol = get_value_or_default(cpacs.tixi, WB_MAX_FUEL_VOL_XPATH, 0)
    mass_cargo = get_value_or_default(cpacs.tixi, MASS_CARGO_XPATH, 0.0)
    fuel_density = get_value_or_default(cpacs.tixi, F_XPATH + "/density", 800)
    add_uid(cpacs.tixi, F_XPATH, "kerosene")
    turboprop = get_value_or_default(cpacs.tixi, TURBOPROP_XPATH, False)
    is_double_floor = get_value_or_default(cpacs.tixi, WB_DOUBLE_FLOOR_XPATH, 0)

    # Classes
    masses = MassesWeights()

    ag = geometry.AircraftGeometry()
    ag.fuse_geom_eval(cpacs)
    ag.wing_geom_eval(cpacs)
    ag.produce_output_txt()

    inside_dim = InsideDimensions(ag)
    inside_dim.get_inside_dim(cpacs)

    if max_fuel_vol >= ag.wing_fuel_vol:
        max_fuel_vol = ag.wing_fuel_vol

    # Maximum payload allowed, set 0 if equal to max passenger mass.
    masses.max_payload = max_payload

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

    # Maximum Take Off Mass Evaluation
    masses.maximum_take_off_mass = estimate_mtom(
        fuselage_length=ag.fuse_length[0],
        fuselage_width=ag.fuse_width,
        wing_area=ag.wing_area,
        wing_span=ag.wing_span[0],
        results_dir=result_dir,
    )

    # Wing loading
    wing_loading = masses.maximum_take_off_mass / np.sum(ag.wing_plt_area)

    # Operating Empty Mass evaluation
    masses.operating_empty_mass = estimate_oem(
        masses.maximum_take_off_mass,
        ag.fuse_length[0],
        ag.wing_span[0],
        turboprop,
    )

    # Cabin

    cabin_width = ag.fuse_width / (1 + (inside_dim.fuse_thick / 100))

    cabin = Cabin(cpacs, cabin_length_tot, cabin_width, masses.max_payload)
    cabin.save_to_cpacs()
    cabin.write_seat_config(Path(result_dir, "Seats_disposition.out"))

    # TODO: tmp to test cabin function (will be removed)
    masses.mass_payload = cabin.passenger_mass + mass_cargo
    masses.mass_crew = cabin.crew_mass
    masses.mass_people = cabin.people_mass

    maxp = False
    if masses.max_payload > 0 and masses.mass_payload > masses.max_payload:
        masses.mass_payload = masses.max_payload
        maxp = True
        new_passenger_nb = masses.max_payload / (PASSENGER_MASS)
        log.info(f"With the fixed payload, passenger nb reduced to: {new_passenger_nb}")

    # Fuel Mass evaluation
    # Maximum fuel that can be stored with maximum number of passengers.

    if not max_fuel_vol:  # TODO while retesting, redo fitting
        if turboprop:
            if ag.wing_area > 55.00:
                coef = 4.6
            else:
                coef = 3.6
        elif ag.wing_area < 90.00:
            if ag.fuse_length[0] < 60.00:
                coef = 4.3
            else:
                coef = 4.0
        elif ag.wing_area < 300.00:
            if ag.fuse_length[0] < 35.00:
                coef = 3.6
            else:
                coef = 3.8
        elif ag.wing_area < 400.00:
            coef = 2.2
        elif ag.wing_area < 600.00:
            coef = 2.35
        else:
            coef = 2.8

        masses.mass_fuel_max = round(masses.maximum_take_off_mass / coef, 3)
    else:
        masses.mass_fuel_max = round(max_fuel_vol * fuel_density, 3)

    masses.mass_fuel_maxpass = round(
        masses.maximum_take_off_mass - masses.operating_empty_mass - masses.mass_payload, 3
    )

    if masses.MAX_FUEL_MASS > 0 and masses.mass_fuel_maxpass > masses.MAX_FUEL_MASS:
        masses.mass_fuel_maxpass = masses.MAX_FUEL_MASS
        log.info(f"Maximum fuel amount allowed reached {masses.mass_fuel_maxpass}[kg]: ")
        if masses.maximum_take_off_mass > (
            masses.mass_fuel_maxpass + masses.operating_empty_mass + masses.mass_payload
        ):
            masses.mass_cargo = masses.maximum_take_off_mass - (
                masses.mass_fuel_maxpass + masses.operating_empty_mass + masses.mass_payload
            )
            if not maxp:
                log.info(f"Adding extra payload mass {masses.mass_cargo} [kg]: ")
                masses.mass_payload = masses.mass_payload + masses.mass_cargo
            else:
                masses.maximum_take_off_mass = masses.maximum_take_off_mass - masses.mass_cargo
                log.info(
                    "With all the constrains on the fuel and payload, "
                    + "the maximum take off mass is not reached."
                )
                log.info(f"Maximum take off mass {masses.maximum_take_off_mass}[kg]")
    else:
        log.info(f"Fuel mass with maximum passengers: {masses.mass_fuel_maxpass} [kg]")

    if masses.MAX_FUEL_MASS > 0 and masses.mass_fuel_max > masses.MAX_FUEL_MASS:
        masses.mass_fuel_max = masses.MAX_FUEL_MASS

    # Zero Fuel Mass evaluation
    masses.zero_fuel_mass = (
        masses.maximum_take_off_mass
        - masses.mass_fuel_maxpass
        + UNUSABLE_FUEL_RATIO * masses.mass_fuel_max
    )

    log.info("---- Geometry evaluation from CPACS file ----")
    log.info(f"Fuselage length: {round(ag.fuse_length[0], 3)}  [m]")
    log.info(f"Fuselage width: {round(ag.fuse_width, 3)}  [m]")
    log.info(f"Fuselage mean width: {round(ag.fuse_mean_width, 3)}  [m]")
    log.info(f"Wing Span: {round(ag.wing_span[0], 3)}  [m]")

    log.info("--------- Masses evaluated: -----------")
    log.info(f"Maximum Take Off Mass: {int(round(masses.maximum_take_off_mass))} [kg]")
    log.info(f"Operating Empty Mass: {int(round(masses.operating_empty_mass))} [kg]")
    log.info(f"Zero Fuel Mass: {int(round(masses.zero_fuel_mass))} [kg]")
    log.info(f"Wing loading : {int(round(wing_loading))} [kg/m^2]")
    log.info("Maximum amount of fuel allowed with no passengers:")
    log.info(f" -> {int(masses.mass_fuel_max)} [kg]")
    log.info(f" -> {int(masses.mass_fuel_max / fuel_density * 1000)} [l]")
    log.info("--------- Passengers evaluated: ---------")
    log.info(f"Passengers: {cabin.passenger_nb}")
    log.info(f"Lavatory: {cabin.toilet_nb}")
    log.info(f"Payload mass: {masses.mass_payload} [kg]")
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


# self.wing_loading = 0
# self.mass_fuel_maxpass = 0
# self.mass_fuel_max = 0
# self.maximum_take_off_mass = 0
# self.operating_empty_mass = 0
# self.MAX_FUEL_MASS = 0
# self.mass_payload = 0
# self.max_payload = 0
# self.mass_cargo = 0
# self.zero_fuel_mass = 0
