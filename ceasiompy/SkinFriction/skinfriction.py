"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Calculate skin friction drag coefficent

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2019-06-13
| Last modifiction: 2019-08-12
"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import math

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.standardatmosphere import get_atmosphere
from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi, \
                                     get_value, get_value_or_default,  \
                                     create_branch


from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements
from ceasiompy.SkinFriction.__specs__ import cpacs_inout


log = get_logger(__file__.split('.')[0])


#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def get_largest_wing_dim(tixi,tigl):
    """ Get Wing Area and Span of the largest wing present in the cpacs file.

    Function 'get_largest_wing_dim' look at all wings in the CPACS file and
    return the wing area and the wing span of the largest.

    Source:
        * TIXI functions : http://tixi.sourceforge.net/Doc/
        * TIGL functions : http://tigl.sourceforge.net/Doc/

    Args:
        tixi (handles):  TIXI Handle
        tigl (handles): TIGL Handle

    Returns:
        wing_area_max (float): Max Wing Area [m^2]
        wing_span_max (float): Max Wing Span [m]
    """

    wings_xpath = '/cpacs/vehicles/aircraft/model/wings'

    # Get Number of wings
    if tixi.checkElement(wings_xpath):
        wing_count = tixi.getNamedChildrenCount(wings_xpath, 'wing')
        log.info(str(wing_count) + ' wing has been found : ')
    else:
        wing_count = 0
        log.warning('No wing found in this CPACS file!')

    wing_span_max = 0
    wing_area_max = 0
    for i_wing in range(wing_count):
        wing_xpath = wings_xpath + '/wing[' + str(i_wing+1) + ']'
        wing_uid = tixi.getTextAttribute(wing_xpath,'uID')
        log.info("  -" + str(wing_uid))

        # *2 to take the symetry into account
        wing_area = tigl.wingGetReferenceArea(i_wing+1,1) * 2

        # Get value from the largest wing (larger span)
        if wing_area > wing_area_max:
            wing_area_max = wing_area
            wing_span = tigl.wingGetSpan(wing_uid)
            wing_span_max = wing_span

    log.info("Largest wing area [m^2]= " + str(wing_area_max))
    log.info("Largest wing span [m]= " + str(wing_span_max))

    return wing_area_max, wing_span_max



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
    log.error(alt)
    # Get atmosphere values at this altitude
    Atm = get_atmosphere(alt)

    kinetic_visc = Atm.visc/Atm.dens

    # Get speed from Mach Number
    speed = mach * Atm.sos

    # Reynolds number based on the ratio Wetted Area / Wing Span
    reynolds_number = (wetted_area/wing_span) * speed / kinetic_visc
    log.info('Reynolds number:' + str(round(reynolds_number)))

    # Skin friction coefficient, formula from source (see function description)
    cfe = 0.00258 + 0.00102 * math.exp(-6.28*1e-9*reynolds_number) \
          + 0.00295 * math.exp(-2.01*1e-8*reynolds_number)
    log.info('Skin friction coefficient:' + str(round(cfe,5)))

    # Drag coefficient due to skin friction
    cd0 = cfe * wetted_area / wing_area
    log.info("Skin friction drag coef: " + str(cd0))

    return cd0


def add_skin_friction(cpacs_path,cpacs_out_path):
    """ Function to add the skin frinction drag coeffienct to the CPACS file

    Function 'add_skin_friction' add the skin friction drag 'cd0' to the CPACS
    file, then it could be added to the drag coeffienct obtain with Euler
    calcualtions or other methods

    Args:
        cpacs_path (str):  Path to CPACS file
        cpacs_out_path (str): Path to CPACS output file
    """

    tixi = open_tixi(cpacs_path)
    tigl = open_tigl(tixi)

    wing_area_max, wing_span_max = get_largest_wing_dim(tixi,tigl)

    analysis_xpath = '/cpacs/toolspecific/CEASIOMpy/geometry/analysis'
    range_xpath = '/cpacs/toolspecific/CEASIOMpy/ranges'

    # Requiered input data from CPACS
    wetted_area = get_value(tixi,analysis_xpath + '/wettedArea')

    # Not requiered input data (a default value will be used if no
    # value has been found in the CPACS file)
    wing_area_xpath = analysis_xpath + '/wingArea'
    tixi, wing_area = get_value_or_default(tixi,wing_area_xpath, wing_area_max)
    if wing_area != wing_area_max:
        log.warning('Wing area found in the CPACS file /toolspecific is \
                     different from the one calculated from geometry, \
                     /toolspecific value will be used')

    wing_span_xpath = analysis_xpath + '/wingSpan'
    tixi, wing_span = get_value_or_default(tixi,wing_span_xpath, wing_span_max)
    if wing_span != wing_span_max:
       log.warning('Wing span found in the CPACS file /toolspecific is \
                    different from the one calculated from geometry, \
                    /toolspecific value will be used')

    cruise_alt_xpath = range_xpath + '/cruiseAltitude'
    tixi, cruise_alt = get_value_or_default(tixi,cruise_alt_xpath,12000)

    cruise_mach_xpath = range_xpath + '/cruiseMach'
    tixi, cruise_mach = get_value_or_default(tixi,cruise_mach_xpath,0.78)

    # Calculate Cd0
    cd0 = estimate_skin_friction_coef(wetted_area,wing_area,wing_span, \
                                      cruise_mach,cruise_alt)

    # Save Cd0 in the CPACS file
    cd0_xpath = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/skinFriction/cd0'
    tixi = create_branch(tixi, cd0_xpath)
    tixi.updateDoubleElement(cd0_xpath,cd0,'%g')
    log.info('Skin friction drag coeffienct (cd0) has been saved in the \
              CPACS file')

    close_tixi(tixi,cpacs_out_path)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = MODULE_DIR + '/ToolInput/ToolInput.xml'
    cpacs_out_path = MODULE_DIR + '/ToolOutput/ToolOutput.xml'

    check_cpacs_input_requirements(cpacs_path, cpacs_inout, __file__)

    add_skin_friction(cpacs_path,cpacs_out_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
