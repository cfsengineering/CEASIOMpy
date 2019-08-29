"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script saves the input value required for the weight analysis,
obtaining them from the CPACS file or from user input in the
ceasiompy.Input_class/conventional/weight_user_input.py script.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-11-21
| Last modifiction: 2019-08-29 (AJ)
"""


#=============================================================================
#   IMPORTS
#=============================================================================

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils import cpacsfunctions as cpf
from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                           add_uid, create_branch

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

def get_user_inputs(ind, ui, ag, cpacs_in, cpacs):
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
    CESAIOM_PATH = '/cpacs/toolspecific/CEASIOMpy'
    GEOM_PATH = CESAIOM_PATH + '/geometry'
    FUEL_PATH = CESAIOM_PATH + '/fuels'
    W_PATH = CESAIOM_PATH + '/weight'
    C_PATH = W_PATH + '/crew'
    pilots_path = C_PATH + '/pilots'
    CC_PATH = C_PATH + '/cabinCrewMembers'
    PASS_PATH = W_PATH + '/passengers'
    ML_PATH = W_PATH + '/massLimits'
    PROP_PATH = CESAIOM_PATH + '/propulsion'
    F_PATH = '/cpacs/vehicles/fuels/fuel'
    MC_PATH = '/cpacs/vehicles/aircraft/model/analyses/massBreakdown/'\
              + 'payload/mCargo/massDescription'

    create_branch(tixi, MC_PATH, False)
    create_branch(tixi, FUEL_PATH, False)
    create_branch(tixi, GEOM_PATH, False)
    create_branch(tixi, pilots_path, False)
    create_branch(tixi, CC_PATH, False)
    create_branch(tixi, PASS_PATH, False)
    create_branch(tixi, ML_PATH, False)
    create_branch(tixi, PROP_PATH, False)
    create_branch(tixi, F_PATH, False)

    add_uid(tixi, F_PATH, 'kerosene')
    ### Geometry =============================================================
    if not tixi.checkElement(GEOM_PATH + '/description'):
        tixi.createElement(GEOM_PATH, 'description')
        tixi.updateTextElement(GEOM_PATH + '/description', 'User '\
                               + 'geometry input')
    # Extracting geometry input data (Double Floor)
    if not tixi.checkElement(GEOM_PATH + '/isDoubleFloor'):
        tixi.createElement(GEOM_PATH, 'isDoubleFloor')
        tixi.updateIntegerElement(GEOM_PATH + '/isDoubleFloor',\
                                 ui.IS_DOUBLE_FLOOR, '%i')
    else:
        temp = tixi.getIntegerElement(GEOM_PATH + '/isDoubleFloor')
        if temp != ui.IS_DOUBLE_FLOOR:
            ui.IS_DOUBLE_FLOOR = temp
    # Extracting geometry input data (seatWidth)
    if not tixi.checkElement(GEOM_PATH + '/seatWidth'):
        tixi.createElement(GEOM_PATH, 'seatWidth')
        tixi.updateDoubleElement(GEOM_PATH + '/seatWidth',\
                                 ind.seat_width, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_PATH + '/seatWidth')
        if temp != ind.seat_width and temp > 0:
            ind.seat_width = temp
    # Extracting geometry input data (seatLength)
    if not tixi.checkElement(GEOM_PATH + '/seatLength'):
        tixi.createElement(GEOM_PATH, 'seatLength')
        tixi.updateDoubleElement(GEOM_PATH + '/seatLength',\
                                 ind.seat_length, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_PATH + '/seatLength')
        if temp != ind.seat_length and temp > 0:
            ind.seat_length = temp
    # Extracting geometry input data (aisleWidth)
    if not tixi.checkElement(GEOM_PATH + '/aisleWidth'):
        tixi.createElement(GEOM_PATH, 'aisleWidth')
        tixi.updateDoubleElement(GEOM_PATH + '/aisleWidth',\
                                 ind.aisle_width, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_PATH + '/aisleWidth')
        if temp != ind.aisle_width and temp > 0:
            ind.aisle_width = temp
    # Extracting geometry input data (fuseThick)
    if not tixi.checkElement(GEOM_PATH + '/fuseThick'):
        tixi.createElement(GEOM_PATH, 'fuseThick')
        tixi.updateDoubleElement(GEOM_PATH + '/fuseThick',\
                                 ind.fuse_thick, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_PATH + '/fuseThick')
        if temp != ind.fuse_thick and temp > 0:
            ind.fuse_thick = temp
    # Extracting geometry input data (toiletLength)
    if not tixi.checkElement(GEOM_PATH + '/toiletLength'):
        tixi.createElement(GEOM_PATH, 'toiletLength')
        tixi.updateDoubleElement(GEOM_PATH + '/toiletLength',\
                                 ind.toilet_length, '%g')
    else:
        temp = tixi.getDoubleElement(GEOM_PATH + '/toiletLength')
        if temp != ind.toilet_length and temp > 0:
            ind.toilet_length = temp

    ### Weight ===============================================================
    # Pilots user input data
    if not tixi.checkElement(pilots_path + '/pilotNb'):
        tixi.createElement(pilots_path, 'pilotNb')
        tixi.updateIntegerElement(pilots_path + '/pilotNb',\
                                 ui.PILOT_NB, '%i')
    else:
        temp = tixi.getIntegerElement(pilots_path + '/pilotNb')
        if temp != ui.PILOT_NB and temp > 0:
            ui.PILOT_NB = temp
    if not tixi.checkElement(pilots_path + '/pilotMass'):
        tixi.createElement(pilots_path, 'pilotMass')
        tixi.updateDoubleElement(pilots_path + '/pilotMass',\
                                 ui.MASS_PILOT, '%g')
    else:
        temp = tixi.getDoubleElement(pilots_path + '/pilotMass')
        if temp != ui.MASS_PILOT and temp > 0:
            ui.MASS_PILOT = temp

    # Cabin crew user input data
    if not tixi.checkElement(CC_PATH + '/cabinCrewMemberMass'):
        tixi.createElement(CC_PATH, 'cabinCrewMemberMass')
        tixi.updateDoubleElement(CC_PATH + '/cabinCrewMemberMass',\
                                 ui.MASS_CABIN_CREW, '%g')
    else:
        temp = tixi.getDoubleElement(CC_PATH + '/cabinCrewMemberMass')
        if temp != ui.MASS_CABIN_CREW and temp > 0:
            ui.MASS_CABIN_CREW = temp

    # Passengers user input data
    if not tixi.checkElement(PASS_PATH + '/passMass'):
        tixi.createElement(PASS_PATH, 'passMass')
        tixi.updateDoubleElement(PASS_PATH + '/passMass',\
                                 ui.MASS_PASS, '%g')
    else:
        temp = tixi.getDoubleElement(PASS_PATH+ '/passMass')
        if temp != ui.MASS_PASS and temp > 0:
            ui.MASS_PASS = temp

    if not tixi.checkElement(PASS_PATH + '/passPerToilet'):
        tixi.createElement(PASS_PATH, 'passPerToilet')
        tixi.updateIntegerElement(PASS_PATH + '/passPerToilet',\
                                 ui.PASS_PER_TOILET, '%i')
    else:
        temp = tixi.getIntegerElement(PASS_PATH + '/passPerToilet')
        if temp != ui.PASS_PER_TOILET and temp > 0:
            ui.PASS_PER_TOILET = temp

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
        if temp != ui.MAX_PAYLOAD and temp > 0:
            ui.MAX_PAYLOAD = temp
    if not tixi.checkElement(ML_PATH + '/maxFuelVol'):
        tixi.createElement(ML_PATH, 'maxFuelVol')
        tixi.updateDoubleElement(ML_PATH + '/maxFuelVol',\
                                 ui.MAX_FUEL_VOL, '%g')
    else:
        temp = tixi.getDoubleElement(ML_PATH + '/maxFuelVol')
        if temp != ui.MAX_FUEL_VOL and temp > 0:
            ui.MAX_FUEL_VOL = temp

    if tixi.checkElement(MC_PATH + '/massCargo'):
        temp = tixi.getDoubleElement(MC_PATH + '/massCargo')
        if temp != ui.MASS_CARGO and temp != 0:
            ui.MASS_CARGO = temp

    # Fuel density ===========================================================

    if not tixi.checkElement(F_PATH + '/density'):
        tixi.createElement(F_PATH, 'density')
        tixi.updateDoubleElement(F_PATH + '/density',\
                                 ui.FUEL_DENSITY, '%g')
    else:
        temp = tixi.getDoubleElement(F_PATH + '/density')
        if temp != ui.FUEL_DENSITY and temp > 0:
            ui.FUEL_DENSITY = temp

    # Propulsion =============================================================
    if not tixi.checkElement(PROP_PATH + '/turboprop'):
        create_branch(tixi, PROP_PATH, False)
        tixi.createElement(PROP_PATH, 'turboprop')
        if ui.TURBOPROP:
            tixi.updateTextElement(PROP_PATH + '/turboprop', 'True')
        else:
            tixi.updateTextElement(PROP_PATH + '/turboprop', 'False')
    else:
        temp = tixi.getTextElement(PROP_PATH + '/turboprop')
        if temp == 'False':
            ui.TURBOPROP = False
        else:
            ui.TURBOPROP = True

    if not tixi.checkElement(FUEL_PATH + '/resFuelPerc'):
        tixi.createElement(FUEL_PATH, 'resFuelPerc')
        tixi.updateDoubleElement(FUEL_PATH + '/resFuelPerc',\
                                 ui.RES_FUEL_PERC, '%g')
    else:
        temp = tixi.getDoubleElement(FUEL_PATH + '/resFuelPerc')
        if temp != ui.RES_FUEL_PERC and temp > 0:
            ui.RES_FUEL_PERC = temp

    log.info('Data from CPACS file succesfully extracted')

    # Saving and closing the cpacs file --------------------------------------
    tixi.saveDocument(cpacs_in)
    close_tixi(tixi, cpacs_in)

    # Openign and closing again the cpacs file -------------------------------
    tixi = open_tixi(cpacs_in)
    tigl = open_tigl(tixi)
    tixi.saveDocument(cpacs_in)
    close_tixi(tixi, cpacs_in)

    return(ind, ui)


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('###########################################################')
    log.warning('#### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ####')
    log.warning('###########################################################')
