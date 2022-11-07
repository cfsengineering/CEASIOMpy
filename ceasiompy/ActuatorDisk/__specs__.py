from pathlib import Path

from ceasiompy.utils.commonxpath import (
    AEROPERFORMANCE_XPATH,
    RANGE_XPATH,
    PROP_XPATH,
)
from ceasiompy.utils.moduleinterfaces import CPACSInOut

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = True

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "AD")

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ----- Input -----

cpacs_inout.add_input(
    var_name="cruise_mach",
    var_type=float,
    default_value=0.4,
    unit="1",
    descr="Aircraft cruise Mach number",
    xpath=RANGE_XPATH + "/cruiseMach",
    gui=False,
    gui_name="Cruise Mach",
)

cpacs_inout.add_input(
    var_name="cruise_alt",
    var_type=float,
    default_value=9000.0,
    unit="m",
    descr="Aircraft cruise altitude",
    xpath=RANGE_XPATH + "/cruiseAltitude",
    gui=False,
    gui_name="Cruise Altitude",
)

cpacs_inout.add_input(
    var_name="station",
    var_type=float,
    default_value=20,
    unit=None,
    descr="Number of elements for blade discretization",
    xpath=PROP_XPATH + "/propeller/blade/discretization",
    gui=True,
    gui_name="Blade discretization",
    gui_group="Optimal prop settings",
)

cpacs_inout.add_input(
    var_name="radius",
    var_type=float,
    default_value=2,
    unit="m",
    descr="Propeller radius",
    xpath=PROP_XPATH + "/propeller/blade/discretization",
    gui=True,
    gui_name="radius setting",
    gui_group="Optimal prop settings",
)

cpacs_inout.add_input(
    var_name="thrust",
    var_type=float,
    default_value=6500,
    unit="N",
    descr="Aircraft thrust",
    xpath=PROP_XPATH + "propeller/thrust",
    gui=True,
    gui_name="Thrust setting",
    gui_group="Optimal prop settings",
)

cpacs_inout.add_input(
    var_name="n",
    var_type=float,
    default_value=2000,
    unit="1/s",
    descr="Propeller rotational velocity",
    xpath=PROP_XPATH + "propeller/rotational_velocity",
    gui=True,
    gui_name="Rotational velocity setting",
    gui_group="Optimal prop settings",
)

cpacs_inout.add_input(
    var_name="prandtl",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="No Prandtl tip loss correction",
    xpath=PROP_XPATH + "propeller/blade/loss",
    gui=True,
    gui_name="Tip without loss correction",
    gui_group="Optimal prop settings",
)

cpacs_inout.add_input(
    var_name="prandtl",
    var_type=bool,
    default_value=True,
    unit=None,
    descr="Enable the tip loss correction of Prandtl",
    xpath=PROP_XPATH + "propeller/blade/loss",
    gui=True,
    gui_name="Tip loss correction",
    gui_group="Optimal prop settings",
)

cpacs_inout.add_input(
    var_name="blades_number",
    var_type=int,
    default_value=2,
    unit=None,
    descr="Number of propeller blades",
    xpath=PROP_XPATH + "propeller/bladeNumber",
    gui=True,
    gui_name="Propeller blades numbers",
    gui_group="Optimal prop settings",
)

# ----- Output -----

cpacs_inout.add_output(
    var_name="thrust_coefficient_distribution",
    default_value=None,
    unit="1",
    descr="Distribution of thrust coefficient along the radius",
    xpath=AEROPERFORMANCE_XPATH + "/aeroMap/aeroPerformanceMap",
)
