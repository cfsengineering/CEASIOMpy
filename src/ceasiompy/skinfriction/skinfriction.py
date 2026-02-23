"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Calculate skin friction drag coefficient.
"""

# Imports

import math

from ceasiompy.utils.ceasiompyutils import (
    call_main,
    get_selected_aeromap,
)

from pathlib import Path
from pandas import DataFrame
from ambiance import Atmosphere
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.skinfriction import MODULE_NAME


# Methods

def estimate_skin_friction_coef(
    alt: float,
    mach: float,
    wing_area: float,
    wing_span: float,
    wetted_area: float,
) -> float:
    """Return an estimation of skin friction drag coefficient based on an empirical formulas.

    Source:
        * Gerard W. H. van Es.  "Rapid Estimation of the Zero-Lift Drag
          Coefficient of Transport Aircraft", Journal of Aircraft, Vol. 39,
          No. 4 (2002), pp. 597-599. https://doi.org/10.2514/2.2997

    Returns:
        cd0 (float): Drag coefficient due to skin friction.
    """

    # Get atmosphere values at this altitude
    atmosphere = Atmosphere(alt)

    # Get speed from Mach Number
    speed = mach * atmosphere.speed_of_sound[0]
    log.info(f"Mach number: {mach} [-] -> Velocity: {round(speed)} [m/s]")

    # Reynolds number based on the ratio Wetted Area / Wing Span
    reynolds_number = (wetted_area / wing_span) * speed / atmosphere.kinematic_viscosity[0]
    log.info(f"Reynolds number: {reynolds_number:.2E} [-]")

    # Skin friction coefficient, formula from source (see function description)
    cfe = (
        0.00258
        + 0.00102 * math.exp(-6.28 * 1e-9 * reynolds_number)
        + 0.00295 * math.exp(-2.01 * 1e-8 * reynolds_number)
    )
    log.info(f"Skin friction coefficient: {cfe:.5f} [-]")

    # Drag coefficient due to skin friction
    cd0 = cfe * wetted_area / wing_area
    log.info(f"Skin friction drag coefficient: {cd0:.5f} [-]")

    return cd0


def _compute_wetted_area(cpacs: CPACS) -> float:
    """
    Computes the total wetted area by summing the surface area of 
    all wings and fuselages via the TiGL configuration.
    """
    # Access the configuration manager
    aircraft_config = cpacs.aircraft.configuration

    # Initialize the total wetted area
    total_wetted_area = 0.0

    # 1. Sum wetted area of all fuselages
    for f in range(1, aircraft_config.get_fuselage_count() + 1):
        fuselage = aircraft_config.get_fuselage(f)
        total_wetted_area += fuselage.get_surface_area()

    # 2. Sum wetted area of all wings
    for wing_idx in range(1, aircraft_config.get_wing_count() + 1):
        wing = aircraft_config.get_wing(wing_idx)
        wing_uid = wing.get_uid()
        total_wetted_area += cpacs.tigl.wingGetWettedArea(wing_uid)

    return total_wetted_area


# Main
def main(cpacs: CPACS, results_dir: Path) -> None:
    """Computes the skin friction drag 'cd0'."""

    # Compute geometric properties
    wetted_area = _compute_wetted_area(cpacs)
    wing_area = cpacs.aircraft.wing_area
    wing_span = cpacs.aircraft.wing_span

    # FIX 1: Remove 'axis=0' from DataFrame constructor
    geometry_df = DataFrame(
        data=[
            {
                "Wetted Area [m^2]": wetted_area,
                "Wing Area [m^2]": wing_area,
                "Wing Span [m]": wing_span,
            }
        ]
    )
    geometry_df.to_csv(
        Path(results_dir, "geometry.csv"),
        index=False,
    )

    # Note: Ensure get_selected_aeromap returns the object, not just the UID
    # If it returns a UID, use: aeromap = cpacs.get_aeromap_by_uid(selected_aeromap)
    selected_aeromap = get_selected_aeromap(cpacs)

    # 1. Create a DataFrame of unique flight conditions (alt, mach)
    df_unique_conditions = selected_aeromap.df[["altitude", "machNumber"]].drop_duplicates().copy()

    # 2. Compute cd0 for these unique points
    df_unique_conditions["cd0"] = df_unique_conditions.apply(
        lambda row: estimate_skin_friction_coef(
            alt=row["altitude"],
            mach=row["machNumber"],
            wing_area=wing_area, 
            wing_span=wing_span,
            wetted_area=wetted_area,
        ),
        axis=1,
    )

    # FIX 2: Use .rename() instead of .apply() to change column names
    df_rename = df_unique_conditions.rename(
        columns={
            "machNumber": "mach",
            "cd0": "Skin Friction Drag Coefficient",
        }
    )

    # 3. Save this specific computation to a CSV
    csv_path = Path(results_dir, "skin_friction.csv")
    df_rename.to_csv(csv_path, index=False)


if __name__ == "__main__":
    call_main(main, MODULE_NAME)
