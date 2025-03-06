from pathlib import Path
from ceasiompy.utils.commonxpath import (
    MFSMTRAIN_XPATH,
    MFSMTRAIN_DOE,
    MFSMTRAIN_NEWDATA,
    MFSMTRAIN_RS,
    CEASIOMPY_XPATH,
)
from ceasiompy.utils.moduleinterfaces import CPACSInOut

# from ceasiompy.utils.commonxpath import MFSMTRAIN_XPATH

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = True

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "MFSMTrain")

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

include_gui = True

# ----- Input -----


cpacs_inout.add_input(
    var_name="fidelity_levels",
    var_type=int,
    default_value="1",
    descr="Defining the number of fidelity level used to train the surrogate model",
    xpath=MFSMTRAIN_XPATH + "/fidelityLevel",
    gui=include_gui,
    gui_name="Number of fidelity level",
    gui_group="Global Settings",
)


cpacs_inout.add_input(
    var_name="training_dataset1",
    var_type="pathtype",
    default_value="-",
    descr="CSV file to be used to train a model",
    xpath=MFSMTRAIN_XPATH + "/csvPath1",
    gui=include_gui,
    gui_name="First training dataset",
    gui_group="Training Options",
)

cpacs_inout.add_input(
    var_name="training_dataset2",
    var_type="pathtype",
    default_value="-",
    descr="CSV file to be used to train a model",
    xpath=MFSMTRAIN_XPATH + "/csvPath2",
    gui=include_gui,
    gui_name="Second Training dataset",
    gui_group="Training Options",
)

cpacs_inout.add_input(
    var_name="training_dataset3",
    var_type="pathtype",
    default_value="-",
    descr="CSV file to be used to train a model",
    xpath=MFSMTRAIN_XPATH + "/csvPath3",
    gui=include_gui,
    gui_name="Third Training dataset",
    gui_group="Training Options",
)

cpacs_inout.add_input(
    var_name="trainig_part",
    var_type=float,
    default_value="0.7",
    descr="Defining the percentage of the data to use to train the model in [0;1]",
    xpath=MFSMTRAIN_XPATH + "/trainingPercentage",  # decidere anche divisione test e validation?
    gui=include_gui,
    gui_name="% of training data",
    gui_group="Global Settings",
)

cpacs_inout.add_input(
    var_name="objectives",
    var_type=str,
    default_value="Total CL",
    unit="-",
    descr="""Objective function list for the surrogate model to predict \n Warning !
    The parameter name must match the ones in the CSV file !""",
    xpath=MFSMTRAIN_XPATH + "/objective",
    gui=include_gui,
    gui_name="Objective",
    gui_group="Global Settings",
)

cpacs_inout.add_input(
    var_name="show_validation_plot",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Choose if the validation plot must be shown or not",
    xpath=MFSMTRAIN_XPATH + "/ValidationPlot",
    gui=include_gui,
    gui_name="Validation plot",
    gui_group="Global Settings",
)

# cpacs_inout.add_input(
#     var_name="response_surface",
#     var_type=bool,
#     default_value=False,
#     unit=None,
#     descr="Choose if the response surface must be shown or not",
#     xpath=MFSMTRAIN_RS + "/Plot",
#     gui=include_gui,
#     gui_name="Response Surface",
#     gui_group="Response Surface",
# )

# cpacs_inout.add_input(
#     var_name="x_rSurf",
#     var_type=str,
#     default_value="angleOfAttack",
#     descr="""Variable on X axe of Response Surface  \n Warning !
#     The parameter name must match the ones in the CSV file !""",
#     xpath=MFSMTRAIN_RS + "/VariableOnX",
#     gui=include_gui,
#     gui_name="Variable on X ",
#     gui_group="Response Surface",
# )

# cpacs_inout.add_input(
#     var_name="x_rSurf_low_limit",
#     var_type=float,
#     default_value="0.0",
#     descr="Low limit of the Variable on X axe of Response Surface",
#     xpath=MFSMTRAIN_RS + "/VariableOnX/LowLimit",
#     gui=include_gui,
#     gui_name="Low limit of the Variable on X ",
#     gui_group="Response Surface",
# )

# cpacs_inout.add_input(
#     var_name="x_rSurf_high_limit",
#     var_type=float,
#     default_value="0.0",
#     descr="High limit of the Variable on X axe of Response Surface",
#     xpath=MFSMTRAIN_RS + "/VariableOnX/HighLimit",
#     gui=include_gui,
#     gui_name="High limit of the Variable on X ",
#     gui_group="Response Surface",
# )

# cpacs_inout.add_input(
#     var_name="y_rSurf",
#     var_type=str,
#     default_value="machNumber",
#     descr="""Variable on Y axe of Response Surface \n Warning !
#     The parameter name must match the ones in the CSV file !""",
#     xpath=MFSMTRAIN_RS + "/VariableOnY",
#     gui=include_gui,
#     gui_name="Variable on Y",
#     gui_group="Response Surface",
# )

# cpacs_inout.add_input(
#     var_name="y_rSurf_low_limit",
#     var_type=float,
#     default_value="0.0",
#     descr="Low limit of the Variable on Y axe of Response Surface",
#     xpath=MFSMTRAIN_RS + "/VariableOnY/LowLimit",
#     gui=include_gui,
#     gui_name="Low limit of the Variable on Y ",
#     gui_group="Response Surface",
# )

# cpacs_inout.add_input(
#     var_name="y_rSurf_high_limit",
#     var_type=float,
#     default_value="0.0",
#     descr="High limit of the Variable on Y axe of Response Surface",
#     xpath=MFSMTRAIN_RS + "/VariableOnY/HighLimit",
#     gui=include_gui,
#     gui_name="High limit of the Variable on Y",
#     gui_group="Response Surface",
# )

# cpacs_inout.add_input(
#     var_name="first_constant_variable",
#     var_type=str,
#     default_value="altitude",
#     descr=""" Firts Variable to mantain constant while the response surface is plotted \n Warning !
#     The parameter name must match the ones in the CSV file !""",
#     xpath=MFSMTRAIN_RS + "/FirstConstantVariable",
#     gui=include_gui,
#     gui_name="First Constant Variable",
#     gui_group="Response Surface",
# )

# cpacs_inout.add_input(
#     var_name="val_of_first_constant_variable",
#     var_type=float,
#     default_value="1000",
#     descr="Value of the First Variable to mantain constant while the response surface is plotted",
#     xpath=MFSMTRAIN_RS + "/FirstConstantVariable/value",
#     gui=include_gui,
#     gui_name="Value of First Constant Variable",
#     gui_group="Response Surface",
# )

# cpacs_inout.add_input(
#     var_name="second_constant_variable",
#     var_type=str,
#     default_value="angleOfSideslip",
#     descr=""" Second Variable to mantain constant while the response surface is plotted \n Warning !
#     The parameter name must match the ones in the CSV file !""",
#     xpath=MFSMTRAIN_RS + "/SecondConstantVariable",
#     gui=include_gui,
#     gui_name="Second Constant Variable",
#     gui_group="Response Surface",
# )

# cpacs_inout.add_input(
#     var_name="val_of_second_constant_variable",
#     var_type=float,
#     default_value="0",
#     descr="Value of the Second Variable to mantain constant while the response surface is plotted",
#     xpath=MFSMTRAIN_RS + "/SecondConstantVariable/value",
#     gui=include_gui,
#     gui_name="Value of Second Constant Variable",
#     gui_group="Response Surface",
# )

# cpacs_inout.add_input(
#     var_name="new_dataset",
#     var_type=bool,
#     default_value=False,
#     unit=None,
#     descr="Choose if you want a new suggested dataset to improve the multy-fidelity surrogate model",
#     xpath=MFSMTRAIN_NEWDATA,
#     gui=include_gui,
#     gui_name="New Dataset",
#     gui_group="New Suggested Dataset",
# )

cpacs_inout.add_input(
    var_name="fraction_of_new_samples",
    var_type=int,
    default_value=2,
    unit=None,
    descr="Choose the fraction of new samples for the new dataset",
    xpath=MFSMTRAIN_NEWDATA + "/newSamples",
    gui=include_gui,
    gui_name="Fraction of new samples",
    gui_group="New Suggested Dataset",
)


cpacs_inout.add_input(
    var_name="number_of_samples",
    var_type=int,
    default_value=100,  # devono essere 2 o piu!!
    unit=None,
    descr="Choose the number of samples",
    xpath=MFSMTRAIN_DOE + "/nSamples",
    gui=include_gui,
    gui_name="Number of samples",
    gui_group="Domain settings",
)

# cpacs_inout.add_input(
#     var_name="altitude_low_limit",
#     var_type=float,
#     default_value=0,
#     unit=None,
#     descr="Insert the altitude low limit",
#     xpath=MFSMTRAIN_DOE + "/altitudeLowLimit",
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
#     xpath=MFSMTRAIN_DOE + "/altitudeHighLimit",
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
#     xpath=MFSMTRAIN_DOE + "/machLowLimit",
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
#     xpath=MFSMTRAIN_DOE + "/machHighLimit",
#     gui=include_gui,
#     gui_name="Mach High Limit",
#     gui_group="Domain settings",
# )

# cpacs_inout.add_input(
#     var_name="aoa_low_limit",
#     var_type=int,
#     default_value=0,
#     unit=None,
#     descr="Insert the AOA low limit",
#     xpath=MFSMTRAIN_DOE + "/aoaLowLimit",
#     gui=include_gui,
#     gui_name="AOA Low Limit",
#     gui_group="Domain settings",
# )

# cpacs_inout.add_input(
#     var_name="aoa_high_limit",
#     var_type=int,
#     default_value=0,
#     unit=None,
#     descr="Insert the AOA high limit",
#     xpath=MFSMTRAIN_DOE + "/aoaHighLimit",
#     gui=include_gui,
#     gui_name="AOA High Limit",
#     gui_group="Domain settings",
# )

# cpacs_inout.add_input(
#     var_name="aos_low_limit",
#     var_type=int,
#     default_value=0,
#     unit=None,
#     descr="Insert the AOS low limit",
#     xpath=MFSMTRAIN_DOE + "/aosLowLimit",
#     gui=include_gui,
#     gui_name="AOS Low Limit",
#     gui_group="Domain settings",
# )

# cpacs_inout.add_input(
#     var_name="aos_high_limit",
#     var_type=int,
#     default_value=0,
#     unit=None,
#     descr="Insert the AOS high limit",
#     xpath=MFSMTRAIN_DOE + "/aosHighLimit",
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
    xpath=MFSMTRAIN_XPATH + "/surrogateModelPath",
)
