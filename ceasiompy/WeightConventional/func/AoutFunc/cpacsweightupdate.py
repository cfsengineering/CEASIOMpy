"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The code updates the cpacs file after the weight analysis.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-11-21
| Last modifiction: 2019-08-29 (AJ)
"""


#=============================================================================
#   IMPORTS
#=============================================================================

from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                           create_branch, add_uid

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

def toolspecific_update(mw, out, out_xml):
    """ The function updates the cpacs file after the Weight analysis.

        INPUT
        (class) mw         --Arg.: MassesWeights class.
        (class) out        --Arg.: WeightOutput class.
        ##======= Classes are defined in the classes folder =======##

        (char) out_xml     --Arg.: Path of the output file.

        OUTPUT
        (file) cpacs.xml     --Out.: Updated cpacs file.
    """

    tixi = open_tixi(out_xml)

    # Path creation ==========================================================
    CEASIOM_PATH = '/cpacs/toolspecific/CEASIOMpy'

    W_PATH = CEASIOM_PATH + '/weight'
    C_PATH = W_PATH + '/crew'

    PASS_PATH = W_PATH + '/passengers'

    # Path update ============================================================
    if not tixi.checkElement(C_PATH + '/cabinCrewMembers/cabinCrewMemberNb'):
        tixi.createElement(C_PATH + '/cabinCrewMembers', 'cabinCrewMemberNb')
    tixi.updateDoubleElement(C_PATH + '/cabinCrewMembers/cabinCrewMemberNb',\
                             out.cabin_crew_nb, '%g')

    if not tixi.checkElement(PASS_PATH + '/passNb'):
        tixi.createElement(PASS_PATH, 'passNb')
    tixi.updateIntegerElement(PASS_PATH + '/passNb', out.pass_nb, '%i')
    if not tixi.checkElement(PASS_PATH + '/rowNb'):
        tixi.createElement(PASS_PATH, 'rowNb')
    tixi.updateIntegerElement(PASS_PATH + '/rowNb', out.row_nb, '%i')
    if not tixi.checkElement(PASS_PATH + '/aisleNb'):
        tixi.createElement(PASS_PATH, 'aisleNb')
    tixi.updateIntegerElement(PASS_PATH + '/aisleNb', out.aisle_nb, '%i')
    if not tixi.checkElement(PASS_PATH + '/toiletNb'):
        tixi.createElement(PASS_PATH, 'toiletNb')
    tixi.updateIntegerElement(PASS_PATH + '/toiletNb', out.toilet_nb, '%i')
    if not tixi.checkElement(PASS_PATH + '/abreastNb'):
        tixi.createElement(PASS_PATH, 'abreastNb')
    tixi.updateIntegerElement(PASS_PATH + '/abreastNb', out.abreast_nb, '%i')

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

def cpacs_weight_update(out, mw, out_xml):
    """ The function updates the cpacs file after the Weight analysis.

        INPUT
        (class) out         --Arg.: WeightOutput class.
        (class) mw          --Arg.: MassesWeights class.
        (char) out_xml      --Arg.: Path of the output file.
        ##======= Classes are defined in the classes folder =======##

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
    OIM_PATH = MB_PATH + '/mOEM/mOperatorItems/mCrewMembers'\
               + '/massDescription'

    create_branch(tixi, MTOM_PATH + '/mass', False)
    create_branch(tixi, MZFM_PATH + '/mass', False)
    create_branch(tixi, MF_PATH + '/mass', False)
    create_branch(tixi, OEM_PATH + '/mass', False)
    create_branch(tixi, PAY_PATH + '/mass', False)
    create_branch(tixi, MC_PATH, False)
    create_branch(tixi, OIM_PATH + '/mass', False)

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

    # PAYLOAD MASS AND FUEL WITH MAX PAYLOAD =================================
    add_uid(tixi, PAY_PATH, 'MPM')
    tixi.createElement(PAY_PATH, 'name')
    tixi.updateTextElement(PAY_PATH + '/name', 'Max payload mass')
    tixi.createElement(PAY_PATH, 'description')
    tixi.updateTextElement(PAY_PATH + '/description', 'Maximum '\
                           + 'payload mass [kg].')
    tixi.updateDoubleElement(PAY_PATH + '/mass', mw.mass_payload, '%g')

    if mw.mass_cargo:
        tixi.createElement(MC_PATH, 'massCargo')
        tixi.updateDoubleElement(MC_PATH + '/massCargo', mw.mass_cargo, '%g')
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
    log.warning('###########################################################')
    log.warning('#### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ####')
    log.warning('###########################################################')
