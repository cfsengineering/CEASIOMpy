"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This script store all the aircraft masses ...

| Author : Aidan Jungo
| Creation: 2022-06-01

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.WeightConventional.func.mtom import estimate_mtom
from ceasiompy.WeightConventional.func.oem import estimate_oem

from ceasiompy import log
from ceasiompy.utils.commonxpaths import (
    FUEL_MASS_XPATH,
    MASS_CARGO_XPATH,
    MOEM_XPATH,
    MTOM_XPATH,
    MZFM_XPATH,
    PAYLOAD_MASS_XPATH,
    WB_MAX_PAYLOAD_XPATH,
)
from ceasiompy.WeightConventional.func.weightutils import UNUSABLE_FUEL_RATIO

from cpacspy.cpacsfunctions import add_value, get_value_or_default


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
            "zfm": MZFM_XPATH,
            "mass_fuel_max_passenger": FUEL_MASS_XPATH,
            "payload_mass": PAYLOAD_MASS_XPATH,
        }

        for attr, xpath in attr_to_xpath.items():
            add_value(self.gui_settings.tixi, xpath, getattr(self, attr))

    def write_masses_output(self, masses_output_file):
        """Write the seat configuration in a file in the result directory."""

        lines = open(masses_output_file, "w")
        lines.write("\n### MASSES")
        lines.write("\n#### Masses estimation")
        lines.write(f"\n- Maximum take off mass : {int(self.mtom)} [kg]")
        lines.write(f"\n- Operating empty mass : {int(self.oem)} [kg]")
        lines.write(f"\n- Zero fuel mass : {int(self.zfm)} [kg]")
        lines.write("\n#### Payload and Fuel")
        lines.write(f"\n- Maximum payload mass : {int(self.payload_mass)} [kg]")
        lines.write(f"\n- Cargo mass : {int(self.cargo_mass)} [kg]")
        lines.write(
            f"\n- Maximum fuel mass with max passengers : {int(self.mass_fuel_max_passenger)} [kg]"
        )
        lines.write(f"\n- Maximum fuel mass with no passengers : {int(self.mass_fuel_max)} [kg]")
        lines.write(
            "\n- Maximum fuel volume with no passengers:"
            f"{int(self.mass_fuel_max / self.fuel_density * 1000)} [l]"
        )
        lines.write(f"\n- Wing loading: {int(self.wing_loading)} [kg/m^2]")

        lines.close()
