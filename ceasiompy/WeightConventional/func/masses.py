"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This script store all the aircraft masses ...

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2022-06-01

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.WeightConventional.func.mtom import estimate_mtom
from ceasiompy.WeightConventional.func.oem import estimate_oem

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonxpath import (
    MASS_CARGO_XPATH,
    MOEM_XPATH,
    MTOM_XPATH,
    WB_MAX_PAYLOAD_XPATH,
)
from ceasiompy.WeightConventional.func.weightutils import UNUSABLE_FUEL_RATIO

from cpacspy.cpacsfunctions import add_value, get_value_or_default

log = get_logger()


# =================================================================================================
#   CLASSES
# =================================================================================================


class AircfaftMasses:
    """
    Class to store and calculate aircraft masses.

    Attributes:
        ...

    """

    def __init__(self, cpacs):

        self.cpacs = cpacs

        # User input
        # Maximum payload allowed, set 0 if equal to max passenger mass.
        self.max_payload_mass = get_value_or_default(cpacs.tixi, WB_MAX_PAYLOAD_XPATH, 0)
        self.cargo_mass = get_value_or_default(cpacs.tixi, MASS_CARGO_XPATH, 0.0)
        self.fuel_density = 800  # TODO: deal with multiple fuel store in cpacs
        # self.fuel_density = get_value_or_default(cpacs.tixi, FUEL_DENSITY_XPATH, 800)
        # add_uid(cpacs.tixi, FUEL_DENSITY_XPATH, "kerosene")

        self.mass_fuel_max = 0
        self.payload_mass = 0

    def get_mtom(self, fuselage_length, fuselage_width, wing_area, wing_span, results_dir):
        """Maximum Take-Off Mass evaluation"""

        self.mtom = estimate_mtom(
            fuselage_length, fuselage_width, wing_area, wing_span, results_dir
        )

    def get_oem(self, fuselage_length, wing_span, turboprop):
        """Operating Empty Mass evaluation"""

        self.oem = estimate_oem(self.mtom, fuselage_length, wing_span, turboprop)

    def get_payload_mass(self, passenger_mass):
        """Payload Mass evaluation"""

        self.payload_mass = self.cargo_mass + passenger_mass

        if self.max_payload_mass > 0 and self.payload_mass > self.max_payload_mass:
            self.payload_mass = self.max_payload_mass
            log.warning("Maximum payload exceeded, set payload to maximum payload.")

    @property
    def mass_fuel_max_passenger(self):
        return self.mtom - self.oem - self.payload_mass

    @property
    def zfm(self):
        """Zero Fuel Mass evaluation"""

        return self.mtom - self.mass_fuel_max_passenger + UNUSABLE_FUEL_RATIO * self.mass_fuel_max

    def get_mass_fuel_max(self, wing_area, fuse_length, turboprop):
        """Maximum fuel mass evaluation, maximum fuel that can be stored with maximum
        number of passengers.

        Args:
            wing_area (float): Wing area [m^2]
            fuse_length (float): Fuselage length [m]
            turboprop (bool): True if turboprop is used, False otherwise.\

        """

        if turboprop:
            if wing_area > 55.00:
                coef = 4.6
            else:
                coef = 3.6
        elif wing_area < 90.00:
            if fuse_length < 60.00:
                coef = 4.3
            else:
                coef = 4.0
        elif wing_area < 300.00:
            if fuse_length < 35.00:
                coef = 3.6
            else:
                coef = 3.8
        elif wing_area < 400.00:
            coef = 2.2
        elif wing_area < 600.00:
            coef = 2.35
        else:
            coef = 2.8

        self.mass_fuel_max = self.mtom / coef

    def get_wing_loading(self, wings_area):
        self.wing_loading = self.mtom / wings_area

    def save_to_cpacs(self):
        """Save mass to cpacs"""

        attr_to_xpath = {
            "mtom": MTOM_XPATH,
            "oem": MOEM_XPATH,
        }

        for attr, xpath in attr_to_xpath.items():
            add_value(self.cpacs.tixi, xpath, getattr(self, attr))

    # TODO: save as above
    # if not tixi.checkElement(PASS_XPATH + "/fuelMassMaxpass"):
    #     tixi.createElement(PASS_XPATH, "fuelMassMaxpass")
    # FMP_XPATH = PASS_XPATH + "/fuelMassMaxpass"
    # if not tixi.checkElement(FMP_XPATH + "/description"):
    #     tixi.createElement(FMP_XPATH, "description")
    # tixi.updateTextElement(
    #     FMP_XPATH + "/description", "Maximum amount of " + "fuel with maximum payload [kg]"
    # )
    # if not tixi.checkElement(FMP_XPATH + "/mass"):
    #     tixi.createElement(FMP_XPATH, "mass")
    # tixi.updateDoubleElement(FMP_XPATH + "/mass", mw.mass_fuel_maxpass, "%g")

    # # CPACS MASS BREAKDOWN UPDATE

    # MD_XPATH = MASSBREAKDOWN_XPATH + "/designMasses"
    # MTOM_XPATH = MD_XPATH + "/mTOM"
    # MZFM_XPATH = MD_XPATH + "/mZFM"
    # MF_XPATH = MASSBREAKDOWN_XPATH + "/fuel/massDescription"
    # OEM_XPATH = MASSBREAKDOWN_XPATH + "/mOEM/massDescription"
    # PAY_XPATH = MASSBREAKDOWN_XPATH + "/payload/massDescription"
    # MC_XPATH = MASSBREAKDOWN_XPATH + "/payload/mCargo"
    # OIM_XPATH = MASSBREAKDOWN_XPATH + "/mOEM/mOperatorItems/mCrewMembers/massDescription"

    # # DESIGN MASSES
    # add_uid(tixi, MTOM_XPATH, "MTOM")
    # tixi.createElement(MTOM_XPATH, "name")
    # tixi.updateTextElement(MTOM_XPATH + "/name", "Maximum take-off mass")
    # tixi.createElement(MTOM_XPATH, "description")
    # tixi.updateTextElement(
    #     MTOM_XPATH + "/description",
    #     "Maximum " + "take off mass [kg], CoG coordinate [m] and " + "moment of inertia.",
    # )
    # tixi.updateDoubleElement(MTOM_XPATH + "/mass", mw.maximum_take_off_mass, "%g")

    # # MZFM
    # add_uid(tixi, MZFM_XPATH, "MZFM")
    # tixi.createElement(MZFM_XPATH, "name")
    # tixi.updateTextElement(MZFM_XPATH + "/name", "Maximum zero fuel mass")
    # tixi.createElement(MZFM_XPATH, "description")
    # tixi.updateTextElement(
    #     MZFM_XPATH + "/description",
    #     "Maximum "
    #     + "zero fuel mass [kg] and corresponding CoG "
    #     + "coordinate [m], moment of inertia.",
    # )
    # tixi.updateDoubleElement(MZFM_XPATH + "/mass", mw.zero_fuel_mass, "%g")

    # # FUEL MASS
    # add_uid(tixi, MF_XPATH, "MFM")
    # tixi.createElement(MF_XPATH, "name")
    # tixi.updateTextElement(MF_XPATH + "/name", "Max fuel mass")
    # tixi.createElement(MF_XPATH, "description")
    # tixi.updateTextElement(MF_XPATH + "/description", "Maximum fuel mass [kg]")
    # tixi.updateDoubleElement(MF_XPATH + "/mass", mw.mass_fuel_max, "%g")

    # # OEM
    # add_uid(tixi, OEM_XPATH, "OEM")
    # tixi.createElement(OEM_XPATH, "name")
    # tixi.updateTextElement(OEM_XPATH + "/name", "Operating empty mass")
    # tixi.createElement(OEM_XPATH, "description")
    # tixi.updateTextElement(
    #     OEM_XPATH + "/description", "Operating empty" + " mass [kg] and related inertia [kgm^2]."
    # )
    # tixi.updateDoubleElement(OEM_XPATH + "/mass", mw.operating_empty_mass, "%g")
    # tixi.updateDoubleElement(OIM_XPATH + "/mass", mw.mass_crew, "%g")
    # add_uid(tixi, OIM_XPATH, "massCrew")

    # # PAYLOAD MASS AND FUEL WITH MAX PAYLOAD
    # add_uid(tixi, PAY_XPATH, "MPM")
    # tixi.createElement(PAY_XPATH, "name")
    # tixi.updateTextElement(PAY_XPATH + "/name", "Max payload mass")
    # tixi.createElement(PAY_XPATH, "description")
    # tixi.updateTextElement(PAY_XPATH + "/description", "Maximum " + "payload mass [kg].")
    # tixi.updateDoubleElement(PAY_XPATH + "/mass", mw.mass_payload, "%g")

    # if mw.mass_cargo:
    #     tixi.createElement(MC_XPATH, "massCargo")
    #     tixi.updateDoubleElement(MC_XPATH + "/massCargo", mw.mass_cargo, "%g")

    def write_masses_output(self, masses_output_file):
        """Write the seat configuration in a file in the result directory."""

        lines = open(masses_output_file, "w")
        lines.write("\n---------------------------------------------")
        lines.write("\n---------------- MASSES ---------------------")
        lines.write("\n---------------------------------------------")
        lines.write("\nMasses estimation ---------------------------")
        lines.write(f"\nMaximum take off mass : {int(self.mtom)} [kg]")
        lines.write(f"\nOperating empty mass : {int(self.oem)} [kg]")
        lines.write(f"\nZero fuel mass : {int(self.zfm)} [kg]")
        lines.write("\n---------------------------------------------")
        lines.write("\nPayload and Fuel ----------------------------")
        lines.write(f"\nMaximum payload mass : {int(self.payload_mass)} [kg]")
        lines.write(f"\nCargo mass : {int(self.cargo_mass)} [kg]")
        lines.write(
            f"\nMaximum fuel mass with max passengers : {int(self.mass_fuel_max_passenger)} [kg]"
        )
        lines.write(f"\nMaximum fuel mass with no passengers : {int(self.mass_fuel_max)} [kg]")
        lines.write(
            "\nMaximum fuel volume with no passengers:"
            f"{int(self.mass_fuel_max / self.fuel_density *1000)} [l]"
        )
        lines.write(f"\nWing loading: {int(self.wing_loading)} [kg/m^2]")

        lines.close()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
