"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Output text and plot generation function for unconventional
aircraft with fuselage.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-11-21
| Last modifiction: 2019-08-29 (AJ)
"""


#=============================================================================
#   IMPORTS
#=============================================================================

from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.cpacsfunctions import open_tixi,open_tigl, close_tixi,   \
                                           add_uid, create_branch

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================

"""All classes are defined inside the classes folder and in the
   Input
   classes/Unconventional folder."""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def toolspecific_update(f_nb, awg, mw, out, out_xml):
    """ The function that update the cpacs file after the Weight_unc_main
        program.

        INPUT
        (integer) f_nb     --Arg.: Number of fuselage [-].
        (class) awg        --Arg.: AircraftWingGeometry class.
        (class) mw         --Arg.: Masses and Weights class.
        (class) out        --Arg.: Output class.
        (char) out_xml     --Arg.: Path of the output file.
        ##======= Class are defined in the InputClasses folder =======##

        OUTPUT
        (file) cpacs.xml     --Out.: Updated cpacs file.
    """

    tixi = open_tixi(out_xml)

    # Path creation ==========================================================
    CEASIOM_PATH = '/cpacs/toolspecific/CEASIOMpy'

    W_PATH = CEASIOM_PATH + '/weight'
    C_PATH = W_PATH + '/crew'
    create_branch(tixi, C_PATH + '/cabinCrewMembers', False)

    PASS_PATH = W_PATH + '/passengers'
    create_branch(tixi, PASS_PATH, False)

    # Path update ============================================================
    if not tixi.checkElement(C_PATH + '/cabinCrewMembers/cabinCrewMemberNb'):
        tixi.createElement(C_PATH + '/cabinCrewMembers', 'cabinCrewMemberNb')
    tixi.updateDoubleElement(C_PATH + '/cabinCrewMembers/cabinCrewMemberNb',\
                             out.cabin_crew_nb, '%g')

    if not tixi.checkElement(PASS_PATH + '/passNb'):
        tixi.createElement(PASS_PATH, 'passNb')
    tixi.updateIntegerElement(PASS_PATH + '/passNb', out.pass_nb, '%i')
    if not tixi.checkElement(PASS_PATH + '/mass'):
        tixi.createElement(PASS_PATH, 'mass')
    tixi.updateDoubleElement(PASS_PATH + '/mass', mw.mass_pass, '%g')
    if not tixi.checkElement(PASS_PATH + '/toiletNb'):
        tixi.createElement(PASS_PATH, 'toiletNb')
    tixi.updateIntegerElement(PASS_PATH + '/toiletNb',int(out.toilet_nb),'%i')

    if not tixi.checkElement(PASS_PATH + '/fuelMassMaxpass'):
        tixi.createElement(PASS_PATH, 'fuelMassMaxpass')
    FMP_PATH = PASS_PATH + '/fuelMassMaxpass'
    if not tixi.checkElement(FMP_PATH + '/description'):
        tixi.createElement(FMP_PATH, 'description')
    tixi.updateTextElement(FMP_PATH + '/description', 'Maximum amount of '\
                           + 'fuel with maximum payload [kg]')
    if not tixi.checkElement(FMP_PATH + '/mass'):
        tixi.createElement(FMP_PATH, 'mass')
    tixi.updateDoubleElement(FMP_PATH + '/mass', mw.mass_fuel_maxpass, '%g')

    # Saving and closing the new cpacs file inside the ToolOutput folder -----
    tixi.saveDocument(out_xml)
    close_tixi(tixi, out_xml)

    # Openign and closing again the cpacs file, formatting purpose -----------
    tixi = open_tixi(out_xml)
    tigl = open_tigl(tixi)
    tixi.saveDocument(out_xml)
    close_tixi(tixi, out_xml)

    return()


#=============================================================================
# CPACS MASS BREAKDOWN UPDATE
#=============================================================================

def cpacs_weight_update(out, mw, ui, out_xml):
    """ The function that update the cpacs file after the Weight_unc_main
        program.

        INPUT
        (class) out      --Arg.: Output class.
        (class) mw       --Arg.: Mass and weight class.
        (class) ui       --Arg.: UserInputs class.
        (char) out_xml   --Arg.: Path of the output file.
        ##======= Class are defined in the InputClasses folder =======##

        OUTPUT
        (file) cpacs.xml --Out.: Updated cpacs file.
    """
    tixi = open_tixi(out_xml)
    tigl = open_tigl(tixi)

    # Path creation ==========================================================
    MB_PATH = '/cpacs/vehicles/aircraft/model/analyses/massBreakdown'

    if tixi.checkElement(MB_PATH):
        tixi.removeElement(MB_PATH)

    MD_PATH = MB_PATH + '/designMasses'
    MTOM_PATH = MD_PATH + '/mTOM'
    MZFM_PATH = MD_PATH + '/mZFM'
    MF_PATH = MB_PATH + '/fuel/massDescription'
    OEM_PATH = MB_PATH + '/mOEM/massDescription'
    PAY_PATH = MB_PATH + '/payload/massDescription'
    MC_PATH = MB_PATH + '/payload/mCargo'
    EM_PATH = MB_PATH + '/mOEM/mEM'
    OIM_PATH = MB_PATH + '/mOEM/mOperatorItems/mCrewMembers'\
               + '/massDescription'

    MSYS_PATH = EM_PATH + '/mSystems/massDescription/mass'
    MSTR_PATH = EM_PATH + '/mStructure/massDescription/mass'
    MEN_PATH = EM_PATH + '/mPowerUnits/massDescription/mass'

    create_branch(tixi, MTOM_PATH + '/mass', False)
    create_branch(tixi, MZFM_PATH + '/mass', False)
    create_branch(tixi, MF_PATH + '/mass', False)
    create_branch(tixi, OEM_PATH + '/mass', False)
    create_branch(tixi, PAY_PATH + '/mass', False)
    create_branch(tixi, MC_PATH, False)
    create_branch(tixi, OIM_PATH + '/mass', False)
    create_branch(tixi, EM_PATH, False)
    create_branch(tixi, MSYS_PATH, False)
    create_branch(tixi, MSTR_PATH, False)
    create_branch(tixi, MEN_PATH, False)

    # DESIGN MASSES ==========================================================
    add_uid(tixi, MTOM_PATH, 'MTOM')
    tixi.createElement(MTOM_PATH, 'name')
    tixi.updateTextElement(MTOM_PATH + '/name', 'Maximum take-off mass')
    tixi.createElement(MTOM_PATH, 'description')
    tixi.updateTextElement(MTOM_PATH + '/description', 'Maximum '\
                           + 'take off mass [kg], CoG coordinate [m] and '\
                           + 'moment of inertia.')
    tixi.updateDoubleElement(MTOM_PATH + '/mass',\
                             mw.maximum_take_off_mass, '%g')

    # MZFM -------------------------------------------------------------------
    add_uid(tixi, MZFM_PATH, 'MZFM')
    tixi.createElement(MZFM_PATH, 'name')
    tixi.updateTextElement(MZFM_PATH + '/name', 'Maximum zero fuel mass')
    tixi.createElement(MZFM_PATH, 'description')
    tixi.updateTextElement(MZFM_PATH + '/description', 'Maximum '\
                           + 'zero fuel mass [kg] and corresponding CoG '\
                           + 'coordinate [m], moment of inertia.')
    tixi.updateDoubleElement(MZFM_PATH + '/mass', mw.zero_fuel_mass, '%g')


    # FUEL MASS ==============================================================
    add_uid(tixi, MF_PATH, 'MFM')
    tixi.createElement(MF_PATH, 'name')
    tixi.updateTextElement(MF_PATH + '/name', 'Max fuel mass')
    tixi.createElement(MF_PATH, 'description')
    tixi.updateTextElement(MF_PATH + '/description', 'Maximum '\
                           + 'fuel mass [kg].')
    tixi.updateDoubleElement(MF_PATH + '/mass', mw.mass_fuel_max, '%g')

    # OEM ====================================================================
    add_uid(tixi, OEM_PATH, 'OEM')
    tixi.createElement(OEM_PATH, 'name')
    tixi.updateTextElement(OEM_PATH + '/name', 'Operating empty mass')
    tixi.createElement(OEM_PATH, 'description')
    tixi.updateTextElement(OEM_PATH + '/description', 'Operating empty'\
                           + ' mass [kg] and related inertia [kgm^2].')
    tixi.updateDoubleElement(OEM_PATH + '/mass', mw.operating_empty_mass, '%g')

    tixi.updateDoubleElement(OIM_PATH + '/mass', mw.mass_crew, '%g')
    add_uid(tixi, OIM_PATH, 'massCrew')
    tixi.updateDoubleElement(MSYS_PATH, mw.mass_systems, '%g')
    add_uid(tixi, EM_PATH\
                       + '/mSystems/massDescription', 'mSys')
    tixi.updateDoubleElement(MSTR_PATH, mw.mass_structure, '%g')
    add_uid(tixi, EM_PATH\
                       + '/mStructure/massDescription', 'mStrt')
    tixi.updateDoubleElement(MEN_PATH, mw.mass_engines, '%g')
    add_uid(tixi, EM_PATH\
                       +'/mPowerUnits/massDescription', 'mEng')

    # PAYLOAD MASS AND FUEL CARGO MASS =======================================
    add_uid(tixi, PAY_PATH, 'MPM')
    tixi.createElement(PAY_PATH, 'name')
    tixi.updateTextElement(PAY_PATH + '/name', 'Max payload mass')
    tixi.createElement(PAY_PATH, 'description')
    tixi.updateTextElement(PAY_PATH + '/description', 'Maximum '\
                           + 'payload mass [kg].')
    tixi.updateDoubleElement(PAY_PATH + '/mass', mw.mass_payload, '%g')

    tixi.createElement(MC_PATH, 'massCargo')
    tixi.updateDoubleElement(MC_PATH + '/massCargo', ui.MASS_CARGO, '%g')

    # Saving and closing the new cpacs file inside the ToolOutput folder -----
    tixi.saveDocument(out_xml)
    close_tixi(tixi, out_xml)

    # Openign and closing again the cpacs file, formatting purpose -----------
    tixi = open_tixi(out_xml)
    tigl = open_tigl(tixi)
    tixi.saveDocument(out_xml)
    close_tixi(tixi, out_xml)

    return()


#=============================================================================
# CPACS ENGINE UPDATE
#=============================================================================

def cpacs_engine_update(ui, ed, mw, out_xml):
    """ The function that update the cpacs file after the Weight_unc_main
        program.

        INPUT
        (class) mw          --Arg.: MassesWeihts class.
        (class) ui          --Arg.: UserInputs class.
        (class) ed          --Arg.: EngineData class.
        ##======= Class are defined in the Input_Classes folder =======##
        (char) out_xml      --Arg.: Path of the output file.

        OUTPUT
        (file) cpacs.xml --Out.: Updated cpacs file.
    """
    tixi = open_tixi(out_xml)
    tigl = open_tigl(tixi)

    # Path creation ==========================================================
    EN_PATH = '/cpacs/vehicles/engines'
    if tixi.checkElement(EN_PATH):
        tixi.removeElement(EN_PATH)
    for e in range(0,ed.NE):
        EN_PATH = '/cpacs/vehicles/engines/engine' + str(e+1)
        create_branch(tixi, EN_PATH, True)
        EN_UID = 'EngineuID_' + str(e+1)
        add_uid(tixi, EN_PATH, EN_UID)
        tixi.createElement(EN_PATH, 'name')
        if not ed.EN_NAME[e]:
            EN_NAME = 'Engine_' + str(e+1)
            tixi.updateTextElement(EN_PATH + '/name', EN_NAME)
        else:
            tixi.updateTextElement(EN_PATH + '/name', ed.EN_NAME[e])
        ENA_PATH = EN_PATH + '/analysis/mass'
        create_branch(tixi, ENA_PATH, False)
        add_uid(tixi, EN_PATH, EN_UID+'_mass')
        tixi.createElement(ENA_PATH, 'mass')
        tixi.updateDoubleElement(ENA_PATH + '/mass', ed.en_mass, '%g')
        ENT_PATH = EN_PATH + '/analysis'
        tixi.createElement(ENT_PATH, 'thrust00')
        tixi.updateDoubleElement(ENT_PATH + '/thrust00', ed.max_thrust, '%g')
    # Saving and closing the new cpacs file inside the ToolOutput folder -----
    tixi.saveDocument(out_xml)
    close_tixi(tixi, out_xml)

    # Openign and closing again the cpacs file, formatting purpose -----------
    tixi = open_tixi(out_xml)
    tigl = open_tigl(tixi)
    tixi.saveDocument(out_xml)
    close_tixi(tixi, out_xml)

    return()


#=============================================================================
#   MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('#########################################################')
    log.warning('# ERROR NOT A STANDALONE PROGRAM, RUN weightuncmain.py  #')
    log.warning('#########################################################')
