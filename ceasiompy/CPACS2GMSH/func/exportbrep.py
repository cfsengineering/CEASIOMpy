"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Small description of the script

Python version: >=3.7

| Author: Tony Govoni
| Creation: 2022-03-22

TODO:

    - Handle engine position correctly

"""


# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ceasiompy.CPACS2GMSH.func.engineconversion import engine_conversion
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonnames import GMSH_ENGINE_CONFIG_NAME
from ceasiompy.utils.configfiles import ConfigFile
from tigl3.import_export_helper import export_shapes

log = get_logger()

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def export(shape, brep_dir, uid):
    """
    Export a shape to a brep file and store its UID

    Parameters
    ----------
    shape: TiGL Cshape
        The shape to be exported
    brep_dir (Paht): Path to the brep directory
        Path object to the directory where the brep files are saved
    uid: str
        The uID of the shape

    Returns
    -------
    None

    """

    brep_dir.mkdir(exist_ok=True)
    brep_file = Path(brep_dir, f"{uid}.brep")

    export_shapes([shape], str(brep_file))

    if not brep_file.exists():
        log.error(f"Failed to export {uid}")
        raise FileNotFoundError(f"Failed to export {uid}")


def engine_export(cpacs, engine, brep_dir, engines_cfg_file, engine_surface_percent):
    """
    Export the engine to a brep file

    Parameters
    ----------
    cpacs : CPACS object
        CPACS object (from cpacspy)
    engine: TiGL engine
        Engine part to be exported
    brep_dir : Path
        Path object to the directory where the brep files are saved
    engines_cfg_file : Path
        Path object to the config file for the engines
    engine_surface_percent : tuple
        Tuple containing the position percentage of the surface intake and exhaust bc
        for the engine
    """

    engine_uids = []
    engine_uid = engine.get_uid()
    engine_uids.append(engine_uid)
    nacelle = engine.get_nacelle()

    if nacelle:
        center_cowl = nacelle.get_center_cowl()
        if center_cowl:
            center_cowl_uid = center_cowl.get_uid()
            engine_uids.append(center_cowl_uid)
            center_cowl_shape = center_cowl.build_loft()
            export(center_cowl_shape, brep_dir, center_cowl_uid)

        core_cowl = nacelle.get_core_cowl()
        if core_cowl:
            core_cowl_uid = core_cowl.get_uid()
            engine_uids.append(core_cowl_uid)
            core_cowl_shape = core_cowl.build_loft()
            export(core_cowl_shape, brep_dir, core_cowl_uid)

        fan_cowl = nacelle.get_fan_cowl()
        if fan_cowl:
            fan_cowl_uid = fan_cowl.get_uid()
            engine_uids.append(fan_cowl_uid)
            fan_cowl_shape = fan_cowl.build_loft()
            export(fan_cowl_shape, brep_dir, fan_cowl_uid)

        # Determine engine type and save it in the engine config files
        config_file = ConfigFile(engines_cfg_file)

        config_file[f"{engine_uid}_DOUBLE_FLUX"] = "0"
        if fan_cowl and core_cowl:
            config_file[f"{engine_uid}_DOUBLE_FLUX"] = "1"

        config_file.write_file(engines_cfg_file, overwrite=True)

    engine_conversion(cpacs, engine_uids, brep_dir, engines_cfg_file, engine_surface_percent)


def export_brep(cpacs, brep_dir, engine_surface_percent=(20, 20)):
    """Function to generate and export the geometries of a .xml file

    Function 'export_brep' is a subfunction of CPACS2GMSH that generate with TiGL
    the airplane geometry of the .xml file. Then all the airplane parts are
    exported in .brep format with their uid name
    mirrored element of the airplane have the subscript _mirrored : Wing1_mirrored.brep

    Args:
    cpacs : CPACS object (from cpacspy)
        CPACS object (from cpacspy)
    brep_dir : Path
        Path object to the directory where the brep files are saved
    engine_surface_percent : tuple
        Tuple containing the position percentage of the surface intake and exhaust bc
        for the engine

    Returns
    -------
    None

    """

    aircraft_config = cpacs.aircraft.configuration

    # Retrieve aircraft parts
    fuselage_cnt = aircraft_config.get_fuselage_count()
    wing_cnt = aircraft_config.get_wing_count()
    # rotor_cnt = aircraft_config.get_rotor_count()
    # rotor_blade_cnt = aircraft_config.get_rotor_blade_count()
    pylons_config = aircraft_config.get_engine_pylons()
    engines_config = aircraft_config.get_engines()

    # Export into brep

    # Fuselage
    for k in range(1, fuselage_cnt + 1):
        fuselage = aircraft_config.get_fuselage(k)
        fuselage_uid = fuselage.get_uid()
        fuselage_geom = fuselage.get_loft()
        export(fuselage_geom, brep_dir, fuselage_uid)

    # Wing
    for k in range(1, wing_cnt + 1):
        wing = aircraft_config.get_wing(k)
        wing_uid = wing.get_uid()
        wing_geom = wing.get_loft()
        export(wing_geom, brep_dir, wing_uid)

        wing_m_geom = aircraft_config.get_wing(k).get_mirrored_loft()
        if wing_m_geom is not None:
            export(wing_m_geom, brep_dir, wing_uid + "_mirrored")

    # Pylon
    if pylons_config:
        pylon_cnt = pylons_config.get_pylon_count()
        for k in range(1, pylon_cnt + 1):
            pylon = pylons_config.get_engine_pylon(k)
            pylon_uid = pylon.get_uid()
            pylon_geom = pylon.get_loft()
            export(pylon_geom, brep_dir, pylon_uid)

            pylon_m_geom = pylons_config.get_engine_pylon(k).get_mirrored_loft()
            if pylon_m_geom is not None:
                export(pylon_m_geom, brep_dir, pylon_uid + "_mirrored")

    # Engine
    if engines_config:
        nb_engine = engines_config.get_engine_count()

        # Create config file for the engine conversion
        engines_cfg_file = Path(brep_dir, GMSH_ENGINE_CONFIG_NAME)
        config_file = ConfigFile()
        config_file.write_file(engines_cfg_file, overwrite=True)

        # Export each engine
        for k in range(1, nb_engine + 1):
            engine = engines_config.get_engine(k)
            engine_export(cpacs, engine, brep_dir, engines_cfg_file, engine_surface_percent)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
