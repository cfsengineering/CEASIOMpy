"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Output text and plot generation function for unconventional
aircraft with fuselage.

| Author : Stefano Piccini
| Date of creation: 2018-11-21

"""

# =============================================================================
#   IMPORTS
# =============================================================================

from cpacspy.cpacsfunctions import add_uid, create_branch, open_tixi
from ceasiompy.utils.commonxpaths import CREW_XPATH, MASSBREAKDOWN_XPATH, PASS_XPATH
from ceasiompy import log

# =============================================================================
#   FUNCTIONS
# =============================================================================


def toolspecific_update(mw, out, cpacs_out_path):
    """The function that update the cpacs file after the Weight_unc_main
    program.

    Args:
        fus_nb (integer): Number of fuselage [-].
        awg (class): AircraftWingGeometry class.
        mw (class): Masses and Weights class.
        out (class): Output class.
        cpacs_out_path (str): Path of the output file.


    """

    tixi = open_tixi(cpacs_out_path)

    # Path creation
    create_branch(tixi, CREW_XPATH + "/cabinCrewMembers", False)
    create_branch(tixi, PASS_XPATH, False)

    # Path update
    if not tixi.checkElement(CREW_XPATH + "/cabinCrewMembers/cabinCrewMemberNb"):
        tixi.createElement(CREW_XPATH + "/cabinCrewMembers", "cabinCrewMemberNb")
    tixi.updateDoubleElement(
        CREW_XPATH + "/cabinCrewMembers/cabinCrewMemberNb", out.cabin_crew_nb, "%g"
    )

    if not tixi.checkElement(PASS_XPATH + "/passNb"):
        tixi.createElement(PASS_XPATH, "passNb")
    tixi.updateIntegerElement(PASS_XPATH + "/passNb", out.pass_nb, "%i")

    if not tixi.checkElement(PASS_XPATH + "/mass"):
        tixi.createElement(PASS_XPATH, "mass")
    tixi.updateDoubleElement(PASS_XPATH + "/mass", mw.mass_pass, "%g")

    if not tixi.checkElement(PASS_XPATH + "/toiletNb"):
        tixi.createElement(PASS_XPATH, "toiletNb")
    tixi.updateIntegerElement(PASS_XPATH + "/toiletNb", int(out.toilet_nb), "%i")

    if not tixi.checkElement(PASS_XPATH + "/fuelMassMaxpass"):
        tixi.createElement(PASS_XPATH, "fuelMassMaxpass")
    FMP_PATH = PASS_XPATH + "/fuelMassMaxpass"

    if not tixi.checkElement(FMP_PATH + "/description"):
        tixi.createElement(FMP_PATH, "description")
    tixi.updateTextElement(
        FMP_PATH + "/description", "Maximum amount of " + "fuel with maximum payload [kg]"
    )

    if not tixi.checkElement(FMP_PATH + "/mass"):
        tixi.createElement(FMP_PATH, "mass")
    tixi.updateDoubleElement(FMP_PATH + "/mass", mw.mass_fuel_maxpass, "%g")

    tixi.save(cpacs_out_path)


# =============================================================================
# CPACS MASS BREAKDOWN UPDATE
# =============================================================================


def cpacs_weight_update(out, mw, ui, cpacs_out_path):
    """The function that update the cpacs file after the Weight_unc_main
        program.

    Args:
        out (class): Output class.
        mw (class): Mass and weight class.
        ui (class): UserInputs class.
        cpacs_out_path (str): Path of the output file.

    """

    tixi = open_tixi(cpacs_out_path)

    if tixi.checkElement(MASSBREAKDOWN_XPATH):
        tixi.removeElement(MASSBREAKDOWN_XPATH)

    MD_PATH = MASSBREAKDOWN_XPATH + "/designMasses"
    MTOM_PATH = MD_PATH + "/mTOM"
    MZFM_PATH = MD_PATH + "/mZFM"
    MF_PATH = MASSBREAKDOWN_XPATH + "/fuel/massDescription"
    OEM_PATH = MASSBREAKDOWN_XPATH + "/mOEM/massDescription"
    PAY_PATH = MASSBREAKDOWN_XPATH + "/payload/massDescription"
    MC_PATH = MASSBREAKDOWN_XPATH + "/payload/mCargo"
    EM_PATH = MASSBREAKDOWN_XPATH + "/mOEM/mEM"
    OIM_PATH = MASSBREAKDOWN_XPATH + "/mOEM/mOperatorItems/mCrewMembers/massDescription"
    MSYS_PATH = EM_PATH + "/mSystems/massDescription/mass"
    MSTR_PATH = EM_PATH + "/mStructure/massDescription/mass"
    MEN_PATH = EM_PATH + "/mPowerUnits/massDescription/mass"

    create_branch(tixi, MTOM_PATH + "/mass", False)
    create_branch(tixi, MZFM_PATH + "/mass", False)
    create_branch(tixi, MF_PATH + "/mass", False)
    create_branch(tixi, OEM_PATH + "/mass", False)
    create_branch(tixi, PAY_PATH + "/mass", False)
    create_branch(tixi, MC_PATH, False)
    create_branch(tixi, OIM_PATH + "/mass", False)
    create_branch(tixi, EM_PATH, False)
    create_branch(tixi, MSYS_PATH, False)
    create_branch(tixi, MSTR_PATH, False)
    create_branch(tixi, MEN_PATH, False)

    # DESIGN MASSES
    add_uid(tixi, MTOM_PATH, "MTOM")
    tixi.createElement(MTOM_PATH, "name")
    tixi.updateTextElement(MTOM_PATH + "/name", "Maximum take-off mass")
    tixi.createElement(MTOM_PATH, "description")
    tixi.updateTextElement(
        MTOM_PATH + "/description",
        "Maximum " + "take off mass [kg], CoG coordinate [m] and " + "moment of inertia.",
    )
    tixi.updateDoubleElement(MTOM_PATH + "/mass", mw.maximum_take_off_mass, "%g")

    # MZFM
    add_uid(tixi, MZFM_PATH, "MZFM")
    tixi.createElement(MZFM_PATH, "name")
    tixi.updateTextElement(MZFM_PATH + "/name", "Maximum zero fuel mass")
    tixi.createElement(MZFM_PATH, "description")
    tixi.updateTextElement(
        MZFM_PATH + "/description",
        "Maximum "
        + "zero fuel mass [kg] and corresponding CoG "
        + "coordinate [m], moment of inertia.",
    )
    tixi.updateDoubleElement(MZFM_PATH + "/mass", mw.zero_fuel_mass, "%g")

    # FUEL MASS
    add_uid(tixi, MF_PATH, "MFM")
    tixi.createElement(MF_PATH, "name")
    tixi.updateTextElement(MF_PATH + "/name", "Max fuel mass")
    tixi.createElement(MF_PATH, "description")
    tixi.updateTextElement(MF_PATH + "/description", "Maximum fuel mass [kg].")
    tixi.updateDoubleElement(MF_PATH + "/mass", mw.mass_fuel_max, "%g")

    # OEM
    add_uid(tixi, OEM_PATH, "OEM")
    tixi.createElement(OEM_PATH, "name")
    tixi.updateTextElement(OEM_PATH + "/name", "Operating empty mass")
    tixi.createElement(OEM_PATH, "description")
    tixi.updateTextElement(
        OEM_PATH + "/description", "Operating empty" + " mass [kg] and related inertia [kgm^2]."
    )
    tixi.updateDoubleElement(OEM_PATH + "/mass", mw.operating_empty_mass, "%g")

    tixi.updateDoubleElement(OIM_PATH + "/mass", mw.mass_crew, "%g")
    add_uid(tixi, OIM_PATH, "massCrew")
    tixi.updateDoubleElement(MSYS_PATH, mw.mass_systems, "%g")
    add_uid(tixi, EM_PATH + "/mSystems/massDescription", "mSys")
    tixi.updateDoubleElement(MSTR_PATH, mw.mass_structure, "%g")
    add_uid(tixi, EM_PATH + "/mStructure/massDescription", "mStrt")
    tixi.updateDoubleElement(MEN_PATH, mw.mass_engines, "%g")
    add_uid(tixi, EM_PATH + "/mPowerUnits/massDescription", "mEng")

    # PAYLOAD MASS AND FUEL CARGO MASS =======================================
    add_uid(tixi, PAY_PATH, "MPM")
    tixi.createElement(PAY_PATH, "name")
    tixi.updateTextElement(PAY_PATH + "/name", "Max payload mass")
    tixi.createElement(PAY_PATH, "description")
    tixi.updateTextElement(PAY_PATH + "/description", "Maximum payload mass [kg].")
    tixi.updateDoubleElement(PAY_PATH + "/mass", mw.mass_payload, "%g")
    tixi.createElement(MC_PATH, "massCargo")
    tixi.updateDoubleElement(MC_PATH + "/massCargo", ui.mass_cargo, "%g")

    tixi.save(cpacs_out_path)


# =============================================================================
# CPACS ENGINE UPDATE
# =============================================================================


def cpacs_engine_update(ui, ed, mw, cpacs_out_path):
    """The function that update the cpacs file after the Weight_unc_main
        program.

    Args:
        mw (class): MassesWeihts class.
        ui (class): UserInputs class.
        ed (class): EngineData class.
        cpacs_out_path (str): Path of the CPACS output file.

    """

    tixi = open_tixi(cpacs_out_path)

    EN_XPATH = "/cpacs/vehicles/engines"

    if tixi.checkElement(EN_XPATH):
        tixi.removeElement(EN_XPATH)
    for e in range(0, ed.NE):

        EN_XPATH = "/cpacs/vehicles/engines/engine" + str(e + 1)
        create_branch(tixi, EN_XPATH, True)

        EN_UID = "EngineuID_" + str(e + 1)
        add_uid(tixi, EN_XPATH, EN_UID)
        tixi.createElement(EN_XPATH, "name")

        if not ed.EN_NAME[e]:
            EN_NAME = "Engine_" + str(e + 1)
            tixi.updateTextElement(EN_XPATH + "/name", EN_NAME)
        else:
            tixi.updateTextElement(EN_XPATH + "/name", ed.EN_NAME[e])

        ENA_XPATH = EN_XPATH + "/analysis/mass"
        create_branch(tixi, ENA_XPATH, False)
        add_uid(tixi, EN_XPATH, EN_UID + "_mass")
        tixi.createElement(ENA_XPATH, "mass")
        tixi.updateDoubleElement(ENA_XPATH + "/mass", ed.en_mass, "%g")

        ENT_XPATH = EN_XPATH + "/analysis"
        tixi.createElement(ENT_XPATH, "thrust00")
        tixi.updateDoubleElement(ENT_XPATH + "/thrust00", ed.max_thrust, "%g")

    tixi.save(cpacs_out_path)


# =============================================================================
#   MAIN
# =============================================================================

if __name__ == "__main__":

    log.warning("#########################################################")
    log.warning("# ERROR NOT A STANDALONE PROGRAM, RUN weightuncmain.py  #")
    log.warning("#########################################################")
