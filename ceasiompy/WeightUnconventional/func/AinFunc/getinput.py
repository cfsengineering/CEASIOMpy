"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script obtain all the informations required for the Unconventional
weight analysis from the CPACS file

| Author : Stefano Piccini
| Date of creation: 2018-11-21

TODO:

    * A lot of things could be simplified...
    * Get flight condition for aeromap, how?
    * Get user inptut for engines

"""

# =============================================================================
#   IMPORTS
# =============================================================================

from cpacspy.cpacsfunctions import add_uid, create_branch, get_value_or_default, open_tixi
from ceasiompy.utils.commonxpaths import (
    CAB_CREW_XPATH,
    F_XPATH,
    FUEL_XPATH,
    GEOM_XPATH,
    MASSBREAKDOWN_XPATH,
    TURBOPROP_XPATH,
    WB_MASS_LIMIT_XPATH,
    PASS_XPATH,
    PILOTS_XPATH,
    PROP_XPATH,
    RANGE_LD_RATIO_XPATH,
    RANGE_XPATH,
    WB_MAX_FUEL_VOL_XPATH,
    WB_MAX_PAYLOAD_XPATH,
)

from ceasiompy import log


# =============================================================================
#   FUNCTIONS
# =============================================================================


def get_user_fuel(fus_nb, ui, cpacs_in):
    """Function to extract fuel data from a CPACS file

    Function 'get_user_fuel' extracts fuel data from the CPACS file, the code
    will use the default value when they are missing.

    Args:
        fus_nb (int): Number of fuselage.
        ui (class): UserInputs class
        cpacs_in (str): Path to the CPACS file

    Returns:
        ui (class): Modified UserInputs class

    """

    log.info("Starting data extraction from CPACS file")

    tixi = open_tixi(cpacs_in)

    create_branch(tixi, FUEL_XPATH, False)

    if fus_nb:
        for i in range(0, fus_nb):
            if fus_nb > 1:
                F = "fuelOnCabin" + str(i + 1)
            else:
                F = "fuelOnCabin"
            if not tixi.checkElement(FUEL_XPATH + "/" + F):
                tixi.createElement(FUEL_XPATH, F)
                tixi.updateDoubleElement(FUEL_XPATH + "/" + F, ui.F_FUEL[i], "%g")
            else:
                ui.F_FUEL[i] = tixi.getDoubleElement(FUEL_XPATH + "/" + F)
    else:
        if not tixi.checkElement(FUEL_XPATH + "/fuelOnCabin"):
            tixi.createElement(FUEL_XPATH, "fuelOnCabin")
            tixi.updateDoubleElement(FUEL_XPATH + "/fuelOnCabin", ui.FUEL_ON_CABIN, "%g")
        else:
            temp = tixi.updateDoubleElement(FUEL_XPATH + "/fuelOnCabin", ui.FUEL_ON_CABIN, "%g")
            if temp != ui.FUEL_ON_CABIN and temp > 0:
                ui.FUEL_ON_CABIN = temp

    log.info("Data from CPACS file succesfully extracted")

    tixi.save(cpacs_in)

    return ui


def get_user_inputs(ed, ui, adui, cpacs_in):
    """Function to extract from the xml file the required input data,
        the code will use the default value when they are missing.

    Function 'get_user_inputs' ...

    Args:
        ed (int): EngineData class.
        ui (class): UserInputs class
        adui (str): AdvancedInputs class.
        cpacs_in (str): Path to the CPACS file

    Returns:
        ed (int): Updated ngineData class.
        ui (class): Updated UserInputs class
        adui (str): Updated AdvancedInputs class.

    """

    log.info("Starting data extraction from CPACS file")

    tixi = open_tixi(cpacs_in)

    create_branch(tixi, FUEL_XPATH, False)
    create_branch(tixi, GEOM_XPATH, False)
    create_branch(tixi, RANGE_XPATH, False)
    create_branch(tixi, PILOTS_XPATH, False)
    create_branch(tixi, CAB_CREW_XPATH, False)
    create_branch(tixi, PASS_XPATH, False)
    create_branch(tixi, WB_MASS_LIMIT_XPATH, False)
    create_branch(tixi, PROP_XPATH, False)

    # cpacs/vehicles
    MC_XPATH = MASSBREAKDOWN_XPATH + "/payload/mCargo/massDescription"

    create_branch(tixi, MC_XPATH, False)
    create_branch(tixi, F_XPATH, False)
    add_uid(tixi, F_XPATH, "kerosene")

    # Gathering data =========================================================
    # Geometry ===============================================================
    if not tixi.checkElement(GEOM_XPATH + "/description"):
        tixi.createElement(GEOM_XPATH, "description")
        tixi.updateTextElement(GEOM_XPATH + "/description", "User " + "geometry input")

    ui.FLOORS_NB = get_value_or_default(tixi, GEOM_XPATH + "/floorsNb", ui.FLOORS_NB)
    adui.VRT_THICK = get_value_or_default(tixi, GEOM_XPATH + "/virtualThick", 0.00014263)
    adui.VRT_STR_DENSITY = get_value_or_default(tixi, GEOM_XPATH + "/virtualDensity", 2700.0)
    ui.H_LIM_CABIN = get_value_or_default(tixi, GEOM_XPATH + "/cabinHeight", 2.3)

    # People =================================================================
    # Pilots user input data
    adui.PASS_BASE_DENSITY = get_value_or_default(tixi, PASS_XPATH + "/passDensity", 1.66)

    # what to to with this input
    if tixi.checkElement(PASS_XPATH + "/passNb"):
        temp = tixi.getIntegerElement(PASS_XPATH + "/passNb")
        if temp != ui.MAX_PASS and temp > 0:
            ui.MAX_PASS = temp

    # Fuel ===================================================================
    adui.fuel_density = get_value_or_default(tixi, F_XPATH + "/density", 800)

    # Weight =================================================================
    # Mass limits data
    if not tixi.checkElement(WB_MASS_LIMIT_XPATH + "/description"):
        tixi.createElement(WB_MASS_LIMIT_XPATH, "description")
        tixi.updateTextElement(
            WB_MASS_LIMIT_XPATH + "/description",
            "Desired max fuel " + "volume [m^3] and payload mass [kg]",
        )

    ui.max_payload = get_value_or_default(tixi, WB_MAX_PAYLOAD_XPATH, 0.0)
    ui.max_fuel_volume = get_value_or_default(tixi, WB_MAX_FUEL_VOL_XPATH, 0.0)
    ui.mass_cargo = get_value_or_default(tixi, MC_XPATH + "/massCargo", 0.0)
    # If the cargo mass is defined in the UserInputs class will be added
    # in the CPACS file after the analysis.

    # Flight =================================================================

    ed.TSFC_CRUISE = get_value_or_default(tixi, PROP_XPATH + "/tSFC", 0.5)

    # TODO: These data should be taken from aeroMaps...
    if not tixi.checkElement(RANGE_LD_RATIO_XPATH):
        tixi.createElement(RANGE_XPATH, "lDRatio")
        tixi.updateDoubleElement(RANGE_LD_RATIO_XPATH, ui.LD, "%g")
    else:
        temp = tixi.getIntegerElement(RANGE_LD_RATIO_XPATH)
        if temp != ui.LD and temp > 0:
            ui.LD = temp

    if not tixi.checkElement(RANGE_XPATH + "/cruiseSpeed"):
        tixi.createElement(RANGE_XPATH, "cruiseSpeed")
        tixi.updateDoubleElement(RANGE_XPATH + "/cruiseSpeed", ui.CRUISE_SPEED, "%g")
    else:
        temp = tixi.getIntegerElement(RANGE_XPATH + "/cruiseSpeed")
        if temp != ui.CRUISE_SPEED and temp > 0:
            ui.CRUISE_SPEED = temp

    # TODO: see how to enter input for Engines
    if not tixi.checkElement(PROP_XPATH + "/userEngineOption"):
        tixi.createElement(PROP_XPATH, "userEngineOption")
        if ui.USER_ENGINES:
            tixi.updateTextElement(PROP_XPATH + "/userEngineOption", "True")
        else:
            tixi.updateTextElement(PROP_XPATH + "/userEngineOption", "False")
    else:
        temp = tixi.getTextElement(PROP_XPATH + "/userEngineOption")
        if temp == "False":
            ui.USER_ENGINES = False
        else:
            ui.USER_ENGINES = True

    if not tixi.checkElement(PROP_XPATH + "/singleHydraulics"):
        tixi.createElement(PROP_XPATH, "singleHydraulics")
        if adui.SINGLE_HYDRAULICS:
            tixi.updateTextElement(PROP_XPATH + "/singleHydraulics", "True")
        else:
            tixi.updateTextElement(PROP_XPATH + "/singleHydraulics", "False")
    else:
        temp = tixi.getTextElement(PROP_XPATH + "/singleHydraulics")
        if temp == "False":
            adui.SINGLE_HYDRAULICS = False
        else:
            adui.SINGLE_HYDRAULICS = True

    log.info("Data from CPACS file successfully extracted")

    tixi.save(cpacs_in)

    return (ed, ui, adui)


# ====================== ENGINES INPUT EXTRACTION DATA ======================= #


def get_engine_inputs(ui, ed, cpacs_in):
    """Function to extract from the xml file the required input data,
    the code will use the default value when they are missing.

    INPUT
    (class) ui     --Arg.: UserInputs class.
    (class) ed     --Arg.: EngineData class.
    ##======= Class ares defined in the InputClasses folder =======##
    (char) cpacs_in  --Arg.: Relative location of the xml file in the
                             ToolInput folder (cpacs option) or
                             relative location of the temp. xml file in
                             the ToolOutput folder (input option).
    OUTPUT
    (class) ed       --Out.: EngineData class.
    (file) cpacs_in  --Out.: Updated cpacs file
    """

    log.info("Starting engine data extraction from CPACS file")

    tixi = open_tixi(cpacs_in)

    create_branch(tixi, PROP_XPATH, False)

    # Propulsion =============================================================
    if not tixi.checkElement(TURBOPROP_XPATH):
        create_branch(tixi, PROP_XPATH, False)
        tixi.createElement(PROP_XPATH, "turboprop")
        if ed.turboprop:
            tixi.updateTextElement(TURBOPROP_XPATH, "True")
        else:
            tixi.updateTextElement(TURBOPROP_XPATH, "False")
    else:
        temp = tixi.getTextElement(TURBOPROP_XPATH)
        if temp == "False":
            ed.turboprop = False
        else:
            ed.turboprop = True
    if not tixi.checkElement(PROP_XPATH + "/auxiliaryPowerUnit"):
        tixi.createElement(PROP_XPATH, "auxiliaryPowerUnit")
        if ed.APU:
            tixi.updateTextElement(PROP_XPATH + "/auxiliaryPowerUnit", "True")
        else:
            tixi.updateTextElement(PROP_XPATH + "/auxiliaryPowerUnit", "False")
    else:
        temp = tixi.getTextElement(PROP_XPATH + "/auxiliaryPowerUnit")
        if temp == "False":
            ed.APU = False
        else:
            ed.APU = True
    if not tixi.checkElement(PROP_XPATH + "/engineNumber"):
        tixi.createElement(PROP_XPATH, "engineNumber")
        tixi.updateIntegerElement(PROP_XPATH + "/engineNumber", ed.NE, "%i")
    else:
        ed.NE = tixi.getIntegerElement(PROP_XPATH + "/engineNumber")

    # Engines (TODO: check this _XPATH)
    mp = []
    tp = []
    EN_XPATH = "/cpacs/vehicles/engines"
    if tixi.checkElement(EN_XPATH):
        for e in range(0, ed.NE - 1):
            if ed.NE > 1:
                EN_XPATH += "/engine" + str(e + 1)
            else:
                EN_XPATH += "/engine"
            if not tixi.checkElement(EN_XPATH):
                raise Exception(
                    "Engine definition incomplete, missing"
                    + " one or more engines in the cpacs file"
                )
            if not tixi.checkElement(EN_XPATH + "/name"):
                ed.EN_NAME.append("Engine_" + str(e + 1))
                tixi.createElement(EN_XPATH, "name")
                tixi.updateTextElement(EN_XPATH + "/name", ed.EN_NAME[e])
            else:
                if e > len(ed.EN_NAME):
                    ed.EN_NAME.append(tixi.getTextElement(EN_XPATH + "/name"))
            ENA_XPATH = EN_XPATH + "/analysis/mass"
            if tixi.checkElement(ENA_XPATH + "/mass"):
                ed.en_mass = tixi.getDoubleElement(ENA_XPATH + "/mass")
                mp.append(ed.en_mass)
                if e > 0 and ed.en_mass != mp[e - 1]:
                    raise Exception(
                        "The engines have different masses, this"
                        + " can lead to an unbalanced aircraft"
                    )
            elif ed.en_mass:
                tixi.createElement(ENA_XPATH, "mass")
                tixi.updateDoubleElement(ENA_XPATH + "/mass", ed.en_mass, "%g")
            else:
                raise Exception(
                    "Engine definition incomplete, missing" + " engine mass in the cpacs file"
                )

            if tixi.checkElement(EN_XPATH + "/analysis/thrust00"):
                ed.max_thrust = tixi.getDoubleElement(EN_XPATH + "/analysis/thrust00")
                tp.append(ed.max_thrust)
                if e > 0 and ed.max_thrust != tp[e - 1]:
                    raise Exception("The engines have different thrust, this")
                    # + ' can lead to an unbalanced flight')
            elif ed.max_thrust:
                tixi.createElement(EN_XPATH, "/analysisthrust00")
                tixi.updateDoubleElement(EN_XPATH + "/analysis/thrust00", ed.max_thrust, "%g")
            else:
                raise Exception(
                    "Engine definition incomplete, missing" + " engine thrust in the cpacs file"
                )
    log.info("Data from CPACS file successfully extracted")

    tixi.save(cpacs_in)

    return ed


# =============================================================================
#    MAIN
# =============================================================================

if __name__ == "__main__":

    log.warning("########################################################")
    log.warning("# ERROR NOT A STANDALONE PROGRAM, RUN weightuncmain.py #")
    log.warning("########################################################")
