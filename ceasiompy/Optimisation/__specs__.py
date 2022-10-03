from pathlib import Path
from ceasiompy.utils.moduleinterfaces import CPACSInOut
from ceasiompy.utils.commonxpath import OPTIM_XPATH

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working of not ready)
module_status = False

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "Optimisation")


# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

include_gui = True

# ----- Input -----

cpacs_inout.add_input(
    var_name="Objective function",
    var_type=str,
    default_value="cl",
    unit="-",
    descr="""Objective function of the optimisation problem. \n Warning !
    The parameters name must match the ones in the CSV file !""",
    xpath=OPTIM_XPATH + "/objective",
    gui=include_gui,
    gui_name="Objective",
    gui_group="Global settings",
)

cpacs_inout.add_input(
    var_name="",
    var_type=list,
    default_value=None,
    unit=None,
    descr="Name of the aero map to evaluate",
    xpath=OPTIM_XPATH + "/aeroMapUID",
    gui=True,
    gui_name="__AEROMAP_SELECTION",
    gui_group="Global settings",
)

cpacs_inout.add_input(
    var_name="minmax",
    var_type=list,
    default_value=["min", "max"],
    unit=None,
    descr="Objective function of the optimisation problem",
    xpath=OPTIM_XPATH + "/minmax",
    gui=include_gui,
    gui_name="Optimisation goal",
    gui_group="Optimisation settings",
)


# For now only the COBYLA algorithm should be used.
# (only one to deal with gradient-free, constrained optimisation)
cpacs_inout.add_input(
    var_name="driver",
    var_type=list,
    default_value=["COBYLA", "Nelder-Mead"],
    unit=None,
    descr="Choose the driver to run the routine with",
    xpath=OPTIM_XPATH + "/parameters/driver",
    gui=False,
    gui_name="Driver",
    gui_group="Optimisation settings",
)

cpacs_inout.add_input(
    var_name="max_iter",
    var_type=int,
    default_value=200,
    unit=None,
    descr="Number of iterations to do",
    xpath=OPTIM_XPATH + "/iterationNB",
    gui=include_gui,
    gui_name="Max number of iterations",
    gui_group="Optimisation settings",
)

cpacs_inout.add_input(
    var_name="tol",
    var_type=float,
    default_value=1e-3,
    unit="-",
    descr="Tolerance criterion",
    xpath=OPTIM_XPATH + "/tolerance",
    gui=include_gui,
    gui_name="Tolerance",
    gui_group="Optimisation settings",
)

# Is it ok to comment that?
# cpacs_inout.add_input(
#     var_name='modules',
#     var_type=list,
#     default_value='-',
#     unit=None,
#     descr='List of modules to run',
#     gui=False,
# )

cpacs_inout.add_input(
    var_name="doedriver",
    var_type=list,
    default_value=["Uniform", "FullFactorial", "LatinHypercube", "PlackettBurman", "CSVGenerated"],
    unit=None,
    descr="Choose the type of sample generator",
    xpath=OPTIM_XPATH + "/parameters/DoE/driver",
    gui=include_gui,
    gui_name="Driver (DoE)",
    gui_group="DoE settings",
)

cpacs_inout.add_input(
    var_name="samplesnb",
    var_type=int,
    default_value=3,
    unit=None,
    descr="Needed to indicate the number of samples to be generated",
    xpath=OPTIM_XPATH + "/parameters/DoE/sampleNB",
    gui=include_gui,
    gui_name="Sample # parameter",
    gui_group="DoE settings",
)

cpacs_inout.add_input(
    var_name="UseAeromap",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Enables use of an entire aeromap for computation",
    xpath=OPTIM_XPATH + "/Config/useAero",
    gui=True,
    gui_name="Use whole aeromap",
    gui_group="DoE settings",
)

cpacs_inout.add_input(
    var_name="file_saving",
    var_type=int,
    default_value=1,
    unit="iteration",
    descr="Save file every X iteration",
    xpath=OPTIM_XPATH + "/saving/perIter",
    gui=include_gui,
    gui_name="Saving geometry every",
    gui_group="Configuration",
)

cpacs_inout.add_input(
    var_name="Configuration file path",
    var_type="pathtype",
    default_value="-",
    unit="1",
    descr="Absolute path to the CSV file",
    xpath=OPTIM_XPATH + "/Config/filepath",
    gui=True,
    gui_name="CSV file path",
    gui_group="Configuration",
)

# ----- Output -----

# cpacs_inout.add_output(
#     var_name='output',
#     default_value='-',
#     unit='1',
#     descr='Description of the output',
#     xpath='/cpacs/toolspecific/CEASIOMpy/test/myOutput',
# )
