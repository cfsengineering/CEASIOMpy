"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Small description of the script

Python version: >=3.8

| Author: Tony Govoni
| Creation: 2022-03-22

TODO:

    - When TIGL new version is incorporated, function like get_uid may change for
    get_object_uid
"""


# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ceasiompy.CPACS2GMSH.func.engineconversion import engine_conversion
from ceasiompy import log
from ceasiompy.utils.commonnames import GMSH_ENGINE_CONFIG_NAME
from ceasiompy.utils.commonxpath import GMSH_EXPORT_PROP_XPATH
from ceasiompy.utils.configfiles import ConfigFile
from cpacspy.cpacsfunctions import get_value_or_default

from tigl3.import_export_helper import export_shapes


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
    brep_dir (Path): Path to the brep directory
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


def rotor_config(rotorcraft_config, brep_dir):
    """
    Store the rotor configuration of the aircraft in a .cfg file in order to
    replace in gmsh the rotor by disk for the disk actuator modeling

    Args:
    rotorcraft_config : tixi
        rotor configuration of the aircraft
    brep_dir : Path
        Path object to the directory where the brep files are saved
    """
    rotor_cnt = rotorcraft_config.get_rotor_count()
    # create config file for the engine conversion
    rotors_cfg_file_path = Path(brep_dir, "config_rotors.cfg")
    config_file = ConfigFile()

    config_file["NB_ROTOR"] = f"{rotor_cnt}"
    for k in range(1, rotor_cnt + 1):
        rotor = rotorcraft_config.get_rotor(k)
        config_file[f"UID_{k}"] = f"{rotor.get_uid()}"
        config_file[f"{rotor.get_uid()}_ROTOR_RADIUS"] = f"{rotor.get_radius()}"

        symmetric = rotor.get_symmetry()
        config_file[f"{rotor.get_uid()}_SYMMETRIC"] = f"{symmetric}"

        config_file[f"{rotor.get_uid()}_TRANS_X"] = f"{rotor.get_translation().x}"
        config_file[f"{rotor.get_uid()}_TRANS_Y"] = f"{rotor.get_translation().y}"
        config_file[f"{rotor.get_uid()}_TRANS_Z"] = f"{rotor.get_translation().z}"

        config_file[f"{rotor.get_uid()}_ROT_X"] = f"{rotor.get_rotation().x}"
        config_file[f"{rotor.get_uid()}_ROT_Y"] = f"{rotor.get_rotation().y}"
        config_file[f"{rotor.get_uid()}_ROT_Z"] = f"{rotor.get_rotation().z}"

        # Note that scaling is not used and needed since the
        # rotor.get_radius() is already scaled correctly
    config_file.write_file(rotors_cfg_file_path, overwrite=True)


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
    """

    tixi = cpacs.tixi

    # Get rotor config
    if get_value_or_default(tixi, GMSH_EXPORT_PROP_XPATH, False):
        try:
            rotorcraft_config = cpacs.rotorcraft.configuration
            rotor_config(rotorcraft_config, brep_dir)
        except AttributeError:
            pass

    # get the aircraft configuration
    aircraft_config = cpacs.aircraft.configuration

    # Retrieve aircraft parts
    fuselage_cnt = aircraft_config.get_fuselage_count()
    wing_cnt = aircraft_config.get_wing_count()

    # Pylon configuration
    pylons_config = aircraft_config.get_engine_pylons()
    engines_config = aircraft_config.get_engines()

    # Export into brep

    # Fuselage
    for k in range(1, fuselage_cnt + 1):
        fuselage = aircraft_config.get_fuselage(k)
        fuselage_uid = fuselage.get_uid()
        fuselage_geom = fuselage.get_loft()
        export(fuselage_geom, brep_dir, fuselage_uid)

        fuse_m_geom = fuselage.get_mirrored_loft()
        if fuse_m_geom is not None:
            export(fuse_m_geom, brep_dir, fuselage_uid + "_mirrored")

    # Wing
    for k in range(1, wing_cnt + 1):
        wing = aircraft_config.get_wing(k)
        wing_uid = wing.get_uid()
        wing_geom = wing.get_loft()
        export(wing_geom, brep_dir, wing_uid)

        wing_m_geom = wing.get_mirrored_loft()
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

            pylon_m_geom = pylon.get_mirrored_loft()
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
    log.info("Nothing to execute!")
