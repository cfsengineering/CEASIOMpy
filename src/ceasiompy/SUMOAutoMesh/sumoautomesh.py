"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to create a simple SU2 mesh from SUMO file (.smx)

| Author : Aidan Jungo
| Creation: 2018-10-29

TODO:

    * Add support on WindowsOS
    * Add multi-pass mesh with tetgen option...
    * Add automatic refine mesh if error ? (increasing refine_level)

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import math
import shutil
import platform

from cpacspy.cpacsfunctions import (
    open_tixi,
    get_value,
    create_branch,
    get_value_or_default,
)

from ceasiompy.utils.ceasiompyutils import (
    call_main,
    run_software,
    aircraft_name,
    get_results_directory,
    get_reasonable_nb_cpu,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy import log

from ceasiompy.utils.commonxpaths import (
    SU2MESH_XPATH,
    SUMO_REFINE_LEVEL_XPATH,
    SUMOFILE_XPATH,
    SPECIFIED_SUMOFILE_XPATH,
)

from ceasiompy.SUMOAutoMesh import MODULE_NAME
from ceasiompy.CPACS2SUMO import MODULE_NAME as CPACS2SUMO

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_part_count(sumo, ROOT_XPATH, part_name):
    """Function to get the count of a specific part 'part_name' in a SUMO file.

    Args:
        sumo (object): TIXI object representing the SUMO file.
        ROOT_XPATH (str): XPath to the root of the SUMO file.
        part_name: name of the part for which the count is to be returned.

    """

    if sumo.checkElement(ROOT_XPATH):
        part_cnt = sumo.getNamedChildrenCount(ROOT_XPATH, part_name)
        log.info(f"{part_cnt} {part_name} has been found.")
        return part_cnt

    log.warning(f"No {part_name} has been found in this SUMO file!")
    return 0


def update_fuselage_caps(sumo, body_xpath):
    """Function to write the correct fuselage (body) caps in the SUMO file.

    Args:
        sumo (object): TIXI object representing the SUMO file.
        body_xpath (str): XPath to the body in the SUMO file.

    """

    # Remove existing fuselage caps
    cap_cnt = sumo.getNamedChildrenCount(body_xpath, "Cap")
    for i in range(1, cap_cnt + 1):
        cap_xpath = body_xpath + f"/Cap[{i}]"
        sumo.removeElement(cap_xpath)

    # Add new caps
    sumo.addTextElementAtIndex(body_xpath, "Cap", "", 1)
    cap1_xpath = body_xpath + "/Cap[1]"
    sumo.addTextAttribute(cap1_xpath, "height", "0")
    sumo.addTextAttribute(cap1_xpath, "shape", "LongCap")
    sumo.addTextAttribute(cap1_xpath, "side", "south")

    cap2_xpath = body_xpath + "/Cap[2]"
    sumo.addTextElementAtIndex(body_xpath, "Cap", "", 2)
    sumo.addTextAttribute(cap2_xpath, "height", "0")
    sumo.addTextAttribute(cap2_xpath, "shape", "LongCap")
    sumo.addTextAttribute(cap2_xpath, "side", "north")


def add_mesh_parameters(sumo_file_path, refine_level=0.0):
    """Function to add mesh parameter options in SUMO geometry (.smx file)

    Function 'add_mesh_parameters' is used to add meshing parameters in the SUMO geometry (.smx)
    to get finer meshes. The only user input parameter is the refinement level which allows to
    generate finer meshes. 0 correspond to the default (close to values obtain with SUMO GUI).
    Then, increasing refinement level of 1 correspond to approximately two time more cells in the
    mesh. You can also use float number (e.g. refine_level=2.4).

    Source :
        * sumo source code: https://www.larosterna.com/oss/

    Args:
        sumo_file_path (Path): Path to the SUMO geometry (.smx)
        refine_level (float): Refinement level of the mesh. Default is 1.0

    """

    REFINE_RATIO = 0.6  # to get approx. double mesh cell when +1 on "refine_level"
    refine_factor = REFINE_RATIO**refine_level
    log.info("Refinement factor is {}".format(refine_factor))

    # Open SUMO (.smx) with tixi library
    sumo = open_tixi(sumo_file_path)
    ROOT_XPATH = "/Assembly"

    body_cnt = get_part_count(sumo, ROOT_XPATH, part_name="BodySkeleton")

    for i_body in range(body_cnt):
        body_xpath = ROOT_XPATH + f"/BodySkeleton[{i_body + 1}]"

        circ_list = []
        min_radius = 10e6

        # Go through every Boby frame (fuselage sections)
        frame_cnt = sumo.getNamedChildrenCount(body_xpath, "BodyFrame")
        for i_sec in range(1, frame_cnt + 1):
            frame_xpath = body_xpath + f"/BodyFrame[{i_sec}]"

            # Estimate circumference and add to the list
            height = sumo.getDoubleAttribute(frame_xpath, "height")
            width = sumo.getDoubleAttribute(frame_xpath, "width")
            circ_list.append(2 * math.pi * math.sqrt((height**2 + width**2) / 2))

            # Get overall minimum radius (semi-minor axi for ellipse)
            min_radius = min(min_radius, height, width)

        mean_circ = sum(circ_list) / len(circ_list)

        # Calculate mesh parameters from inputs and geometry
        # In SUMO, minlen is min_radius/2, but sometimes it leads to meshing errors
        maxlen = (0.08 * mean_circ) * refine_factor
        minlen = min(0.1 * maxlen, min_radius / 4) * refine_factor

        # Add mesh parameters in the XML file (.smx)
        meshcrit_xpath = body_xpath + "/MeshCriterion"
        if not sumo.checkElement(meshcrit_xpath):
            sumo.addTextElement(body_xpath, "MeshCriterion", "")

        sumo.addTextAttribute(meshcrit_xpath, "defaults", "false")
        sumo.addTextAttribute(meshcrit_xpath, "maxlen", str(maxlen))
        sumo.addTextAttribute(meshcrit_xpath, "minlen", str(minlen))
        sumo.addTextAttribute(meshcrit_xpath, "maxphi", "30")
        sumo.addTextAttribute(meshcrit_xpath, "maxstretch", "6")
        sumo.addTextAttribute(meshcrit_xpath, "nvmax", "1073741824")
        sumo.addTextAttribute(meshcrit_xpath, "xcoarse", "false")

        update_fuselage_caps(sumo, body_xpath)

    wing_cnt = get_part_count(sumo, ROOT_XPATH, part_name="WingSkeleton")

    for i_wing in range(wing_cnt):
        wing_xpath = ROOT_XPATH + f"/WingSkeleton[{i_wing + 1}]"

        chord_list = []

        # Go through every WingSection
        section_cnt = sumo.getNamedChildrenCount(wing_xpath, "WingSection")
        for i_sec in range(1, section_cnt + 1):
            section_xpath = wing_xpath + f"/WingSection[{i_sec}]"
            chord_list.append(sumo.getDoubleAttribute(section_xpath, "chord"))

        # In SUMO refChord is calculated from Area and Span, but this is not
        # trivial to get those value for each wing from the .smx file
        ref_chord = sum(chord_list) / len(chord_list)

        # Calculate mesh parameter from inputs and geometry
        maxlen = (0.15 * ref_chord) * refine_factor
        minlen = (0.08 * maxlen) * refine_factor
        # in sumo it is 0.08*maxlen or 0.7*min leading edge radius...?

        # Default value in SUMO
        lerfactor = 1 / 4.0
        terfactor = 1 / 4.0

        if refine_level > 1:
            lerfactor = 1 / (4.0 + 0.5 * (refine_level - 1))
            terfactor = 1 / (4.0 + 0.5 * (refine_level - 1))

        # Add mesh parameters in the XML file (.smx)
        meshcrit_xpath = wing_xpath + "/WingCriterion"
        if not sumo.checkElement(meshcrit_xpath):
            sumo.addTextElement(wing_xpath, "WingCriterion", "")

        sumo.addTextAttribute(meshcrit_xpath, "defaults", "false")
        sumo.addTextAttribute(meshcrit_xpath, "maxlen", str(maxlen))
        sumo.addTextAttribute(meshcrit_xpath, "minlen", str(minlen))
        sumo.addTextAttribute(meshcrit_xpath, "lerfactor", str(lerfactor))
        sumo.addTextAttribute(meshcrit_xpath, "terfactor", str(terfactor))
        sumo.addTextAttribute(meshcrit_xpath, "maxphi", "30")
        sumo.addTextAttribute(meshcrit_xpath, "maxstretch", "6")
        sumo.addTextAttribute(meshcrit_xpath, "nvmax", "1073741824")
        sumo.addTextAttribute(meshcrit_xpath, "xcoarse", "false")

    sumo.save(str(sumo_file_path))


def main(cpacs: CPACS, wkdir: Path):
    """Function to create a simple SU2 mesh form an SUMO file (.smx)

    Function 'create_mesh' is used to generate an unstructured mesh with  SUMO
    (which integrate Tetgen for the volume mesh) using a SUMO (.smx) geometry
    file as input.
    Meshing option could be change manually (only in the script for now)

    Source :
        * sumo help, tetgen help (in the folder /doc)

    """
    tixi = cpacs.tixi

    cpacs_to_sumo_wkdir = get_results_directory(CPACS2SUMO)
    su2_mesh_path = Path(cpacs_to_sumo_wkdir, "ToolOutput.smx")

    if tixi.checkElement(SUMOFILE_XPATH):
        sumo_file_path = Path(get_value(tixi, SUMOFILE_XPATH))
    else:
        sumo_file_path = Path(get_value(tixi, SPECIFIED_SUMOFILE_XPATH))

    if not sumo_file_path.exists():
        raise FileNotFoundError(f"No SUMO file has been found at: {sumo_file_path}")

    refine_level = get_value_or_default(tixi, SUMO_REFINE_LEVEL_XPATH, 1.0)
    log.info(f"Mesh refinement level: {refine_level}")
    add_mesh_parameters(sumo_file_path, refine_level)

    # Tetgen option, see the help for more options
    output = "smx"
    options = "pq1.16VY"
    arguments = [
        "-batch",
        f"-output={output}",
        f"-tetgen-options={options}",
        str(sumo_file_path),
    ]

    current_os = platform.system()

    nb_cpu = get_reasonable_nb_cpu()

    if (current_os == "Darwin") or (current_os == "Linux"):
        log.info("Your OS is supported by SUMOAutoMesh.")

        # The complete command line to run is:
        # /Applications/SUMO/dwfsumo.app/Contents/MacOS/dwfsumo
        # -batch output=su2 -tetgen-options=pq1.16VY ToolOutput.smx

        # On MacOS, the symbolic link to "sumo" as it is done on Linux is not working, an error
        # with QT occurs when trying to run the command.
        # The folder which contains the 'dwfsumo' executable must be in the PATH

        run_software(
            software_name="dwfsumo",
            arguments=arguments,
            wkdir=wkdir,
            with_mpi=False,
            nb_cpu=nb_cpu
        )

    elif current_os == "Windows":
        log.info("Your OS is Windows")
        # TODO: implement this part and test on Windows

        log.warning("OS not supported yet by SUMOAutoMesh!")
        raise NotImplementedError("OS not supported yet!")

    else:
        raise OSError("OS not recognize!")

    # Copy the mesh in the MESH directory
    su2_mesh_name = aircraft_name(tixi) + "_baseline.su2"
    su2_mesh_out_path = Path(wkdir, su2_mesh_name)

    if not os.path.exists(su2_mesh_path):
        log.error(f"SU2 mesh file does not exist: {su2_mesh_path}")
        return

    shutil.copyfile(su2_mesh_path, su2_mesh_out_path)

    if not su2_mesh_out_path.exists():
        raise ValueError("No SU2 Mesh file has been generated!")
    else:
        log.info("A SU2 Mesh has been correctly generated.")

        create_branch(tixi, SU2MESH_XPATH)
        tixi.updateTextElement(SU2MESH_XPATH, str(su2_mesh_out_path))
        su2_mesh_path.unlink()

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    call_main(main, MODULE_NAME)
