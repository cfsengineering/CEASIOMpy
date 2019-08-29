"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script obtain all the informations reuired for the Unconventional
weight analysis from the CPACS file

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-11-21
| Last modifiction: 2019-08-29 (AJ)
"""


#=============================================================================
#   IMPORTS
#=============================================================================

from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.cpacsfunctions import open_tixi,open_tigl, close_tixi,    \
                                           add_uid, create_branch

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================

"""All classes are defined inside the classes folder and in the
   InputClasses/Unconventional folder."""


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


#=============================================================================

def get_user_inputs(ed, ui, adui, cpacs_in):
    """ Function to extract from the xml file the required input data,
        the code will use the default value when they are missing.

        INPUT
        (class) adui   --Arg.: AdvancedInputs class.
        (class) ed     --Arg.: EngineData class.
        (class) ui     --Arg.: UserInputs class.
        ##======= Classes are defined in the InputClasses folder =======##

        (char) cpacs_in  --Arg.: Relative location of the xml file in the
                                 ToolInput folder (cpacs option) or
                                 relative location of the temp. xml file in
                                 the ToolOutput folder (input option).
        OUTPUT
        (class) adui     --Out.: AdvancedInputs class updated
        (class) ui       --Out.: UserInputs class updated.
        (class) ed       --AOut.:EngineData class updated.
        (file) cpacs_in  --Out.: Updated cpasc file
    """

    log.info('Starting data extraction from CPACS file')
    # Path creation ==========================================================
    tixi = open_tixi(cpacs_in)
    # toolspecific
    CEASIOM_PATH = '/cpacs/toolspecific/CEASIOMpy'
    GEOM_PATH = CEASIOM_PATH + '/geometry'
    RANGE_PATH = CEASIOM_PATH + '/ranges'
    W_PATH = CEASIOM_PATH + '/weight'
    C_PATH = W_PATH + '/crew'
    PILOTS_PATH = C_PATH + '/pilots'
    CC_PATH = C_PATH + '/cabinCrewMembers'
    PASS_PATH = W_PATH + '/passengers'
    ML_PATH = W_PATH + '/massLimits'
    PROP_PATH = CEASIOM_PATH + '/propulsion'
    FUEL_PATH = '/cpacs/toolspecific/CEASIOMpy/fuels'

    create_branch(tixi, FUEL_PATH, False)
    create_branch(tixi, GEOM_PATH, False)
    create_branch(tixi, RANGE_PATH, False)
    create_branch(tixi, PILOTS_PATH, False)
    create_branch(tixi, CC_PATH, False)
    create_branch(tixi, PASS_PATH, False)
    create_branch(tixi, ML_PATH, False)
    create_branch(tixi, PROP_PATH, False)

    # cpacs/vehicles
    MC_PATH = '/cpacs/vehicles/aircraft/model/analyses/massBreakdown/'\
              + 'payload/mCargo/massDescription'
    F_PATH = '/cpacs/vehicles/fuels/fuel'

    create_branch(tixi, MC_PATH, False)
    create_branch(tixi, F_PATH, False)
    add_uid(tixi, F_PATH, 'kerosene')
    # Gathering data =========================================================
    # Geometry ===============================================================
    if not tixi.checkElement(GEOM_PATH + '/description'):
        tixi.createElement(GEOM_PATH, 'description')
        tixi.updateTextElement(GEOM_PATH + '/description', 'User '\
                               + 'geometry input')

    # Number of floors.
    if not tixi.checkElement(GEOM_PATH + '/floorsNb'):
        tixi.createElement(GEOM_PATH, 'floorsNb')
        tixi.updateDoubleElement(GEOM_PATH + '/floorsNb',\
                                 ui.FLOORS_NB, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_PATH + '/floorsNb')
        if temp != ui.FLOORS_NB and temp > 0:
            ui.FLOORS_NB = temp

    # Extracting fuselage material data.
    if not tixi.checkElement(GEOM_PATH + '/virtualThick'):
        tixi.createElement(GEOM_PATH, 'virtualThick')
        tixi.updateDoubleElement(GEOM_PATH + '/virtualThick',\
                                 adui.VRT_THICK, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_PATH + '/virtualThick')
        if temp != adui.VRT_THICK and temp > 0:
            adui.VRT_THICK = temp

    if not tixi.checkElement(GEOM_PATH + '/virtualDensity'):
        tixi.createElement(GEOM_PATH, 'virtualDensity')
        tixi.updateDoubleElement(GEOM_PATH + '/virtualDensity',\
                                 adui.VRT_STR_DENSITY, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_PATH + '/virtualDensity')
        if temp != adui.VRT_STR_DENSITY and temp > 0:
            adui.VRT_STR_DENSITY = temp

    if not tixi.checkElement(GEOM_PATH + '/cabinHeight'):
        tixi.createElement(GEOM_PATH, 'cabinHeight')
        tixi.updateDoubleElement(GEOM_PATH + '/cabinHeight',\
                                 ui.H_LIM_CABIN, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_PATH + '/cabinHeight')
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
    if not tixi.checkElement(CC_PATH + '/cabinCrewMemberMass'):
        tixi.createElement(CC_PATH, 'cabinCrewMemberMass')
        tixi.updateDoubleElement(CC_PATH + '/cabinCrewMemberMass',\
                                 adui.MASS_CABIN_CREW, '%g')
    else:
        temp = tixi.getDoubleElement(CC_PATH + '/cabinCrewMemberMass')
        if temp != adui.MASS_CABIN_CREW and temp > 0:
            adui.MASS_CABIN_CREW = temp

    # Passengers user input data
    if not tixi.checkElement(PASS_PATH + '/passMass'):
        tixi.createElement(PASS_PATH, 'passMass')
        tixi.updateDoubleElement(PASS_PATH + '/passMass',\
                                 adui.MASS_PASS, '%g')
    else:
        temp = tixi.getDoubleElement(PASS_PATH+ '/passMass')
        if temp != adui.MASS_PASS and temp > 0:
            adui.MASS_PASS = temp

    if tixi.checkElement(PASS_PATH + '/passNb'):
        temp = tixi.getIntegerElement(PASS_PATH+ '/passNb')
        if temp != ui.MAX_PASS and temp > 0:
            ui.MAX_PASS = temp

    if not tixi.checkElement(PASS_PATH + '/passDensity'):
        tixi.createElement(PASS_PATH, 'passDensity')
        tixi.updateDoubleElement(PASS_PATH + '/passDensity',\
                                 ui.PASS_BASE_DENSITY, '%i')
    else:
        temp = tixi.getDoubleElement(PASS_PATH + '/passDensity')
        if temp != ui.PASS_BASE_DENSITY and temp > 0:
            ui.PASS_BASE_DENSITY = temp

    if not tixi.checkElement(PASS_PATH + '/passPerToilet'):
        tixi.createElement(PASS_PATH, 'passPerToilet')
        tixi.updateIntegerElement(PASS_PATH + '/passPerToilet',\
                                 adui.PASS_PER_TOILET, '%i')
    else:
        temp = tixi.getIntegerElement(PASS_PATH + '/passPerToilet')
        if temp != adui.PASS_PER_TOILET and temp > 0:
            adui.PASS_PER_TOILET = temp

    # Fuel ===================================================================
    if not tixi.checkElement(F_PATH + '/density'):
        tixi.createElement(F_PATH, 'density')
        tixi.updateDoubleElement(F_PATH + '/density',\
                                 adui.FUEL_DENSITY, '%g')
    else:
        temp = tixi.getDoubleElement(F_PATH + '/density')
        if temp != adui.FUEL_DENSITY and temp > 0:
            adui.FUEL_DENSITY = temp

    if not tixi.checkElement(FUEL_PATH + '/resFuelPerc'):
        tixi.createElement(FUEL_PATH, 'resFuelPerc')
        tixi.updateDoubleElement(FUEL_PATH + '/resFuelPerc',\
                                 adui.RES_FUEL_PERC, '%g')
    else:
        temp = tixi.getDoubleElement(FUEL_PATH + '/resFuelPerc')
        if temp != adui.RES_FUEL_PERC and temp > 0:
            adui.RES_FUEL_PERC = temp

    # Weight =================================================================
    # Mass limits data
    if not tixi.checkElement(ML_PATH + '/description'):
        tixi.createElement(ML_PATH, 'description')
        tixi.updateTextElement(ML_PATH + '/description', 'Desired max fuel '\
                               + 'volume [m^3] and payload mass [kg]')
    if not tixi.checkElement(ML_PATH + '/maxPayload'):
        tixi.createElement(ML_PATH, 'maxPayload')
        tixi.updateDoubleElement(ML_PATH + '/maxPayload',\
                                 ui.MAX_PAYLOAD, '%g')
    else:
        temp = tixi.getDoubleElement(ML_PATH + '/maxPayload')
        if temp != ui.MAX_PAYLOAD and temp != 0:
            ui.MAX_PAYLOAD = temp
    if not tixi.checkElement(ML_PATH + '/maxFuelVol'):
        tixi.createElement(ML_PATH, 'maxFuelVol')
        tixi.updateDoubleElement(ML_PATH + '/maxFuelVol',\
                                 ui.MAX_FUEL_VOL, '%g')
    else:
        temp = tixi.getDoubleElement(ML_PATH + '/maxFuelVol')
        if temp != ui.MAX_FUEL_VOL and temp != 0:
            ui.MAX_FUEL_VOL = temp

    if tixi.checkElement(MC_PATH + '/massCargo'):
        temp = tixi.getDoubleElement(MC_PATH + '/massCargo')
        if temp != ui.MASS_CARGO and temp != 0:
            ui.MASS_CARGO = temp
        # If the cargo mass is defined in the UserInputs class will be added
        # in the CPACS file after the analysis.

    # Flight =================================================================
    if not tixi.checkElement(RANGE_PATH + '/lDRatio'):
        tixi.createElement(RANGE_PATH, 'lDRatio')
        tixi.updateDoubleElement(RANGE_PATH + '/lDRatio',\
                                  ui.LD, '%g')
    else:
        temp = tixi.getIntegerElement(RANGE_PATH + '/lDRatio')
        if temp != ui.LD and temp > 0:
            ui.LD = temp

    if not tixi.checkElement(RANGE_PATH + '/cruiseSpeed'):
        tixi.createElement(RANGE_PATH, 'cruiseSpeed')
        tixi.updateDoubleElement(RANGE_PATH + '/cruiseSpeed',\
                                 ui.CRUISE_SPEED, '%g')
    else:
        temp = tixi.getIntegerElement(RANGE_PATH + '/cruiseSpeed')
        if temp != ui.CRUISE_SPEED and temp > 0:
            ui.CRUISE_SPEED = temp

    TSFC_PATH = PROP_PATH + '/tSFC'
    create_branch(tixi, TSFC_PATH, False)
    if not tixi.checkElement(TSFC_PATH + '/tsfcCruise'):
        tixi.createElement(TSFC_PATH, 'tsfcCruise')
        tixi.updateDoubleElement(TSFC_PATH + '/tsfcCruise',\
                                 ed.TSFC_CRUISE, '%g')
    else:
        temp = tixi.getDoubleElement(TSFC_PATH + '/tsfcCruise')
        if temp != ed.TSFC_CRUISE and temp > 0:
            ed.TSFC_CRUISE = temp

    if not tixi.checkElement(PROP_PATH + '/userEngineOption'):
        tixi.createElement(PROP_PATH, 'userEngineOption')
        if ui.USER_ENGINES:
            tixi.updateTextElement(PROP_PATH + '/userEngineOption', 'True')
        else:
            tixi.updateTextElement(PROP_PATH + '/userEngineOption', 'False')
    else:
        temp = tixi.getTextElement(PROP_PATH + '/userEngineOption')
        if temp == 'False':
            ui.USER_ENGINES = False
        else:
            ui.USER_ENGINES = True

    if not tixi.checkElement(PROP_PATH + '/singleHydraulics'):
        tixi.createElement(PROP_PATH, 'singleHydraulics')
        if adui.SINGLE_HYDRAULICS:
            tixi.updateTextElement(PROP_PATH + '/singleHydraulics', 'True')
        else:
            tixi.updateTextElement(PROP_PATH + '/singleHydraulics', 'False')
    else:
        temp = tixi.getTextElement(PROP_PATH + '/singleHydraulics')
        if temp == 'False':
            adui.SINGLE_HYDRAULICS = False
        else:
            adui.SINGLE_HYDRAULICS = True

    log.info('Data from CPACS file succesfully extracted')

    # Saving and closing the cpacs file --------------------------------------
    tixi.saveDocument(cpacs_in)
    close_tixi(tixi, cpacs_in)

    # Openign and closing again the cpacs file -------------------------------
    tixi = open_tixi(cpacs_in)
    tigl = open_tigl(tixi)
    tixi.saveDocument(cpacs_in)
    close_tixi(tixi, cpacs_in)

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

    # Path creation ==========================================================
    tixi = open_tixi(cpacs_in)
    CEASIOM_PATH = '/cpacs/toolspecific/CEASIOMpy'

    PROP_PATH = CEASIOM_PATH + '/propulsion'
    create_branch(tixi, PROP_PATH, False)
    # Propulsion =============================================================
    if not tixi.checkElement(PROP_PATH + '/turboprop'):
        create_branch(tixi, PROP_PATH, False)
        tixi.createElement(PROP_PATH, 'turboprop')
        if ed.TURBOPROP:
            tixi.updateTextElement(PROP_PATH + '/turboprop', 'True')
        else:
            tixi.updateTextElement(PROP_PATH + '/turboprop', 'False')
    else:
        temp = tixi.getTextElement(PROP_PATH + '/turboprop')
        if temp == 'False':
            ed.TURBOPROP = False
        else:
            ed.TURBOPROP = True
    if not tixi.checkElement(PROP_PATH + '/auxiliaryPowerUnit'):
        tixi.createElement(PROP_PATH, 'auxiliaryPowerUnit')
        if ed.APU:
            tixi.updateTextElement(PROP_PATH + '/auxiliaryPowerUnit', 'True')
        else:
            tixi.updateTextElement(PROP_PATH + '/auxiliaryPowerUnit', 'False')
    else:
        temp = tixi.getTextElement(PROP_PATH + '/auxiliaryPowerUnit')
        if temp == 'False':
            ed.APU = False
        else:
            ed.APU = True
    if not tixi.checkElement(PROP_PATH + '/engineNumber'):
        tixi.createElement(PROP_PATH, 'engineNumber')
        tixi.updateIntegerElement(PROP_PATH + '/engineNumber', ed.NE, '%i')
    else:
        ed.NE = tixi.getIntegerElement(PROP_PATH + '/engineNumber')

    #Engines
    mp = []
    tp = []
    EN_PATH = '/cpacs/vehicles/engines'
    if tixi.checkElement(EN_PATH):
        for e in range(0,ed.NE-1):
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
                tixi.createElement(EN_PATH, 'name')
                tixi.updateTextElement(EN_PATH + '/name', ed.EN_NAME[e])
            else:
                if e > len(ed.EN_NAME):
                    ed.EN_NAME.append(tixi.getTextElement(EN_PATH + '/name'))
            ENA_PATH = EN_PATH + '/analysis/mass'
            if tixi.checkElement(ENA_PATH + '/mass'):
                ed.en_mass = tixi.getDoubleElement(ENA_PATH + '/mass')
                mp.append(ed.en_mass)
                if e>0 and ed.en_mass != mp[e-1]:
                    raise Exception('The engines have different masses, this'\
                                    + ' can lead to an unbalanced aircraft')
            elif ed.en_mass:
                tixi.createElement(ENA_PATH, 'mass')
                tixi.updateDoubleElement(ENA_PATH + '/mass', ed.en_mass, '%g')
            else:
                raise Exception('Engine definition inclomplete, missing'\
                                + ' engine mass in the cpacs file')
            ENT_PATH = EN_PATH + '/analysis'
            if tixi.checkElement(ENT_PATH + '/thrust00'):
                ed.max_thrust = tixi.getDoubleElement(ENT_PATH + '/thrust00')
                tp.append(ed.max_thrust)
                if e>0 and ed.max_thrust != tp[e-1]:
                    raise Exception('The engines have different thrust, this')
                                    #+ ' can lead to an unbalanced flight')
            elif ed.max_thrust:
                tixi.createElement(ENT_PATH, 'thrust00')
                tixi.updateDoubleElement(ENT_PATH + '/thrust00',
                                         ed.max_thrust, '%g')
            else:
                raise Exception('Engine definition inclomplete, missing'\
                                + ' engine thrust in the cpacs file')
    log.info('Data from CPACS file succesfully extracted')

    # Saving and closing the cpacs file --------------------------------------
    tixi.saveDocument(cpacs_in)
    close_tixi(tixi, cpacs_in)

    # Openign and closing again the cpacs file -------------------------------
    tixi = open_tixi(cpacs_in)
    tigl = open_tigl(tixi)
    tixi.saveDocument(cpacs_in)
    close_tixi(tixi, cpacs_in)

    return(ed)


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('########################################################')
    log.warning('# ERROR NOT A STANDALONE PROGRAM, RUN weightuncmain.py #')
    log.warning('########################################################')
