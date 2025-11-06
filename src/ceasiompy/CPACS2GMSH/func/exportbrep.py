"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Small description of the script

| Author: Tony Govoni
| Creation: 2022-03-22

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import math
import shutil

from tigl3.import_export_helper import export_shapes
from cpacspy.cpacsfunctions import get_value_or_default
from ceasiompy.utils.geometryfunctions import elements_number
from ceasiompy.CPACS2GMSH.func.engineconversion import engine_conversion

from pathlib import Path
from typing import Union, Optional
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.stp import STP
from ceasiompy.utils.configfiles import ConfigFile
from ceasiompy.utils.guisettings import GUISettings
from ceasiompy.utils.generalclasses import Transformation

from ceasiompy import log
from ceasiompy.CPACS2GMSH import GMSH_EXPORT_PROP_XPATH
from ceasiompy.utils.commonnames import GMSH_ENGINE_CONFIG_NAME

from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.BRepTools import breptools_Write
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_SHELL
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_GTransform, BRepBuilderAPI_Transform
from OCC.Core.gp import (
    gp_Ax1,
    gp_Dir,
    gp_GTrsf,
    gp_Mat,
    gp_Pnt,
    gp_Trsf,
    gp_Vec,
    gp_XYZ,
)
from tixi3.tixi3wrapper import Tixi3Exception

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


def _apply_cpacs_transformation(shape, transf: Transformation):
    """Apply CPACS scaling, rotation, and translation to the given shape."""

    transformed_shape = shape

    scaling = (
        float(transf.scaling.x),
        float(transf.scaling.y),
        float(transf.scaling.z),
    )
    if not all(math.isclose(val, 1.0, abs_tol=1e-12) for val in scaling):
        gtrsf = gp_GTrsf()
        gtrsf.SetVectorialPart(
            gp_Mat(
                scaling[0],
                0.0,
                0.0,
                0.0,
                scaling[1],
                0.0,
                0.0,
                0.0,
                scaling[2],
            )
        )
        gtrsf.SetTranslationPart(gp_XYZ(0.0, 0.0, 0.0))
        transformed_shape = BRepBuilderAPI_GTransform(transformed_shape, gtrsf, True).Shape()

    rotations = (
        math.radians(float(transf.rotation.x)),
        math.radians(float(transf.rotation.y)),
        math.radians(float(transf.rotation.z)),
    )
    axes = (gp_Dir(1.0, 0.0, 0.0), gp_Dir(0.0, 1.0, 0.0), gp_Dir(0.0, 0.0, 1.0))
    for angle, axis in zip(rotations, axes):
        if math.isclose(angle, 0.0, abs_tol=1e-12):
            continue
        trsf = gp_Trsf()
        trsf.SetRotation(gp_Ax1(gp_Pnt(0.0, 0.0, 0.0), axis), angle)
        transformed_shape = BRepBuilderAPI_Transform(transformed_shape, trsf, True).Shape()

    translation = (
        float(transf.translation.x),
        float(transf.translation.y),
        float(transf.translation.z),
    )
    if not all(math.isclose(val, 0.0, abs_tol=1e-12) for val in translation):
        trsf = gp_Trsf()
        trsf.SetTranslation(gp_Vec(*translation))
        transformed_shape = BRepBuilderAPI_Transform(transformed_shape, trsf, True).Shape()

    return transformed_shape


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


def export_cpacs_brep(
    cpacs: CPACS,
    gui_settings: GUISettings,
    brep_dir: Path,
    engine_surface_percent: tuple[float, float] = (20, 20),
) -> None:
    # Get rotor config
    if get_value_or_default(gui_settings.tixi, GMSH_EXPORT_PROP_XPATH, False):
        try:
            rotorcraft_config = cpacs.rotorcraft.configuration
            rotor_config(rotorcraft_config, brep_dir)
        except AttributeError as e:
            log.warning(f"Could not configure rotors {e=}")

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

    # Export geometric components
    tixi = cpacs.tixi

    # Assume first model is aircraft\
    gen_geometric_xpath = "/cpacs/vehicles/aircraft/model/genericGeometryComponents"

    gen_geometric_nb = elements_number(
        tixi=tixi,
        xpath=gen_geometric_xpath,
        element="genericGeometryComponent",
        logg=False,
    )
    if gen_geometric_nb == 0:
        log.info("No Generic Geometric Components found.")
        return None

    brep_dir.mkdir(exist_ok=True, parents=True)
    cpacs_dir = (
        Path(cpacs.cpacs_file).parent
        if getattr(cpacs, "cpacs_file", None) is not None
        else Path()
    )

    for gen_geometric_idx in range(1, gen_geometric_nb + 1):
        component_xpath = (
            f"{gen_geometric_xpath}/genericGeometryComponent[{gen_geometric_idx}]"
        )
        component_uid = tixi.getTextAttribute(component_xpath, "uID")
        link_xpath = f"{component_xpath}/linkToFile"

        if not tixi.checkElement(link_xpath):
            log.warning(
                "Generic geometry component '%s' has no linkToFile element; skipping.",
                component_uid,
            )
            continue

        geometry_ref = tixi.getTextElement(link_xpath).strip()
        if geometry_ref == "":
            log.warning(
                "Generic geometry component '%s' has an empty linkToFile; skipping.",
                component_uid,
            )
            continue

        try:
            geometry_format = tixi.getTextAttribute(link_xpath, "format")
        except Tixi3Exception:
            geometry_format = ""

        geometry_format = (geometry_format or "").lower()
        source_path = Path(geometry_ref)
        if not source_path.is_absolute() and cpacs_dir:
            source_path = (cpacs_dir / source_path).resolve()

        if not source_path.exists():
            log.warning(
                "Generic geometry component '%s' references missing file '%s'; skipping.",
                component_uid,
                source_path,
            )
            continue

        target_brep = brep_dir / f"{component_uid}.brep"
        transf = Transformation()
        transf.get_cpacs_transf(tixi, component_xpath)

        if geometry_format in {"step", "stp"}:
            try:
                reader = STEPControl_Reader()
                status = reader.ReadFile(str(source_path))
                if status != IFSelect_RetDone:
                    raise RuntimeError(f"STEP reader returned status {status}")

                reader.TransferRoots()
                shape = reader.OneShape()
                transformed_shape = _apply_cpacs_transformation(shape, transf)
                breptools_Write(transformed_shape, str(target_brep))
                log.info(
                    "Converted generic geometry component '%s' from STEP to %s.",
                    component_uid,
                    target_brep.name,
                )
            except Exception as exc:
                log.warning(
                    "Failed to export generic geometry component '%s' from STEP: %s",
                    component_uid,
                    exc,
                )
        elif geometry_format == "brep":
            try:
                shutil.copy2(source_path, target_brep)
                log.info(
                    "Copied generic geometry component '%s' BREP to %s.",
                    component_uid,
                    target_brep.name,
                )
            except Exception as exc:
                log.warning(
                    "Failed to copy BREP for generic geometry component '%s': %s",
                    component_uid,
                    exc,
                )
        else:
            log.warning(
                "Unsupported generic geometry format '%s' for component '%s'.",
                geometry_format,
                component_uid,
            )


def export_stp_brep(
    stp: STP,
    gui_settings: GUISettings,
    brep_dir: Path,
) -> None:
    """
    Export parts contained in a STEP file as individual .brep files.
    Each found solid is written as: <STEP_stem>_part_<i>.brep
    If no solids are found, the whole shape is written as <STEP_stem>.brep
    """

    if not stp.stp_path.exists():
        raise FileNotFoundError(f"Geometry file not found: {stp.stp_path}")

    brep_dir.mkdir(exist_ok=True, parents=True)

    suffix = stp.stp_path.suffix.lower()

    # If already a .brep just copy it
    if suffix == ".brep":
        target_brep = brep_dir / (stp.stp_path.stem + ".brep")
        shutil.copy2(stp.stp_path, target_brep)
        log.info(f"Copied existing BREP to {target_brep}")
        return

    # If STEP/ STP try to convert to BREP using pythonocc, export each solid as its own BREP
    if suffix not in (".stp", ".step"):
        # Unsupported file type
        raise ValueError(f"Unsupported geometry file type: {stp.stp_path.suffix}")

    try:
        reader = STEPControl_Reader()
        status = reader.ReadFile(str(stp.stp_path))
        if status != IFSelect_RetDone:
            raise RuntimeError("STEP reader failed")

        reader.TransferRoots()
        shape = reader.OneShape()

        def _export_topology(topology_name: str, topo_type) -> list[Path]:
            # Export each sub-shape of the given topology as its own BREP
            explorer = TopExp_Explorer(shape, topo_type)
            exported_parts: list[Path] = []
            part_idx = 1
            while explorer.More():
                sub_shape = explorer.Current()
                part_brep = brep_dir / f"{stp.stp_path.stem}_{topology_name}_{part_idx}.brep"
                breptools_Write(sub_shape, str(part_brep))
                log.info(f"Exported STEP {topology_name} {part_idx} -> {part_brep.name}")
                exported_parts.append(part_brep)
                part_idx += 1
                explorer.Next()
            return exported_parts

        # Try solids first, then shells, finally individual faces
        exported_solids = []
        exported_shells = []
        exported_faces = []

        # If not exported_solids:
        exported_shells = _export_topology("shell", TopAbs_SHELL)

        # exported_faces = _export_topology("face", TopAbs_FACE)

        total_exported = len(exported_solids) + len(exported_shells) + len(exported_faces)

        # If no sub-shapes were found, fall back to exporting the whole shape
        target_brep = brep_dir / (stp.stp_path.stem + ".brep")
        if total_exported == 0:
            breptools_Write(shape, str(target_brep))
            log.info(
                "No individual solids/shells/faces found. "
                f"Converted STEP {stp.stp_path.name} -> BREP {target_brep.name}"
            )
        else:
            log.info(
                f"Exported {total_exported} sub-shape(s) "
                f"from {stp.stp_path.name} to {brep_dir}"
            )
        return
    except Exception as e:
        log.warning(f"Could not convert STEP to BREP ({e}). Copying STEP to brep dir instead.")
        shutil.copy2(stp.stp_path, brep_dir / stp.stp_path.name)
        return


def export_brep(
    geometry: Union[CPACS, STP],
    gui_settings: GUISettings,
    results_dir: Path,
    surf: Optional[str] = None,
    angle: Optional[str] = None,
    engine_surface_percent: tuple[float, float] = (20, 20),
) -> Path:
    """
    Function to generate and export the geometries of a .xml file

    Function 'export_brep' is a subfunction of CPACS2GMSH that generate with TiGL
    the airplane geometry of the .xml file. Then all the airplane parts are
    exported in .brep format with their uid name
    mirrored element of the airplane have the subscript _mirrored : Wing1_mirrored.brep
    """

    # Create corresponding brep directory.
    if surf is None:
        brep_dir = Path(results_dir, "brep_files")
    else:
        brep_dir = Path(results_dir, f"brep_files_{surf}_{angle}")

    if isinstance(geometry, CPACS):
        export_cpacs_brep(
            cpacs=geometry,
            gui_settings=gui_settings,
            brep_dir=brep_dir,
            engine_surface_percent=engine_surface_percent,
        )

    if isinstance(geometry, STP):
        export_stp_brep(
            stp=geometry,
            gui_settings=gui_settings,
            brep_dir=brep_dir,
        )

    return brep_dir
