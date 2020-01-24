"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script obtain all the informations required for the Unconventional
weight analysis from the CPACS file

Python version: >=3.6

| Author : Stefano Piccini
| Date of creation: 2018-11-21
| Last modifiction: 2020-01-20 (AJ)

"""

#=============================================================================
#   IMPORTS
#=============================================================================

import ceasiompy.utils.cpacsfunctions as cpsf

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

    tixi = cpsf.open_tixi(cpacs_in)
    FUEL_XPATH = '/cpacs/toolspecific/CEASIOMpy/fuels'
    cpsf.create_branch(tixi, FUEL_XPATH, False)

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

    cpsf.close_tixi(tixi, cpacs_in)

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

    tixi = cpsf.open_tixi(cpacs_in)

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

    cpsf.create_branch(tixi, FUEL_XPATH, False)
    cpsf.create_branch(tixi, GEOM_XPATH, False)
    cpsf.create_branch(tixi, RANGE_XPATH, False)
    cpsf.create_branch(tixi, PILOTS_PATH, False)
    cpsf.create_branch(tixi, CAB_CREW_XPATH, False)
    cpsf.create_branch(tixi, PASS_XPATH, False)
    cpsf.create_branch(tixi, ML_XPATH, False)
    cpsf.create_branch(tixi, PROP_XPATH, False)

    # cpacs/vehicles
    MC_XPATH = '/cpacs/vehicles/aircraft/model/analyses/massBreakdown/payload/mCargo/massDescription'
    F_XPATH = '/cpacs/vehicles/fuels/fuel'

    cpsf.create_branch(tixi, MC_XPATH, False)
    cpsf.create_branch(tixi, F_XPATH, False)
    cpsf.add_uid(tixi, F_XPATH, 'kerosene')

    # Gathering data =========================================================
    # Geometry ===============================================================
    if not tixi.checkElement(GEOM_XPATH + '/description'):
        tixi.createElement(GEOM_XPATH, 'description')
        tixi.updateTextElement(GEOM_XPATH + '/description', 'User '\
                               + 'geometry input')

    # Number of floors.
    if not tixi.checkElement(GEOM_XPATH + '/floorsNb'):
        tixi.createElement(GEOM_XPATH, 'floorsNb')
        tixi.updateDoubleElement(GEOM_XPATH + '/floorsNb',\
                                 ui.FLOORS_NB, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_XPATH + '/floorsNb')
        if temp != ui.FLOORS_NB and temp > 0:
            ui.FLOORS_NB = temp

    # Extracting fuselage material data.
    if not tixi.checkElement(GEOM_XPATH + '/virtualThick'):
        tixi.createElement(GEOM_XPATH, 'virtualThick')
        tixi.updateDoubleElement(GEOM_XPATH + '/virtualThick',\
                                 adui.VRT_THICK, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_XPATH + '/virtualThick')
        if temp != adui.VRT_THICK and temp > 0:
            adui.VRT_THICK = temp

    if not tixi.checkElement(GEOM_XPATH + '/virtualDensity'):
        tixi.createElement(GEOM_XPATH, 'virtualDensity')
        tixi.updateDoubleElement(GEOM_XPATH + '/virtualDensity',\
                                 adui.VRT_STR_DENSITY, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_XPATH + '/virtualDensity')
        if temp != adui.VRT_STR_DENSITY and temp > 0:
            adui.VRT_STR_DENSITY = temp

    if not tixi.checkElement(GEOM_XPATH + '/cabinHeight'):
        tixi.createElement(GEOM_XPATH, 'cabinHeight')
        tixi.updateDoubleElement(GEOM_XPATH + '/cabinHeight',\
                                 ui.H_LIM_CABIN, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_XPATH + '/cabinHeight')
        if temp != ui.H_LIM_CABIN and temp > 0:
            ui.H_LIM_CABIN = temp

    # People =================================================================
    # Pilots user input data
    if not tixi.checkElement(PILOTS_PATH + '/pilotNb'):
        tixi.createElement(PILOTS_PATH, 'pilotNb')
        tixi.updateIntegerElement(PILOTS_PATH + '/pilotNb',\
                                 adui.PILOT_NB, '%i')
    else:
        temp = tixi.getIntegerElement(PILOTS_PATH + '/pilotNb')
        if temp != adui.PILOT_NB and temp > 0:
            adui.PILOT_NB = temp

    if not tixi.checkElement(PILOTS_PATH + '/pilotMass'):
        tixi.createElement(PILOTS_PATH, 'pilotMass')
        tixi.updateDoubleElement(PILOTS_PATH + '/pilotMass',\
                                 adui.MASS_PILOT, '%g')
    else:
        temp = tixi.getDoubleElement(PILOTS_PATH + '/pilotMass')
        if temp != adui.MASS_PILOT and temp > 0:
            adui.MASS_PILOT = temp

    # Cabin crew user input data
    if not tixi.checkElement(CAB_CREW_XPATH + '/cabinCrewMemberMass'):
        tixi.createElement(CAB_CREW_XPATH, 'cabinCrewMemberMass')
        tixi.updateDoubleElement(CAB_CREW_XPATH + '/cabinCrewMemberMass',\
                                 adui.MASS_CABIN_CREW, '%g')
    else:
        temp = tixi.getDoubleElement(CAB_CREW_XPATH + '/cabinCrewMemberMass')
        if temp != adui.MASS_CABIN_CREW and temp > 0:
            adui.MASS_CABIN_CREW = temp

    # Passengers user input data
    if not tixi.checkElement(PASS_XPATH + '/passMass'):
        tixi.createElement(PASS_XPATH, 'passMass')
        tixi.updateDoubleElement(PASS_XPATH + '/passMass',\
                                 adui.MASS_PASS, '%g')
    else:
        temp = tixi.getDoubleElement(PASS_XPATH+ '/passMass')
        if temp != adui.MASS_PASS and temp > 0:
            adui.MASS_PASS = temp

    if tixi.checkElement(PASS_XPATH + '/passNb'):
        temp = tixi.getIntegerElement(PASS_XPATH+ '/passNb')
        if temp != ui.MAX_PASS and temp > 0:
            ui.MAX_PASS = temp

    if not tixi.checkElement(PASS_XPATH + '/passDensity'):
        tixi.createElement(PASS_XPATH, 'passDensity')
        tixi.updateDoubleElement(PASS_XPATH + '/passDensity',\
                                 ui.PASS_BASE_DENSITY, '%i')
    else:
        temp = tixi.getDoubleElement(PASS_XPATH + '/passDensity')
        if temp != ui.PASS_BASE_DENSITY and temp > 0:
            ui.PASS_BASE_DENSITY = temp

    if not tixi.checkElement(PASS_XPATH + '/passPerToilet'):
        tixi.createElement(PASS_XPATH, 'passPerToilet')
        tixi.updateIntegerElement(PASS_XPATH + '/passPerToilet',\
                                 adui.PASS_PER_TOILET, '%i')
    else:
        temp = tixi.getIntegerElement(PASS_XPATH + '/passPerToilet')
        if temp != adui.PASS_PER_TOILET and temp > 0:
            adui.PASS_PER_TOILET = temp

    # Fuel ===================================================================
    if not tixi.checkElement(F_XPATH + '/density'):
        tixi.createElement(F_XPATH, 'density')
        tixi.updateDoubleElement(F_XPATH + '/density',\
                                 adui.FUEL_DENSITY, '%g')
    else:
        temp = tixi.getDoubleElement(F_XPATH + '/density')
        if temp != adui.FUEL_DENSITY and temp > 0:
            adui.FUEL_DENSITY = temp

    if not tixi.checkElement(FUEL_XPATH + '/resFuelPerc'):
        tixi.createElement(FUEL_XPATH, 'resFuelPerc')
        tixi.updateDoubleElement(FUEL_XPATH + '/resFuelPerc',\
                                 adui.RES_FUEL_PERC, '%g')
    else:
        temp = tixi.getDoubleElement(FUEL_XPATH + '/resFuelPerc')
        if temp != adui.RES_FUEL_PERC and temp > 0:
            adui.RES_FUEL_PERC = temp

    # Weight =================================================================
    # Mass limits data
    if not tixi.checkElement(ML_XPATH + '/description'):
        tixi.createElement(ML_XPATH, 'description')
        tixi.updateTextElement(ML_XPATH + '/description', 'Desired max fuel '\
                               + 'volume [m^3] and payload mass [kg]')
    if not tixi.checkElement(ML_XPATH + '/maxPayload'):
        tixi.createElement(ML_XPATH, 'maxPayload')
        tixi.updateDoubleElement(ML_XPATH + '/maxPayload',\
                                 ui.MAX_PAYLOAD, '%g')
    else:
        temp = tixi.getDoubleElement(ML_XPATH + '/maxPayload')
        if temp != ui.MAX_PAYLOAD and temp != 0:
            ui.MAX_PAYLOAD = temp
    if not tixi.checkElement(ML_XPATH + '/maxFuelVol'):
        tixi.createElement(ML_XPATH, 'maxFuelVol')
        tixi.updateDoubleElement(ML_XPATH + '/maxFuelVol',\
                                 ui.MAX_FUEL_VOL, '%g')
    else:
        temp = tixi.getDoubleElement(ML_XPATH + '/maxFuelVol')
        if temp != ui.MAX_FUEL_VOL and temp != 0:
            ui.MAX_FUEL_VOL = temp

    if tixi.checkElement(MC_XPATH + '/massCargo'):
        temp = tixi.getDoubleElement(MC_XPATH + '/massCargo')
        if temp != ui.MASS_CARGO and temp != 0:
            ui.MASS_CARGO = temp
        # If the cargo mass is defined in the UserInputs class will be added
        # in the CPACS file after the analysis.

    # Flight =================================================================
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

    TSFC_PATH = PROP_XPATH + '/tSFC'
    cpsf.create_branch(tixi, TSFC_PATH, False)
    if not tixi.checkElement(TSFC_PATH + '/tsfcCruise'):
        tixi.createElement(TSFC_PATH, 'tsfcCruise')
        tixi.updateDoubleElement(TSFC_PATH + '/tsfcCruise',\
                                 ed.TSFC_CRUISE, '%g')
    else:
        temp = tixi.getDoubleElement(TSFC_PATH + '/tsfcCruise')
        if temp != ed.TSFC_CRUISE and temp > 0:
            ed.TSFC_CRUISE = temp

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

    cpsf.close_tixi(tixi, cpacs_in)

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

    tixi = cpsf.open_tixi(cpacs_in)
    CEASIOM_XPATH = '/cpacs/toolspecific/CEASIOMpy'

    PROP_XPATH = CEASIOM_XPATH + '/propulsion'
    cpsf.create_branch(tixi, PROP_XPATH, False)
    # Propulsion =============================================================
    if not tixi.checkElement(PROP_XPATH + '/turboprop'):
        cpsf.create_branch(tixi, PROP_XPATH, False)
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

    cpsf.close_tixi(tixi, cpacs_in)

    return(ed)


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':

    log.warning('########################################################')
    log.warning('# ERROR NOT A STANDALONE PROGRAM, RUN weightuncmain.py #')
    log.warning('########################################################')
