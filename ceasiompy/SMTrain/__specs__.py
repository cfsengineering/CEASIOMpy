from pathlib import Path
from ceasiompy.utils.commonxpath import (
    SMTRAIN_XPATH,
    SMTRAIN_DOE,
    CEASIOMPY_XPATH,
)
from ceasiompy.utils.moduleinterfaces import CPACSInOut

# from ceasiompy.utils.commonxpath import SMTRAIN_XPATH

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = True

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "SMTrain")

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

include_gui = True

# ----- Input -----


cpacs_inout.add_input(
    var_name="fidelity_levels",
    var_type=int,
    default_value="1",
    descr="Defining the number of fidelity level used to train the surrogate model",
    xpath=SMTRAIN_XPATH + "/fidelityLevel",
    gui=include_gui,
    gui_name="Number of fidelity level",
    gui_group="Global Settings",
)

cpacs_inout.add_input(
    var_name="training_datasets",
    var_type=list,
    default_value=None,
    unit=None,
    descr="Select, in the RIGHT ORDER, training datasets from the aeromaps",
    xpath=SMTRAIN_XPATH + "/aeromapForTraining",
    gui=include_gui,
    gui_name="__AEROMAP_CHECKBOX",
    gui_group="Training Dataset",
)


cpacs_inout.add_input(
    var_name="trainig_part",
    var_type=float,
    default_value="0.7",
    descr="Defining the percentage of the data to use to train the model in [0;1]",
    xpath=SMTRAIN_XPATH + "/trainingPercentage",  # decidere anche divisione test e validation?
    gui=include_gui,
    gui_name="% of training data",
    gui_group="Global Settings",
)

cpacs_inout.add_input(
    var_name="objective",
    var_type=str,
    default_value="cl",
    unit="-",
    descr="""Objective function list for the surrogate model to predict \n Warning !
    The parameter name must match the ones in the aeromap: cl, cd, cs, cmd, cml, cms """,
    xpath=SMTRAIN_XPATH + "/objective",
    gui=include_gui,
    gui_name="Objective",
    gui_group="Global Settings",
)

cpacs_inout.add_input(
    var_name="show_validation_plot",
    var_type=bool,
    default_value=True,
    unit=None,
    descr="Choose if the validation plot must be shown or not",
    xpath=SMTRAIN_XPATH + "/ValidationPlot",
    gui=include_gui,
    gui_name="Validation plot",
    gui_group="Global Settings",
)

cpacs_inout.add_input(
    var_name="new_dataset",
    var_type=bool,
    default_value=True,
    unit=None,
    descr="""Choose if you want a new suggested dataset to improve the multy-fidelity
    surrogate model""",
    xpath=SMTRAIN_XPATH + "/newDataset",
    gui=include_gui,
    gui_name="New Dataset",
    gui_group="New Suggested Dataset",
)

cpacs_inout.add_input(
    var_name="fraction_of_new_samples",
    var_type=int,
    default_value=2,
    unit=None,
    descr="Choose the fraction of new samples for the new dataset",
    xpath=SMTRAIN_XPATH + "/newDatasetFraction",
    gui=include_gui,
    gui_name="Fraction of new samples",
    gui_group="New Suggested Dataset",
)

cpacs_inout.add_input(
    var_name="designOfExperiments",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="""Choose if you want to start a Design of Experiments with the Latin 
    Hypercube Sampling""",
    xpath=SMTRAIN_DOE + "/newDoe",
    gui=include_gui,
    gui_name="Design of Experiments",
    gui_group="Domain settings",
)

cpacs_inout.add_input(
    var_name="fidelity_level_doe",
    var_type=list,
    default_value=["One level", "Two level"],
    unit=None,
    descr="""Select if you want to train a simple Kriging (1 level of fidelity) or you want to
    train a Multi-Fidelity Kriging with adaprive sampling""",
    xpath=SMTRAIN_DOE + "/fidelityLevel",
    gui=True,
    gui_name="Choice of fidelity level",
    gui_group="Domain settings",
)


cpacs_inout.add_input(
    var_name="useAVL",
    var_type=bool,
    default_value=True,
    unit=None,
    descr="""Choose if you want to use AVL for low fidelity simulation""",
    xpath=SMTRAIN_DOE + "/AVL",
    gui=include_gui,
    gui_name="Use of AVL for low fidelity simulations",
    gui_group="Domain settings",
)

cpacs_inout.add_input(
    var_name="useSU2",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="""Choose if you want to use SU2 for high fidelity simulations""",
    xpath=SMTRAIN_DOE + "/SU2",
    gui=include_gui,
    gui_name="Use of SU2 for high fidelity simulations",
    gui_group="Domain settings",
)

cpacs_inout.add_input(
    var_name="rmse_objective",
    var_type=float,
    default_value=0.05,
    unit=None,
    descr="Selects the model's RMSE threshold value for Bayesian optimisation",
    xpath=SMTRAIN_DOE + "/rmseThreshold",
    gui=include_gui,
    gui_name="RMSE Threshold",
    gui_group="Domain settings",
)


cpacs_inout.add_input(
    var_name="number_of_samples",
    var_type=int,
    default_value=100,  # devono essere 2 o piu!!
    unit=None,
    descr="Choose the number of samples",
    xpath=SMTRAIN_DOE + "/nSamples",
    gui=include_gui,
    gui_name="Number of samples",
    gui_group="Domain settings",
)


cpacs_inout.add_input(
    var_name="dataset_for_doe",
    var_type=list,
    default_value=None,
    unit=None,
    descr="Select the aeromap with ranges for the Design of Experiments",
    xpath=SMTRAIN_XPATH + "/aeromapForDoe",
    gui=include_gui,
    gui_name="__AEROMAP_CHECKBOX",
    gui_group="Dataset with ranges",
)


# cpacs_inout.add_input(
#     var_name="altitude_low_limit",
#     var_type=float,
#     default_value=0,
#     unit=None,
#     descr="Insert the altitude low limit",
#     xpath=SMTRAIN_DOE + "/altitudeLowLimit",
#     gui=include_gui,
#     gui_name="Altitude Low Limit",
#     gui_group="Domain settings",
# )

# cpacs_inout.add_input(
#     var_name="altitude_high_limit",
#     var_type=float,
#     default_value=0,
#     unit=None,
#     descr="Insert the altitude high limit",
#     xpath=SMTRAIN_DOE + "/altitudeHighLimit",
#     gui=include_gui,
#     gui_name="Altitude High Limit",
#     gui_group="Domain settings",
# )

# cpacs_inout.add_input(
#     var_name="mach_low_limit",
#     var_type=float,
#     default_value=0,
#     unit=None,
#     descr="Insert the mach low limit",
#     xpath=SMTRAIN_DOE + "/machLowLimit",
#     gui=include_gui,
#     gui_name="Mach Low Limit",
#     gui_group="Domain settings",
# )

# cpacs_inout.add_input(
#     var_name="mach_high_limit",
#     var_type=float,
#     default_value=0,
#     unit=None,
#     descr="Insert the mach high limit",
#     xpath=SMTRAIN_DOE + "/machHighLimit",
#     gui=include_gui,
#     gui_name="Mach High Limit",
#     gui_group="Domain settings",
# )

# cpacs_inout.add_input(
#     var_name="aoa_low_limit",
#     var_type=float,
#     default_value=0,
#     unit=None,
#     descr="Insert the AOA low limit",
#     xpath=SMTRAIN_DOE + "/aoaLowLimit",
#     gui=include_gui,
#     gui_name="AOA Low Limit",
#     gui_group="Domain settings",
# )

# cpacs_inout.add_input(
#     var_name="aoa_high_limit",
#     var_type=float,
#     default_value=0,
#     unit=None,
#     descr="Insert the AOA high limit",
#     xpath=SMTRAIN_DOE + "/aoaHighLimit",
#     gui=include_gui,
#     gui_name="AOA High Limit",
#     gui_group="Domain settings",
# )

# cpacs_inout.add_input(
#     var_name="aos_low_limit",
#     var_type=float,
#     default_value=0,
#     unit=None,
#     descr="Insert the AOS low limit",
#     xpath=SMTRAIN_DOE + "/aosLowLimit",
#     gui=include_gui,
#     gui_name="AOS Low Limit",
#     gui_group="Domain settings",
# )

# cpacs_inout.add_input(
#     var_name="aos_high_limit",
#     var_type=float,
#     default_value=0,
#     unit=None,
#     descr="Insert the AOS high limit",
#     xpath=SMTRAIN_DOE + "/aosHighLimit",
#     gui=include_gui,
#     gui_name="AOS High Limit",
#     gui_group="Domain settings",
# )


# DOE LIMITS???


# print(cpacs_inout.inputs[1])


# for entry in cpacs_inout.inputs:
#     print(f"Variable Name: {entry.var_name}, Default Value: {entry.default_value}")


# bayesian or random seach?


# ----- Output ----

cpacs_inout.add_output(
    var_name="output",
    default_value=None,
    unit="1",
    descr="Description of the output",
    xpath=CEASIOMPY_XPATH + "/test/myOutput",
)

cpacs_inout.add_output(
    var_name="surrogateModel",
    default_value=None,
    unit="1",
    descr="path of the trained surrogate model",
    xpath=SMTRAIN_XPATH + "/surrogateModelPath",
)
