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
    * Use Pathlib and asolute path when refactor this module

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================


from pathlib import Path

import numpy as np
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import aircraft_name
from ceasiompy.utils.commonxpath import F_XPATH, GEOM_XPATH, MASS_CARGO, ML_XPATH, PROP_XPATH
from ceasiompy.utils.InputClasses.Conventional import weightconvclass
from ceasiompy.utils.moduleinterfaces import (
    check_cpacs_input_requirements,
    get_toolinput_file_path,
    get_tooloutput_file_path,
)
from ceasiompy.utils.WB.ConvGeometry import geometry
from ceasiompy.WeightConventional.func.AoutFunc import cpacsweightupdate, outputweightgen
from ceasiompy.WeightConventional.func.Crew.crewmembers import estimate_crew
from ceasiompy.WeightConventional.func.Masses.mtom import estimate_mtom
from ceasiompy.WeightConventional.func.Masses.oem import estimate_operating_empty_mass
from ceasiompy.WeightConventional.func.Passengers.passengers import estimate_passengers
from ceasiompy.WeightConventional.func.Passengers.seatsconfig import get_seat_config
from ceasiompy.WeightConventional.func.weight_utils import (
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

"""
    All classes are defined in the Classes and in the Input_classes folders.
"""


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_weight_estimations(cpacs_path, cpacs_out_path):
    """Function to estimate the all weights for a conventional aircraft.

    Function 'get_weight_estimations' ...

    Source:
        * Reference paper or book, with author and date, see ...

    Args:
        cpacs_path (Path): Path to CPACS file
        cpacs_out_path (Path):Path to CPACS output file

    """

    cpacs = CPACS(cpacs_path)

    # Get user input

    # has been remove:
    # self.IS_DOUBLE_FLOOR
    # self.MAX_PAYLOAD
    # self.MAX_FUEL_VOL
    # self.MASS_CARGO
    # self.FUEL_DENSITY
    # self.TURBOPROP

    description = "Desired max fuel volume [m^3] and payload mass [kg]"
    get_value_or_default(cpacs.tixi, ML_XPATH + "/description", description)

    max_payload = get_value_or_default(cpacs.tixi, ML_XPATH + "/maxPayload", 0)
    max_fuel_vol = get_value_or_default(cpacs.tixi, ML_XPATH + "/maxFuelVol", 0)
    mass_cargo = get_value_or_default(cpacs.tixi, MASS_CARGO, 0.0)
    fuel_density = get_value_or_default(cpacs.tixi, F_XPATH + "/density", 800)
    add_uid(cpacs.tixi, F_XPATH, "kerosene")
    turboprop = get_value_or_default(cpacs.tixi, PROP_XPATH + "/turboprop", False)
    is_double_floor = get_value_or_default(cpacs.tixi, GEOM_XPATH + "/isDoubleFloor", 0)

    # Classes
    # TODO: REmove class or subclasses

    masses = weightconvclass.MassesWeights()
    out = weightconvclass.WeightOutput()

    name = aircraft_name(cpacs_path)

    # ag = geometry.geometry_eval(cpacs_path, name)
    ag = geometry.AircraftGeometry()
    ag.fuse_geom_eval(cpacs)
    ag.wing_geom_eval(cpacs)
    ag.produce_output_txt()

    fuse_length = round(ag.fuse_length[0], 3)
    fuse_width = round(np.amax(ag.fuse_sec_width[:, 0]), 3)
    ind = weightconvclass.InsideDimensions(fuse_length, fuse_width)
    ind.nose_length = round(ag.fuse_nose_length[0], 3)
    ind.tail_length = round(ag.fuse_tail_length[0], 3)
    ind.cabin_length = round(ag.fuse_cabin_length[0], 3)
    wing_area = round(ag.wing_plt_area_main, 3)
    wing_span = round(ag.wing_span[ag.main_wing_index - 1], 3)
    wing_area_tot = np.sum(ag.wing_plt_area)

    # Has been replace by classes function
    # (ind, ui) = getinput.get_user_inputs(ind, ui, ag, cpacs_out_path)
    # TODO: from here
    ind.get_inside_dim(cpacs_out_path)

    if max_fuel_vol >= ag.wing_fuel_vol:
        max_fuel_vol = ag.wing_fuel_vol

    # Maximum payload allowed, set 0 if equal to max passenger mass.
    masses.MAX_PAYLOAD = max_payload

    # Adding extra length in case of aircraft with second floor [m].
    if is_double_floor == 1:
        cabin_length2 = ind.cabin_length * 1.91
    elif is_double_floor == 2:
        cabin_length2 = ind.cabin_length * 1.20
    elif is_double_floor == 0:
        cabin_length2 = ind.cabin_length
    else:
        log.warning(
            "Warning, double floor index can be only 0 (1 floor),\
                    2 (B747-2nd floor type) or 3 (A380-2nd floor type).\
                    Set Default value (0)"
        )
        cabin_length2 = ind.cabin_length

    # Maximum Take Off Mass Evaluation
    masses.maximum_take_off_mass = estimate_mtom(
        fuse_length, fuse_width, wing_area, wing_span, name
    )

    # Wing loading
    out.wing_loading = masses.maximum_take_off_mass / wing_area_tot

    # Operating Empty Mass evaluation
    masses.operating_empty_mass = estimate_operating_empty_mass(
        masses.maximum_take_off_mass, fuse_length, fuse_width, wing_area, wing_span, turboprop
    )

    # Passengers and Crew mass evaluation
    if (fuse_width / (1 + (ind.fuse_thick / 100))) > (ind.seat_width + ind.aisle_width):
        (
            out.pass_nb,
            out.row_nb,
            out.abreast_nb,
            out.aisle_nb,
            out.toilet_nb,
            ind,
        ) = estimate_passengers(cabin_length2, fuse_width, ind)

        get_seat_config(
            out.pass_nb,
            out.row_nb,
            out.abreast_nb,
            out.aisle_nb,
            is_double_floor,
            out.toilet_nb,
            fuse_length,
            ind,
            name,
        )
    else:
        out.pass_nb = 0
        raise Exception(
            "The aircraft can not transport passengers, increase"
            + " fuselage width."
            + "\nCabin Width [m] = "
            + str((fuse_width / (1 + ind.fuse_thick)))
            + " is less than seat width [m]"
            + " + aisle width [m] = "
            + str(ind.seat_width + ind.aisle_width)
        )

    out.crew_nb, out.cabin_crew_nb, masses.mass_crew = estimate_crew(
        out.pass_nb, masses.maximum_take_off_mass
    )

    masses.mass_payload = out.pass_nb * PASSENGER_MASS + mass_cargo

    masses.mass_people = masses.mass_crew + out.pass_nb * PASSENGER_MASS

    maxp = False
    if masses.MAX_PAYLOAD > 0 and masses.mass_payload > masses.MAX_PAYLOAD:
        masses.mass_payload = masses.MAX_PAYLOAD
        maxp = True
        log.info(
            "With the fixed payload, passenger nb reduced to: "
            + str(round(masses.MAX_PAYLOAD / (PASSENGER_MASS), 0))
        )

    # Fuel Mass evaluation
    # Maximum fuel that can be stored with maximum number of passengers.

    if not max_fuel_vol:  # TODO while retesting, redo fitting
        if turboprop:
            if wing_area > 55.00:
                masses.mass_fuel_max = round(masses.maximum_take_off_mass / 4.6, 3)
            else:
                masses.mass_fuel_max = round(masses.maximum_take_off_mass / 3.6, 3)
        elif wing_area < 90.00:
            if fuse_length < 60.00:
                masses.mass_fuel_max = round(masses.maximum_take_off_mass / 4.3, 3)
            else:
                masses.mass_fuel_max = round(masses.maximum_take_off_mass / 4.0, 3)
        elif wing_area < 300.00:
            if fuse_length < 35.00:
                masses.mass_fuel_max = round(masses.maximum_take_off_mass / 3.6, 3)
            else:
                masses.mass_fuel_max = round(masses.maximum_take_off_mass / 3.8, 3)
        elif wing_area < 400.00:
            masses.mass_fuel_max = round(masses.maximum_take_off_mass / 2.2, 3)
        elif wing_area < 600.00:
            masses.mass_fuel_max = round(masses.maximum_take_off_mass / 2.35, 3)
        else:
            masses.mass_fuel_max = round(masses.maximum_take_off_mass / 2.8, 3)
    else:
        masses.mass_fuel_max = round(max_fuel_vol * fuel_density, 3)

    masses.mass_fuel_maxpass = round(
        masses.maximum_take_off_mass - masses.operating_empty_mass - masses.mass_payload, 3
    )

    if masses.MAX_FUEL_MASS > 0 and masses.mass_fuel_maxpass > masses.MAX_FUEL_MASS:
        masses.mass_fuel_maxpass = masses.MAX_FUEL_MASS
        log.info("Maximum fuel amount allowed reached [kg]: " + str(masses.mass_fuel_maxpass))
        if masses.maximum_take_off_mass > (
            masses.mass_fuel_maxpass + masses.operating_empty_mass + masses.mass_payload
        ):
            masses.mass_cargo = masses.maximum_take_off_mass - (
                masses.mass_fuel_maxpass + masses.operating_empty_mass + masses.mass_payload
            )
            if not maxp:
                log.info("Adding extra payload mass [kg]: " + str(masses.mass_cargo))
                masses.mass_payload = masses.mass_payload + masses.mass_cargo
            else:
                masses.maximum_take_off_mass = masses.maximum_take_off_mass - masses.mass_cargo
                log.info(
                    "With all the constrains on the fuel and payload, "
                    + "the maximum take off mass is not reached."
                    + "\n Maximum take off mass [kg]: "
                    + str(masses.maximum_take_off_mass)
                )
    else:
        log.info("Fuel mass with maximum passengers [kg]: " + str(masses.mass_fuel_maxpass))

    if masses.MAX_FUEL_MASS > 0 and masses.mass_fuel_max > masses.MAX_FUEL_MASS:
        masses.mass_fuel_max = masses.MAX_FUEL_MASS

    # Zero Fuel Mass evaluation
    masses.zero_fuel_mass = (
        masses.maximum_take_off_mass
        - masses.mass_fuel_maxpass
        + UNUSABLE_FUEL_RATIO * masses.mass_fuel_max
    )

    # Log writting  (TODO: maybe create a separate function)
    log.info("---- Geometry evaluation from CPACS file ----")
    log.info("Fuselage length [m]: " + str(round(fuse_length, 3)))
    log.info("Fuselage width [m]: " + str(round(fuse_width, 3)))
    log.info("Fuselage mean width [m]: " + str(round(ag.fuse_mean_width, 3)))
    log.info("Wing Span [m]: " + str(round(wing_span, 3)))

    log.info("--------- Masses evaluated: -----------")
    log.info("Maximum Take Off Mass [kg]: " + str(int(round(masses.maximum_take_off_mass))))
    log.info("Operating Empty Mass [kg]: " + str(int(round(masses.operating_empty_mass))))
    log.info("Zero Fuel Mass [kg]: " + str(int(round(masses.zero_fuel_mass))))
    log.info("Wing loading [kg/m^2]: " + str(int(round(out.wing_loading))))
    log.info(
        "Maximum amount of fuel allowed with no passengers [kg]: "
        + str(int(round(masses.mass_fuel_max)))
    )
    log.info(
        "Maximum ammount of fuel allowed with no passengers [l]: "
        + str(int(round(masses.mass_fuel_max / fuel_density)))
    )
    log.info("--------- Passegers evaluated: ---------")
    log.info("Passengers: " + str(out.pass_nb))
    log.info("Lavatory: " + str(out.toilet_nb))
    log.info("Payload mass [kg]: " + str(masses.mass_payload))
    log.info("------- Crew members evaluated: --------")
    log.info("Pilots: " + str(PILOT_NB))
    log.info("Cabin crew members: " + str(out.cabin_crew_nb))
    log.info("############### Weight estimation completed ###############")

    # Output writting
    log.info("-------- Generating output text file --------")
    outputweightgen.output_txt(out, masses, ind, ui, name)

    # CPACS writting (TODO: save directly in cpacs_out_path)
    cpacsweightupdate.cpacs_update(masses, out, cpacs_path, cpacs_out_path)


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
