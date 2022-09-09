from ceasiompy.utils.moduleinterfaces import CPACSInOut
from ceasiompy.utils.commonxpath import GEOM_XPATH, RANGE_XPATH, SF_XPATH, PLOT_XPATH


cpacs_inout = CPACSInOut()

# ===== Input =====

cpacs_inout.add_input(
    var_name="",
    var_type=list,
    default_value=None,
    descr="To which aeroMap the skin friction coef should be added",
    xpath=SF_XPATH + "/aeroMapToCalculate",
    gui=True,
    gui_name="__AEROMAP_CHECHBOX",
    gui_group="Aeromap settings",
)

cpacs_inout.add_input(
    var_name="wetted_area",
    var_type=float,
    default_value=None,
    unit="m^2",
    descr="Wetted area of the aircraft (calculated by SU2)",
    xpath=GEOM_XPATH + "/analysis/wettedArea",
    gui=False,
    gui_name="Wetted Area",
    gui_group=None,
)

cpacs_inout.add_input(
    var_name="",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Delete original aeroMap once skin friction coefficient has been added",
    xpath=SF_XPATH + "/deleteOriginal",
    gui=True,
    gui_name="Delete Original",
    gui_group=None,
)

cpacs_inout.add_input(
    var_name="cruise_mach",
    default_value=0.78,
    unit="-",
    descr="Aircraft cruise Mach number",
    xpath=RANGE_XPATH + "/cruiseMach",
)

cpacs_inout.add_input(
    var_name="cruise_alt",
    default_value=12000,
    unit="m",
    descr="Aircraft cruise altitude",
    xpath=RANGE_XPATH + "/cruiseAltitude",
)

# ===== Output =====

cpacs_inout.add_output(
    var_name="cd0",
    default_value=None,
    unit="1",
    descr="Skin friction drag coefficient",
    xpath=SF_XPATH + "/cd0",
)

cpacs_inout.add_output(
    var_name="main_wing_area",
    default_value=None,
    unit="m^2",
    descr="Wing area of the main (largest) wing",
    xpath=GEOM_XPATH + "/analyses/wingArea",
)

cpacs_inout.add_output(
    var_name="main_wing_span",
    default_value=None,
    unit="m",
    descr="Wing span of the main (largest) wing",
    xpath=GEOM_XPATH + "/analyses/wingSpan",
)

cpacs_inout.add_output(
    var_name="new_aeromap_to_plot",
    default_value=None,
    unit="m",
    descr="List of aeroMap to plot",
    xpath=PLOT_XPATH + "/aeroMapToPlot",
)
