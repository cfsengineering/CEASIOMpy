"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of SaveAeroCoefficients.

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy.SaveAeroCoefficients import (
    INCLUDE_GUI,
    AEROMAP_FEATURES,
)

from ceasiompy.utils.commonxpaths import (
    RS_XPATH,
    PLOT_XPATH,
    AEROMAP_TO_PLOT_XPATH,
)

# ==============================================================================
#   VARIABLE
# ==============================================================================

cpacs_inout = CPACSInOut()

# ==============================================================================
#   GUI INPUTS
# ==============================================================================

cpacs_inout.add_input(
    var_name="",
    var_type=list,
    default_value=None,
    descr="List of aeroMap to plot",
    xpath=AEROMAP_TO_PLOT_XPATH,
    gui=INCLUDE_GUI,
    gui_name="__AEROMAP_CHECKBOX",
    gui_group="Aeromap settings",
)

cpacs_inout.add_input(
    var_name="alt_crit",
    var_type=str,
    default_value="None",
    descr="Altitude inclusion criteria",
    xpath=PLOT_XPATH + "/criterion/alt",
    gui=INCLUDE_GUI,
    gui_name="Altitude criteria",
    gui_group="Plot vs AoA",
)

cpacs_inout.add_input(
    var_name="mach_crit",
    var_type=str,
    default_value="None",
    descr="Mach inclusion criteria",
    xpath=PLOT_XPATH + "/criterion/mach",
    gui=INCLUDE_GUI,
    gui_name="Mach criteria",
    gui_group="Plot vs AoA",
)

cpacs_inout.add_input(
    var_name="aos_crit",
    var_type=str,
    default_value="None",
    descr="Angle of Sideslip (AoS) inclusion criteria",
    xpath=PLOT_XPATH + "/criterion/aos",
    gui=INCLUDE_GUI,
    gui_name="AoS criteria",
    gui_group="Plot vs AoA",
)

cpacs_inout.add_input(
    var_name="response_surface",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Choose if the response surface must be shown or not",
    xpath=RS_XPATH + "/Plot",
    gui=INCLUDE_GUI,
    gui_name="Response Surface",
    gui_group="Response Surface",
)

cpacs_inout.add_input(
    var_name="x_rSurf",
    var_type=list,
    default_value=["angleOfAttack", "altitude", "machNumber", "angleOfSideslip"],
    descr="""Variable on X axe of Response Surface  \n Warning !
    The parameter name must match the ones in the CSV file !""",
    xpath=RS_XPATH + "/VariableOnX/Variable",
    gui=INCLUDE_GUI,
    gui_name="Variable on X ",
    gui_group="Response Surface",
)

cpacs_inout.add_input(
    var_name="x_rSurf_low_limit",
    var_type=float,
    default_value=0.0,
    descr="Low limit of the Variable on X axe of Response Surface",
    xpath=RS_XPATH + "/VariableOnX/LowLimit",
    gui=INCLUDE_GUI,
    gui_name="Low limit of the Variable on X ",
    gui_group="Response Surface",
)

cpacs_inout.add_input(
    var_name="x_rSurf_high_limit",
    var_type=float,
    default_value=0.0,
    descr="High limit of the Variable on X axe of Response Surface",
    xpath=RS_XPATH + "/VariableOnX/HighLimit",
    gui=INCLUDE_GUI,
    gui_name="High limit of the Variable on X ",
    gui_group="Response Surface",
)

cpacs_inout.add_input(
    var_name="y_rSurf",
    var_type=list,
    default_value=["machNumber", "altitude", "angleOfAttack", "angleOfSideslip"],
    descr="""Variable on Y axe of Response Surface \n Warning !
    The parameter name must match the ones in the CSV file !""",
    xpath=RS_XPATH + "/VariableOnY/Variable",
    gui=INCLUDE_GUI,
    gui_name="Variable on Y",
    gui_group="Response Surface",
)

cpacs_inout.add_input(
    var_name="y_rSurf_low_limit",
    var_type=float,
    default_value=0.0,
    descr="Low limit of the Variable on Y axe of Response Surface",
    xpath=RS_XPATH + "/VariableOnY/LowLimit",
    gui=INCLUDE_GUI,
    gui_name="Low limit of the Variable on Y ",
    gui_group="Response Surface",
)

cpacs_inout.add_input(
    var_name="y_rSurf_high_limit",
    var_type=float,
    default_value=0.0,
    descr="High limit of the Variable on Y axe of Response Surface",
    xpath=RS_XPATH + "/VariableOnY/HighLimit",
    gui=INCLUDE_GUI,
    gui_name="High limit of the Variable on Y",
    gui_group="Response Surface",
)

cpacs_inout.add_input(
    var_name="first_constant_variable",
    var_type=list,
    default_value=AEROMAP_FEATURES,
    descr="""Firts Variable to mantain constant while the response surface is plotted
    \n Warning ! The parameter name must match the ones in the CSV file !""",
    xpath=RS_XPATH + "/FirstConstantVariable",
    gui=INCLUDE_GUI,
    gui_name="First Constant Variable",
    gui_group="Response Surface",
)

cpacs_inout.add_input(
    var_name="val_of_first_constant_variable",
    var_type=float,
    default_value=10000,
    descr="Value of the First Variable to mantain constant while the response surface is plotted",
    xpath=RS_XPATH + "/FirstConstantVariableValue",
    gui=INCLUDE_GUI,
    gui_name="Value of First Constant Variable",
    gui_group="Response Surface",
)

cpacs_inout.add_input(
    var_name="second_constant_variable",
    var_type=list,
    default_value=["angleOfSideslip", "altitude", "machNumber", "angleOfAttack"],
    descr="""Second Variable to mantain constant while the response surface is plotted
    \n Warning! The parameter name must match the ones in the CSV file !""",
    xpath=RS_XPATH + "/SecondConstantVariable",
    gui=INCLUDE_GUI,
    gui_name="Second Constant Variable",
    gui_group="Response Surface",
)

cpacs_inout.add_input(
    var_name="val_of_second_constant_variable",
    var_type=float,
    default_value=0.0,
    descr="Value of the Second Variable to mantain constant while the response surface is plotted",
    xpath=RS_XPATH + "/SecondConstantVariableValue",
    gui=INCLUDE_GUI,
    gui_name="Value of Second Constant Variable",
    gui_group="Response Surface",
)

cpacs_inout.add_input(
    var_name="scatterPlots",
    var_type=list,
    default_value=None,
    descr="Select aeromaps for scatter points",
    xpath=PLOT_XPATH + "/aeroScatter",
    gui=INCLUDE_GUI,
    gui_name="__AEROMAP_CHECKBOX",
    gui_group="Aeromap list for scatter points",
)
