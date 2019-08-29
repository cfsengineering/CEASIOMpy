"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

This script updates the CPACS fiel and copy it on the ToolOutput folder.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-11-21
| Last modifiction: 2019-08-29 (AJ)
"""

#=============================================================================
#   IMPORTS
#=============================================================================

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,  \
                                           add_uid, create_branch

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================

"""All classes are defined inside the InputClasses/Conventional"""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def cpacs_mbd_update(out, mw, bi, ms_zpm, out_xml):
    """ The function updates the cpacs file after the Weight_and_Balance
        program.

        INPUT
        (float) mass_pass   --Arg.: Passenger mass, countig also the
                                          extra mass.
        (class) out         --Arg.: BalanceOutput class.
        (class) mw          --Arg.: MassesWeights class.
        (class) bi          --Arg.: BalanceInput class.
        ##======= Classes are defined in the InputClasses folder =======##
        (cahr) out_xml      --Arg.: Path of the output file.

        OUTPUT
        (file) cpacs.xml --Out.: Updated cpacs file.
    """
    tixi = open_tixi(out_xml)
    tigl = open_tigl(tixi)

    # CREATING PATH ==========================================================
    MB_PATH = '/cpacs/vehicles/aircraft/'\
                          + 'model/analyses/massBreakdown'

    MD_PATH = MB_PATH + '/designMasses'
    MTOM_PATH = MD_PATH + '/mTOM'

    MZFM_PATH = MD_PATH + '/mZFM'

    OEM_PATH = MB_PATH + '/mOEM/massDescription'
    J_PATH = OEM_PATH + '/massInertia/J'
    CG_PATH = OEM_PATH + '/location/'

    create_branch(tixi, MTOM_PATH + '/location/x', False)
    create_branch(tixi, MTOM_PATH + '/location/y', False)
    create_branch(tixi, MTOM_PATH + '/location/z', False)
    create_branch(tixi, MTOM_PATH + '/massInertia/Jxx', False)
    create_branch(tixi, MTOM_PATH + '/massInertia/Jyy', False)
    create_branch(tixi, MTOM_PATH + '/massInertia/Jzz', False)
    create_branch(tixi, MTOM_PATH + '/massInertia/Jxy', False)
    create_branch(tixi, MTOM_PATH + '/massInertia/Jyz', False)
    create_branch(tixi, MTOM_PATH + '/massInertia/Jxz', False)

    create_branch(tixi, MZFM_PATH + '/location/x', False)
    create_branch(tixi, MZFM_PATH + '/location/y', False)
    create_branch(tixi, MZFM_PATH + '/location/z', False)
    create_branch(tixi, MZFM_PATH + '/massInertia/Jxx', False)
    create_branch(tixi, MZFM_PATH + '/massInertia/Jyy', False)
    create_branch(tixi, MZFM_PATH + '/massInertia/Jzz', False)
    create_branch(tixi, MZFM_PATH + '/massInertia/Jxy', False)
    create_branch(tixi, MZFM_PATH + '/massInertia/Jyz', False)
    create_branch(tixi, MZFM_PATH + '/massInertia/Jxz', False)

    create_branch(tixi, OEM_PATH + '/location/x', False)
    create_branch(tixi, OEM_PATH + '/location/y', False)
    create_branch(tixi, OEM_PATH + '/location/z', False)
    create_branch(tixi, OEM_PATH + '/massInertia/Jxx', False)
    create_branch(tixi, OEM_PATH + '/massInertia/Jyy', False)
    create_branch(tixi, OEM_PATH + '/massInertia/Jzz', False)
    create_branch(tixi, OEM_PATH + '/massInertia/Jxy', False)
    create_branch(tixi, OEM_PATH + '/massInertia/Jyz', False)
    create_branch(tixi, OEM_PATH + '/massInertia/Jxz', False)

    # DESIGN MASSES ==========================================================
    # MTOM -------------------------------------------------------------------
    tixi.uIDSetToXPath(MTOM_PATH + '/location', 'MTOMloc')

    tixi.updateDoubleElement(MTOM_PATH + '/location'+'/x',\
                             out.center_of_gravity[0], '%g')
    tixi.updateDoubleElement(MTOM_PATH + '/location'+'/y',\
                             out.center_of_gravity[1], '%g')
    tixi.updateDoubleElement(MTOM_PATH + '/location'+'/z',\
                             out.center_of_gravity[2], '%g')

    tixi.updateDoubleElement(MTOM_PATH + '/massInertia' + '/Jxx',\
                             out.Ixx_lump, '%g')
    tixi.updateDoubleElement(MTOM_PATH + '/massInertia' + '/Jyy',\
                             out.Iyy_lump,'%g')
    tixi.updateDoubleElement(MTOM_PATH + '/massInertia' + '/Jzz',\
                             out.Izz_lump, '%g')
    tixi.updateDoubleElement(MTOM_PATH + '/massInertia' + '/Jxy',\
                             out.Ixy_lump, '%g')
    tixi.updateDoubleElement(MTOM_PATH + '/massInertia' + '/Jyz',\
                             out.Iyz_lump,'%g')
    tixi.updateDoubleElement(MTOM_PATH + '/massInertia' + '/Jxz',\
                             out.Ixz_lump, '%g')

    # MZFM -------------------------------------------------------------------
    add_uid(tixi, MZFM_PATH + '/location', 'MZFMloc')

    # updating path
    tixi.updateDoubleElement(MZFM_PATH + '/location' + '/x',\
                             out.cg_zpm[0], '%g')
    tixi.updateDoubleElement(MZFM_PATH + '/location' + '/y',\
                             out.cg_zpm[1], '%g')
    tixi.updateDoubleElement(MZFM_PATH + '/location' + '/z',\
                             out.cg_zpm[2], '%g')

    tixi.updateDoubleElement(MZFM_PATH + '/massInertia'\
                             + '/Jxx', out.Ixx_lump_zfm, '%g')
    tixi.updateDoubleElement(MZFM_PATH + '/massInertia'\
                             + '/Jyy', out.Iyy_lump_zfm, '%g')
    tixi.updateDoubleElement(MZFM_PATH + '/massInertia'\
                             + '/Jzz', out.Izz_lump_zfm, '%g')
    tixi.updateDoubleElement(MZFM_PATH + '/massInertia'\
                             + '/Jxy', out.Ixy_lump_zfm, '%g')
    tixi.updateDoubleElement(MZFM_PATH + '/massInertia'\
                             + '/Jyz', out.Iyz_lump_zfm, '%g')
    tixi.updateDoubleElement(MZFM_PATH + '/massInertia'\
                             + '/Jxz', out.Ixz_lump_zfm, '%g')

    # OEM ====================================================================
    add_uid(tixi, OEM_PATH + '/location', 'OEMloc')

    tixi.updateDoubleElement((CG_PATH + 'x'), out.cg_oem[0], '%g')
    tixi.updateDoubleElement((CG_PATH + 'y'), out.cg_oem[1], '%g')
    tixi.updateDoubleElement((CG_PATH + 'z'), out.cg_oem[2], '%g')
    tixi.updateDoubleElement((J_PATH + 'xx'), out.Ixx_lump_oem, '%g')
    tixi.updateDoubleElement((J_PATH + 'yy'), out.Iyy_lump_oem, '%g')
    tixi.updateDoubleElement((J_PATH + 'zz'), out.Izz_lump_oem, '%g')
    tixi.updateDoubleElement((J_PATH + 'xy'), out.Ixy_lump_oem, '%g')
    tixi.updateDoubleElement((J_PATH + 'yz'), out.Iyz_lump_oem, '%g')
    tixi.updateDoubleElement((J_PATH + 'xz'), out.Ixz_lump_oem, '%g')

    # ZPM INERTIA ============================================================
    B_PATH = '/cpacs/toolspecific/CEASIOMpy/balance'
    ZPM_PATH = B_PATH + '/mZPM'
    create_branch(tixi, ZPM_PATH + '/name', False)
    tixi.updateTextElement(ZPM_PATH + '/name', 'Maximum no payload mass')
    create_branch(tixi, ZPM_PATH + '/description', False)
    tixi.updateTextElement(ZPM_PATH + '/description', 'Maximum '\
                           + 'no payload mass [kg], CoG coordinate [m] and '\
                           + 'moment of inertia.')
    create_branch(tixi, ZPM_PATH + '/mass', False)
    tixi.updateDoubleElement(ZPM_PATH + '/mass',\
                             ms_zpm, '%g')

    create_branch(tixi, ZPM_PATH + '/location/x', False)
    create_branch(tixi, ZPM_PATH + '/location/y', False)
    create_branch(tixi, ZPM_PATH + '/location/z', False)
    create_branch(tixi, ZPM_PATH + '/massInertia/Jxx', False)
    create_branch(tixi, ZPM_PATH + '/massInertia/Jyy', False)
    create_branch(tixi, ZPM_PATH + '/massInertia/Jzz', False)
    create_branch(tixi, ZPM_PATH + '/massInertia/Jxy', False)
    create_branch(tixi, ZPM_PATH + '/massInertia/Jyz', False)
    create_branch(tixi, ZPM_PATH + '/massInertia/Jxz', False)

    LOC_PATH = ZPM_PATH + '/location'
    MOI_PATH = ZPM_PATH + '/massInertia'

    add_uid(tixi, ZPM_PATH, 'MZPM')
    add_uid(tixi, LOC_PATH, 'MZPMloc')
    tixi.updateDoubleElement((LOC_PATH + '/x'), out.cg_zpm[0], '%g')
    tixi.updateDoubleElement((LOC_PATH + '/y'), out.cg_zpm[1], '%g')
    tixi.updateDoubleElement((LOC_PATH + '/z'), out.cg_zpm[2], '%g')
    tixi.updateDoubleElement((MOI_PATH + '/Jxx'), out.Ixx_lump_zpm, '%g')
    tixi.updateDoubleElement((MOI_PATH + '/Jyy'), out.Iyy_lump_zpm, '%g')
    tixi.updateDoubleElement((MOI_PATH + '/Jzz'), out.Izz_lump_zpm, '%g')
    tixi.updateDoubleElement((MOI_PATH + '/Jxy'), out.Ixy_lump_zpm, '%g')
    tixi.updateDoubleElement((MOI_PATH + '/Jyz'), out.Iyz_lump_zpm, '%g')
    tixi.updateDoubleElement((MOI_PATH + '/Jxz'), out.Ixz_lump_zpm, '%g')

    # USER CASE ==============================================================
    if bi.USER_CASE:
        UC_PATH = '/cpacs/toolspecific/CEASIOMpy/balance/userBalance'
        LOC_PATH = UC_PATH + '/location'
        MOI_PATH = UC_PATH + '/massInertia'

        create_branch(tixi, LOC_PATH + '/x', False)
        create_branch(tixi, LOC_PATH + '/y', False)
        create_branch(tixi, LOC_PATH + '/z', False)
        create_branch(tixi, MOI_PATH + '/Jxx', False)
        create_branch(tixi, MOI_PATH + '/Jyy', False)
        create_branch(tixi, MOI_PATH + '/Jzz', False)
        create_branch(tixi, MOI_PATH + '/Jxy', False)
        create_branch(tixi, MOI_PATH + '/Jyz', False)
        create_branch(tixi, MOI_PATH + '/Jxz', False)

        add_uid(tixi, LOC_PATH, 'USERCase')
        tixi.updateDoubleElement((LOC_PATH + '/x'), out.cg_user[0], '%g')
        tixi.updateDoubleElement((LOC_PATH + '/y'), out.cg_user[1], '%g')
        tixi.updateDoubleElement((LOC_PATH + '/z'), out.cg_user[2], '%g')
        tixi.updateDoubleElement((MOI_PATH + '/Jxx'), out.Ixx_lump_user, '%g')
        tixi.updateDoubleElement((MOI_PATH + '/Jyy'), out.Iyy_lump_user, '%g')
        tixi.updateDoubleElement((MOI_PATH + '/Jzz'), out.Izz_lump_user, '%g')
        tixi.updateDoubleElement((MOI_PATH + '/Jxy'), out.Ixy_lump_user, '%g')
        tixi.updateDoubleElement((MOI_PATH + '/Jyz'), out.Iyz_lump_user, '%g')
        tixi.updateDoubleElement((MOI_PATH + '/Jxz'), out.Ixz_lump_user, '%g')

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
    log.warning('##########################################################')
    log.warning('### ERROR NOT A STANDALONE PROGRAM, RUN balancemain.py ###')
    log.warning('##########################################################')
