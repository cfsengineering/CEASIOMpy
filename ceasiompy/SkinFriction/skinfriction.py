"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Calculate skin friction drag coefficent

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2019-06-13
| Last modifiction: 2021-10-08

TODO:

    * update __specs__ file
    * Redo test functions
    * (Check if projected value are realistic for different cases)

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import math
from cpacspy.aircraft import Aircraft

from cpacspy.cpacspy import CPACS
from cpacspy.cpacsfunctions import (add_string_vector, create_branch,
                                    get_string_vector, get_value,
                                    get_value_or_default)
import ceasiompy.utils.moduleinterfaces as mi

from ambiance import Atmosphere

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

WINGS_XPATH = '/cpacs/vehicles/aircraft/model/wings'
SF_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/skinFriction'


#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

# def get_largest_wing_dim(tixi,tigl):
#     """ Get Wing Area and Span of the largest wing present in the cpacs file.

#     Function 'get_largest_wing_dim' look at all wings in the CPACS file and
#     return the wing area and the wing span of the largest.

#     Source:
#         * TIXI functions : http://tixi.sourceforge.net/Doc/
#         * TIGL functions : http://tigl.sourceforge.net/Doc/

#     Args:
#         tixi (handles): TIXI Handle
#         tigl (handles): TIGL Handle

#     Returns:
#         wing_area_max (float): Max Wing Area [m^2]
#         wing_span_max (float): Max Wing Span [m]
#     """

#     # Get Number of wings
#     if tixi.checkElement(WINGS_XPATH):
#         wing_count = tixi.getNamedChildrenCount(WINGS_XPATH, 'wing')
#         log.info(str(wing_count) + ' wing has been found : ')
#     else:
#         wing_count = 0
#         log.warning('No wing found in this CPACS file!')

#     wing_span_max = 0
#     wing_area_max = 0
#     for i_wing in range(wing_count):
#         wing_xpath = WINGS_XPATH + '/wing[' + str(i_wing+1) + ']'
#         wing_uid = tixi.getTextAttribute(wing_xpath,'uID')
#         log.info("  -" + str(wing_uid))

#         # *2 to take the symetry into account
#         wing_area = tigl.wingGetReferenceArea(i_wing+1,1) * 2

#         # Get value from the largest wing (larger span)
#         if wing_area > wing_area_max:
#             wing_area_max = wing_area
#             wing_span = tigl.wingGetSpan(wing_uid)
#             wing_span_max = wing_span

#     log.info("Largest wing area [m^2]= " + str(wing_area_max))
#     log.info("Largest wing span [m]= " + str(wing_span_max))

#     return wing_area_max, wing_span_max


def estimate_skin_friction_coef(wetted_area,wing_area,wing_span,mach,alt):
    """ Return an estimation of skin friction drag coefficient.

    Function 'estimate_skin_friction_coef' gives an estimation of the skin
    friction drag coefficient, based on an empirical formala (see source).

    Source:
        * Gerard W. H. van Es.  "Rapid Estimation of the Zero-Lift Drag
          Coefficient of Transport Aircraft", Journal of Aircraft, Vol. 39,
          No. 4 (2002), pp. 597-599. https://doi.org/10.2514/2.2997

    Args:
        wetted_area (float):  Wetted Area of the entire aircraft [m^2]
        wing_area (float):  Main wing area [m^2]
        wing_span (float):  Main wing span [m]
        mach (float):  Cruise Mach number [-]
        alt (float):  Aircraft altitude [m]

    Returns:
        cd0 (float): Drag coefficient due to skin friction [-]
    """

    # Get atmosphere values at this altitude
    Atm = Atmosphere(alt)

    # Get speed from Mach Number
    speed = mach * Atm.speed_of_sound[0]

    # Reynolds number based on the ratio Wetted Area / Wing Span
    reynolds_number = (wetted_area/wing_span) * speed / Atm.kinematic_viscosity[0]
    log.info('Reynolds number:' + str(round(reynolds_number)))

    # Skin friction coefficient, formula from source (see function description)
    cfe = 0.00258 + 0.00102 * math.exp(-6.28*1e-9*reynolds_number) \
          + 0.00295 * math.exp(-2.01*1e-8*reynolds_number)
    log.info('Skin friction coefficient:' + str(round(cfe,5)))

    # Drag coefficient due to skin friction
    cd0 = cfe * wetted_area / wing_area
    log.info("Skin friction drag coefficient: " + str(cd0))

    return cd0


def add_skin_friction(cpacs_path,cpacs_out_path):
    """ Function to add the skin frinction drag coeffienct to aerodynamic coefficients

    Function 'add_skin_friction' add the skin friction drag 'cd0' to  the
    SU2 and pyTornado aeroMap, if their UID is not geven, it will add skin
    friction to all aeroMap. For each aeroMap it creates a new aeroMap where
    the skin friction drag coeffienct is added with the correct projcetions.

    Args:
        cpacs_path (str):  Path to CPACS file
        cpacs_out_path (str): Path to CPACS output file
    """

    # Load a CPACS file
    cpacs = CPACS(cpacs_path)

    analyses_xpath = '/cpacs/toolspecific/CEASIOMpy/geometry/analysis'

    # Requiered input data from CPACS
    wetted_area = get_value(cpacs.tixi,analyses_xpath + '/wettedArea')

    # Wing area/span, default values will be calated if no value found in the CPACS file
    wing_area_xpath = analyses_xpath + '/wingArea'
    wing_area = get_value_or_default(cpacs.tixi,wing_area_xpath, cpacs.aircraft.wing_area)
    wing_span_xpath = analyses_xpath + '/wingSpan'
    wing_span = get_value_or_default(cpacs.tixi,wing_span_xpath, cpacs.aircraft.wing_span)

    # Get aeroMapToCalculate
    aeroMap_to_clculate_xpath = SF_XPATH + '/aeroMapToCalculate'
    if cpacs.tixi.checkElement(aeroMap_to_clculate_xpath):
        aeromap_uid_list = get_string_vector(cpacs.tixi,aeroMap_to_clculate_xpath)
    else:
        aeromap_uid_list = []

    # If no aeroMap in aeroMapToCalculate, get all existing aeroMap
    if len(aeromap_uid_list) == 0:
        aeromap_uid_list = cpacs.get_aeromap_uid_list()

        if not aeromap_uid_list:
            raise ValueError('No aeroMap has been found in this CPACS file, skin friction cannot be added!')

    # Get unique aeroMap list
    aeromap_uid_list = list(set(aeromap_uid_list))
    new_aeromap_uid_list = []

    # Add skin friction to all listed aeroMap
    for aeromap_uid in aeromap_uid_list:

        log.info('adding skin friction coefficients to: ' + aeromap_uid)

        aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

        # Create new aeromap object to store coef with added skin friction
        aeromap_sf = cpacs.duplicate_aeromap(aeromap_uid,aeromap_uid+'_SkinFriction')
        aeromap_sf.description = aeromap_sf.description + ' Skin friction has been add to this AeroMap.'

        # Add skin friction to all force coeffiencent (with projections)
        aeromap_sf.df['cd'] = aeromap.df.apply(lambda row: row['cd']  \
                + estimate_skin_friction_coef(wetted_area,wing_area,wing_span,row['machNumber'],row['altitude']) \
                * math.cos(math.radians(row['angleOfAttack'])) * math.cos(math.radians(row['angleOfSideslip'])), axis=1)

        aeromap_sf.df['cl'] = aeromap.df.apply(lambda row: row['cl']  \
                + estimate_skin_friction_coef(wetted_area,wing_area,wing_span,row['machNumber'],row['altitude']) \
                * math.sin(math.radians(row['angleOfAttack'])), axis=1)

        aeromap_sf.df['cs'] = aeromap.df.apply(lambda row: row['cs']  \
                + estimate_skin_friction_coef(wetted_area,wing_area,wing_span,row['machNumber'],row['altitude']) \
                * math.sin(math.radians(row['angleOfSideslip'])), axis=1)

        # TODO: Shoud we change something in moment coef? e.i. if a force is not apply at aero center...?

        aeromap_sf.save()


    # Get aeroMap list to plot
    plot_xpath = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/plotAeroCoefficient'
    aeromap_to_plot_xpath = plot_xpath + '/aeroMapToPlot'

    if cpacs.tixi.checkElement(aeromap_to_plot_xpath):
        aeromap_uid_list = get_string_vector(cpacs.tixi,aeromap_to_plot_xpath)
        new_aeromap_to_plot = aeromap_uid_list + new_aeromap_uid_list
        new_aeromap_to_plot = list(set(new_aeromap_to_plot))
        add_string_vector(cpacs.tixi,aeromap_to_plot_xpath,new_aeromap_to_plot)
    else:
        create_branch(cpacs.tixi,aeromap_to_plot_xpath)
        add_string_vector(cpacs.tixi,aeromap_to_plot_xpath,new_aeromap_uid_list)

    log.info('AeroMap "' + aeromap_uid + '" has been added to the CPACS file')

    cpacs.save_cpacs(cpacs_out_path,overwrite=True)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','ToolInput.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')

    mi.check_cpacs_input_requirements(cpacs_path)

    add_skin_friction(cpacs_path,cpacs_out_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')


# Old function !!!
# TODO: Adapt the code deal with fixed CL mode case, then this function could be deleted completly

# def add_skin_friction(cpacs_path,cpacs_out_path):
#     cruise_alt_xpath = range_xpath + '/cruiseAltitude'
#     tixi, cruise_alt = get_value_or_default(tixi,cruise_alt_xpath,12000)
#
#     cruise_mach_xpath = range_xpath + '/cruiseMach'
#     tixi, cruise_mach = get_value_or_default(tixi,cruise_mach_xpath,0.78)
#
#     # Calculate Cd0
#     cd0 = estimate_skin_friction_coef(wetted_area,wing_area,wing_span, \
#                                       cruise_mach,cruise_alt)
#
#     # Save Cd0 in the CPACS file
#     cd0_xpath = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/skinFriction/cd0'
#     create_branch(tixi, cd0_xpath)
#     tixi.updateDoubleElement(cd0_xpath,cd0,'%g')
#     log.info('Skin friction drag coeffienct (cd0) has been saved in the \
#               CPACS file')
#
#     tixi.save(cpacs_out_path)
