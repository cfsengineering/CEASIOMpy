"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The code updates the cpacs file after the weight analysis.

Python version: >=3.7

| Author : Stefano Piccini
| Date of creation: 2018-11-21

TODO:
    * also integrate to Class function?

"""

# =============================================================================
#   IMPORTS
# =============================================================================

from cpacspy.cpacsfunctions import add_uid, create_branch, open_tixi
from ceasiompy.utils.xpath import CREW_XPATH, MASSBREAKDOWN_XPATH, PASS_XPATH

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])


# =============================================================================
#   CLASSES
# =============================================================================

#  InsideDimensions class, can be found on the InputClasses folder inside the
#  weightconvclass.py script.


# =============================================================================
#   FUNCTIONS
# =============================================================================


def cpacs_update(mw, out, cpacs_path, cpacs_out_path):
    """The function updates the cpacs file after the Weight analysis.

    Args:
        mw (class) : MassesWeights class
        out (class) : WeightOutput class
        cpacs_path (str) : Path to the CPACS file
        cpacs_out_path (str) : Path to the output CPACS file

    """

    tixi = open_tixi(
        cpacs_out_path
    )  # (because it has been modifed somewre else, TODO: change that)

    # Path update
    if not tixi.checkElement(CREW_XPATH + "/cabinCrewMembers/cabinCrewMemberNb"):
        create_branch(tixi, CREW_XPATH + "/cabinCrewMembers/cabinCrewMemberNb")
    tixi.updateDoubleElement(
        CREW_XPATH + "/cabinCrewMembers/cabinCrewMemberNb", out.cabin_crew_nb, "%g"
    )

    if not tixi.checkElement(PASS_XPATH + "/passNb"):
        tixi.createElement(PASS_XPATH, "passNb")
    tixi.updateIntegerElement(PASS_XPATH + "/passNb", out.pass_nb, "%i")
    if not tixi.checkElement(PASS_XPATH + "/rowNb"):
        tixi.createElement(PASS_XPATH, "rowNb")
    tixi.updateIntegerElement(PASS_XPATH + "/rowNb", out.row_nb, "%i")
    if not tixi.checkElement(PASS_XPATH + "/aisleNb"):
        tixi.createElement(PASS_XPATH, "aisleNb")
    tixi.updateIntegerElement(PASS_XPATH + "/aisleNb", out.aisle_nb, "%i")
    if not tixi.checkElement(PASS_XPATH + "/toiletNb"):
        tixi.createElement(PASS_XPATH, "toiletNb")
    tixi.updateIntegerElement(PASS_XPATH + "/toiletNb", out.toilet_nb, "%i")
    if not tixi.checkElement(PASS_XPATH + "/abreastNb"):
        tixi.createElement(PASS_XPATH, "abreastNb")
    tixi.updateIntegerElement(PASS_XPATH + "/abreastNb", out.abreast_nb, "%i")

    if not tixi.checkElement(PASS_XPATH + "/fuelMassMaxpass"):
        tixi.createElement(PASS_XPATH, "fuelMassMaxpass")
    FMP_XPATH = PASS_XPATH + "/fuelMassMaxpass"
    if not tixi.checkElement(FMP_XPATH + "/description"):
        tixi.createElement(FMP_XPATH, "description")
    tixi.updateTextElement(
        FMP_XPATH + "/description", "Maximum amount of " + "fuel with maximum payload [kg]"
    )
    if not tixi.checkElement(FMP_XPATH + "/mass"):
        tixi.createElement(FMP_XPATH, "mass")
    tixi.updateDoubleElement(FMP_XPATH + "/mass", mw.mass_fuel_maxpass, "%g")

    # CPACS MASS BREAKDOWN UPDATE

    # Path creation
    if tixi.checkElement(MASSBREAKDOWN_XPATH):
        tixi.removeElement(MASSBREAKDOWN_XPATH)

    MD_XPATH = MASSBREAKDOWN_XPATH + "/designMasses"
    MTOM_XPATH = MD_XPATH + "/mTOM"
    MZFM_XPATH = MD_XPATH + "/mZFM"
    MF_XPATH = MASSBREAKDOWN_XPATH + "/fuel/massDescription"
    OEM_XPATH = MASSBREAKDOWN_XPATH + "/mOEM/massDescription"
    PAY_XPATH = MASSBREAKDOWN_XPATH + "/payload/massDescription"
    MC_XPATH = MASSBREAKDOWN_XPATH + "/payload/mCargo"
    OIM_XPATH = MASSBREAKDOWN_XPATH + "/mOEM/mOperatorItems/mCrewMembers/massDescription"

    create_branch(tixi, MTOM_XPATH + "/mass", False)
    create_branch(tixi, MZFM_XPATH + "/mass", False)
    create_branch(tixi, MF_XPATH + "/mass", False)
    create_branch(tixi, OEM_XPATH + "/mass", False)
    create_branch(tixi, PAY_XPATH + "/mass", False)
    create_branch(tixi, MC_XPATH, False)
    create_branch(tixi, OIM_XPATH + "/mass", False)

    # DESIGN MASSES
    add_uid(tixi, MTOM_XPATH, "MTOM")
    tixi.createElement(MTOM_XPATH, "name")
    tixi.updateTextElement(MTOM_XPATH + "/name", "Maximum take-off mass")
    tixi.createElement(MTOM_XPATH, "description")
    tixi.updateTextElement(
        MTOM_XPATH + "/description",
        "Maximum " + "take off mass [kg], CoG coordinate [m] and " + "moment of inertia.",
    )
    tixi.updateDoubleElement(MTOM_XPATH + "/mass", mw.maximum_take_off_mass, "%g")

    # MZFM
    add_uid(tixi, MZFM_XPATH, "MZFM")
    tixi.createElement(MZFM_XPATH, "name")
    tixi.updateTextElement(MZFM_XPATH + "/name", "Maximum zero fuel mass")
    tixi.createElement(MZFM_XPATH, "description")
    tixi.updateTextElement(
        MZFM_XPATH + "/description",
        "Maximum "
        + "zero fuel mass [kg] and corresponding CoG "
        + "coordinate [m], moment of inertia.",
    )
    tixi.updateDoubleElement(MZFM_XPATH + "/mass", mw.zero_fuel_mass, "%g")

    # FUEL MASS
    add_uid(tixi, MF_XPATH, "MFM")
    tixi.createElement(MF_XPATH, "name")
    tixi.updateTextElement(MF_XPATH + "/name", "Max fuel mass")
    tixi.createElement(MF_XPATH, "description")
    tixi.updateTextElement(MF_XPATH + "/description", "Maximum fuel mass [kg]")
    tixi.updateDoubleElement(MF_XPATH + "/mass", mw.mass_fuel_max, "%g")

    # OEM
    add_uid(tixi, OEM_XPATH, "OEM")
    tixi.createElement(OEM_XPATH, "name")
    tixi.updateTextElement(OEM_XPATH + "/name", "Operating empty mass")
    tixi.createElement(OEM_XPATH, "description")
    tixi.updateTextElement(
        OEM_XPATH + "/description", "Operating empty" + " mass [kg] and related inertia [kgm^2]."
    )
    tixi.updateDoubleElement(OEM_XPATH + "/mass", mw.operating_empty_mass, "%g")
    tixi.updateDoubleElement(OIM_XPATH + "/mass", mw.mass_crew, "%g")
    add_uid(tixi, OIM_XPATH, "massCrew")

    # PAYLOAD MASS AND FUEL WITH MAX PAYLOAD
    add_uid(tixi, PAY_XPATH, "MPM")
    tixi.createElement(PAY_XPATH, "name")
    tixi.updateTextElement(PAY_XPATH + "/name", "Max payload mass")
    tixi.createElement(PAY_XPATH, "description")
    tixi.updateTextElement(PAY_XPATH + "/description", "Maximum " + "payload mass [kg].")
    tixi.updateDoubleElement(PAY_XPATH + "/mass", mw.mass_payload, "%g")

    if mw.mass_cargo:
        tixi.createElement(MC_XPATH, "massCargo")
        tixi.updateDoubleElement(MC_XPATH + "/massCargo", mw.mass_cargo, "%g")

    tixi.save(cpacs_out_path)


# =============================================================================
#   MAIN
# =============================================================================

if __name__ == "__main__":

    log.warning("###########################################################")
    log.warning("#### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ####")
    log.warning("###########################################################")
