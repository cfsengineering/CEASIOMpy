"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script obtain all the informations required for the Unconventional
weight analysis from the CPACS file

Python version: >=3.6

| Author : Stefano Piccini
| Date of creation: 2018-11-21
| Last modifiction: 2021-10-14 (AJ)

TODO:

    * A lot of things could be simplified...
    * Get flight condition for aeromap, how?
    * Get user inptut for engines

"""

#=============================================================================
#   IMPORTS
#=============================================================================

from cpacspy.cpacsfunctions import (add_uid, create_branch, 
                                    get_value_or_default, open_tixi)
from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================

"""All classes are defined inside the classes folder and in the
   InputClasses/Unconventional folder."""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def get_user_fuel(fus_nb, ui, cpacs_in):
    """Function to extract fuel data from a CPACS file

    Function 'get_user_fuel' extracts fuel data from the CPACS file, the code
    will use the default value when they are missing.

    Args:
        fus_nb (int): Number of fuselage.
        ui (class): UserInputs class
        cpacs_in (str): Path to the CPACS file

    Returns:
        ui (class): Modified UserInputs class

    """

    log.info('Starting data extraction from CPACS file')

    tixi = open_tixi(cpacs_in)
    FUEL_XPATH = '/cpacs/toolspecific/CEASIOMpy/fuels'
    create_branch(tixi, FUEL_XPATH, False)

    if fus_nb:
        for i in range(0, fus_nb):
            if fus_nb > 1:
                F = 'fuelOnCabin' + str(i+1)
            else:
                F = 'fuelOnCabin'
            if not tixi.checkElement(FUEL_XPATH + '/' + F):
                tixi.createElement(FUEL_XPATH, F)
                tixi.updateDoubleElement(FUEL_XPATH + '/' + F, ui.F_FUEL[i], '%g')
            else:
                ui.F_FUEL[i] = tixi.getDoubleElement(FUEL_XPATH + '/' + F)
    else:
        if not tixi.checkElement(FUEL_XPATH + '/fuelOnCabin'):
            tixi.createElement(FUEL_XPATH, 'fuelOnCabin')
            tixi.updateDoubleElement(FUEL_XPATH + '/fuelOnCabin', ui.FUEL_ON_CABIN, '%g')
        else:
            temp = tixi.updateDoubleElement(FUEL_XPATH + '/fuelOnCabin', ui.FUEL_ON_CABIN, '%g')
            if temp != ui.FUEL_ON_CABIN and temp > 0:
                ui.FUEL_ON_CABIN = temp

    log.info('Data from CPACS file succesfully extracted')

    tixi.save(cpacs_in)

    return(ui)


def get_user_inputs(ed, ui, adui, cpacs_in):
    """Function to extract from the xml file the required input data,
        the code will use the default value when they are missing.

    Function 'get_user_inputs' ...

    Args:
        ed (int): EngineData class.
        ui (class): UserInputs class
        adui (str): AdvancedInputs class.
        cpacs_in (str): Path to the CPACS file

    Returns:
        ed (int): Updated ngineData class.
        ui (class): Updated UserInputs class
        adui (str): Updated AdvancedInputs class.

    """


    log.info('Starting data extraction from CPACS file')

    tixi = open_tixi(cpacs_in)

    # toolspecific
    CEASIOM_XPATH = '/cpacs/toolspecific/CEASIOMpy'
    GEOM_XPATH = CEASIOM_XPATH + '/geometry'
    RANGE_XPATH = CEASIOM_XPATH + '/ranges'
    WEIGHT_XPATH = CEASIOM_XPATH + '/weight'
    CREW_XPATH = WEIGHT_XPATH + '/crew'
    PILOTS_PATH = CREW_XPATH + '/pilots'
    CAB_CREW_XPATH = CREW_XPATH + '/cabinCrewMembers'
    PASS_XPATH = WEIGHT_XPATH + '/passengers'
    ML_XPATH = WEIGHT_XPATH + '/massLimits'
    PROP_XPATH = CEASIOM_XPATH + '/propulsion'
    FUEL_XPATH = '/cpacs/toolspecific/CEASIOMpy/fuels'

    create_branch(tixi, FUEL_XPATH, False)
    create_branch(tixi, GEOM_XPATH, False)
    create_branch(tixi, RANGE_XPATH, False)
    create_branch(tixi, PILOTS_PATH, False)
    create_branch(tixi, CAB_CREW_XPATH, False)
    create_branch(tixi, PASS_XPATH, False)
    create_branch(tixi, ML_XPATH, False)
    create_branch(tixi, PROP_XPATH, False)

    # cpacs/vehicles
    MC_XPATH = '/cpacs/vehicles/aircraft/model/analyses/massBreakdown/payload/mCargo/massDescription'
    F_XPATH = '/cpacs/vehicles/fuels/fuel'

    create_branch(tixi, MC_XPATH, False)
    create_branch(tixi, F_XPATH, False)
    add_uid(tixi, F_XPATH, 'kerosene')

    # Gathering data =========================================================
    # Geometry ===============================================================
    if not tixi.checkElement(GEOM_XPATH + '/description'):
        tixi.createElement(GEOM_XPATH, 'description')
        tixi.updateTextElement(GEOM_XPATH + '/description', 'User '\
                               + 'geometry input')

    ui.FLOORS_NB = get_value_or_default(tixi,GEOM_XPATH + '/floorsNb', ui.FLOORS_NB)
    adui.VRT_THICK = get_value_or_default(tixi,GEOM_XPATH + '/virtualThick', 0.00014263)
    adui.VRT_STR_DENSITY = get_value_or_default(tixi,GEOM_XPATH + '/virtualDensity', 2700.0)
    ui.H_LIM_CABIN = get_value_or_default(tixi,GEOM_XPATH + '/cabinHeight', 2.3)

    # People =================================================================
    # Pilots user input data

    adui.PILOT_NB = get_value_or_default(tixi,PILOTS_PATH + '/pilotNb', 2)
    adui.MASS_PILOT = get_value_or_default(tixi,PILOTS_PATH + '/pilotMass', 102.0)
    adui.MASS_CABIN_CREW = get_value_or_default(tixi,CAB_CREW_XPATH + '/cabinCrewMemberMass', 68.0)
    adui.MASS_PASS = get_value_or_default(tixi,PASS_XPATH + '/passMass', 105.0)
    adui.PASS_BASE_DENSITY = get_value_or_default(tixi,PASS_XPATH + '/passDensity', 1.66)
    adui.PASS_PER_TOILET = get_value_or_default(tixi,PASS_XPATH + '/passPerToilet', 50)

    # what to to with this input
    if tixi.checkElement(PASS_XPATH + '/passNb'):
        temp = tixi.getIntegerElement(PASS_XPATH+ '/passNb')
        if temp != ui.MAX_PASS and temp > 0:
            ui.MAX_PASS = temp


    # Fuel ===================================================================
    adui.FUEL_DENSITY = get_value_or_default(tixi,F_XPATH + '/density', 800)
    adui.RES_FUEL_PERC = get_value_or_default(tixi,F_XPATH + '/resFuelPerc', 0.06)

    # Weight =================================================================
    # Mass limits data
    if not tixi.checkElement(ML_XPATH + '/description'):
        tixi.createElement(ML_XPATH, 'description')
        tixi.updateTextElement(ML_XPATH + '/description', 'Desired max fuel '\
                               + 'volume [m^3] and payload mass [kg]')

    ui.MAX_PAYLOAD = get_value_or_default(tixi,ML_XPATH + '/maxPayload', 0.0)
    ui.MAX_FUEL_VOL = get_value_or_default(tixi,ML_XPATH + '/maxFuelVol', 0.0)
    ui.MASS_CARGO = get_value_or_default(tixi,MC_XPATH + '/massCargo', 0.0)
    # If the cargo mass is defined in the UserInputs class will be added
    # in the CPACS file after the analysis.

    # Flight =================================================================

    ed.TSFC_CRUISE = get_value_or_default(tixi,PROP_XPATH + '/tSFC', 0.5)

    # TODO: These data should be taken from aeroMaps...
    if not tixi.checkElement(RANGE_XPATH + '/lDRatio'):
        tixi.createElement(RANGE_XPATH, 'lDRatio')
        tixi.updateDoubleElement(RANGE_XPATH + '/lDRatio',\
                                  ui.LD, '%g')
    else:
        temp = tixi.getIntegerElement(RANGE_XPATH + '/lDRatio')
        if temp != ui.LD and temp > 0:
            ui.LD = temp

    if not tixi.checkElement(RANGE_XPATH + '/cruiseSpeed'):
        tixi.createElement(RANGE_XPATH, 'cruiseSpeed')
        tixi.updateDoubleElement(RANGE_XPATH + '/cruiseSpeed',\
                                 ui.CRUISE_SPEED, '%g')
    else:
        temp = tixi.getIntegerElement(RANGE_XPATH + '/cruiseSpeed')
        if temp != ui.CRUISE_SPEED and temp > 0:
            ui.CRUISE_SPEED = temp

    # TODO: see how to enter input for Engines
    if not tixi.checkElement(PROP_XPATH + '/userEngineOption'):
        tixi.createElement(PROP_XPATH, 'userEngineOption')
        if ui.USER_ENGINES:
            tixi.updateTextElement(PROP_XPATH + '/userEngineOption', 'True')
        else:
            tixi.updateTextElement(PROP_XPATH + '/userEngineOption', 'False')
    else:
        temp = tixi.getTextElement(PROP_XPATH + '/userEngineOption')
        if temp == 'False':
            ui.USER_ENGINES = False
        else:
            ui.USER_ENGINES = True

    if not tixi.checkElement(PROP_XPATH + '/singleHydraulics'):
        tixi.createElement(PROP_XPATH, 'singleHydraulics')
        if adui.SINGLE_HYDRAULICS:
            tixi.updateTextElement(PROP_XPATH + '/singleHydraulics', 'True')
        else:
            tixi.updateTextElement(PROP_XPATH + '/singleHydraulics', 'False')
    else:
        temp = tixi.getTextElement(PROP_XPATH + '/singleHydraulics')
        if temp == 'False':
            adui.SINGLE_HYDRAULICS = False
        else:
            adui.SINGLE_HYDRAULICS = True

    log.info('Data from CPACS file succesfully extracted')

    tixi.save(cpacs_in)

    return(ed, ui, adui)


## ====================== ENGINES INPUT EXTRACTION DATA =======================#

def get_engine_inputs(ui, ed, cpacs_in):
    """ Function to extract from the xml file the required input data,
        the code will use the default value when they are missing.

        INPUT
        (class) ui     --Arg.: UserInputs class.
        (class) ed     --Arg.: EngineData class.
        ##======= Class ares defined in the InputClasses folder =======##
        (char) cpacs_in  --Arg.: Relative location of the xml file in the
                                 ToolInput folder (cpacs option) or
                                 relative location of the temp. xml file in
                                 the ToolOutput folder (input option).
        OUTPUT
        (class) ed       --Out.: EngineData class.
        (file) cpacs_in  --Out.: Updated cpasc file
    """

    log.info('Starting engine data extraction from CPACS file')

    tixi = open_tixi(cpacs_in)
    CEASIOM_XPATH = '/cpacs/toolspecific/CEASIOMpy'

    PROP_XPATH = CEASIOM_XPATH + '/propulsion'
    create_branch(tixi, PROP_XPATH, False)
    # Propulsion =============================================================
    if not tixi.checkElement(PROP_XPATH + '/turboprop'):
        create_branch(tixi, PROP_XPATH, False)
        tixi.createElement(PROP_XPATH, 'turboprop')
        if ed.TURBOPROP:
            tixi.updateTextElement(PROP_XPATH + '/turboprop', 'True')
        else:
            tixi.updateTextElement(PROP_XPATH + '/turboprop', 'False')
    else:
        temp = tixi.getTextElement(PROP_XPATH + '/turboprop')
        if temp == 'False':
            ed.TURBOPROP = False
        else:
            ed.TURBOPROP = True
    if not tixi.checkElement(PROP_XPATH + '/auxiliaryPowerUnit'):
        tixi.createElement(PROP_XPATH, 'auxiliaryPowerUnit')
        if ed.APU:
            tixi.updateTextElement(PROP_XPATH + '/auxiliaryPowerUnit', 'True')
        else:
            tixi.updateTextElement(PROP_XPATH + '/auxiliaryPowerUnit', 'False')
    else:
        temp = tixi.getTextElement(PROP_XPATH + '/auxiliaryPowerUnit')
        if temp == 'False':
            ed.APU = False
        else:
            ed.APU = True
    if not tixi.checkElement(PROP_XPATH + '/engineNumber'):
        tixi.createElement(PROP_XPATH, 'engineNumber')
        tixi.updateIntegerElement(PROP_XPATH + '/engineNumber', ed.NE, '%i')
    else:
        ed.NE = tixi.getIntegerElement(PROP_XPATH + '/engineNumber')

    #Engines
    mp = []
    tp = []
    EN_XPATH = '/cpacs/vehicles/engines'
    if tixi.checkElement(EN_XPATH):
        for e in range(0,ed.NE-1):
            EN_XPATH = '/cpacs/vehicles/engines'
            if ed.NE > 1:
                EN_XPATH += '/engine' + str(e+1)
            else:
                EN_XPATH += '/engine'
            if not tixi.checkElement(EN_XPATH):
                raise Exception('Engine definition inclomplete, missing'\
                                + ' one or more engines in the cpacs file')
            if not tixi.checkElement(EN_XPATH + '/name'):
                ed.EN_NAME.append('Engine_' + str(e+1))
                tixi.createElement(EN_XPATH, 'name')
                tixi.updateTextElement(EN_XPATH + '/name', ed.EN_NAME[e])
            else:
                if e > len(ed.EN_NAME):
                    ed.EN_NAME.append(tixi.getTextElement(EN_XPATH + '/name'))
            ENA_XPATH = EN_XPATH + '/analysis/mass'
            if tixi.checkElement(ENA_XPATH + '/mass'):
                ed.en_mass = tixi.getDoubleElement(ENA_XPATH + '/mass')
                mp.append(ed.en_mass)
                if e>0 and ed.en_mass != mp[e-1]:
                    raise Exception('The engines have different masses, this'\
                                    + ' can lead to an unbalanced aircraft')
            elif ed.en_mass:
                tixi.createElement(ENA_XPATH, 'mass')
                tixi.updateDoubleElement(ENA_XPATH + '/mass', ed.en_mass, '%g')
            else:
                raise Exception('Engine definition inclomplete, missing'\
                                + ' engine mass in the cpacs file')

            if tixi.checkElement(EN_XPATH + '/analysis/thrust00'):
                ed.max_thrust = tixi.getDoubleElement(EN_XPATH + '/analysis/thrust00')
                tp.append(ed.max_thrust)
                if e>0 and ed.max_thrust != tp[e-1]:
                    raise Exception('The engines have different thrust, this')
                                    #+ ' can lead to an unbalanced flight')
            elif ed.max_thrust:
                tixi.createElement(EN_XPATH, '/analysisthrust00')
                tixi.updateDoubleElement(EN_XPATH + '/analysis/thrust00',
                                         ed.max_thrust, '%g')
            else:
                raise Exception('Engine definition inclomplete, missing'\
                                + ' engine thrust in the cpacs file')
    log.info('Data from CPACS file succesfully extracted')

    tixi.save(cpacs_in)

    return(ed)


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':

    log.warning('########################################################')
    log.warning('# ERROR NOT A STANDALONE PROGRAM, RUN weightuncmain.py #')
    log.warning('########################################################')
