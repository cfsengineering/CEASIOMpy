"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to create a simple SU2 mesh from SUMO file (.smx)

Python version: >=3.8

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

import math
import platform
import shutil
from pathlib import Path

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import aircraft_name, get_results_directory, run_software
from ceasiompy.utils.commonxpath import (
    SU2MESH_XPATH,
    SUMO_REFINE_LEVEL_XPATH,
    SUMOFILE_XPATH,
    SUMO_OUTPUT_MESH_FORMAT_XPATH,
    EDGE_MESH_XPATH,
    EDGE_ABOC_XPATH,
)
from ceasiompy.utils.moduleinterfaces import get_toolinput_file_path, get_tooloutput_file_path
from cpacspy.cpacsfunctions import create_branch, get_value_or_default, open_tixi

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name


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
        * sumo source code: https://www.larosterna.com/products/open-source

    Args:
        sumo_file_path (Path): Path to the SUMO geometry (.smx)
        refine_level (float): Refinement level of the mesh. Default is 1.0

    """

    REFINE_RATIO = 0.6  # to get approx. double mesh cell when +1 on "refine_level"
    refine_factor = REFINE_RATIO**refine_level
    log.info(f"Refinement factor is {refine_factor:.3f}")

    # Open SUMO (.smx) with tixi library
    sumo = open_tixi(sumo_file_path)
    ROOT_XPATH = "/Assembly"

    body_cnt = get_part_count(sumo, ROOT_XPATH, part_name="BodySkeleton")

    for i_body in range(body_cnt):
        body_xpath = ROOT_XPATH + f"/BodySkeleton[{i_body+1}]"

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
        wing_xpath = ROOT_XPATH + f"/WingSkeleton[{i_wing+1}]"

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


def create_mesh(cpacs_path, cpacs_out_path):
    """Function to create a simple SU2 mesh form an SUMO file (.smx)

    Function 'create_mesh' is used to generate an unstructured mesh with  SUMO
    (which integrate Tetgen for the volume mesh) using a SUMO (.smx) geometry
    file as input.
    Meshing option could be change manually (only in the script for now)

    Source :
        * sumo help, tetgen help (in the folder /doc)

    Args:
        cpacs_path (Path): Path to the CPACS file
        cpacs_out_path (Path): Path to the output CPACS file

    """

    tixi = open_tixi(cpacs_path)

    output = get_value_or_default(tixi, SUMO_OUTPUT_MESH_FORMAT_XPATH, "su2")

    if output == "su2":
        file_extension = "su2"
    elif output == "edge":
        file_extension = "bmsh"
    else:
        raise ValueError("Unsupported output format. Use 'su2' or 'edge'")

    log.info(f"The output mesh format is {file_extension}")

    sumo_results_dir = get_results_directory("SUMOAutoMesh")
    mesh_path = Path(sumo_results_dir, f"ToolOutput.{file_extension}")

    sumo_file_path = Path(get_value_or_default(tixi, SUMOFILE_XPATH, ""))
    if not sumo_file_path.exists():
        raise FileNotFoundError(f"No SUMO file has been found at: {sumo_file_path}")

    log.info("Setting mesh parameters...")
    refine_level = get_value_or_default(tixi, SUMO_REFINE_LEVEL_XPATH, 1.0)
    log.info(f"Mesh refinement level: {refine_level}")
    add_mesh_parameters(sumo_file_path, refine_level)

    # Tetgen option, see the help for more options
    # output = "su2"
    options = "pq1.16VY"
    arguments = [
        "-batch",
        f"-output={output}",
        f"-tetgen-options={options}",
        str(sumo_file_path),
    ]

    current_os = platform.system()

    if current_os == "Darwin":
        log.info("Your OS is MacOS")

        # The complete command line to run is:
        # /Applications/SUMO/dwfsumo.app/Contents/MacOS/dwfsumo
        # -batch output=su2 -tetgen-options=pq1.16VY ToolOutput.smx

        # On MacOS, the symbolic link to "sumo" as it is done on Linux is not working, an error
        # with QT occurs when trying to run the command.
        # The folder which contains the 'dwfsumo' executable must be in the PATH

        run_software("dwfsumo", arguments, sumo_results_dir)

    elif current_os == "Linux":
        log.info("Your OS is Linux")

        # The complete command line to run is:
        # sumo -batch -output=su2 -tetgen-options=pq1.16VY ToolOutput.smx

        run_software("dwfsumo", arguments, sumo_results_dir)

    elif current_os == "Windows":
        log.info("Your OS is Windows")
        # TODO: implement this part and test on Windows

        log.warning("OS not supported yet by SUMOAutoMesh!")
        raise NotImplementedError("OS not supported yet!")

    else:
        raise OSError("OS not recognize!")

    # Copy the mesh in the MESH directory
    mesh_name = aircraft_name(tixi) + f"_baseline.{file_extension}"
    mesh_out_path = Path(sumo_results_dir, mesh_name)
    shutil.copyfile(mesh_path, mesh_out_path)

    if not mesh_out_path.exists():
        raise ValueError("No mesh file has been generated!")

    log.info(f"A {output} mesh has been correctly generated.")

    if output == "su2":
        create_branch(tixi, SU2MESH_XPATH)
        tixi.updateTextElement(SU2MESH_XPATH, str(mesh_out_path))
        mesh_path.unlink()

    elif output == "edge":
        create_branch(tixi, EDGE_MESH_XPATH)
        tixi.updateTextElement(EDGE_MESH_XPATH, str(mesh_out_path))

        edge_aboc_path = Path(sumo_results_dir, "ToolOutput.aboc")   # commented by Mengmeng
        edge_aboc_name = aircraft_name(tixi) + f"_baseline.aboc"
        aboc_out_path = Path(sumo_results_dir, edge_aboc_name)
        shutil.copyfile(edge_aboc_path, aboc_out_path)

        create_branch(tixi, EDGE_ABOC_XPATH)
        tixi.updateTextElement(EDGE_ABOC_XPATH, str(aboc_out_path))

        mesh_path.unlink()

    tixi.save(str(cpacs_out_path))


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):
    log.info("----- Start of " + MODULE_NAME + " -----")

    # Call create_mesh with the desired output format
    create_mesh(cpacs_path, cpacs_out_path)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":
    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
