from ceasiompy.utils.moduleinterfaces import CPACSInOut
from ceasiompy.utils.commonxpath import CEASIOMPY_XPATH, FUSELAGES_XPATH

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = False  # Because it is just an example not a real module

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

include_gui = False

# ----- Input -----

# * In the following example we add three (!) new entries to 'cpacs_inout'
# * Try to use (readable) loops instead of copy-pasting three almost same entries :)
for direction in ["x", "y", "z"]:
    cpacs_inout.add_input(
        var_name=direction,
        var_type=float,
        default_value=None,
        unit="1",
        descr=f"Fuselage scaling on {direction} axis",
        xpath=FUSELAGES_XPATH + f"/fuselage/transformation/scaling/{direction}",
        gui=include_gui,
        gui_name=f"{direction.capitalize()} scaling",
        gui_group="Fuselage scaling",
    )

cpacs_inout.add_input(
    var_name="test",
    var_type=str,
    default_value="This is a test",
    unit=None,
    descr="This is a test of description",
    xpath=CEASIOMPY_XPATH + "/test/myTest",
    gui=include_gui,
    gui_name="My test",
    gui_group="Group Test",
)

cpacs_inout.add_input(
    var_name="other_var",
    var_type=list,
    default_value=[2, 33, 444],
    unit="[unit]",
    xpath=CEASIOMPY_XPATH + "/test/myList",
    gui=include_gui,
    gui_name="Choice",
    gui_group="My Selection",
)

# ----- Output -----

cpacs_inout.add_output(
    var_name="output",
    default_value=None,
    unit="1",
    descr="Description of the output",
    xpath=CEASIOMPY_XPATH + "/test/myOutput",
)
