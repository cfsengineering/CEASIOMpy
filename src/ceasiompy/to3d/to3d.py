# Imports

from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.guiobjects import add_value

from pathlib import Path
from cpacspy.cpacspy import CPACS
from tixi3.tixi3wrapper import Tixi3

from ceasiompy.utils.commonxpaths import (
    WINGS_XPATH,
    GEOMETRY_MODE_XPATH,
)
from ceasiompy.to3d import (
    MODULE_NAME,
    TO_THREED_SPAN_XPATH,
    TO_THREED_CHORD_XPATH,
    TO_THREED_TWIST_XPATH,
    TO_THREED_SWEEP_XPATH,
    TO_THREED_DIHEDRAL_XPATH,
)


# Methods

def _retrieve_gui_values(tixi: Tixi3) -> tuple[
    float, float,
    float, float, float,
]:
    span_length = float(get_value(
        tixi=tixi,
        xpath=TO_THREED_SPAN_XPATH,
    ))
    chord_length = float(get_value(
        tixi=tixi,
        xpath=TO_THREED_CHORD_XPATH,
    ))
    twist_angle = float(get_value(
        tixi=tixi,
        xpath=TO_THREED_TWIST_XPATH,
    ))
    sweep_angle = float(get_value(
        tixi=tixi,
        xpath=TO_THREED_SWEEP_XPATH,
    ))
    dihedral_angle = float(get_value(
        tixi=tixi,
        xpath=TO_THREED_DIHEDRAL_XPATH,
    ))
    return (
        span_length, chord_length,
        twist_angle, sweep_angle, dihedral_angle,
    )


# Main

def main(cpacs: CPACS, results_dir: Path) -> None:
    # Define variables
    tixi = cpacs.tixi
    wing_xpath = WINGS_XPATH + "/wing[1]"
    section_xpath = wing_xpath + "/sections/section[2]/transformation"
    positioning_xpath = wing_xpath + "/positionings/positioning[2]"
    chord_xpath = section_xpath + "/scaling/x"
    twist_xpath = section_xpath + "/rotation/y"
    span_xpath = positioning_xpath + "/length"
    sweep_xpath = positioning_xpath + "/sweepAngle"
    dihedral_xpath = positioning_xpath + "/dihedralAngle"

    # Sanity Checks
    dim_mode = get_value(
        tixi=tixi,
        xpath=GEOMETRY_MODE_XPATH,
    )

    if dim_mode != "2D":
        raise ValueError(f"CPACS must be 2D to use {MODULE_NAME} module.")

    # Update the Geometry and override the input/output cpacs file with the new 3D values
    (
        span_length, chord_length,
        twist_angle, sweep_angle, dihedral_angle,
    ) = _retrieve_gui_values(tixi)

    add_value(
        tixi=tixi,
        xpath=chord_xpath,
        value=chord_length,
    )
    add_value(
        tixi=tixi,
        xpath=twist_xpath,
        value=twist_angle,
    )

    # Update with variables
    add_value(
        tixi=tixi,
        xpath=span_xpath,
        value=span_length,
    )
    add_value(
        tixi=tixi,
        xpath=sweep_xpath,
        value=sweep_angle,
    )
    add_value(
        tixi=tixi,
        xpath=dihedral_xpath,
        value=dihedral_angle,
    )
    add_value(
        tixi=tixi,
        xpath=GEOMETRY_MODE_XPATH,
        value="3D",
    )

    # Post-Processing (i.e. store the resulting CPACS .xml file)
    cpacs_path = Path(cpacs.cpacs_file)
    cpacs_out_path = results_dir / str(cpacs_path.stem + f"_{MODULE_NAME}.xml")
    cpacs.save_cpacs(cpacs_out_path, overwrite=True)
