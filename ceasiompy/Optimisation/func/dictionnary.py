"""
CEASIOMpy: Conceptual Aircraft Design Software.

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to create the dictionnary of geometric variables needed
for the optimnization routine.

Python version: >=3.6

| Author : Vivien Riolo
| Creation: 2020-03-24
| Last modification: 2020-06-02

TODO
----
    * Expand the geometric parameters
    * Add constrains between the parameters to disable multiple modifications
      of the same geometric aspect of the plane

"""

# =============================================================================
#   IMPORTS
# =============================================================================

from sys import exit

# import ceasiompy.utils.optimfunctions as optf
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.CPACSUpdater.cpacsupdater as cpud
# import ceasiompy.utils.workflowfunctions as wkf

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

# =============================================================================
#   GLOBALS
# =============================================================================

# Contains the geometric design variables
design_var_dict = {}
XPATH = 'None'

# =============================================================================
#   FUNCTIONS
# =============================================================================


def update_dict(tixi, optim_var_dict):
    """
    Update dictionnary after a workflow

    Parameters
    ----------
    tixi : tixi3 handle
        DESCRIPTION.
    optim_var_dict : dict
        DESCRIPTION.

    Returns
    -------
    None.

    """
    for name, (val_type, listval, minval, maxval, getcommand, setcommand) in optim_var_dict.items():
        if setcommand == '-' or setcommand == '':
            if tixi.checkElement(getcommand):
                new_val = tixi.getDoubleElement(getcommand)
                # Checks type of variable
                if type(new_val) == list:
                    listval.append(new_val[-1])
                    log.info(name + ' ' + str(new_val[-1]))
                else:
                    listval.append(new_val)
                    log.info(name + ' ' + str(new_val))


def create_var(var_name, init_value, getcmd, setcmd, lim=0.2):
    """
    Add design variable to the dictionnary.

    Parameters
    ----------
    var_name : str
        Name of the variable.
    init_value : float
        V.
    getcmd : str
        Command to retrieve a value in the CPACS file.
    setcmd : str
        Command to change a value in the CPACS file.
    lim : float, optional
        Percentage of the initial value to define the upper and lower limit :
            init_value*(1-lim) < init_value < init_value*(1+lim)
        The default is 0.2.

    Returns
    -------
    None.

    """
    if init_value > 0:
        lower_bound = init_value*(1-lim)
        upper_bound = init_value*(1+lim)
    elif init_value < 0:
        lower_bound = init_value*(1+lim)
        upper_bound = init_value*(1-lim)
    else:
        lower_bound = -lim
        upper_bound = lim

    design_var_dict[var_name] = (var_name, [init_value], lower_bound, upper_bound, setcmd, getcmd)


def init_elem_param(sec_name, section, elem_nb, scmd):
    """
    Add design variables and constrains relative to the wing section elements to the dictionnary.

    Returns
    -------
    None.

    """
    for enb in range(1, elem_nb+1):
        cmd = scmd + 'get_section_element({}).get_ctigl_section_element().'.format(enb)
        el_name = sec_name + "_el" + str(enb)

        element = section.get_section_element(enb).get_ctigl_section_element()

        var_name = el_name + "_width"
        init_width = element.get_width()
        getcmd = cmd+'get_width()'
        setcmd = cmd+'set_width({})'.format(var_name)
        create_var(var_name, init_width, getcmd, setcmd)


def init_sec_param(name, wing, sec_nb, wcmd):
    """
    Add design variables and constrains relative to the wing sectionelements to the dictionnary.

    Returns
    -------
    None.

    """
    for s in range(1, sec_nb+1):
        cmd = wcmd + 'get_section({}).'.format(s)
        sec_name = name + "_sec" + str(s)

        section = wing.get_section(s)

        var_name = sec_name + "_Yrotation"
        init_rot = section.get_rotation().y
        getcmd = cmd+'get_rotation().y'
        setcmd = cmd+'set_rotation(geometry.CTiglPoint(0,{},0))'.format(var_name)
        create_var(var_name, init_rot, getcmd, setcmd)

        elem_nb = section.get_section_element_count()
        if elem_nb:
            init_elem_param(sec_name, section, elem_nb, cmd)


def init_wing_param(aircraft, wing_nb):
    """
    Add design variables and constrains relative to the wings to the dictionnary.

    Returns
    -------
    None.

    """
    wings = aircraft.get_wings()

    for w in range(1, wing_nb+1):
        cmd = 'wings.get_wing({}).'.format(w)
        name = "wing" + str(w)

        wing = wings.get_wing(w)

        var_name = name+"_sweep"
        init_sweep = wing.get_sweep()
        getcmd = cmd+'get_sweep()'
        setcmd = cmd+'set_sweep({})'.format(var_name)
        create_var(var_name, init_sweep, getcmd, setcmd)

        var_name = name+"_span"
        init_span = wing.get_wing_half_span()
        getcmd = cmd+'get_wing_half_span()'
        setcmd = cmd+'set_half_span_keep_ar({})'.format(var_name)  # keep_area
        create_var(var_name, init_span, getcmd, setcmd)

        var_name = name + "_aspect_ratio"
        init_AR = wing.get_aspect_ratio()
        getcmd = cmd+'get_aspect_ratio()'
        setcmd = cmd+'set_arkeep_area({})'.format(var_name)#keep_ar
        create_var(var_name, init_AR, getcmd, setcmd)

        var_name = name + "_area"
        init_area = wing.get_surface_area()/2
        getcmd = cmd+'get_surface_area()'
        setcmd = cmd+'set_area_keep_ar({})'.format(var_name)#keep_span
        create_var(var_name, init_area, getcmd, setcmd)

        sec_nb = wing.get_section_count()
        if sec_nb:
            init_sec_param(name, wing, sec_nb, cmd)


def init_fuse_param(aircraft, fuse_nb):
    """
    Add design variables and constrains relative to the fuselage to the dictionnary.

    Returns
    -------
    None.

    """
    for f in range(1, fuse_nb+1):
        name = "fuse" + str(f)
        fuselage = aircraft.get_fuselage(f)

        var_name = name+"_length"
        init_length = fuselage.get_length()
        getcmd = 'fuselage.get_length()'
        setcmd = 'fuselage.set_length({})'.format(var_name)
        create_var(var_name, init_length, getcmd, setcmd)

        var_name = name+"_width"
        init_width = fuselage.get_maximal_width()
        getcmd = 'fuselage.get_maximal_width()'
        setcmd = 'fuselage.set_max_width({})'.format(var_name)
        create_var(var_name, init_width, getcmd, setcmd)

        # Modify a specific section width
        fnb = fuselage.get_section_count()
        if type(fnb) is not int:
            for secnb in fnb:
                var_name = name + "_sec" + str(secnb)
                init_sec_width = fuselage.get_maximal_width()
                getcmd = 'fuselage.get_maximal_width()'
                setcmd = 'fuselage.set_max_width({})'.format(var_name)
                create_var(var_name, init_sec_width, getcmd, setcmd)


def init_design_var_dict(tixi):
    """
    Return the dictionary of the design variables using the TIGL library.

    Parameters
    ----------
    tigl : tigl3_handler

    Returns
    -------
    design_var_dict : dict

    """
    tigl = cpsf.open_tigl(tixi)
    aircraft = cpud.get_aircraft(tigl)

    fuse_nb = aircraft.get_fuselage_count()
    if fuse_nb:
        init_fuse_param(aircraft, fuse_nb)

    wing_nb = aircraft.get_wing_count()
    if wing_nb:
        init_wing_param(aircraft, wing_nb)

    return design_var_dict


if __name__ == "__main__":

    log.info("Launching dictionnary.py programm...")
    log.info("Not a standalone programm. Nothing will be executed !")

    exit()
