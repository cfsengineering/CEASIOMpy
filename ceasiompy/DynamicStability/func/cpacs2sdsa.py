"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Transfer CPACS unsteady data into SDSA with the correct file format (for reference: SDSAEmpty.xml).

| Author: Leon Deligny
| Creation: 27-Jan-2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import shutil
import numpy as np

from ceasiompy.utils.ceasiompyutils import aircraft_name
from ceasiompy.DynamicStability.func.utils import sdsa_format
from ceasiompy.DynamicStability.func.alphamax import get_alpha_max
from ceasiompy.DynamicStability.func.steadyderivatives import get_tables_values
from cpacspy.cpacsfunctions import (
    get_value,
    open_tixi,
)
from ceasiompy.DynamicStability.func.dotderivatives import (
    get_main_wing_le,
    compute_dot_derivatives,
)

from typing import List
from pathlib import Path
from ambiance import Atmosphere
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.PyAVL import SOFTWARE_NAME as AVL_SOFTWARE
from ceasiompy.DynamicStability import MODULE_DIR as DYNAMICSTABILITY_DIR
from ceasiompy.utils.commonxpaths import REF_XPATH as CPACS_REF_XPATH
from ceasiompy.DynamicStability import (
    ALT,
    DYNAMICSTABILITY_CGRID_XPATH,
    DYNAMICSTABILITY_SOFTWARE_XPATH,
    DYNAMICSTABILITY_MACHLIST_XPATH,
    DYNAMICSTABILITY_NSPANWISE_XPATH,
    DYNAMICSTABILITY_NCHORDWISE_XPATH,
    DYNAMICSTABILITY_VISUALIZATION_XPATH,
)
from ceasiompy.DynamicStability.func import (
    ROOT_XPATH,
    AERO_XPATH,
    REF_XPATH,
    PILOTEYE_XPATH,
    AEROTABLE_XPATH,
    CTRLTABLE_XPATH,
    XPATHS_PRIM,
    ALPHAMAX_XPATH,
    FLAPS1_XPATH,
    FLAPS2_XPATH,
    AIRBRAKE_XPATH,
    LANDGEAR_XPATH,
    STATUS_XPATH,
    CGRID_XPATH,
)

# ==============================================================================
#   CLASSES
# ==============================================================================


class SDSAFile:
    """
    This class contains the following public methods:
        generate_xml(self) -> str:
            Generates xml file for SDSA and returns it"s path.

        update_alpha_max(self) -> None:
            Updates SDSA file with AlphaMax values.

        update_dot_derivatives(self) -> None:
            Updates SDSA file with all of it"s dot derivatives.

        update_tables(self) -> None:
            Updates SDSA file with it"s table and ctrltable values.

    Subclassing:
        This class is not meant to be subclassed.

    """

    # SDSA xPath
    root_xpath: str = ROOT_XPATH
    aero_xpath: str = AERO_XPATH
    ref_xpath: str = REF_XPATH
    piloteye_xpath: str = PILOTEYE_XPATH
    aerotable_xpath: str = AEROTABLE_XPATH
    ctrltable_xpath: str = CTRLTABLE_XPATH

    # CPACS xPath
    area_xpath = CPACS_REF_XPATH + "/area"
    length_xpath = CPACS_REF_XPATH + "/length"

    # Dot derivatives xPaths
    xpaths_prim: List = XPATHS_PRIM

    # Set Atmospheric Conditions for Dynamic Stability
    # TODO : Dynamic Stability at which altitude ???
    Atm = Atmosphere(ALT)
    density = Atm.density[0]
    g = Atm.grav_accel[0]

    dynstab_dir = DYNAMICSTABILITY_DIR

    def __init__(self: "SDSAFile", cpacs: CPACS, wkdir: Path) -> None:

        # Import input CPACS file
        self.cpacs = cpacs
        self.tixi = self.cpacs.tixi

        # Import SDSAEmpty.xml file
        self.empty_sdsa_path = self.dynstab_dir / "func/SDSAEmpty.xml"
        self.empty_sdsa_file = open_tixi(self.empty_sdsa_path)

        # Create a copy of the empty SDSA file in Results > DynamicStability
        self.dynamic_stability_dir = wkdir
        self.sdsa_path = str(self.dynamic_stability_dir) + "/SDSA_Input.xml"
        shutil.copy(self.empty_sdsa_path, self.sdsa_path)
        self.sdsa_file = open_tixi(str(self.sdsa_path))

        # Get the reference dimensions
        self.s = self.tixi.getDoubleElement(self.area_xpath)
        self.c = self.tixi.getDoubleElement(self.length_xpath)
        self.b = self.s / self.c

        # Software for data used
        self.software_data = str(get_value(self.tixi, DYNAMICSTABILITY_SOFTWARE_XPATH))

        # Access CEASIOMpy input data
        self.nchordwise = int(get_value(self.tixi, DYNAMICSTABILITY_NCHORDWISE_XPATH))
        self.nspanwise = int(get_value(self.tixi, DYNAMICSTABILITY_NSPANWISE_XPATH))
        self.cgrid = get_value(self.tixi, DYNAMICSTABILITY_CGRID_XPATH)
        self.aircraft_name: str = aircraft_name(self.tixi)
        mach_str: str = get_value(self.tixi, DYNAMICSTABILITY_MACHLIST_XPATH)

        self.plot = get_value(self.tixi, DYNAMICSTABILITY_VISUALIZATION_XPATH)

        log.info(f"self.plot {self.plot}")

        # Extract and unique list of mach identifiers
        self.mach_list = list(set([float(x) for x in str(mach_str).split(';')]))
        self.mach_str = ",".join(str(mach) for mach in self.mach_list)
        self.len_mach_list = len(self.mach_list)

        # Initialize Doublet Lattice Model
        self.model = None

    def update_alpha_max(self: "SDSAFile") -> None:
        """
        Updates SDSA input file with AlphaMax values.
        """

        df_alpha_max = get_alpha_max(self)

        aero_alpha_max_xpath = ALPHAMAX_XPATH
        x_xpath = aero_alpha_max_xpath + "/X"
        values_xpath = aero_alpha_max_xpath + "/Values"

        self.update(x_xpath, sdsa_format(self.mach_list))
        self.update_attribute(x_xpath, f"1 {self.len_mach_list}")
        self.update(aero_alpha_max_xpath + "/NX", f"{self.len_mach_list}")
        self.update(values_xpath, sdsa_format(np.radians(df_alpha_max["alpha_max"]).tolist()))
        self.update_attribute(values_xpath, f"1 {self.len_mach_list}")

    def update_dot_derivatives(self: "SDSAFile") -> None:
        """
        Updates SDSA input file with dot derivatives.

        """

        if self.software_data == AVL_SOFTWARE:
            df_dot = compute_dot_derivatives(self)
            for aero_prim_xpath, column_name in self.xpaths_prim:
                x_xpath = aero_prim_xpath + "/X"
                values_xpath = aero_prim_xpath + "/Values"

                self.update(x_xpath, sdsa_format(self.mach_list))
                self.update_attribute(x_xpath, f"1 {self.len_mach_list}")
                self.update(aero_prim_xpath + "/NX", f"{self.len_mach_list}")
                self.update(values_xpath, sdsa_format(df_dot[column_name].tolist()))
                self.update_attribute(values_xpath, f"1 {self.len_mach_list}")

        else:
            log.warning(
                "Computing dot-derivatives with "
                f"software {self.software_data} is not implemented yet."
            )

    def update_tables(self: "SDSAFile") -> None:
        """
        Updates SDSA input file with table values.

        """

        table_df, ctrl_table_df = get_tables_values(self)

        table_data = []
        ctrl_table_data = []

        # Update Table
        for column in table_df.columns:
            table_data.extend(table_df[column].tolist())

        self.update(self.aerotable_xpath, sdsa_format(table_data))
        self.update_attribute(self.aerotable_xpath, f"{len(table_df)} 12")

        # Update CtrlTable
        for column in ctrl_table_df.columns:
            ctrl_table_data.extend(ctrl_table_df[column].tolist())

        self.update(self.ctrltable_xpath, sdsa_format(ctrl_table_data))
        self.update_attribute(self.ctrltable_xpath, f"{len(ctrl_table_df)} 11")

    def update_piloteye(self: "SDSAFile") -> None:
        if self.model is None:
            log.warning("Issue with DLM model in cpacs2sdsa.py.")
        else:
            x_le, _, z_le = get_main_wing_le(self.model)
            x_cg = x_le + (self.c / 4.0)

            self.update(self.piloteye_xpath + "/X", f"{x_cg}")
            self.update(self.piloteye_xpath + "/Z", f"{z_le}")

    def update_ref(self: "SDSAFile") -> None:
        self.update(self.ref_xpath + "/S", f"{self.s}")
        self.update(self.ref_xpath + "/B", f"{self.b}")
        self.update(self.ref_xpath + "/MAC", f"{self.c}")

    def update_delcoeff(self: "SDSAFile") -> None:
        zeros = "0 " * 5
        self.update(FLAPS1_XPATH, zeros)
        self.update(FLAPS2_XPATH, zeros)
        self.update(AIRBRAKE_XPATH, zeros)
        self.update(LANDGEAR_XPATH, zeros)

    def generate_xml(self: "SDSAFile") -> str:
        """
        Generates xml file for SDSA and returns the path of where it is stored.

        Returns:
            self.sdsa_path (str): Path where the complete xml file is stored.

        """

        self.update_alpha_max()
        self.update_tables()
        self.update_dot_derivatives()
        self.update_delcoeff()
        self.update(STATUS_XPATH, "0")  # Update GEffect
        self.update_ref()
        self.update(CGRID_XPATH, f"{self.cgrid}")  # Update CGrid
        self.update_piloteye()

        self.sdsa_file.save(self.sdsa_path)

        return self.sdsa_path

    def update(self: "SDSAFile", xpath: str, ele: str) -> None:
        self.sdsa_file.updateTextElement(xpath, ele)

    def update_attribute(self: "SDSAFile", xpath: str, ele: str) -> None:
        self.sdsa_file.addTextAttribute(xpath, "size", ele)


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute.")
