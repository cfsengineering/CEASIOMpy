"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

This programm will read the xml file created by the weight module or
the xml file in the cpacs file formatinside the ToolInput folder.

The cpacs file Must contain the:

* maximum_take_off_mass  --In.: Maximum take off mass
* mass_fuel_max          --In.: Maximum fuel mass
* mass_fuel_maxpass      --In.: Maximum fuel with max passengers
* operating_empty_mass   --In.: Operating empty mass
* mass_payload           --In.: Payload mass

The cpacs file Should also contain:

* WING_MOUNTED   --In.: True if the engine are placed on the rear of the
                        aircraft.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-12-05
| Last modifiction: 2019-08-29 (AJ)
"""


#=============================================================================
#   IMPORTS
#=============================================================================

import numpy as np

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi,open_tigl, close_tixi,    \
                                           create_branch

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================

"""All classes are defined inside the classes folder and into the
   InputClasses/Uconventional folder"""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def get_user_fuel(f_nb, ui, cpacs_in):
    """ Function to extract from the xml file the required input data,
        the code will use the default value when they are missing.

        INPUT
        (int) f_nb     --Arg.: Number of fuselage.
        (class) ui     --Arg.: UserInputs class.
        ##======= Classes are defined in the InputClasses folder =======##

        (char) cpacs_in  --Arg.: Relative location of the xml file in the
                                 ToolInput folder (cpacs option) or
                                 relative location of the temp. xml file in
                                 the ToolOutput folder (input option).
        OUTPUT
        (class) ui       --Out.: UserInputs class.
        (file) cpacs_in  --Out.: Updated cpasc file
    """

    log.info('Starting data extraction from CPACS file')

    # Path creation ==========================================================
    tixi = open_tixi(cpacs_in)
    FUEL_PATH = '/cpacs/toolspecific/CEASIOMpy/fuels'
    create_branch(tixi, FUEL_PATH, False)

    if f_nb:
        for i in range(0, f_nb):
            if f_nb > 1:
                F = 'fuelOnCabin' + str(i+1)
            else:
                F = 'fuelOnCabin'
            print((FUEL_PATH + '/' + F))
            if not tixi.checkElement(FUEL_PATH + '/' + F):
                tixi.createElement(FUEL_PATH, F)
                tixi.updateDoubleElement(FUEL_PATH + '/' + F,\
                                         ui.F_FUEL[i], '%g')
            else:
                ui.F_FUEL[i] = tixi.getDoubleElement(FUEL_PATH + '/' + F)
    else:
        if not tixi.checkElement(FUEL_PATH + '/fuelOnCabin'):
            tixi.createElement(FUEL_PATH, 'fuelOnCabin')
            tixi.updateDoubleElement(FUEL_PATH + '/fuelOnCabin',\
                                     ui.FUEL_ON_CABIN, '%g')
        else:
            temp = tixi.updateDoubleElement(FUEL_PATH + '/fuelOnCabin',\
                                            ui.FUEL_ON_CABIN, '%g')
            if temp != ui.FUEL_ON_CABIN and temp > 0:
                ui.FUEL_ON_CABIN = temp

    log.info('Data from CPACS file succesfully extracted')
    # Saving and closing the cpacs file --------------------------------------
    tixi.saveDocument(cpacs_in)
    close_tixi(tixi, cpacs_in)

    # Openign and closing again the cpacs file -------------------------------
    tixi = open_tixi(cpacs_in)
    tigl = open_tigl(tixi)
    tixi.saveDocument(cpacs_in)
    close_tixi(tixi, cpacs_in)

    return(ui)


def get_data(ui, bi, mw, ed, cpacs_in):
    """ The function extracts from the xml file the required input data,
        the code will use the default value when they are missing.

        INPUT
        (class) ui       --Arg.: UserInputs class.
        (class) bi       --Arg.: BalanceInputs class.
        (class) mw       --Arg.: MassesWeight class.
        (class) ed       --Arg.: EngineData class.
        ##======= Classes are defined in the InputClasses folder =======##

        (char) cpacs_in  --Arg.: Relative location of the xml file in the
                                 ToolInput folder (cpacs option) or
                                 relative location of the temp. xml file in
                                 the ToolOutput folder (input option).
        OUTPUT
        (class) mw       --Out.: MassesWeight class updated.
        (class) ed       --Out.: EngineData class updated.
        (file) cpacs_in  --Out.: Updated cpasc file.
    """
    log.info('CPACS file path check')

    # path definition ========================================================
    # Opening CPACS file
    tixi = open_tixi(cpacs_in)


    TSPEC_PATH = '/cpacs/toolspecific/CEASIOMpy'

    GEOM_PATH = TSPEC_PATH + '/geometry'
    FMP_PATH = TSPEC_PATH + '/weight/passengers/fuelMassMaxpass/mass'
    PROP_PATH = TSPEC_PATH + '/propulsion'

    MASS_PATH = '/cpacs/vehicles/aircraft/model/analyses/massBreakdown'
    MTOM_PATH = MASS_PATH + '/designMasses/mTOM/mass'
    F_PATH = MASS_PATH + '/fuel/massDescription/mass'
    OEM_PATH = MASS_PATH + '/mOEM/massDescription/mass'
    PAY_PATH = MASS_PATH + '/payload/massDescription/mass'

    EN_PATH = '/cpacs/vehicles/engines/engine1/analysis/mass/mass'

    BC_PATH = TSPEC_PATH + '/balance/userBalance'
    create_branch(tixi, BC_PATH, False)
    # Compulsory path checks =================================================

    if not tixi.checkElement(TSPEC_PATH):
        raise Exception('Missing required toolspecific path. Run '\
                        + 'Weight_unc_main.py,'\
                        + ' in the 4Weight_unc_module folder.')
    elif not tixi.checkElement(MASS_PATH):
        raise Exception('Missing required massBreakdown path. Run '\
                        + 'Weight_unc_main.py,'\
                        + ' in the 4Weight_unc_module folder.')
    elif not tixi.checkElement(MTOM_PATH):
        raise Exception('Missing required mTOM/mass path. Run '\
                        + 'Weight_unc_main.py,'\
                        + ' in the 4Weight_unc_module folder.')
    elif not tixi.checkElement(FMP_PATH):
        raise Exception('Missing required fuelMassMaxpass/mass path. Run '\
                        + 'Weight_unc_main.py,'\
                        + ' in the 4Weight_unc_module folder.')
    elif not tixi.checkElement(OEM_PATH):
        raise Exception('Missing required mOEM/massDescription/mass '\
                        + 'path. Run Weight_unc_main.py,'\
                        + ' in the 4Weight_unc_module folder.')
    elif not tixi.checkElement(PAY_PATH):
        raise Exception('Missing required payload/massDescription/mass '\
                        + 'path. Run Weight_unc_main.py,'\
                        + ' in the 4Weight_unc_module folder.')
    elif not tixi.checkElement(F_PATH):
        raise Exception('Missing required /fuel/massDescription/mass '\
                        + 'path. Run Weight_unc_main.py,'\
                        + ' in the 4Weight_unc_module folder.')
    elif not tixi.checkElement(EN_PATH):
        raise Exception('Missing required /cpacs/vehicles/engines/engine1'\
                        + '/analysis/mass path. Run Weight_unc_main.py,'\
                        + ' in the 4Weight_unc_module folder.')
    else:
        log.info('All path correctly defined in the toolinput.xml file, '\
                 + 'beginning data extracction.')

    # Gathering data =========================================================
    ## Geometry Data

    if not tixi.checkElement(GEOM_PATH + '/floorsNb'):
        tixi.createElement(GEOM_PATH, 'floorsNb')
        tixi.updateDoubleElement(GEOM_PATH + '/floorsNb',\
                                 ui.FLOORS_NB, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_PATH + '/floorsNb')
        if temp != ui.FLOORS_NB and temp > 0:
            ui.FLOORS_NB = temp

    if not tixi.checkElement(GEOM_PATH + '/cabinHeight'):
        tixi.createElement(GEOM_PATH, 'cabinHeight')
        tixi.updateDoubleElement(GEOM_PATH + '/cabinHeight',\
                                 ui.H_LIM_CABIN, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_PATH + '/cabinHeight')
        if temp != ui.H_LIM_CABIN and temp > 0:
            ui.H_LIM_CABIN = temp

    ## User Case Balance
    if not tixi.checkElement(BC_PATH + '/userCase'):
        tixi.createElement(BC_PATH, 'userCase')
        if bi.USER_CASE:
            tixi.updateTextElement(BC_PATH + '/userCase', 'True')
        else:
            tixi.updateTextElement(BC_PATH + '/userCase', 'False')
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
    ## Engines Data
    ed.en_mass = tixi.getDoubleElement(EN_PATH)

    if not tixi.checkElement(PROP_PATH + '/wingMountedEngine'):
        create_branch(tixi, PROP_PATH, False)
        tixi.createElement(PROP_PATH, 'wingMountedEngine')
        if ed.WING_MOUNTED:
            tixi.updateTextElement(PROP_PATH + '/wingMountedEngine', 'True')
        else:
            tixi.updateTextElement(PROP_PATH + '/wingMountedEngine', 'False')
    else:
        temp = tixi.getTextElement(PROP_PATH + '/wingMountedEngine')
        if temp == 'False':
            ed.WING_MOUNTED = False
        else:
            ed.WING_MOUNTED = True

    if not tixi.checkElement(PROP_PATH + '/userEnginePlacement'):
        tixi.createElement(PROP_PATH, 'userEnginePlacement')
        if bi.USER_EN_PLACEMENT:
            tixi.updateTextElement(PROP_PATH + '/userEnginePlacement', 'True')
        else:
            tixi.updateTextElement(PROP_PATH + '/userEnginePlacement', 'False')
    else:
        temp = tixi.getTextElement(PROP_PATH + '/userEnginePlacement')
        if temp == 'False':
            bi.USER_EN_PLACEMENT = False
        else:
            bi.USER_EN_PLACEMENT = True

    if not tixi.checkElement(PROP_PATH + '/engineNumber'):
        create_branch(tixi, PROP_PATH, False)
        tixi.createElement(PROP_PATH, 'engineNumber')
        tixi.updateIntegerElement(PROP_PATH + '/engineNumber', ed.NE, '%i')
    else:
        ed.NE = tixi.getIntegerElement(PROP_PATH + '/engineNumber')


    ## User Engine Placement
    tp=[]
    ed.EN_NAME=[]
    if tixi.checkElement(EN_PATH):
        for e in range(0,ed.NE):
            EN_PATH = '/cpacs/vehicles/engines'
            if ed.NE > 1:
                EN_PATH += '/engine' + str(e+1)
            else:
                EN_PATH += '/engine'
            if not tixi.checkElement(EN_PATH):
                raise Exception('Engine definition inclomplete, missing'\
                                + ' one or more engines in the cpacs file')
            if not tixi.checkElement(EN_PATH + '/name'):
                ed.EN_NAME.append('Engine_' + str(e+1))
            else:
                ed.EN_NAME.append(tixi.getTextElement(EN_PATH + '/name'))
            ENA_PATH = EN_PATH + '/analysis/mass'
            if tixi.checkElement(ENA_PATH):
                ed.en_mass = tixi.getDoubleElement(ENA_PATH + '/mass')
                tp.append(ed.en_mass)
                if e > 0 and ed.en_mass != tp[e-1]:
                    log.warning('The engines have different masses,'\
                                + 'this can lead to an unbalanced aircraft')
            elif ed.en_mass:
                tixi.createElement(ENA_PATH, 'mass')
                tixi.updateDoubleElement(ENA_PATH + '/mass', ed.en_mass, '%g')
            else:
                raise Exception('Engine definition inclomplete, missing'\
                                + ' engine mass in the cpacs file')

    s = np.shape(ed.EN_PLACEMENT)
    warn = False
    if not ed.NE:
        raise Exception('No engine defined for the aircraft')
    elif s[0] < ed.NE or s[1] < 3 or np.any(ed.EN_PLACEMENT) == False:
        warn=True
    else:
        log.info('EngineData class defined correctly.')

    s = ed.EN_PLACEMENT
    if bi.USER_EN_PLACEMENT:
        ed.EN_PLACEMENT = []
        for e in range(1,ed.NE+1):
            if ed.NE > 1:
                ENLOC_PATH =  '/cpacs/vehicles/engines/engine' + str(e)\
                              + '/analysis/mass/location'
            else:
                ENLOC_PATH =  '/cpacs/vehicles/engines/engine'\
                              + '/analysis/mass/location'
            if not tixi.checkElement(ENLOC_PATH) and warn:
                raise Exception('User engine Placement option defined'\
                                + ' True but no engine placement data in the'\
                                + ' CPACS file.')
            if not tixi.checkElement(ENLOC_PATH) and not warn:
                create_branch(tixi, ENLOC_PATH, False)
                tixi.createElement(ENLOC_PATH, 'x')
                tixi.createElement(ENLOC_PATH, 'y')
                tixi.createElement(ENLOC_PATH, 'z')
                tixi.updateDoubleElement(ENLOC_PATH +'/x', s[e-1][0], '%g')
                tixi.updateDoubleElement(ENLOC_PATH +'/y', s[e-1][1], '%g')
                tixi.updateDoubleElement(ENLOC_PATH +'/z', s[e-1][2], '%g')
                ed.EN_PLACEMENT.append([s[e-1][0], s[e-1][1], s[e-1][2]])
            else:
                x=tixi.getDoubleElement(ENLOC_PATH + '/x')
                y=tixi.getDoubleElement(ENLOC_PATH + '/y')
                z=tixi.getDoubleElement(ENLOC_PATH + '/z')
                ed.EN_PLACEMENT.append([x,y,z])
        ed.EN_PLACEMENT=np.array(ed.EN_PLACEMENT)

    ## REQUIRED TOOLSPECIFIC DATA ============================================
    # Fuel
    mw.mass_fuel_maxpass = tixi.getDoubleElement(FMP_PATH)

    ## REQUIRED MASSBREAKDOWN DATA ===========================================

    mw.maximum_take_off_mass = tixi.getDoubleElement(MTOM_PATH)
    mw.operating_empty_mass = tixi.getDoubleElement(OEM_PATH)
    mw.mass_payload = tixi.getDoubleElement(PAY_PATH)
    mw.mass_fuel_tot = tixi.getDoubleElement(F_PATH)

    log.info('Data from CPACS file succesfully extracted')

    # Saving and closing the cpacs file ======================================
    tixi.saveDocument(cpacs_in)
    close_tixi(tixi, cpacs_in)

    # Openign and closing again the cpacs file ===============================
    tixi = open_tixi(cpacs_in)
    tigl = open_tigl(tixi)
    tixi.saveDocument(cpacs_in)
    close_tixi(tixi, cpacs_in)

    return(mw, ed)


#=============================================================================
#   MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('#########################################################')
    log.warning('# ERROR NOT A STANDALONE PROGRAM, RUN balanceuncmain.py #')
    log.warning('#########################################################')
