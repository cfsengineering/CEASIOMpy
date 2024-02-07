from pathlib import Path
from ceasiompy.utils.moduleinterfaces import CPACSInOut
from ceasiompy.utils.commonxpath import (
    REF_XPATH,
    CLCALC_XPATH,
    SU2_FIXED_CL_XPATH,
    SU2_TARGET_CL_XPATH,
    ENGINE_TYPE_XPATH,
    RANGE_XPATH,
)

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = True

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "Thermodata")

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ===== Input =====


cpacs_inout.add_input(
    var_name="net_force",
    var_type=float,
    default_value=2000,
    unit="1",  # AGGIUNGERE UNITA DI MISURA
    descr="Engine net force",
    xpath=RANGE_XPATH + "/NetForce",
    gui=True,
    gui_name="NetForce",
    gui_group="Cruise",
)

cpacs_inout.add_input(
    var_name="engine type",
    var_type=list,
    default_value=[0, 1],
    unit=None,
    descr="0: TBJ, 1: TBF ",
    xpath=ENGINE_TYPE_XPATH,
    gui=True,
    gui_name="0 for Turbojet 1 for Turbofan",
    gui_group="User inputs",
)


# ===== Output =====

cpacs_inout.add_output(
    var_name="target_cl",
    default_value=None,
    unit="1",
    descr="Value of CL to achieve to have a level flight with the given conditions",
    xpath=SU2_TARGET_CL_XPATH,
)

cpacs_inout.add_output(
    var_name="fixed_cl",
    default_value=None,
    unit="-",
    descr="FIXED_CL_MODE parameter for SU2",
    xpath=SU2_FIXED_CL_XPATH,
)
