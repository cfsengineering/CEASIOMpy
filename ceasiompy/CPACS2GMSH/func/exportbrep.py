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

from ceasiompy.utils.ceasiomlogger import get_logger
from tigl3.import_export_helper import export_shapes

log = get_logger()

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def export(shape, brep_dir_path, uid):
    """
    Export a shape to a brep file and store its UID

    Parameters
    ----------
    shape: TiGL Cshape
        The shape to be exported
    brep_dir_path (obj): Path object
        Path object to the directory where the brep files are saved
    uid: str
        The uID of the shape

    Returns
    -------
    None

    """
    brep_dir_path.mkdir(exist_ok=True)
    brep_file = Path(brep_dir_path, f"{uid}.brep")
    export_shapes([shape], str(brep_file))
    if not brep_file.exists():
        log.error(f"Failed to export {uid}")
        raise FileNotFoundError(f"Failed to export {uid}")


def engine_export(aircraft_config, brep_dir_path, symmetric_engine):
    """
    Export the engine to a brep file

    Parameters
    ----------
    aircraft_config: TiGL AircraftConfiguration
        The aircraft configuration
    brep_dir_path (obj):
        Path object to the directory where the brep files are saved
    symmetric_engine: bool
        True if a second symmetric engine is needed


    """
    engines_config = aircraft_config.get_engines()
    if engines_config:
        nb_engine = engines_config.get_engine_count()

        for k in range(1, nb_engine + 1):

            engine = engines_config.get_engine(k)
            nacelle = engine.get_nacelle()

            if nacelle:

                center_cowl = nacelle.get_center_cowl()
                if center_cowl:
                    center_cowl_shape = center_cowl.build_loft()
                    export(center_cowl_shape, brep_dir_path, f"nacelle_center_cowl{k}")
                    if symmetric_engine:
                        export(center_cowl_shape, brep_dir_path, f"nacelle_center_cowl{k}_m")

                core_cowl = nacelle.get_core_cowl()
                if core_cowl:
                    core_cowl_shape = core_cowl.build_loft()
                    export(core_cowl_shape, brep_dir_path, f"nacelle_core_cowl{k}")
                    if symmetric_engine:
                        export(core_cowl_shape, brep_dir_path, f"nacelle_core_cowl{k}_m")

                fan_cowl = nacelle.get_fan_cowl()
                if fan_cowl:
                    fan_cowl_shape = fan_cowl.build_loft()
                    export(fan_cowl_shape, brep_dir_path, f"nacelle_fan_cowl{k}")
                    if symmetric_engine:
                        export(fan_cowl_shape, brep_dir_path, f"nacelle_fan_cowl{k}_m")


def export_brep(cpacs, brep_dir_path):
    """Function to generate and export the geometries of a .xml file

    Function 'export_brep' is a subfunction of CPACS2GMSH that generate with TiGL
    the airplane geometry of the .xml file. Then all the airplane parts are
    exported in .brep format with their uid name
    mirrored element of the airplane have the subscript _mirrored : Wing1_mirrored.brep

    Args:
        cpacs (obj): CPACS object (from cpacspy)
        brep_dir_path (obj): Path object to the directory where the brep files are saved

    Returns
    -------
    None

    """
    # get the aircraft configuration

    aircraft_config = cpacs.aircraft.configuration

    # Retrieve aircraft parts
    fuselage_cnt = aircraft_config.get_fuselage_count()
    wing_cnt = aircraft_config.get_wing_count()
    # rotor_cnt = aircraft_config.get_rotor_count()
    # rotor_blade_cnt = aircraft_config.get_rotor_blade_count()

    # Pylon configuration
    pylons_config = aircraft_config.get_engine_pylons()

    # Export into brep

    # Fuselage
    for k in range(1, fuselage_cnt + 1):
        fuselage = aircraft_config.get_fuselage(k)
        fuselage_uid = fuselage.get_uid()
        fuselage_geom = fuselage.get_loft()
        export(fuselage_geom, brep_dir_path, fuselage_uid)
    # Wing
    for k in range(1, wing_cnt + 1):
        wing = aircraft_config.get_wing(k)
        wing_uid = wing.get_uid()
        wing_geom = wing.get_loft()
        export(wing_geom, brep_dir_path, wing_uid)

        wing_m_geom = aircraft_config.get_wing(k).get_mirrored_loft()
        if wing_m_geom is not None:
            export(wing_m_geom, brep_dir_path, wing_uid + "_mirrored")

    # Pylon
    if pylons_config:
        pylon_cnt = pylons_config.get_pylon_count()
        for k in range(1, pylon_cnt + 1):
            pylon = pylons_config.get_engine_pylon(k)
            pylon_uid = pylon.get_uid()
            pylon_geom = pylon.get_loft()
            export(pylon_geom, brep_dir_path, pylon_uid)

            pylon_m_geom = pylons_config.get_engine_pylon(k).get_mirrored_loft()
            if pylon_m_geom is not None:
                export(pylon_m_geom, brep_dir_path, pylon_uid + "_mirrored")

    # Engine position

    # The following must be done in a cleaner way using the cpacs.xml file
    # or upgrading TiGL version
    # There also must be a better way to do this and the engine symmetry
    # engine_export(aircraft_config, brep_dir_path, symmetric_engine)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
