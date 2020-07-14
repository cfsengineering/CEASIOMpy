"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

This script updates the cpacs file and copy it on the ToolOutput folder.

| Works with Python 2.7
| Author: Stefano Piccini
| Date of creation: 2018-11-21
| Last modifiction: 2019-08-29 (AJ)
"""

#=============================================================================
#   IMPORTS
#=============================================================================

from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                           add_uid, create_branch, copy_branch

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================


#=============================================================================
#   FUNCTIONS
#=============================================================================

def cpacs_update(mass_pass, out, mw,  out_xml):
    """ The function updates the cpacs file after the range analysis.

        INPUT
        (float) mass_pass         --Arg.: Passenger mass, countig also the
                                          extra mass.
        (class) out               --Arg.: RangeOutput class.
        ##======== Class is defined in the InputClasses folder =======##

        (class) mw                --Arg.: MassesWeights class.
        ##======= Class is defined in the InputClasses folder =======##
        (char) out_xml             --Arg.: Path of the output file.


        OUTPUT
        (file) cpacs.xml --Out.: Updated cpacs file.
    """
    tixi = open_tixi(out_xml)
    tigl = open_tigl(tixi)

    ### PATH CHECKS ==========================================================

    CEASIOM_PATH = '/cpacs/toolspecific/CEASIOMpy'
    # Ranges
    RANGE_PATH = CEASIOM_PATH + '/ranges'
    RANGE_MAXP_PATH = RANGE_PATH + '/rangeMaxP'
    R_DES_MAXP_PATH = RANGE_PATH + '/rangeMaxP/rangeDescription'
    RANGE_MAXF_PATH = RANGE_PATH + '/rangeMaxF'
    R_DES_MAXF_PATH = RANGE_PATH + '/rangeMaxF/rangeDescription'
    RANGE_MAXIMUM_PATH = RANGE_PATH + '/rangeMaximum'
    R_DES_MAXIMUM_PATH = RANGE_PATH + '/rangeMaximum/rangeDescription'

    create_branch(tixi, R_DES_MAXP_PATH + '/range', False)
    create_branch(tixi, R_DES_MAXP_PATH + '/payload', False)
    create_branch(tixi, R_DES_MAXF_PATH + '/range', False)
    create_branch(tixi, R_DES_MAXF_PATH + '/payload', False)
    create_branch(tixi, R_DES_MAXIMUM_PATH + '/range', False)
    create_branch(tixi, R_DES_MAXIMUM_PATH + '/payload', False)

    # Fuel consumption
    FCONS_PATH =  '/cpacs/toolspecific/CEASIOMpy/fuelConsumption'
    FDES_PATH = FCONS_PATH + '/description'
    FTO_PATH = FCONS_PATH + '/fuelForTakeOff'
    FC_PATH = FCONS_PATH + '/fuelForClimb'
    FCR_PATH = FCONS_PATH + '/fuelForCruise'
    FL_PATH = FCONS_PATH + '/fuelForLoiter'
    FLD_PATH = FCONS_PATH + '/fuelForLanding'
    FAL_PATH = FCONS_PATH + '/fuelRemained'

    create_branch(tixi, FDES_PATH, False)
    create_branch(tixi, FTO_PATH, False)
    create_branch(tixi, FC_PATH, False)
    create_branch(tixi, FCR_PATH, False)
    create_branch(tixi, FL_PATH, False)
    create_branch(tixi, FLD_PATH, False)
    create_branch(tixi, FAL_PATH, False)

    ### RANGES ===============================================================
    ### Max payload max range ------------------------------------------------
    add_uid(tixi, R_DES_MAXP_PATH, 'Maximum_range_[km]'\
                       + '_with_maximum_payload_[kg]')
    tixi.updateDoubleElement(R_DES_MAXP_PATH + '/range', out.ranges[1], '%g')
    tixi.updateDoubleElement(R_DES_MAXP_PATH + '/payload',\
                             out.payloads[1], '%g')

    ### Max fuel range with some payload -------------------------------------
    add_uid(tixi, R_DES_MAXF_PATH, 'Range_[km]_with_'\
                       + 'maximum_fuel_and_some_payload_[kg]')
    tixi.updateDoubleElement(R_DES_MAXF_PATH + '/range', out.ranges[2], '%g')
    tixi.updateDoubleElement(R_DES_MAXF_PATH + '/payload',\
                             out.payloads[2], '%g')

    ### Maximum range, no payload and max fuel -------------------------------
    add_uid(tixi, R_DES_MAXIMUM_PATH, 'Maximum_range_[km]_with_'\
                       + 'max_fuel_and_no_payload_[kg]')
    tixi.updateDoubleElement(R_DES_MAXIMUM_PATH + '/range',\
                             out.ranges[3], '%g')
    tixi.updateDoubleElement(R_DES_MAXIMUM_PATH \
                             + '/payload', out.payloads[3], '%g')


    ### FUEL CONSUMPTION =====================================================
    add_uid(tixi, FDES_PATH, 'Fuel required for each flight phase '\
                       + '[kg], with maximum payload.')

    tixi.updateDoubleElement(FTO_PATH, mw.mf_for_to, '%g')
    tixi.updateDoubleElement(FC_PATH, mw.mf_for_climb, '%g')
    tixi.updateDoubleElement(FCR_PATH, mw.mf_for_cruise, '%g')
    tixi.updateDoubleElement(FL_PATH, mw.mf_for_loiter, '%g')
    tixi.updateDoubleElement(FLD_PATH, mw.mf_for_landing, '%g')
    tixi.updateDoubleElement(FAL_PATH, mw.mf_after_land, '%g')

    ### Saving and closing the new cpacs file inside the ToolOutput folder ---
    tixi.saveDocument(out_xml)
    close_tixi(tixi, out_xml)

    ### Openign and closing again the cpacs file, formatting purpose ---------
    tixi = open_tixi(out_xml)
    tigl = open_tigl(tixi)
    tixi.saveDocument(out_xml)
    close_tixi(tixi, out_xml)

    return(out_xml)


#=============================================================================
#   MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('##########################################################')
    log.warning('#### ERROR NOT A STANDALONE PROGRAM, RUN rangemain.py ####')
    log.warning('##########################################################')
