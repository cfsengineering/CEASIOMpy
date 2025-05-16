from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import log

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
MODULE_STATUS = False

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

INCLUDE_GUI = False

# ----- Input -----

# TODO

# * In the following example we add three (!) new entries to 'cpacs_inout'
# * Try to use (readable) loops instead of copy-pasting three almost same entries :)
# for direction in ['x', 'y', 'z']:
#     cpacs_inout.add_input(
#         var_name=direction,
#         var_type=float,
#         default_value=None,
#         unit='1',
#         descr=f"Fuselage scaling on {direction} axis",
#         xpath=AIRCRAFT_XPATH + f'/model/fuselages/fuselage/transformation/scaling/{direction}',
#         gui=INCLUDE_GUI,
#         gui_name=f'{direction.capitalize()} scaling',
#         gui_group='Fuselage scaling',
#     )
#
# cpacs_inout.add_input(
#     var_name='test',
#     var_type=str,
#     default_value='This is a test',
#     unit=None,
#     descr='This is a test of description',
#     xpath='/cpacs/toolspecific/CEASIOMpy/test/myTest',
#     gui=INCLUDE_GUI,
#     gui_name='My test',
#     gui_group='Group Test',
# )
#
# cpacs_inout.add_input(
#     var_name='aeromap_uid',
#     var_type=list,
#     default_value=None,
#     xpath='/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/aeroMapUID',
#     gui=INCLUDE_GUI,
#     gui_name='__AEROMAP_SELECTION',
# )
#
# cpacs_inout.add_input(
#     var_name='aeromap_uid',
#     var_type=list,
#     default_value=None,
#     xpath='/cpacs/toolspecific/CEASIOMpy/aerodynamics/skinFriction/aeroMapToCalculate',
#     gui=INCLUDE_GUI,
#     gui_name='__AEROMAP_CHECKBOX',
# )
#
# cpacs_inout.add_input(
#     var_name='other_var',
#     var_type=list,
#     default_value= [2,33,444],
#     unit='[unit]',
#     xpath='/cpacs/toolspecific/CEASIOMpy/test/myList',
#     gui=INCLUDE_GUI,
#     gui_name='Choice',
#     gui_group='My Selection'
# )
#
# # ----- Output -----
#
# cpacs_inout.add_output(
#     var_name='output',
#     default_value=None,
#     unit='1',
#     descr='Description of the output',
#     xpath='/cpacs/toolspecific/CEASIOMpy/test/myOutput',
# )

# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
