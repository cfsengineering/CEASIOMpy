"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Compute AlphaMax for SDSA from ceasiomp.db.

| Author: Leon Deligny
| Creation: 25 March 2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import numpy as np

from pandas import DataFrame
from ceasiompy.Database.func.storing import CeasiompyDb

from ceasiompy import log
from ceasiompy.DynamicStability import ALT
from ceasiompy.PyAVL import SOFTWARE_NAME as AVL_SOFTWARE

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_alpha_max(self) -> DataFrame:
    """
    Compute alpha max, i.e. d Cm/ d alpha = 0.
    alpha_max will correspond to the the smallest alpha
    such that the derivative is positive:
    alpha_max = argmax_alpha (d Cm/ d alpha) (alpha) < 0.

    Assumptions:
        beta = p = q = r = 0
        alt = 1000.0

    Returns:
        DataFrame: AlphaMax per mach.

    """

    log.info("--- Computing AlphaMax per Mach ---")

    if self.software_data == AVL_SOFTWARE:
        table_name = "avl_data"
    else:
        log.warning(f"software {self.software_data} not implemented yet.")

    # Retrieve data from db
    ceasiompy_db = CeasiompyDb()
    data = ceasiompy_db.get_data(
        table_name=table_name,
        columns=["mach", "alpha", "cms_a"],
        filters=[
            f"mach IN ({self.mach_str})",
            f"aircraft = '{self.aircraft_name}'",
            f"alt = {ALT}",
            "beta = 0.0",
            "pb_2V = 0.0",
            "qc_2V = 0.0",
            "rb_2V = 0.0",
        ],
    )
    ceasiompy_db.close()

    data_array = np.array(data)
    mach_values = data_array[:, 0]
    alpha_values = data_array[:, 1]
    cms_a_values = data_array[:, 2]
    unique_mach = np.unique(mach_values)

    alpha_max_results = []

    # Vectorized computation for each Mach number
    for mach in unique_mach:
        mask = mach_values == mach
        alphas = alpha_values[mask]
        cms_a = cms_a_values[mask]

        sorted_indices = np.argsort(alphas)
        alphas = alphas[sorted_indices]
        cms_a = cms_a[sorted_indices]

        positive_indices = np.where(cms_a < 0)[0]
        if len(positive_indices) > 0:
            # Largest alpha where cms_a < 0
            alpha_max = alphas[positive_indices[-1]]
        else:
            alpha_max = 0.0

        alpha_max_results.append({"mach": mach, "alpha_max": alpha_max})

    alpha_max_df = DataFrame(alpha_max_results)

    log.info("--- Finished computing AlphaMax ---")

    return alpha_max_df


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute.")
