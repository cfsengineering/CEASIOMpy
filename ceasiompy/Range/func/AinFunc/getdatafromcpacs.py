"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

This programm will read the xml file created by the weight module or
the xml file in the cpacs file saved in the ToolInput folder.

The cpacs file MUST contain:

* cabin_crew_nb          --In.: Number of cabin crew members [-].
* maximum_take_off_mass  --In.: Maximum take off mass [kg].
* mass_fuel_max          --In.: Maximum fuel mass [kg].
* mass_fuel_maxpass      --In.: Maximum fuel with max passengers [kg].
* operating_empty_mass   --In.: Operating empty mass [kg].
* mass_payload           --In.: Payload mass [kg].

The cpacs file should also contain:

* pilot_nb       --In.: Number of pilots [-].
* TSFC_CRUISE    --In.: Thrust specific fuel consumption on cruise [1/hr].
* TSFC_TLOITER   --In.: Thrust specific fuel consumption on loiter [1/hr].
* WINGLET        --In.: Winglet option (0 = no winglets, 1 = normale
                            winglets, 2 = high efficiency
                            winglet for cruise).
* TURBOPROP      --In.: Turboprop option ('True', 'False').
* CRUISE_SPEED   --In.: Cruise speed [m/s].
* LOITER_TIME    --In.: Loiter duration [min].
* LD             --In.: Lift over drag voefficient [-].
* MASS_PILOT     --In.: Pilot mass [kg].
* MASS_PASS      --In.: Passenger mass [kg].
* FUEL_DENSITY   --In.: Fuel density [kg/m^3].
* RES_FUEL_PERC  --In.: Unusable fuel percentage [-].
* MASS_CABIN_CREW  --In.: Mass of a cabin crew member [kg].

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-09-27
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

"""All classes are defined inside the classes folder in the
   range_output_class script and into the Input_classes/Conventional
   folder inside the range_user_input.py script."""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def get_data(mw, ri, cpacs_in):
    """ The function extracts from the xml file the required input data,
        the code will use the default value when they are missing.

        INPUT
        (class) mw       --Arg.: MassesWeight class updated
        (class) ri       --Arg.: RangeInput class updated
        ##======= Classes are defined in the Input_classes folder =======##

        (char) opt       --Arg.: Cpacs or input option
        (char) cpacs_in  --Arg.: Relative location of the xml file in the
                                 ToolInput folder (cpacs option) or
                                 relative location of the temp. xml file in
                                 the ToolOutput folder (input option).

        OUTPUT
        (class) mw       --Out.: MassesWeight class updated.
        (class) ri       --Out.: RangeInput class updated.
        (file) cpacs_in  --Out.: Updated cpasc file.
    """
    log.info('CPACS file path check')

    # path definition ========================================================
    # Opening CPACS file
    tixi = open_tixi(cpacs_in)

    TSPEC_PATH = '/cpacs/toolspecific/CEASIOMpy'
    W_PATH = TSPEC_PATH + '/weight'
    C_PATH = W_PATH + '/crew'
    P_PATH = C_PATH + '/pilots'
    CC_PATH = C_PATH + '/cabinCrewMembers'
    PASS_PATH = W_PATH + '/passengers'
    FMP_PATH = PASS_PATH + '/fuelMassMaxpass/mass'
    PROP_PATH = TSPEC_PATH + '/propulsion'
    RANGE_PATH = TSPEC_PATH + '/ranges'

    MASS_PATH = '/cpacs/vehicles/aircraft/model/analyses/massBreakdown'
    DM_PATH = MASS_PATH + '/designMasses'
    MTOM_PATH = DM_PATH + '/mTOM/mass'
    F_PATH = MASS_PATH + '/fuel/massDescription/mass'
    OEM_PATH = MASS_PATH + '/mOEM/massDescription/mass'
    PAY_PATH = MASS_PATH + '/payload/massDescription/mass'

    F1_PATH = '/cpacs/vehicles/fuels/fuel'
    F2_PATH = TSPEC_PATH + '/fuels'

    TSFC_PATH = PROP_PATH + '/tSFC'
    create_branch(tixi, TSFC_PATH, False)
    create_branch(tixi, RANGE_PATH, False)
    create_branch(tixi, P_PATH, False)
    create_branch(tixi, F1_PATH, False)
    create_branch(tixi, F2_PATH, False)
    add_uid(tixi, F1_PATH, 'kerosene')

    # Compulsory path checks =================================================

    if not tixi.checkElement(TSPEC_PATH):
        raise Exception('Missing required toolspecific path. Run '\
                        + 'Weight_main.py, in the 1Weight_module folder.')
    elif not tixi.checkElement(CC_PATH + '/cabinCrewMemberNb'):
        raise Exception('Missing required cabinCrewMemberNb path. Run '\
                        + 'Weight_main.py, in the 1Weight_module folder.')
    elif not tixi.checkElement(MASS_PATH):
        raise Exception('Missing required massBreakdown path. Run '\
                        + 'Weight_main.py, in the 1Weight_module folder.')
    elif not tixi.checkElement(DM_PATH):
        raise Exception('Missing required designMasses path. Run '\
                        + 'Weight_main.py, in the 1Weight_module folder.')
    elif not tixi.checkElement(MTOM_PATH):
        raise Exception('Missing required mTOM/mass path. Run '\
                        + 'Weight_main.py, in the 1Weight_module folder.')
    elif not tixi.checkElement(F_PATH):
        raise Exception('Missing required fuel/massDescription/mass '\
                        + 'path. Run '\
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
    else:
        log.info('All path correctly defined in the toolinput.xml file, '\
                 + 'beginning data extracction.')

    # Gathering data =========================================================
    ## TOOLSPECIFIC ----------------------------------------------------------
    if not tixi.checkElement(RANGE_PATH + '/lDRatio'):
        tixi.createElement(RANGE_PATH, 'lDRatio')
        tixi.updateDoubleElement(RANGE_PATH + '/lDRatio',\
                                  ri.LD, '%g')
    else:
        temp = tixi.getIntegerElement(RANGE_PATH + '/lDRatio')
        if temp != ri.LD and temp > 0:
            ri.LD = temp

    if not tixi.checkElement(RANGE_PATH + '/cruiseSpeed'):
        tixi.createElement(RANGE_PATH, 'cruiseSpeed')
        tixi.updateDoubleElement(RANGE_PATH + '/cruiseSpeed',\
                                  ri.CRUISE_SPEED, '%g')
    else:
        temp = tixi.getIntegerElement(RANGE_PATH + '/cruiseSpeed')
        if temp != ri.CRUISE_SPEED and temp > 0:
            ri.CRUISE_SPEED = temp

    if not tixi.checkElement(RANGE_PATH + '/loiterTime'):
        tixi.createElement(RANGE_PATH, 'loiterTime')
        tixi.updateDoubleElement(RANGE_PATH + '/loiterTime',\
                                  ri.LOITER_TIME, '%g')
    else:
        temp = tixi.getIntegerElement(RANGE_PATH + '/loiterTime')
        if temp != ri.LOITER_TIME and temp > 0:
            ri.LOITER_TIME = temp

    if not tixi.checkElement(TSPEC_PATH + '/geometry/winglet'):
        tixi.createElement(TSPEC_PATH + '/geometry', 'winglet')
        tixi.updateIntegerElement(TSPEC_PATH + '/geometry/winglet',\
                                  ri.WINGLET, '%i')
    else:
        temp = tixi.getIntegerElement(TSPEC_PATH + '/geometry/winglet')
        if temp != ri.WINGLET:
            ri.WINGLET = temp

    if not tixi.checkElement(P_PATH + '/pilotNb'):
        tixi.createElement(P_PATH, 'pilotNb')
        tixi.updateIntegerElement(P_PATH + '/pilotNb',\
                                  ri.pilot_nb, '%i')
    else:
        temp = tixi.getIntegerElement(P_PATH + '/pilotNb')
        if temp != ri.pilot_nb and temp > 0:
            ri.pilot_nb = temp

    # Pilots user input data
    if not tixi.checkElement(P_PATH + '/pilotMass'):
        tixi.createElement(P_PATH, 'pilotMass')
        tixi.updateDoubleElement(P_PATH + '/pilotMass',\
                                 ri.MASS_PILOT, '%g')
    else:
        temp = tixi.getDoubleElement(P_PATH + '/pilotMass')
        if temp != ri.MASS_PILOT and temp > 0:
            ri.MASS_PILOT = temp

    # Cabin crew user input data
    if not tixi.checkElement(CC_PATH + '/cabinCrewMemberMass'):
        tixi.createElement(CC_PATH, 'cabinCrewMemberMass')
        tixi.updateDoubleElement(CC_PATH + '/cabinCrewMemberMass',\
                                 ri.MASS_CABIN_CREW, '%g')
    else:
        temp = tixi.getDoubleElement(CC_PATH + '/cabinCrewMemberMass')
        if temp != ri.MASS_CABIN_CREW and temp > 0:
            ri.MASS_CABIN_CREW = temp

    # Passengers input
    if not tixi.checkElement(PASS_PATH + '/passMass'):
        tixi.createElement(PASS_PATH, 'passMass')
        tixi.updateDoubleElement(PASS_PATH + '/passMass',\
                                 ri.MASS_PASS, '%g')
    else:
        temp = tixi.getDoubleElement(PASS_PATH+ '/passMass')
        if temp != ri.MASS_PASS and temp > 0:
            ri.MASS_PASS = temp

    # Propulsion and Fuel

    if not tixi.checkElement(PROP_PATH + '/turboprop'):
        create_branch(tixi, PROP_PATH, False)
        tixi.createElement(PROP_PATH, 'turboprop')
        if ri.TURBOPROP:
            tixi.updateTextElement(PROP_PATH + '/turboprop', 'True')
        else:
            tixi.updateTextElement(PROP_PATH + '/turboprop', 'False')
    else:
        temp = tixi.getTextElement(PROP_PATH + '/turboprop')
        if temp == 'False':
            ri.TURBOPROP = False
        else:
            ri.TURBOPROP = True

    if not tixi.checkElement(F2_PATH + '/resFuelPerc'):
        tixi.createElement(F2_PATH, 'resFuelPerc')
        tixi.updateDoubleElement(F2_PATH + '/resFuelPerc',\
                                 ri.RES_FUEL_PERC, '%g')
    else:
        temp = tixi.getDoubleElement(F2_PATH + '/resFuelPerc')
        if temp != ri.RES_FUEL_PERC and temp > 0:
            ri.RES_FUEL_PERC = temp

    if not tixi.checkElement(TSFC_PATH + '/tsfcCruise'):
        tixi.createElement(TSFC_PATH, 'tsfcCruise')
        tixi.updateDoubleElement(TSFC_PATH + '/tsfcCruise',\
                                 ri.TSFC_CRUISE, '%g')
    else:
        temp = tixi.getDoubleElement(TSFC_PATH + '/tsfcCruise')
        if temp != ri.TSFC_CRUISE and temp > 0:
            ri.TSFC_CRUISE = temp

    if not tixi.checkElement(TSFC_PATH + '/tsfcLoiter'):
        tixi.createElement(TSFC_PATH, 'tsfcLoiter')
        tixi.updateDoubleElement(TSFC_PATH + '/tsfcLoiter',\
                                 ri.TSFC_LOITER, '%g')
    else:
        temp = tixi.getDoubleElement(TSFC_PATH + '/tsfcLoiter')
        if temp != ri.TSFC_LOITER and temp > 0:
            ri.TSFC_LOITER = temp

    ## REQUIRED DATA =========================================================
    # Cabin Crew
    ri.cabin_crew_nb = tixi.getIntegerElement(CC_PATH + '/cabinCrewMemberNb')

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

    return(mw, ri)


#=============================================================================
#   MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('##########################################################')
    log.warning('#### ERROR NOT A STANDALONE PROGRAM, RUN rangemain.py ####')
    log.warning('##########################################################')
