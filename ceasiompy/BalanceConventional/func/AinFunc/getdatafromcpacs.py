"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

This program will read the XML file created by the weight module or
the XML file in the cpacs file format that must be put by the user in
the ToolInput folder.

The cpacs file Must contain the:

* maximum_take_off_mass  --In.: Maximum take off mass
* mass_fuel_max          --In.: Maximum fuel mass
* mass_fuel_maxpass      --In.: Maximum fuel with max passengers
* operating_empty_mass   --In.: Operating empty mass
* mass_payload           --In.: Payload mass

The cpacs file Should also contain:

* WING_MOUNTED   --In.: True if the engines are on the rear of the
                        aircraft.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-12-5
| Last modifiction: 2019-08-29 (AJ)
"""


#=============================================================================
#   IMPORTS
#=============================================================================

from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                           create_branch

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================

"""All classes are defined inside the InputClasses/Conventional"""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def get_data(mw, bi, cpacs_in):
    """ The function extracts from the XML file the required input data,
        the code will use the default value when they are missing.

        INPUT
        (class) mw       --Arg.: MassesWeight class.
        (class) bi       --Arg.: BalanceInput class.
        ##======= Classes are defined in the InputClasses folder =======##

        (char) cpacs_in  --Arg.: Relative location of the xml file in the
                                 ToolInput folder (cpacs option) or
                                 relative location of the temp. xml file in
                                 the ToolOutput folder (input option).

        OUTPUT
        (class) mw       --Out.: MassesWeight class updated.
        (class) bi       --Out.: RangeInput class updated.
        (file) cpacs_in  --Out.: Updated cpasc file.
    """
    log.info('CPACS file path check')

    # path definition ========================================================
    # Opening CPACS file
    tixi = open_tixi(cpacs_in)

    TSPEC_PATH = '/cpacs/toolspecific/CEASIOMpy'
    FMP_PATH = TSPEC_PATH + '/weight/passengers/fuelMassMaxpass/mass'
    PROP_PATH = TSPEC_PATH + '/propulsion'

    BC_PATH = TSPEC_PATH + '/balance/userBalance'
    create_branch(tixi, BC_PATH, False)
    MASS_PATH = '/cpacs/vehicles/aircraft/model/analyses/massBreakdown'
    MTOM_PATH = MASS_PATH + '/designMasses/mTOM/mass'
    F_PATH = MASS_PATH + '/fuel/massDescription/mass'
    OEM_PATH = MASS_PATH + '/mOEM/massDescription/mass'
    PAY_PATH = MASS_PATH + '/payload/massDescription/mass'


    # Compulsory path checks =================================================

    if not tixi.checkElement(TSPEC_PATH):
        raise Exception('Missing required toolspecific path. Run '\
                        + 'Weight_main.py, in the 1Weight_module folder.')
    elif not tixi.checkElement(MASS_PATH):
        raise Exception('Missing required massBreakdown path. Run '\
                        + 'Weight_main.py, in the 1Weight_module folder.')
    elif not tixi.checkElement(MTOM_PATH):
        raise Exception('Missing required mTOM/mass path. Run '\
                        + 'Weight_main.py, in the 1Weight_module folder.')
    elif not tixi.checkElement(FMP_PATH):
        raise Exception('Missing required fuelMassMaxpass/mass path. Run '\
                        + 'Weight_main.py, in the 1Weight_module folder.')
    elif not tixi.checkElement(OEM_PATH):
        raise Exception('Missing required mOEM/massDescription/mass '\
                        + 'path. Run '\
                        + 'Weight_main.py, in the 1Weight_module folder.')
    elif not tixi.checkElement(PAY_PATH):
        raise Exception('Missing required payload/massDescription/mass '\
                        + 'path. Run '\
                        + 'Weight_main.py, in the 1Weight_module folder.')
    elif not tixi.checkElement(F_PATH):
        raise Exception('Missing required /fuel/massDescription/mass '\
                        + 'path. Run '\
                        + 'Weight_main.py, in the 1Weight_module folder.')
    else:
        log.info('All path correctly defined in the toolinput.xml file, '\
                 + 'beginning data extracction.')

    # Gathering data =========================================================
    ## TOOLSPECIFIC ----------------------------------------------------------
    if not tixi.checkElement(PROP_PATH + '/wingMountedEngine'):
        create_branch(tixi, PROP_PATH, False)
        tixi.createElement(PROP_PATH, 'wingMountedEngine')
        if bi.WING_MOUNTED:
            tixi.updateTextElement(PROP_PATH + '/wingMountedEngine', 'True')
        else:
            tixi.updateTextElement(PROP_PATH + '/wingMountedEngine', 'False')
    else:
        temp = tixi.getTextElement(PROP_PATH + '/wingMountedEngine')
        if temp == 'False':
            bi.WING_MOUNTED = False
        else:
            bi.WING_MOUNTED = True

    ## User Case Balance
    if not tixi.checkElement(BC_PATH + '/userCase'):
        tixi.createElement(BC_PATH, 'userCase')
        if bi.USER_CASE:
            tixi.updateTextElement(BC_PATH + '/userCase', 'True')
            print('1')
        else:
            tixi.updateTextElement(BC_PATH + '/userCase', 'False')
            print('2')
    else:
        temp = tixi.getTextElement(BC_PATH + '/userCase')
        if temp == 'False':
            bi.USER_CASE = False
        else:
            bi.USER_CASE = True

    if bi.USER_CASE:
        if tixi.checkElement(BC_PATH + '/fuelPercentage'):
            bi.F_PERC=tixi.getDoubleElement(BC_PATH + '/fuelPercentage')
        elif bi.F_PERC:
            tixi.createElement(BC_PATH, 'fuelPercentage')
            tixi.updateDoubleElement(BC_PATH + '/fuelPercentage',\
                                     bi.F_PERC, '%g')
        else:
            raise Exception('User balance option defined'\
                            + ' True but no fuel percentage data in the'\
                            + ' CPACS file or in th BalanceInput class.')
        if tixi.checkElement(BC_PATH + '/payloadPercentage'):
            bi.P_PERC=tixi.getDoubleElement(BC_PATH + '/payloadPercentage')
        elif bi.P_PERC:
            tixi.createElement(BC_PATH, 'payloadPercentage')
            tixi.updateDoubleElement(BC_PATH + '/payloadPercentage',\
                                     bi.P_PERC, '%g')
        else:
            raise Exception('User balance option defined'\
                            + ' True but no payload percentage data in'\
                            + ' the CPACS file or in th BalanceInput class.')

    ## REQUIRED TOOLSPECIFIC DATA ============================================
    # Fuel
    mw.mass_fuel_maxpass = tixi.getDoubleElement(FMP_PATH)

    ## REQUIRED MASSBREAKDOWN DATA ===========================================

    mw.maximum_take_off_mass = tixi.getDoubleElement(MTOM_PATH)
    mw.operating_empty_mass = tixi.getDoubleElement(OEM_PATH)
    mw.mass_payload = tixi.getDoubleElement(PAY_PATH)
    mw.mass_fuel_max = tixi.getDoubleElement(F_PATH)

    log.info('Data from CPACS file succesfully extracted')
    # Saving and closing the cpacs file ======================================
    tixi.saveDocument(cpacs_in)
    close_tixi(tixi, cpacs_in)

    # Openign and closing again the cpacs file ===============================
    tixi = open_tixi(cpacs_in)
    tigl = open_tigl(tixi)
    tixi.saveDocument(cpacs_in)
    close_tixi(tixi, cpacs_in)

    return(mw, bi)

#=============================================================================
#   MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('##########################################################')
    log.warning('### ERROR NOT A STANDALONE PROGRAM, RUN balancemain.py ###')
    log.warning('##########################################################')
