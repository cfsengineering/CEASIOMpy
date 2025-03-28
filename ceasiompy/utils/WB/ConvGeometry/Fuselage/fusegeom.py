"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

This file will analyse the fuselage geometry from cpacs file.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-09-27

"""


# =================================================================================================
#   IMPORTS
# =================================================================================================

import numpy as np

from ceasiompy import log


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def fuselage_check_segment_connection(fus_nb, fuse_seg_nb, tigl):
    """The function checks for each segment the start and end section index
        and it reorders them.

    ARGUMENTS
    (int) fus_nb          -- Arg.: Number of fuselage.
    (int) fuse_seg_nb   -- Arg.: Number of segments.
    (int) fuse_sec_nb   -- Arg.: Number of sections.
    (char) tigl         -- Arg.: Tigl handle.

    RETURN
    (int) sec_nb             --Out.: Number of sections for each fuselage.
    (int) start_index        --Out.: Start section index for each fuselage.
    (float-array) seg_sec_reordered --Out.: Reordered segments with
                                            respective start and end section
                                            for each fuselage.
    (float_array) sec_index  --Out.: List of section index reordered.
    """

    log.info("---------------------------------------------")
    log.info("--- Checking fuselage segments connection ---")
    log.info("---------------------------------------------")

    # Initialising arrays
    nbmax = np.amax(fuse_seg_nb)
    seg_sec = np.zeros((nbmax, fus_nb, 3))
    seg_sec_reordered = np.zeros(np.shape(seg_sec))
    sec_index = np.zeros((nbmax, fus_nb))
    fuse_sec_index = []
    start_index = []
    sec_nb = []

    # First for each segment the start and end sections are found, then
    # they are reordered considering that the end section of a segment
    # is the start section of the next one.
    # The first section is the one that has the lowest x position.
    # The code works if a section is defined and not used in the segment
    # definition and if the segments are not defined
    # with a significant order.
    # WARNING The code does not work if a segment is defined
    #         and then not used.
    #         The aircraft should be designed along the x-axis
    #         and on the x-y plane

    for j in range(1, fuse_seg_nb[fus_nb - 1] + 1):
        (s0, e) = tigl.fuselageGetStartSectionAndElementIndex(fus_nb, j)
        (s1, e) = tigl.fuselageGetEndSectionAndElementIndex(fus_nb, j)
        seg_sec[j - 1, fus_nb - 1, 0] = s0
        seg_sec[j - 1, fus_nb - 1, 1] = s1
        seg_sec[j - 1, fus_nb - 1, 2] = j
    slpx = tigl.fuselageGetPoint(fus_nb, 1, 0.0, 0.0)[0]
    seg_sec_reordered[0, fus_nb - 1, :] = seg_sec[0, fus_nb - 1, :]
    start_index.append(1)
    for j in range(2, fuse_seg_nb[fus_nb - 1] + 1):
        x = tigl.fuselageGetPoint(fus_nb, j, 1.0, 0.0)[0]
        if x < slpx:
            slpx = x
            start_index.append(j)
            seg_sec_reordered[0, fus_nb - 1, :] = seg_sec[j - 1, fus_nb - 1, :]
    for j in range(2, fuse_seg_nb[fus_nb - 1] + 1):
        end_sec = seg_sec_reordered[j - 2, fus_nb - 1, 1]
        start_next = np.where(seg_sec[:, fus_nb - 1, 0] == end_sec)
        seg_sec_reordered[j - 1, fus_nb - 1, :] = seg_sec[start_next[0], :]
    fuse_sec_index.append(seg_sec[0, 0, 0])
    for j in range(2, fuse_seg_nb[fus_nb - 1] + 1):
        if seg_sec_reordered[j - 1, fus_nb - 1, 0] not in fuse_sec_index:
            fuse_sec_index.append(seg_sec_reordered[j - 1, fus_nb - 1, 0])
    if seg_sec_reordered[j - 1, fus_nb - 1, 1] not in fuse_sec_index:
        fuse_sec_index.append(seg_sec_reordered[j - 1, fus_nb - 1, 1])
    nb = np.shape(fuse_sec_index)
    if nb[0] > nbmax:
        nbmax = nb[0]
    print(nbmax, fus_nb)
    print("--------------========================-------")
    sec_index.resize(nbmax, fus_nb, refcheck=False)

    sec_index[0 : nb[0], fus_nb - 1] = fuse_sec_index[0 : nb[0]]
    sec_nb.append(nb[0])

    return sec_nb, start_index, seg_sec_reordered


def rel_dist(fus_nb, sec_nb, seg_nb, tigl, seg_sec, start_index):
    """The function evaluates the relative distance of each section
        used from the start section.

    ARGUMENTS
    (int) fus_nb          -- Arg.: Number of fuselage.
    (int) sec_nb        -- Arg.: Number of sections of the current fuselage.
    (int) seg_nb        -- Arg.: Number of segments of the current fuselage.
    (char) tigl         -- Arg.: Tigl handle.
    (float-array) seg_sec_reordered --Arg.: Reordered segments with
                                            respective start and end section
                                            for each fuselage.
    (int) start_index   --Arg.: Start section index of the current fuselage.

    RETURN
    (float-array) rel_section_dist[:,0]   --Out.: Relative distance of each section
                                             from the start section of the
                                             current fuselage [m].
    (float-array) rel_section_dist[:,1]   --Out.: Segment index relative to the
                                             section of rel_section_dist[:,0].
    """

    log.info("Evaluating absolute section distance")

    rel_section_dist = np.zeros((sec_nb, 2))
    # rel_section_distt_index = np.zeros((sec_nb, 2))

    # Relative distance evaluated by the difference between the x position of
    # of the 1st section of the aircraft and the x position of the jth section

    rel_section_dist[0, 0] = 0.0
    rel_section_dist[0, 1] = 0

    slpx, _, _ = tigl.fuselageGetPoint(fus_nb, start_index, 0.0, 0.0)
    for j in range(1, seg_nb + 1):
        k = int(seg_sec[j - 1, 2])
        slpx2, _, _ = tigl.fuselageGetPoint(fus_nb, k, 1.0, 0.0)
        rel_section_dist[j, 0] = abs(slpx2 - slpx)
        rel_section_dist[j, 1] = k

    return (rel_section_dist[:, 0], rel_section_dist[:, 1])


# =================================================================================================
#   MAIN
# =================================================================================================

if __name__ == "__main__":

    log.info("Nothing to execute!")
