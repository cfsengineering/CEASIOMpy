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

import numpy as np
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.CPACSUpdater.cpacsupdater as cpud

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

# =============================================================================
#   GLOBALS
# =============================================================================

# Contains the geometric design variables
geom_var_dict = {}
XPATH = 'None'

# =============================================================================
#   FUNCTIONS
# =============================================================================
def add_am_to_dict(optim_var_dict, am_dict):
    """Add aeromap values to variable dictionary.

    All values are dupplicated to reach the same number of value than the
    aeromap parameters and coefficient. This is done to add the aeromap points
    that are not taken into account by the driver, but still computed in one
    iteration.

    Args:
        optim_var_dict (dct): Variable dictionary.
        am_dict (dct): Dictionary with the entire aeromap.

    Returns:
        None.

    """
    # Take a variable from the optim dict to compute the length to add
    var_in_dict = list(optim_var_dict.keys())[0]
    am_length = int(len(am_dict['cl'][1])/len(optim_var_dict[var_in_dict][1]))
    log.info("Adding the whole aeromap to the dictionary")
    for name, infos in optim_var_dict.items():
        if name not in apmf.XSTATES+apmf.COEF_LIST:
            # Calling a new list instance else the clear method will also clean l
            l = list(infos[1])
            infos[1].clear()
            infos[1].extend(np.repeat(l, am_length))

    for name, infos in am_dict.items():
        optim_var_dict[name] = infos


def update_am_dict(tixi, aeromap_uid, am_dict):
    """Save the aeromap results.

    Appends the new aeromap results to a dictionary.

    Args:
        tixi (tixi3 handle): TIXI handle of the CPACS file.
        aeromap_uid (str): uID of the aeromap in use.
        am_dict (dct): Contains the results of old aeromap calculations.

    Returns
        None.

    """
    Coef = apmf.get_aeromap(tixi, aeromap_uid)
    d = Coef.to_dict()
    for name , infos in am_dict.items():
        infos[1].extend(d[name])


def update_dict(tixi, optim_var_dict):
    """Update dictionnary after one iteration.

    The dictionary containing all the problem variables (obj, des, const) is
    updated with the new values from the resulting CPACS file after one run
    through the all the modules that are contained in one iteration of the
    routine.

    Args:
        tixi (tixi3 handle) : TIXI handle of the CPACS file
        optim_var_dict (dict) : Variable dictionary.

    Returns:
        None.

    """
    for name, infos in optim_var_dict.items():
        if infos[5] in ['', '-']:
            if tixi.checkElement(infos[4]):
                new_val = tixi.getDoubleElement(infos[4])
                infos[1].append(new_val)


def create_var(var_name, init_value, getcmd, setcmd, lim=0.2):
    """Add design variable to the dictionary.

    Add the parameters of one variable to the dictionary, which are saved in a
    tuple as (Name, initial value, lower bound, upper bound, setcommand
    getcommand).

    Args:
        var_name (str) : Name of the variable.
        init_value (float) :
        getcmd (str) : Command to retrieve a value in the CPACS file.
        setcmd (str) : Command to change a value in the CPACS file.
        lim (float) : Percentage of the initial value to define the upper and lower limit :
            init_value*(1-lim) < init_value < init_value*(1+lim)
            The default is 0.2.

    Returns:
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

    geom_var_dict[var_name] = (var_name, [init_value], lower_bound, upper_bound, setcmd, getcmd)


def init_elem_param(sec_name, section, elem_nb, scmd):
    """Create wing section element variable.

    Add design variables and constrains relative to the wing section elements
    to the dictionnary.

    Args:
        sec_name (str) : Name of the wing section
        section (handle) : Handle of the wing section
        elem_nb (int) : Number of section elements
        scmd (str) : Command to get the section handle

    Returns:
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
    """Create wing section variable

    Add design variables and constrains relative to the wing sections to the
    dictionnary.

    Args:
        name (str) : Name of the wing
        wing (handle) : Handle of the wing
        sec_nb (int) : Number of wing elements
        wcmd (str) : Command to get the wing handle

    Returns:
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
    """Create wing variable

    Add design variables and constrains relative to the wings to the
    dictionnary.

    Args:
        aircraft (handle) : Handle of the aircraft
        wing_nb (int) : Number of wings

    Returns:
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
    """Create fuselage variable

    Add design variables and constrains relative to the aircraft fuselages to
    the dictionnary.

    Args:
        aircraft (handle) : Handle of the aircraft
        fuse_nb (int) : Number of fuselages

    Returns:
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
        if not isinstance(fnb, int):
            for secnb in fnb:
                var_name = name + "_sec" + str(secnb)
                init_sec_width = fuselage.get_maximal_width()
                getcmd = 'fuselage.get_maximal_width()'
                setcmd = 'fuselage.set_max_width({})'.format(var_name)
                create_var(var_name, init_sec_width, getcmd, setcmd)


def init_geom_var_dict(tixi):
    """Create design variable dictionary

    Return the dictionary of the design variables using the TIGL library.
    Add design variables and constrains relative to the aircraft fuselages to
    the dictionnary.

    Args:
        tixi (handle) : Handle of the CPACS file

    Returns:
        geom_var_dict (dict) : dictionary with the geometric parameters of
        the routine.

    """
    tigl = cpsf.open_tigl(tixi)
    aircraft = cpud.get_aircraft(tigl)

    fuse_nb = aircraft.get_fuselage_count()
    if fuse_nb:
        init_fuse_param(aircraft, fuse_nb)

    wing_nb = aircraft.get_wing_count()
    if wing_nb:
        init_wing_param(aircraft, wing_nb)

    return geom_var_dict


if __name__ == "__main__":

    log.info("Launching dictionnary.py programm...")
    log.info("Not a standalone programm. Nothing will be executed !")

    exit()
