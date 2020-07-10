"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

This file will analyse the fuselage geometry from cpacs file.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-09-27
| Last modifiction: 2019-08-29 (AJ)
"""


#==============================================================================
#   IMPORTS
#==============================================================================

import numpy as np
import math

from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi

log = get_logger(__file__.split('.')[0])


#==============================================================================
#   CLASSES
#==============================================================================

"""All classes are defined inside the InputClasses/Conventional"""


#==============================================================================
#   FUNCTIONS
#==============================================================================

def check_segment_connection(fus_nb, fuse_seg_nb, fuse_sec_nb, tigl):
    """ The function checks for each segment the start and end section index
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

    log.info('---------------------------------------------')
    log.info('--- Checking fuselage segments connection ---')
    log.info('---------------------------------------------')

    # Initialising arrays
    nbmax = np.amax(fuse_seg_nb)
    seg_sec = np.zeros((nbmax,fus_nb,3))
    seg_sec_reordered = np.zeros(np.shape(seg_sec))
    sec_index = np.zeros((nbmax,fus_nb))
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

    for j in range(1,fuse_seg_nb[fus_nb-1]+1):
        (s0,e) = tigl.fuselageGetStartSectionAndElementIndex(fus_nb,j)
        (s1,e) = tigl.fuselageGetEndSectionAndElementIndex(fus_nb,j)
        seg_sec[j-1,fus_nb-1,0] = s0
        seg_sec[j-1,fus_nb-1,1] = s1
        seg_sec[j-1,fus_nb-1,2] = j
    (slpx,slpy,slpz) = tigl.fuselageGetPoint(fus_nb,1,0.0,0.0)
    seg_sec_reordered[0,fus_nb-1,:] = seg_sec[0,fus_nb-1,:]
    start_index.append(1)
    for j in range(2,fuse_seg_nb[fus_nb-1]+1):
        (x,y,z) = tigl.fuselageGetPoint(fus_nb,j,1.0,0.0)
        if x < slpx:
            (slpx,slpy,slpz) = (x,y,z)
            start_index.append(j)
            seg_sec_reordered[0,fus_nb-1,:] = seg_sec[j-1,fus_nb-1,:]
    for j in range(2,fuse_seg_nb[fus_nb-1]+1):
        end_sec = seg_sec_reordered[j-2,fus_nb-1,1]
        start_next = np.where(seg_sec[:,fus_nb-1,0]==end_sec)
        seg_sec_reordered[j-1,fus_nb-1,:] = seg_sec[start_next[0],:]
    fuse_sec_index.append(seg_sec[0,0,0])
    for j in range(2,fuse_seg_nb[fus_nb-1]+1):
         if (seg_sec_reordered[j-1,fus_nb-1,0] in fuse_sec_index) == False:
            fuse_sec_index.append(seg_sec_reordered[j-1,fus_nb-1,0])
    if (seg_sec_reordered[j-1,fus_nb-1,1] in fuse_sec_index) == False:
        fuse_sec_index.append(seg_sec_reordered[j-1,fus_nb-1,1])
    nb = np.shape(fuse_sec_index)
    if nb[0] > nbmax:
        nbmax = nb[0]
    sec_index.resize(nbmax,fus_nb)
    sec_index[0:nb[0],fus_nb-1] = fuse_sec_index[0:nb[0]]
    sec_nb.append(nb[0])

    return(sec_nb, start_index, seg_sec_reordered, sec_index)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

def rel_dist(fus_nb, sec_nb, seg_nb, tigl, seg_sec, start_index):
    """ The function evaluates the relative distance of each section
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
    (float-array) rel_sec_dis[:,0]   --Out.: Relative distance of each section
                                             from the start section of the
                                             current fuselage [m].
    (float-array) rel_sec_dis[:,1]   --Out.: Segment index relative to the
                                             section of rel_sec_dis[:,0].
    """
    log.info('---------------------------------------------')
    log.info('---- Evaluating absolute section distance ---')
    log.info('---------------------------------------------')


    rel_sec_dis = np.zeros((sec_nb,2))
    rel_sec_dist_index = np.zeros((sec_nb,2))

    # Relative distance evaluated by the difference between the x position of
    # of the 1st section of the aircraft and the x position of the jth section

    rel_sec_dis[0,0] = 0.0
    rel_sec_dis[0,1] = 0
    (slpx,slpy,slpz) = tigl.fuselageGetPoint(fus_nb,start_index,0.0,0.0)
    for j in range(1,seg_nb+1):
        k = int(seg_sec[j-1,2])
        (slpx2,slpy2,slpz2) = tigl.fuselageGetPoint(fus_nb,k,1.0,0.0)
        rel_sec_dis[j,0] = abs(slpx2-slpx)
        rel_sec_dis[j,1] = k

    return(rel_sec_dis[:,0],rel_sec_dis[:,1])


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

def fuse_geom_eval(ag, cpacs_in):
    """ Main function to evaluate the fuselage geometry.

    INPUT
    (class) ag    --Arg.: AircraftGeometry class.
    ##======= Class is defined in the InputClasses folder =======##
    (char) cpacs_in  -- Arg.: Cpacs xml file location
    OUTPUT
    (class) ag  --Out.: AircraftGeometry class updated .
    """

##===========================================================================##
    log.info('---------------------------------------------')
    log.info('-------- Analysing fuselage geometry --------')
    log.info('---------------------------------------------')

    # Opening tixi and tigl
    tixi = open_tixi(cpacs_in)
    tigl = open_tigl(tixi)

## ----------------------------------------------------------------------------
## COUNTING 1 -----------------------------------------------------------------
## Counting fuselage number ---------------------------------------------------
## ----------------------------------------------------------------------------

    fus_nb = tixi.getNamedChildrenCount('/cpacs/vehicles/aircraft/model/fuselages','fuselage')
## ----------------------------------------------------------------------------
## INITIALIZATION 1 -----------------------------------------------------------
## ----------------------------------------------------------------------------

    ag.fus_nb = fus_nb
    ag.fuse_nb = fus_nb
    i = ag.fus_nb

## ----------------------------------------------------------------------------
## COUNTING 2 -----------------------------------------------------------------
## Counting sections and segments----------------------------------------------
## ----------------------------------------------------------------------------

    double = 1
    ag.fuse_sym.append(tigl.fuselageGetSymmetry(i))
    if ag.fuse_sym[i-1] != 0:
        ag.fuse_nb += 1
        double = 2
    ag.fuse_sec_nb.append(tigl.fuselageGetSectionCount(i))
    ag.fuse_seg_nb.append(tigl.fuselageGetSegmentCount(i))
    ag.fuse_vol.append(tigl.fuselageGetVolume(i) * double)

## Checking segment and section connection and reordering them
    (ag.fuse_sec_nb, start_index, seg_sec, fuse_sec_index)\
      = check_segment_connection(fus_nb, ag.fuse_seg_nb,\
                                 ag.fuse_sec_nb, tigl)

## ----------------------------------------------------------------------------
## INITIALIZATION 2 -----------------------------------------------------------
## ----------------------------------------------------------------------------

    max_sec_nb = np.amax(ag.fuse_sec_nb)
    max_seg_nb = np.amax(ag.fuse_seg_nb)
    ag.fuse_sec_circ=np.zeros((max_sec_nb,fus_nb))
    ag.fuse_sec_width=np.zeros((max_sec_nb,fus_nb))
    ag.fuse_sec_rel_dist=np.zeros((max_sec_nb,fus_nb))
    ag.fuse_seg_index=np.zeros((max_sec_nb,fus_nb))
    ag.fuse_seg_length=np.zeros((max_seg_nb,fus_nb))
    fuse_center_section_point=np.zeros((max_sec_nb,fus_nb,3))
    ag.fuse_center_seg_point=np.zeros((max_seg_nb,ag.fuse_nb,3))
    ag.fuse_center_sec_point=np.zeros((max_sec_nb,ag.fuse_nb,3))
    ag.fuse_seg_vol=np.zeros((max_seg_nb,fus_nb))

##===========================================================================##
## ----------------------------------------------------------------------------
## FUSELAGE ANALYSIS ----------------------------------------------------------
## ----------------------------------------------------------------------------
## Aircraft total length ------------------------------------------------------

    ag.tot_length = tigl.configurationGetLength()

## Evaluating fuselage: sections circumference, segments volume and length ---
    (ag.fuse_sec_rel_dist[:,i-1],ag.fuse_seg_index[:,i-1])\
        = rel_dist(i,ag.fuse_sec_nb[i-1],ag.fuse_seg_nb[i-1],\
                   tigl,seg_sec[:,i-1,:],start_index[i-1])
    ag.fuse_length.append(ag.fuse_sec_rel_dist[-1,i-1])
    for j in range(1, ag.fuse_seg_nb[i-1]+1):
        k = int(ag.fuse_seg_index[j][i-1])
        ag.fuse_sec_circ[j][i-1]\
            = tigl.fuselageGetCircumference(i,k,1.0)
        (fpx,fpy,fpz) = tigl.fuselageGetPoint(i,k,1.0,0.0)
        (fpx2,fpy2,fpz2) = tigl.fuselageGetPoint(i,k,1.0,0.5)
        ag.fuse_seg_vol[j-1][i-1] = abs(tigl.fuselageGetSegmentVolume(i,k))
        fuse_center_section_point[j][i-1][0] = (fpx+fpx2) / 2
        fuse_center_section_point[j][i-1][1] = (fpy+fpy2) / 2
        fuse_center_section_point[j][i-1][2] = (fpz+fpz2) / 2
        hw1 = 0
        hw2 = 0
        for zeta in np.arange(0.0, 1.0, 0.001):
            (fpx,fpy,fpz) = tigl.fuselageGetPoint(i,k,1.0,zeta)
            if abs(fpz-fuse_center_section_point[j][i-1][2])< 0.01:
                if (fpy>fuse_center_section_point[j][i-1][1] and hw1 == 0):
                    hw1 = abs(fpy-fuse_center_section_point[j][i-1][1])
                elif (fpy<fuse_center_section_point[j][i-1][1] and hw2 == 0):
                    hw2 = abs(fpy-fuse_center_section_point[j][i-1][1])
                    break
        ag.fuse_sec_width[j][i-1] = hw1+hw2
        (fslpx,fslpy,fslpz) = tigl.fuselageGetPoint(1,k,0.0,0.0)
        (fslpx2,fslpy2,fslpz2) = tigl.fuselageGetPoint(1,k,1.0,0.0)
        ag.fuse_seg_length[j-1][i-1] = abs(fslpx2-fslpx)
    k = int(ag.fuse_seg_index[1][i-1])
    ag.fuse_sec_circ[0][i-1] = tigl.fuselageGetCircumference(i,k,0.0)
    (fpx,fpy,fpz) = tigl.fuselageGetPoint(i,k,0.0,0.0)
    (fpx2,fpy2,fpz2) = tigl.fuselageGetPoint(i,k,0.0,0.5)
    fuse_center_section_point[0][i-1][0] = (fpx+fpx2) / 2
    fuse_center_section_point[0][i-1][1] = (fpy+fpy2) / 2
    fuse_center_section_point[0][i-1][2] = (fpz+fpz2) / 2
    hw1 = 0
    hw2 = 0
    for zeta in np.arange(0.0, 1.0, 0.001):
        (fpx,fpy,fpz) = tigl.fuselageGetPoint(i,k,0.0,zeta)
        if abs(fpz-fuse_center_section_point[0][i-1][2])< 0.01:
            if (fpy>fuse_center_section_point[0][i-1][1] and hw1 ==0):
                hw1 = abs(fpy-fuse_center_section_point[0][i-1][1])
            elif (fpy<fuse_center_section_point[0][i-1][1] and hw2 ==0):
                hw2 = abs(fpy-fuse_center_section_point[0][i-1][1])
                break
    ag.fuse_sec_width[0][i-1] = hw1 + hw2
    ag.fuse_mean_width.append(np.mean(ag.fuse_sec_width[:,i-1]))

## Evaluating the point at the center of each segment, symmetry is considered

    a = 0
    cs = False
    for i in range(int(ag.fuse_nb)):
        if cs:
            cs = False
            continue
        for j in range(1, ag.fuse_seg_nb[i-a-1]+1):
            ag.fuse_center_seg_point[j-1][i-1][0]\
                = (fuse_center_section_point[j-1][i-a-1][0]\
                   + fuse_center_section_point[j][i-a-1][0])/2
            ag.fuse_center_seg_point[j-1][i-1][1]\
                = (fuse_center_section_point[j-1][i-a-1][1]\
                   + fuse_center_section_point[j][i-a-1][1])/2
            ag.fuse_center_seg_point[j-1][i-1][2]\
                = (fuse_center_section_point[j-1][i-a-1][2]\
                   + fuse_center_section_point[j][i-a-1][2])/2
            ag.fuse_center_sec_point[j-1][i-1][:]\
                = fuse_center_section_point[j-1][i-a-1][:]
        if ag.fuse_sym[i-1-a] != 0:
            if ag.fuse_sym[i-1-a] == 1:
                symy = 1
                symx = 1
                symz = -1
            if ag.fuse_sym[i-1-a] == 2:
                symy = -1
                symx = 1
                symz = 1
            if ag.fuse_sym[i-1-a] == 3:
                symy = 1
                symx = -1
                symz = 1
            ag.fuse_center_seg_point[:,i,0]\
                = ag.fuse_center_seg_point[:,i-1,0] * symx
            ag.fuse_center_seg_point[:,i,1]\
                = ag.fuse_center_seg_point[:,i-1,1] * symy
            ag.fuse_center_seg_point[:,i,2]\
                = ag.fuse_center_seg_point[:,i-1,2] * symz
            ag.fuse_center_sec_point[j-1][i][:]\
                = fuse_center_section_point[j-1][i-a-1][:]
            cs = True
            a += 1

# Evaluating cabin length and volume, nose length and tail_length ------------
    ex = False
    corr = 1.25 + np.zeros((1,fus_nb))
    c = False
    cabin_nb = np.zeros((1,fus_nb))
    cabin_seg = np.zeros((max_seg_nb,fus_nb))
    cabin_length = 0
    cabin_volume = 0
    nose_length = 0
    tail_length = 0
    for j in range(1,ag.fuse_seg_nb[i-1]+1):
        if (round(ag.fuse_sec_width[j][i-1],3)\
            == round(np.amax(ag.fuse_sec_width[:,i-1]),3)):
            cabin_length += ag.fuse_seg_length[j-1,i-1]
            cabin_volume += ag.fuse_seg_vol[j-1,i-1]
            cabin_seg[j-1][i-1] = 1
            c = True
        elif not c:
            nose_length += ag.fuse_seg_length[j-1,i-1]
    if cabin_length >= 0.65 * ag.fuse_length[i-1]:
    # If the aircraft is designed with 1 or more sections with
    # maximum width and the sun of their length is greater the 65%
    # of the total length, the cabin will be considered only in those
    # sections
        tail_length = ag.fuse_length[i-1] - cabin_length - nose_length
        cabin_nb[i-1] = 1
        ex = True
    while ex is False:
        c = False
        cabin_seg = np.zeros((max_seg_nb,fus_nb))
        nose_length = 0
        tail_length = 0
        cabin_length = 0
        cabin_volume = 0
        for j in range(1,ag.fuse_seg_nb[i-1]+1):
            if (ag.fuse_sec_width[j][i-1] >= (corr[i-1]\
                * ag.fuse_mean_width[i-1])):
                cabin_length += ag.fuse_seg_length[j-1,i-1]
                cabin_volume += ag.fuse_seg_vol[j-1,i-1]
                cabin_seg[j-1][i-1] = 1
                c = True
            elif c:
                tail_length += ag.fuse_seg_length[j-1,i-1]
            else:
                nose_length += ag.fuse_seg_length[j-1,i-1]
        if corr[i-1] > 0.0 and cabin_length < (0.20 * ag.fuse_length[i-1]):
            corr[i-1] -= 0.05
        else:
            ex = True

    ag.fuse_nose_length.append(nose_length)
    ag.fuse_tail_length.append(tail_length)
    ag.fuse_cabin_length.append(cabin_length)
    ag.fuse_cabin_vol.append(cabin_volume)
    ag.f_seg_sec = seg_sec
    ag.cabin_nb = cabin_nb
    ag.cabin_seg = cabin_seg
    ag.fuse_mean_width = ag.fuse_mean_width[0]

    close_tixi(tixi, cpacs_in)

# log info display ------------------------------------------------------------

    log.info('---------------------------------------------')
    log.info('---------- Geometry Evaluations -------------')
    log.info('---------- USEFUL INFO ----------------------\n'\
             + 'If fuselage or wing number is greater than 1 the '\
             + 'informations\nof each part is listed in an '\
             + 'array ordered per column progressively')
    log.info('Symmetry output: 0 = no symmetry, 1 =  x-y, '\
             + '2 = x-z, 3 = y-z planes')
    log.info('---------------------------------------------')
    log.info('---------- Fuselage Results -----------------')
    log.info('Number of fuselage [-]: ' + str(ag.fuse_nb))
    log.info('Fuselage symmetry plane [-]: ' + str(ag.fuse_sym))
    log.info('Number of fuselage sections (not counting symmetry) [-]: ' + str(ag.fuse_sec_nb))
    log.info('Number of fuselage segments (not counting symmetry) [-]: ' + str(ag.fuse_seg_nb))
    # log.info('Cabin segments array [-]: ' + str(cabin_seg))
    log.info('Fuse Length [m]: ' + str(ag.fuse_length))
    log.info('Fuse nose Length [m]: ' + str(ag.fuse_nose_length))
    log.info('Fuse cabin Length [m]: ' + str(ag.fuse_cabin_length))
    log.info('Fuse tail Length [m]: ' + str(ag.fuse_tail_length))
    log.info('Aircraft Length [m]: ' + str(ag.tot_length))
    # log.info('Circumference of each section of each fuselage [m]: \n' + str(ag.fuse_sec_circ))
    # log.info('Relative distance of each section of each fuselage [m]: \n' + str(ag.fuse_sec_rel_dist))
    # log.info('Length of each segment of each fuselage [m]: \n' + str(ag.fuse_seg_length))
    log.info('Mean fuselage width [m]: ' + str(ag.fuse_mean_width))
    # log.info('Width of each section of each fuselage [m]: \n' + str(ag.fuse_sec_width))
    # log.info('Volume of all the segmetns of each fuselage [m^3]: \n' + str(ag.fuse_seg_vol))
    log.info('Volume of each cabin [m^3]: ' + str(ag.fuse_cabin_vol))
    log.info('Volume of each fuselage [m^3]: ' + str(ag.fuse_vol))
    log.info('---------------------------------------------')

    return(ag)


#==============================================================================
#   MAIN
#==============================================================================

if __name__ == '__main__':
    log.warning('##########################################################')
    log.warning('############# ERROR NOT A STANDALONE PROGRAM #############')
    log.warning('##########################################################')
