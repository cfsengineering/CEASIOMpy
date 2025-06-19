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

from defusedxml.minidom import parse
from ceasiompy.utils.ceasiompyutils import aircraft_name
from ceasiompy.DynamicStability.func.utils import sdsa_format
from ceasiompy.DynamicStability.func.alphamax import get_alpha_max
from ceasiompy.DynamicStability.func.steadyderivatives import (
    get_tables_values,
    compute_nb_rows_aero,
    compute_nb_rows_ctrl,
)
from ceasiompy.utils.ceasiompyutils import (
    get_value,
    open_tixi,
    get_aeromap_conditions,
)
from ceasiompy.DynamicStability.func.dotderivatives import (
    get_main_wing_le,
    get_beta_dot_derivatives,
    get_alpha_dot_derivatives,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from tixi3.tixi3wrapper import Tixi3

from ceasiompy import log
from ceasiompy.PyAVL import SOFTWARE_NAME as AVL_SOFTWARE
from ceasiompy.DynamicStability import MODULE_DIR as DYNAMICSTABILITY_DIR
from ceasiompy.utils.commonxpaths import (
    AREA_XPATH,
    LENGTH_XPATH,
)
from ceasiompy.DynamicStability import (
    DYNAMICSTABILITY_CGRID_XPATH,
    DYNAMICSTABILITY_SOFTWARE_XPATH,
    DYNAMICSTABILITY_NSPANWISE_XPATH,
    DYNAMICSTABILITY_NCHORDWISE_XPATH,
    DYNAMICSTABILITY_AEROMAP_UID_XPATH,
    DYNAMICSTABILITY_VISUALIZATION_XPATH,
    DYNAMICSTABILITY_BETA_DERIVATIVES_XPATH as BETA_DERIVATIVES_XPATH,
    DYNAMICSTABILITY_ALPHA_DERIVATIVES_XPATH as ALPHA_DERIVATIVES_XPATH,
)
from ceasiompy.DynamicStability.func import (
    ROOT_XPATH,
    AERO_XPATH,
    REF_XPATH,
    PILOTEYE_XPATH,
    AEROTABLE_XPATH,
    CTRLTABLE_XPATH,
    TABLE_AEROTABLE_XPATH,
    TABLE_CTRLTABLE_XPATH,
    BETA_PRIM_XPATHS,
    ALPHA_PRIM_XPATHS,
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
    table_aerotable_xpath: str = TABLE_AEROTABLE_XPATH
    table_ctrltable_xpath: str = TABLE_CTRLTABLE_XPATH

    # Dot derivatives xPaths
    beta_prim_xpaths = BETA_PRIM_XPATHS
    alpha_prim_xpaths = ALPHA_PRIM_XPATHS

    dynstab_dir = DYNAMICSTABILITY_DIR

    def __init__(
        self: "SDSAFile",
        cpacs: CPACS,
        wkdir: Path,
        open_sdsa: bool = False,
    ) -> None:

        # Import input CPACS file
        self.cpacs = cpacs
        self.tixi = self.cpacs.tixi
        self.open_sdsa = open_sdsa

        # Import SDSAEmpty.xml file
        self.empty_sdsa_path = self.dynstab_dir / "files/SDSAEmpty.xml"
        self.empty_sdsa_file = open_tixi(self.empty_sdsa_path)

        # Create a copy of the empty SDSA file in Results > DynamicStability
        self.dynamic_stability_dir = wkdir
        self.sdsa_path = str(self.dynamic_stability_dir) + "/sdsaInputFile.xml"
        shutil.copy(self.empty_sdsa_path, self.sdsa_path)
        self.sdsa_file: Tixi3 = open_tixi(str(self.sdsa_path))

        # Get the reference dimensions
        self.s = self.tixi.getDoubleElement(AREA_XPATH)
        self.c = self.tixi.getDoubleElement(LENGTH_XPATH)
        self.b = self.s / self.c

        # Software for data used
        self.software_data = str(get_value(self.tixi, DYNAMICSTABILITY_SOFTWARE_XPATH))

        # Access CEASIOMpy input data
        self.nchordwise = int(get_value(self.tixi, DYNAMICSTABILITY_NCHORDWISE_XPATH))
        self.nspanwise = int(get_value(self.tixi, DYNAMICSTABILITY_NSPANWISE_XPATH))
        self.cgrid = get_value(self.tixi, DYNAMICSTABILITY_CGRID_XPATH)
        self.aircraft_name: str = aircraft_name(self.tixi)

        self.plot = get_value(self.tixi, DYNAMICSTABILITY_VISUALIZATION_XPATH)
        log.info(f"{self.plot=}")

        # Initialize Doublet Lattice Model
        self.model = None

        # Define constants for table and ctrltable
        self.nalpha: int = 19
        self.nmach: int = 6
        self.nbeta: int = 8

        # 0.0 is contained
        self.nq: int = 3
        self.np: int = 3
        self.nr: int = 3

        self.nelevator: int = 3
        self.naileron: int = 3
        self.nrudder: int = 3

        self.aero_nb: int = compute_nb_rows_aero(
            self.nalpha, self.nmach, self.nbeta, self.nq, self.np, self.nr
        )
        self.ctrl_nb: int = compute_nb_rows_ctrl(
            self.nalpha, self.nmach, self.nelevator, self.nrudder, self.naileron
        )

        # Dot-derivatives to compute
        self.alpha_derivatives = bool(get_value(self.tixi, ALPHA_DERIVATIVES_XPATH))
        self.beta_derivatives = bool(get_value(self.tixi, BETA_DERIVATIVES_XPATH))
        if self.alpha_derivatives:
            log.info("Computing alpha, alpha-dot derivatives")
        if self.beta_derivatives:
            log.info("Computing beta, beta-dot derivatives")
        if not self.alpha_derivatives and not self.beta_derivatives:
            log.info("You decided to not computing dot derivatives")

        # Aeromap for dot-derivatives and mach values
        (
            alt_list, mach_list, aoa_list, aos_list,
        ) = get_aeromap_conditions(self.cpacs, DYNAMICSTABILITY_AEROMAP_UID_XPATH)

        self.alt_list = alt_list

        self.mach_list: list = mach_list
        self.unique_mach_list = list(set(mach_list))
        self.len_unique_mach_list = len(self.unique_mach_list)
        self.mach_str: str = ",".join(str(mach) for mach in self.unique_mach_list)

        self.aoa_list = aoa_list
        self.aos_list = aos_list

        if self.open_sdsa:
            if not all(a == 0.0 for a in self.alt_list):
                raise ValueError("Only zero altitude is supported for sdsa.")
        if not all(a == 0.0 for a in self.aoa_list):
            raise ValueError("Only zero aoa is supported.")
        if not all(a == 0.0 for a in self.aos_list):
            raise ValueError("Only zero aos is supported.")

    def update_alpha_max(self: "SDSAFile") -> None:
        """
        Updates SDSA input file with AlphaMax values.
        """

        df_alpha_max = get_alpha_max(self)

        aero_alpha_max_xpath = ALPHAMAX_XPATH
        x_xpath = aero_alpha_max_xpath + "/X"
        values_xpath = aero_alpha_max_xpath + "/Values"

        self.update(x_xpath, sdsa_format(self.unique_mach_list))
        self.update_attribute(x_xpath, f"1 {self.len_unique_mach_list}")
        self.update(aero_alpha_max_xpath + "/NX", f"{self.len_unique_mach_list}")
        self.update(values_xpath, sdsa_format(np.radians(df_alpha_max["alpha_max"]).tolist()))
        self.update_attribute(values_xpath, f"1 {self.len_unique_mach_list}")

    def update_dot_derivatives(self: "SDSAFile") -> None:
        """
        Updates SDSA input file with dot derivatives.
        """

        if self.software_data == AVL_SOFTWARE:
            if self.open_sdsa or (not self.open_sdsa and self.alpha_derivatives):
                df_alpha_dot = get_alpha_dot_derivatives(self)
                if self.open_sdsa:
                    mach_list = df_alpha_dot["mach"].tolist()
                    len_mach_list = len(mach_list)
                    for aero_prim_xpath, column_name in self.alpha_prim_xpaths:
                        x_xpath = aero_prim_xpath + "/X"
                        values_xpath = aero_prim_xpath + "/Values"
                        self.update(x_xpath, sdsa_format(mach_list))
                        self.update_attribute(x_xpath, f"1 {len_mach_list}")
                        self.update(aero_prim_xpath + "/NX", f"{len_mach_list}")
                        self.update(values_xpath, sdsa_format(df_alpha_dot[column_name].tolist()))
                        self.update_attribute(values_xpath, f"1 {len_mach_list}")

            if self.open_sdsa or (not self.open_sdsa and self.beta_derivatives):
                df_beta_dot = get_beta_dot_derivatives(self)
                if self.open_sdsa:
                    mach_list = df_alpha_dot["mach"].tolist()
                    len_mach_list = len(mach_list)
                    for aero_prim_xpath, column_name in self.beta_prim_xpaths:
                        x_xpath = aero_prim_xpath + "/X"
                        values_xpath = aero_prim_xpath + "/Values"
                        self.update(x_xpath, sdsa_format(mach_list))
                        self.update_attribute(x_xpath, f"1 {len_mach_list}")
                        self.update(aero_prim_xpath + "/NX", f"{len_mach_list}")
                        self.update(values_xpath, sdsa_format(df_beta_dot[column_name].tolist()))
                        self.update_attribute(values_xpath, f"1 {len_mach_list}")

        else:
            log.warning(
                "Computing dot-derivatives with "
                f"software {self.software_data} is not implemented yet."
            )

    def update_tables(self: "SDSAFile") -> None:
        """
        Updates SDSA input file with table values.
        """
        table_data, ctrl_table_data = [], []
        table_df, ctrl_table_df = get_tables_values(self)

        # Update Table
        for column in table_df.columns:
            table_data.extend(table_df[column].tolist())

        self.update(self.table_aerotable_xpath, sdsa_format(table_data))
        self.update_attribute(self.table_aerotable_xpath, f"{self.aero_nb} 12")

        # Update NAlpha, NMach, Nbeta, Nq, Np, Nr
        self.update(self.aerotable_xpath + "/NAlpha", f"{self.nalpha}")
        self.update(self.aerotable_xpath + "/NMach", f"{self.nmach}")
        self.update(self.aerotable_xpath + "/Nbeta", f"{self.nbeta}")
        self.update(self.aerotable_xpath + "/Nq", f"{self.nq}")
        self.update(self.aerotable_xpath + "/Np", f"{self.np}")
        self.update(self.aerotable_xpath + "/Nr", f"{self.nr}")

        # Update CtrlTable
        for column in ctrl_table_df.columns:
            ctrl_table_data.extend(ctrl_table_df[column].tolist())

        self.update(self.table_ctrltable_xpath, sdsa_format(ctrl_table_data))
        self.update_attribute(self.table_ctrltable_xpath, f"{self.ctrl_nb} 11")

        # Update NAlpha, NMach, NElevator, NAileron, NRudder
        self.update(self.ctrltable_xpath + "/NAlpha", f"{self.nalpha}")
        self.update(self.ctrltable_xpath + "/NMach", f"{self.nmach}")
        self.update(self.ctrltable_xpath + "/NElevator", f"{self.nelevator}")
        self.update(self.ctrltable_xpath + "/NAileron", f"{self.naileron}")
        self.update(self.ctrltable_xpath + "/NRudder", f"{self.nrudder}")

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

        # If you want to open SDSA you need to update a lot more entries
        if self.open_sdsa:
            self.update_alpha_max()
            self.update_tables()
            self.update_delcoeff()
            self.update(STATUS_XPATH, "0")  # Update GEffect
            self.update_ref()
            self.update(CGRID_XPATH, f"{self.cgrid}")  # Update CGrid
            self.update_piloteye()

        self.update_dot_derivatives()
        self.save_xml()

        return self.sdsa_path

    def update(self: "SDSAFile", xpath: str, ele: str) -> None:
        self.sdsa_file.updateTextElement(xpath, ele)

    def update_attribute(self: "SDSAFile", xpath: str, ele: str) -> None:
        self.sdsa_file.addTextAttribute(xpath, "size", ele)

    def save_xml(self: "SDSAFile") -> None:
        self.sdsa_file.save(self.sdsa_path)
        dom = parse(self.sdsa_path)
        with open(self.sdsa_path, "w") as f:
            f.write(dom.toprettyxml())
