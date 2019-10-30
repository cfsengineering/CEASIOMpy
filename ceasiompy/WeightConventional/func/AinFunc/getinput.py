# TODO: This scipt will be remove, now integrated with weightconvclass.py

""""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script saves the input value required for the weight analysis,
obtaining them from the CPACS file or from user input in the
ceasiompy.Input_class/conventional/weight_user_input.py script.

| Works with Python 3.6
| Author : Stefano Piccini
| Date of creation: 2018-11-21
| Last modifiction: 2019-10-29 (AJ)
"""


#=============================================================================
#   IMPORTS
#=============================================================================

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils import cpacsfunctions as cpf
from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                           add_uid, create_branch, get_value_or_default

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================

"""
 InsideDimensions class, can be found on the InputClasses folder inside the
 weightconvclass.py script.
"""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def get_user_inputs(ind, ui, ag, cpacs_in):
    """ The function to extracts from the XML file the required input data,
        the code will use the default value when they are missing.

        INPUT
        (class) ind  --Arg.: InsideDimensions class.
        (class) ui   --Arg.: UserInputs class.
        ##======= Classes are defined in the InputClasses folder =======##

        (class) ag   --Arg.: AircraftGeometry class
        ##=======  Classes are defined in the InputClasses folder ======##

        (char) cpacs_in  --Arg.: Relative location of the xml file in the
                                 ToolInput folder (cpacs option) or
                                 relative location of the temp. xml file in
                                 the ToolOutput folder (input option).
        (char) cpacs       --Arg.: cpacs True or False option

        OUTPUT
        (class) ind  --Out.: InsideDimensions class updated
        (class) ui   --Out.: UserInputs class updated.
        ##======  Classes are defined in the InputClasses folder ======##

        (file) cpacs_in  --Out.: Updated cpasc file
    """

    log.info('Starting data extraction from CPACS file')

    # Path creation ==========================================================
    tixi = open_tixi(cpacs_in)

    CESAIOM_XPATH = '/cpacs/toolspecific/CEASIOMpy'
    GEOM_XPATH = CESAIOM_XPATH + '/geometry'
    FUEL_XPATH = CESAIOM_XPATH + '/fuels'
    W_XPATH = CESAIOM_XPATH + '/weight'
    C_XPATH = W_XPATH + '/crew'
    pilots_xpath = C_XPATH + '/pilots'
    CC_XPATH = C_XPATH + '/cabinCrewMembers'
    PASS_XPATH = W_XPATH + '/passengers'
    ML_XPATH = W_XPATH + '/massLimits'
    PROP_XPATH = CESAIOM_XPATH + '/propulsion'
    F_XPATH = '/cpacs/vehicles/fuels/fuel'
    MC_XPATH = '/cpacs/vehicles/aircraft/model/analyses/massBreakdown/'\
              + 'payload/mCargo/massDescription'

    create_branch(tixi, MC_XPATH, False)
    create_branch(tixi, FUEL_XPATH, False)
    create_branch(tixi, GEOM_XPATH, False)
    create_branch(tixi, pilots_xpath, False)
    create_branch(tixi, CC_XPATH, False)
    create_branch(tixi, PASS_XPATH, False)
    create_branch(tixi, ML_XPATH, False)
    create_branch(tixi, PROP_XPATH, False)
    create_branch(tixi, F_XPATH, False)

    add_uid(tixi, F_XPATH, 'kerosene')
    ### Geometry =============================================================
    if not tixi.checkElement(GEOM_XPATH + '/description'):
        tixi.createElement(GEOM_XPATH, 'description')
        tixi.updateTextElement(GEOM_XPATH + '/description', 'User '\
                               + 'geometry input')

    # Extracting geometry input data (Double Floor)
    ui.IS_DOUBLE_FLOOR = get_value_or_default(tixi,GEOM_XPATH + '/isDoubleFloor',ui.IS_DOUBLE_FLOOR)


    # if not tixi.checkElement(GEOM_XPATH + '/isDoubleFloor'):
    #     tixi.createElement(GEOM_XPATH, 'isDoubleFloor')
    #     tixi.updateIntegerElement(GEOM_XPATH + '/isDoubleFloor',\
    #                              ui.IS_DOUBLE_FLOOR, '%i')
    # else:
    #     temp = tixi.getIntegerElement(GEOM_XPATH + '/isDoubleFloor')
    #     if temp != ui.IS_DOUBLE_FLOOR:
    #         ui.IS_DOUBLE_FLOOR = temp

    # Extracting geometry input data (seatWidth)
    if not tixi.checkElement(GEOM_XPATH + '/seatWidth'):
        tixi.createElement(GEOM_XPATH, 'seatWidth')
        tixi.updateDoubleElement(GEOM_XPATH + '/seatWidth',\
                                 ind.seat_width, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_XPATH + '/seatWidth')
        if temp != ind.seat_width and temp > 0:
            ind.seat_width = temp
    # Extracting geometry input data (seatLength)
    if not tixi.checkElement(GEOM_XPATH + '/seatLength'):
        tixi.createElement(GEOM_XPATH, 'seatLength')
        tixi.updateDoubleElement(GEOM_XPATH + '/seatLength',\
                                 ind.seat_length, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_XPATH + '/seatLength')
        if temp != ind.seat_length and temp > 0:
            ind.seat_length = temp
    # Extracting geometry input data (aisleWidth)
    if not tixi.checkElement(GEOM_XPATH + '/aisleWidth'):
        tixi.createElement(GEOM_XPATH, 'aisleWidth')
        tixi.updateDoubleElement(GEOM_XPATH + '/aisleWidth',\
                                 ind.aisle_width, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_XPATH + '/aisleWidth')
        if temp != ind.aisle_width and temp > 0:
            ind.aisle_width = temp
    # Extracting geometry input data (fuseThick)
    if not tixi.checkElement(GEOM_XPATH + '/fuseThick'):
        tixi.createElement(GEOM_XPATH, 'fuseThick')
        tixi.updateDoubleElement(GEOM_XPATH + '/fuseThick',\
                                 ind.fuse_thick, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_XPATH + '/fuseThick')
        if temp != ind.fuse_thick and temp > 0:
            ind.fuse_thick = temp
    # Extracting geometry input data (toiletLength)
    if not tixi.checkElement(GEOM_XPATH + '/toiletLength'):
        tixi.createElement(GEOM_XPATH, 'toiletLength')
        tixi.updateDoubleElement(GEOM_XPATH + '/toiletLength',\
                                 ind.toilet_length, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_XPATH + '/toiletLength')
        if temp != ind.toilet_length and temp > 0:
            ind.toilet_length = temp

    ### Weight ===============================================================
    # Pilots user input data
    if not tixi.checkElement(pilots_xpath + '/pilotNb'):
        tixi.createElement(pilots_xpath, 'pilotNb')
        tixi.updateIntegerElement(pilots_xpath + '/pilotNb',\
                                 ui.PILOT_NB, '%i')
    else:
        temp = tixi.getIntegerElement(pilots_xpath + '/pilotNb')
        if temp != ui.PILOT_NB and temp > 0:
            ui.PILOT_NB = temp
    if not tixi.checkElement(pilots_xpath + '/pilotMass'):
        tixi.createElement(pilots_xpath, 'pilotMass')
        tixi.updateDoubleElement(pilots_xpath + '/pilotMass',\
                                 ui.MASS_PILOT, '%g')
    else:
        temp = tixi.getDoubleElement(pilots_xpath + '/pilotMass')
        if temp != ui.MASS_PILOT and temp > 0:
            ui.MASS_PILOT = temp

    # Cabin crew user input data
    if not tixi.checkElement(CC_XPATH + '/cabinCrewMemberMass'):
        tixi.createElement(CC_XPATH, 'cabinCrewMemberMass')
        tixi.updateDoubleElement(CC_XPATH + '/cabinCrewMemberMass',\
                                 ui.MASS_CABIN_CREW, '%g')
    else:
        temp = tixi.getDoubleElement(CC_XPATH + '/cabinCrewMemberMass')
        if temp != ui.MASS_CABIN_CREW and temp > 0:
            ui.MASS_CABIN_CREW = temp

    # Passengers user input data
    if not tixi.checkElement(PASS_XPATH + '/passMass'):
        tixi.createElement(PASS_XPATH, 'passMass')
        tixi.updateDoubleElement(PASS_XPATH + '/passMass',\
                                 ui.MASS_PASS, '%g')
    else:
        temp = tixi.getDoubleElement(PASS_XPATH+ '/passMass')
        if temp != ui.MASS_PASS and temp > 0:
            ui.MASS_PASS = temp

    if not tixi.checkElement(PASS_XPATH + '/passPerToilet'):
        tixi.createElement(PASS_XPATH, 'passPerToilet')
        tixi.updateIntegerElement(PASS_XPATH + '/passPerToilet',\
                                 ui.PASS_PER_TOILET, '%i')
    else:
        temp = tixi.getIntegerElement(PASS_XPATH + '/passPerToilet')
        if temp != ui.PASS_PER_TOILET and temp > 0:
            ui.PASS_PER_TOILET = temp

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
        if temp != ui.MAX_PAYLOAD and temp > 0:
            ui.MAX_PAYLOAD = temp
    if not tixi.checkElement(ML_XPATH + '/maxFuelVol'):
        tixi.createElement(ML_XPATH, 'maxFuelVol')
        tixi.updateDoubleElement(ML_XPATH + '/maxFuelVol',\
                                 ui.MAX_FUEL_VOL, '%g')
    else:
        temp = tixi.getDoubleElement(ML_XPATH + '/maxFuelVol')
        if temp != ui.MAX_FUEL_VOL and temp > 0:
            ui.MAX_FUEL_VOL = temp

    if tixi.checkElement(MC_XPATH + '/massCargo'):
        temp = tixi.getDoubleElement(MC_XPATH + '/massCargo')
        if temp != ui.MASS_CARGO and temp != 0:
            ui.MASS_CARGO = temp

    # Fuel density ===========================================================

    if not tixi.checkElement(F_XPATH + '/density'):
        tixi.createElement(F_XPATH, 'density')
        tixi.updateDoubleElement(F_XPATH + '/density',\
                                 ui.FUEL_DENSITY, '%g')
    else:
        temp = tixi.getDoubleElement(F_XPATH + '/density')
        if temp != ui.FUEL_DENSITY and temp > 0:
            ui.FUEL_DENSITY = temp

    # Propulsion =============================================================
    if not tixi.checkElement(PROP_XPATH + '/turboprop'):
        create_branch(tixi, PROP_XPATH, False)
        tixi.createElement(PROP_XPATH, 'turboprop')
        if ui.TURBOPROP:
            tixi.updateTextElement(PROP_XPATH + '/turboprop', 'True')
        else:
            tixi.updateTextElement(PROP_XPATH + '/turboprop', 'False')
    else:
        temp = tixi.getTextElement(PROP_XPATH + '/turboprop')
        if temp == 'False':
            ui.TURBOPROP = False
        else:
            ui.TURBOPROP = True

    if not tixi.checkElement(FUEL_XPATH + '/resFuelPerc'):
        tixi.createElement(FUEL_XPATH, 'resFuelPerc')
        tixi.updateDoubleElement(FUEL_XPATH + '/resFuelPerc',\
                                 ui.RES_FUEL_PERC, '%g')
    else:
        temp = tixi.getDoubleElement(FUEL_XPATH + '/resFuelPerc')
        if temp != ui.RES_FUEL_PERC and temp > 0:
            ui.RES_FUEL_PERC = temp

    log.info('Data from CPACS file succesfully extracted')

    close_tixi(tixi, cpacs_in)

    return(ind, ui)


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('###########################################################')
    log.warning('#### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ####')
    log.warning('###########################################################')
