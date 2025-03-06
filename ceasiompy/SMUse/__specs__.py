from pathlib import Path
from ceasiompy.utils.commonxpath import MFSMUSE_XPATH, MFSMUSE_RS
from ceasiompy.utils.moduleinterfaces import CPACSInOut

# from ceasiompy.utils.commonxpath import MFSMTRAIN_XPATH

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = True

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "MFSMUse")

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

include_gui = True

# ----- Input -----


cpacs_inout.add_input(
    var_name="model_file",
    var_type="pathtype",
    default_value="-",
    descr="File that contains a trained model",
    xpath=MFSMUSE_XPATH + "/modelFile",
    gui=include_gui,
    gui_name="Model to use",
    gui_group="Prediction options",
)

cpacs_inout.add_input(
    var_name="prediction_dataset",
    var_type="pathtype",
    default_value="-",
    descr="CSV file with inputs to be predicted",
    xpath=MFSMUSE_XPATH + "/predictionDataset",
    gui=include_gui,
    gui_name="Prediction Dataset",
    gui_group="Use options",
)


# DOE LIMITS???


# print(cpacs_inout.inputs[1])


# for entry in cpacs_inout.inputs:
#     print(f"Variable Name: {entry.var_name}, Default Value: {entry.default_value}")


# bayesian or random seach?


# ----- Output ----

# cpacs_inout.add_output(
#     var_name="output",
#     default_value=None,
#     unit="1",
#     descr="Description of the output",
#     xpath=CEASIOMPY_XPATH + "/test/myOutput",
# )

# cpacs_inout.add_output(
#     var_name="surrogateModel",
#     default_value=None,
#     unit="1",
#     descr="path of the trained surrogate model",
#     xpath=MFSMTRAIN_XPATH + "/surrogateModelPath",
# )
