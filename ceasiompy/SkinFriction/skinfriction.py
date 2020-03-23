"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Calculate skin friction drag coefficent

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2019-06-13
| Last modifiction: 2020-03-18

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

import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.utils.standardatmosphere import get_atmosphere

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

WINGS_XPATH = '/cpacs/vehicles/aircraft/model/wings'
SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

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
        tixi (handles): TIXI Handle
        tigl (handles): TIGL Handle

    Returns:
        wing_area_max (float): Max Wing Area [m^2]
        wing_span_max (float): Max Wing Span [m]
    """

    # Get Number of wings
    if tixi.checkElement(WINGS_XPATH):
        wing_count = tixi.getNamedChildrenCount(WINGS_XPATH, 'wing')
        log.info(str(wing_count) + ' wing has been found : ')
    else:
        wing_count = 0
        log.warning('No wing found in this CPACS file!')

    wing_span_max = 0
    wing_area_max = 0
    for i_wing in range(wing_count):
        wing_xpath = WINGS_XPATH + '/wing[' + str(i_wing+1) + ']'
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

    tixi = cpsf.open_tixi(cpacs_path)
    tigl = cpsf.open_tigl(tixi)

    wing_area_max, wing_span_max = get_largest_wing_dim(tixi,tigl)

    analyses_xpath = '/cpacs/toolspecific/CEASIOMpy/geometry/analysis'

    # Requiered input data from CPACS
    wetted_area = cpsf.get_value(tixi,analyses_xpath + '/wettedArea')

    # Wing area/span, default values will be calated if no value found in the CPACS file
    wing_area_xpath = analyses_xpath + '/wingArea'
    wing_area = cpsf.get_value_or_default(tixi,wing_area_xpath, wing_area_max)
    wing_span_xpath = analyses_xpath + '/wingSpan'
    wing_span = cpsf.get_value_or_default(tixi,wing_span_xpath, wing_span_max)

    aeromap_uid_list = []
    # Try to get SU2 aeroMap
    su2_aeroMap_xpath = SU2_XPATH + '/aeroMapUID'
    if tixi.checkElement(su2_aeroMap_xpath):
        aeromap_uid_list.append(cpsf.get_value(tixi,su2_aeroMap_xpath))

    # Try to get pyTornado aeroMap
    pyTornado_aeroMap_xpath = '/cpacs/toolspecific/pytornado/aeroMapUID'
    if tixi.checkElement(pyTornado_aeroMap_xpath):
        aeromap_uid_list.append(cpsf.get_value(tixi,pyTornado_aeroMap_xpath))

    # If pyTornado and SU2 aeroMap was not define, get all existing aeroMap
    if len(aeromap_uid_list) == 0:
        aeromap_uid_list = apmf.get_aeromap_uid_list(tixi)

    # If no aeroMap --> Error
    if len(aeromap_uid_list) == 0:
        raise ValueError('No aeroMap has been found in this CPACS file, skin friction cannot be added!')

    # Get unique aeroMap list
    aeromap_uid_list = list(set(aeromap_uid_list))

    # Add skin friction to all listed aeroMap
    for aeromap_uid in aeromap_uid_list:

        log.info('adding skin friction coefficients to: ' + aeromap_uid)

        # Get orignial aeroPerformanceMap
        AeroCoef = apmf.get_aeromap(tixi,aeromap_uid)
        AeroCoef.complete_with_zeros()

        # Create new aeroCoefficient object to store coef with added skin friction
        AeroCoefSF = apmf.AeroCoefficient()
        AeroCoefSF.alt = AeroCoef.alt
        AeroCoefSF.mach = AeroCoef.mach
        AeroCoefSF.aoa = AeroCoef.aoa
        AeroCoefSF.aos = AeroCoef.aos

        # Iterate over all cases
        case_count = AeroCoef.get_count()
        for case in range(case_count):

            # Get parameters for this case
            alt = AeroCoef.alt[case]
            mach = AeroCoef.mach[case]
            aoa = AeroCoef.aoa[case]
            aos = AeroCoef.aos[case]

            # Calculate Cd0 for this case
            cd0 = estimate_skin_friction_coef(wetted_area,wing_area,wing_span, \
                                              mach,alt)

            # Projection of cd0 on cl, cd and cs axis
            #TODO: Should Cd0 be projected or not???
            aoa_rad = math.radians(aoa)
            aos_rad = math.radians(aos)
            cd0_cl = cd0 * math.sin(aoa_rad)
            cd0_cd = cd0 * math.cos(aoa_rad) * math.cos(aos_rad)
            cd0_cs = cd0 * math.sin(aos_rad)

            # Update aerodynamic coefficients
            cl = AeroCoef.cl[case] + cd0_cl
            cd = AeroCoef.cd[case] + cd0_cd
            cs = AeroCoef.cs[case] + cd0_cs

            # Shoud we change something? e.i. if a force is not apply at aero center...?
            if len(AeroCoef.cml):
                cml = AeroCoef.cml[case]
            else:
                cml = 0.0  # Shoud be change, just to test pyTornado
            if len(AeroCoef.cmd):
                cmd = AeroCoef.cmd[case]
            else:
                cmd = 0.0
            if len(AeroCoef.cms):
                cms = AeroCoef.cms[case]
            else:
                cms = 0.0

            # Add new coefficients into the aeroCoefficient object
            AeroCoefSF.add_coefficients(cl,cd,cs,cml,cmd,cms)

        # Create new aeroMap UID
        aeromap_sf_uid = aeromap_uid + '_SkinFriction'

        # Create new description
        description_xpath = tixi.uIDGetXPath(aeromap_uid) + '/description'
        sf_description = cpsf.get_value(tixi,description_xpath) +  ' Skin friction has been add to this AeroMap.'
        apmf.create_empty_aeromap(tixi,aeromap_sf_uid, sf_description)

        # Save aeroCoefficient object Coef in the CPACS file
        apmf.save_parameters(tixi,aeromap_sf_uid,AeroCoefSF)
        apmf.save_coefficients(tixi,aeromap_sf_uid,AeroCoefSF)

    log.info('AeroMap "' + aeromap_uid + '" has been added to the CPACS file')

    cpsf.close_tixi(tixi,cpacs_out_path)


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

#
#     cruise_alt_xpath = range_xpath + '/cruiseAltitude'
#     tixi, cruise_alt = cpsf.get_value_or_default(tixi,cruise_alt_xpath,12000)
#
#     cruise_mach_xpath = range_xpath + '/cruiseMach'
#     tixi, cruise_mach = cpsf.get_value_or_default(tixi,cruise_mach_xpath,0.78)
#
#     # Calculate Cd0
#     cd0 = estimate_skin_friction_coef(wetted_area,wing_area,wing_span, \
#                                       cruise_mach,cruise_alt)
#
#     # Save Cd0 in the CPACS file
#     cd0_xpath = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/skinFriction/cd0'
#     cpsf.create_branch(tixi, cd0_xpath)
#     tixi.updateDoubleElement(cd0_xpath,cd0,'%g')
#     log.info('Skin friction drag coeffienct (cd0) has been saved in the \
#               CPACS file')
#
#     cpsf.close_tixi(tixi,cpacs_out_path)
