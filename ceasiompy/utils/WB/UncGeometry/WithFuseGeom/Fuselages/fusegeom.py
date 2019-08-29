"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The scrpt will analyse the fuselage geometry from cpacs file for an
unconventional aircraft.

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

from ceasiompy.utils.cpacsfunctions import open_tixi,open_tigl, close_tixi

log = get_logger(__file__.split('.')[0])


#==============================================================================
#   CLASSES
#==============================================================================

"""All classes are defined inside the classes folder and into the
   InputClasses/Uconventional folder"""


#==============================================================================
#   FUNCTIONS
#==============================================================================

def check_segment_connection(f_nb, fuse_seg_nb, fuse_sec_nb, tigl):
    """ The function checks for each segment the start and end section index
        and to reorder them.

    ARGUMENTS
    (int) f_nb          -- Arg.: Number of fuselages.
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

    log.info('---------------------------------------------------------------')
    log.info('---------- Checking fuselage segments connection --------------')
    log.info('---------------------------------------------------------------')

    # Initialising arrays
    nbmax = np.amax(fuse_seg_nb)
    seg_sec = np.zeros((nbmax,f_nb,3))
    seg_sec_reordered = np.zeros(np.shape(seg_sec))
    sec_index = np.zeros((nbmax,f_nb))
    start_index = []
    sec_nb = []

    # First for each segment the start and end section are found, then
    # they are reordered considering that the end section of a segment
    # is the start sectio of the next one.
    # The first section is the one that has the lowest x position.
    # The code works if a section is defined and not used in the segment
    # definition and if the segments are not defined
    # with a consequential order.
    # WARNING The code does not work if a segment is defined
    #         and then not used.
    #         The aircraft should be designed along the x axis
    #         and on the x-y plane

    for i in range(1,f_nb+1):
        fuse_sec_index = []
        for j in range(1,fuse_seg_nb[i-1]+1):
            (seg_sec[j-1,i-1,0],e)\
                = tigl.fuselageGetStartSectionAndElementIndex(i,j)
            (seg_sec[j-1,i-1,1],e)\
                = tigl.fuselageGetEndSectionAndElementIndex(i,j)
            seg_sec[j-1,i-1,2] = j
        (slpx,slpy,slpz) = tigl.fuselageGetPoint(i,1,0.0,0.0)
        seg_sec_reordered[0,i-1,:] = seg_sec[0,i-1,:]
        start_index.append(1)
        for j in range(2,fuse_seg_nb[i-1]+1):
            (x,y,z) = tigl.fuselageGetPoint(i,j,1.0,0.0)
            if x < slpx:
                (slpx,slpy,slpz) = (x,y,z)
                start_index.append(j)
                seg_sec_reordered[0,i-1,:] = seg_sec[j-1,i-1,:]
        for j in range(2,fuse_seg_nb[i-1]+1):
            end_sec = seg_sec_reordered[j-2,i-1,1]
            start_next = np.where(seg_sec[:,i-1,0]==end_sec)
            seg_sec_reordered[j-1,i-1,:] = seg_sec[start_next[0],i-1,:]
        fuse_sec_index.append(seg_sec[0,i-1,0])
        for j in range(2,fuse_seg_nb[i-1]+1):
            if (seg_sec_reordered[j-1,i-1,0] in fuse_sec_index) == False:
                fuse_sec_index.append(seg_sec_reordered[j-1,i-1,0])
        if (seg_sec_reordered[-1,i-1,1] in fuse_sec_index) == False:
            fuse_sec_index.append(seg_sec_reordered[-1,i-1,1])
        nb = np.shape(fuse_sec_index)
        if nb[0] > nbmax:
            nbmax = nb[0]
        sec_index.resize(nbmax,f_nb)
        sec_index[0:nb[0],i-1] = fuse_sec_index[0:nb[0]]
        sec_nb.append(nb[0])

    return(sec_nb, start_index, seg_sec_reordered, sec_index)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

def rel_dist(i, sec_nb, seg_nb, tigl, seg_sec, start_index):
    """ Function to evaluate the relative distance of each section
        used from the start section.

    ARGUMENTS
    (int) i             -- Arg.: Index of the current fuselage.
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
    log.info('-----------------------------------------------------------')
    log.info('---------- Evaluating absolute section distance -----------')
    log.info('-----------------------------------------------------------')


    rel_sec_dis = np.zeros((sec_nb,2))
    rel_sec_dist_index = np.zeros((sec_nb,2))

    # Relative distance evaluated by the difference between the x position of
    # of the 1st section of the aircraft and the x position of the jth section

    rel_sec_dis[0,0] = 0.0
    rel_sec_dis[0,1] = 0
    (slpx,slpy,slpz) = tigl.fuselageGetPoint(i,start_index,0.0,0.0)
    for j in range(1,seg_nb+1):
        k = int(seg_sec[j-1,2])
        (slpx2,slpy2,slpz2) = tigl.fuselageGetPoint(i,k,1.0,0.0)
        rel_sec_dis[j,0] = abs(slpx2-slpx)
        rel_sec_dis[j,1] = k

    return(rel_sec_dis[:,0],rel_sec_dis[:,1])


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

def fuse_geom_eval(f_nb, h_min, fuse_thick, F_FUEL, afg, cpacs_in):
    """ Main function to evaluate the fuselage geometry

    INPUT
    (int) f_nb              --Arg.: Number of fuselages.
    (float) h_min           --Arg.: Minimum height for the fuselage [m].
    (float) fuse_thick      --Arg.: Thickness of the fuselage [mm].
    (float-array) F_FUEL    --Arg.: Percentage of the total volume of
                                    the fuel tank fuselage, used for
                                    fuel straging (set False if fuselage
                                    is ment for payload/passengers).
    (class) afg    --Arg.: AircraftGeometry class look at
                          aircraft_geometry_class.py in the
                          classes folder for explanation.
    (char) cpacs_in  -- Arg.: Cpacs xml file location

    OUTPUT
    (class) afg      --Out.: Updated aircraft_geometry class
    """

##===========================================================================##
    log.info('-----------------------------------------------------------')
    log.info('---------- Analysing fuselage geometry --------------------')
    log.info('-----------------------------------------------------------')

    # Opening tixi and tigl
    tixi = open_tixi(cpacs_in)
    tigl = open_tigl(tixi)

## ----------------------------------------------------------------------------
## INITIALIZATION 1 -----------------------------------------------------------
## ----------------------------------------------------------------------------

    afg.f_nb = f_nb

## ----------------------------------------------------------------------------
## COUNTING  ------------------------------------------------------------------
## Counting sections and segments----------------------------------------------
## ----------------------------------------------------------------------------

    for i in range(1,afg.f_nb + 1):
        afg.fuse_sec_nb.append(tigl.fuselageGetSectionCount(i))
        afg.fuse_seg_nb.append(tigl.fuselageGetSegmentCount(i))
        afg.fuse_vol.append(tigl.fuselageGetVolume(i))
        afg.fuse_surface.append(tigl.fuselageGetSurfaceArea(i))

## Checking segment and section connection and reordering them
    (afg.fuse_sec_nb, start_index, seg_sec, fuse_sec_index)\
      = check_segment_connection(afg.f_nb, afg.fuse_seg_nb,\
                                 afg.fuse_sec_nb, tigl)
    afg.f_seg_sec = seg_sec

## ----------------------------------------------------------------------------
## INITIALIZATION 2 -----------------------------------------------------------
## ----------------------------------------------------------------------------

    max_sec_nb = np.amax(afg.fuse_sec_nb)
    max_seg_nb = np.amax(afg.fuse_seg_nb)
    afg.fuse_sec_per = np.zeros((max_sec_nb,afg.f_nb))
    afg.fuse_sec_width = np.zeros((max_sec_nb,afg.f_nb))
    afg.fuse_sec_height = np.zeros((max_sec_nb,afg.f_nb))
    afg.fuse_sec_rel_dist = np.zeros((max_sec_nb,afg.f_nb))
    afg.fuse_seg_index = np.zeros((max_sec_nb,afg.f_nb))
    afg.fuse_seg_length = np.zeros((max_seg_nb,afg.f_nb))
    afg.fuse_center_section_point = np.zeros((max_sec_nb,afg.f_nb,3))
    afg.fuse_center_seg_point = np.zeros((max_sec_nb,afg.f_nb,3))
    afg.fuse_seg_vol = np.zeros((max_seg_nb,afg.f_nb))
    x1 = np.zeros((max_sec_nb,afg.f_nb))
    y1 = np.zeros((max_sec_nb,afg.f_nb))
    z1 = np.zeros((max_sec_nb,afg.f_nb))
    x2 = np.zeros((max_sec_nb,afg.f_nb))
    y2 = np.zeros((max_sec_nb,afg.f_nb))
    z2 = np.zeros((max_sec_nb,afg.f_nb))

##===========================================================================##
## ----------------------------------------------------------------------------
## FUSELAGE ANALYSIS ----------------------------------------------------------
## ----------------------------------------------------------------------------

## Aircraft total length ------------------------------------------------------
    afg.tot_length = tigl.configurationGetLength()

## Evaluating fuselage: sections perimeter, segments volume and length ---
    for i in range(1,afg.f_nb+1):
        (afg.fuse_sec_rel_dist[:,i-1],afg.fuse_seg_index[:,i-1])\
            = rel_dist(i, afg.fuse_sec_nb[i-1], afg.fuse_seg_nb[i-1],\
                       tigl, seg_sec[:,i-1,:], start_index[i-1])
        afg.fuse_length.append(round(afg.fuse_sec_rel_dist[-1,i-1],3))
        for j in range(1, afg.fuse_seg_nb[i-1]+1):
            k = int(afg.fuse_seg_index[j][i-1])
            afg.fuse_sec_per[j][i-1]\
                = tigl.fuselageGetCircumference(i,k,1.0)
            (fpx,fpy,fpz) = tigl.fuselageGetPoint(i,k,1.0,0.0)
            (fpx2,fpy2,fpz2) = tigl.fuselageGetPoint(i,k,1.0,0.5)
            afg.fuse_seg_vol[j-1][i-1] = tigl.fuselageGetSegmentVolume(i,k)
            afg.fuse_center_section_point[j][i-1][0] = (fpx+fpx2) / 2
            afg.fuse_center_section_point[j][i-1][1] = (fpy+fpy2) / 2
            afg.fuse_center_section_point[j][i-1][2] = (fpz+fpz2) / 2
            hw1 = 0.0
            hw2 = 0.0
            for zeta in np.arange(0.0, 1.0, 0.001):
                (fpx,fpy,fpz) = tigl.fuselageGetPoint(i,k,1.0,zeta)
                if abs(fpz-afg.fuse_center_section_point[j][i-1][2])< 0.01:
                    if (fpy>afg.fuse_center_section_point[j][i-1][1] and hw1 == 0.0):
                        hw1 = abs(fpy-afg.fuse_center_section_point[j][i-1][1])
                        x1[j,i-1] = fpx
                        y1[j,i-1] = fpy
                        z1[j,i-1] = fpz
                    elif (fpy<afg.fuse_center_section_point[j][i-1][1]\
                          and hw2 == 0.0):
                        hw2= abs(fpy-afg.fuse_center_section_point[j][i-1][1])
                        x2[j,i-1] = fpx
                        y2[j,i-1] = fpy
                        z2[j,i-1] = fpz
                        break
            afg.fuse_sec_width[j][i-1] = hw1 + hw2
            hh1 = 0.0
            hh2 = 0.0
            for zeta in np.arange(0.0, 1.0, 0.001):
                (fpx,fpy,fpz) = tigl.fuselageGetPoint(i,k,1.0,zeta)
                if abs(fpy-afg.fuse_center_section_point[j][i-1][1])< 0.01:
                    if (fpz>afg.fuse_center_section_point[j][i-1][2]\
                        and hh1 == 0.0):
                        hh1 = abs(fpz-afg.fuse_center_section_point[j][i-1][2])
                    elif (fpz<afg.fuse_center_section_point[j][i-1][2]\
                          and hh2 == 0.0):
                        hh2 = abs(fpz-afg.fuse_center_section_point[j][i-1][2])
                        break
            afg.fuse_sec_height[j][i-1] = hh1 + hh2
            (fslpx,fslpy,fslpz) = tigl.fuselageGetPoint(1,k,0.0,0.0)
            (fslpx2,fslpy2,fslpz2) = tigl.fuselageGetPoint(1,k,1.0,0.0)
            afg.fuse_seg_length[j-1][i-1] = abs(fslpx2-fslpx)
        k = int(afg.fuse_seg_index[1][i-1])
        afg.fuse_sec_per[0][i-1]\
            = tigl.fuselageGetCircumference(i,k,0.0)
        (fpx,fpy,fpz) = tigl.fuselageGetPoint(i,k,0.0,0.0)
        (fpx2,fpy2,fpz2) = tigl.fuselageGetPoint(i,k,0.0,0.5)
        afg.fuse_center_section_point[0][i-1][0] = (fpx+fpx2) / 2
        afg.fuse_center_section_point[0][i-1][1] = (fpy+fpy2) / 2
        afg.fuse_center_section_point[0][i-1][2] = (fpz+fpz2) / 2
        hw1 = 0
        hw2 = 0
        for zeta in np.arange(0.0, 1.0, 0.001):
            (fpx,fpy,fpz) = tigl.fuselageGetPoint(i,k,0.0,zeta)
            if abs(fpz-afg.fuse_center_section_point[0][i-1][2])< 0.01:
                if (fpy>afg.fuse_center_section_point[0][i-1][1] and hw1 ==0):
                    hw1 = abs(fpy-afg.fuse_center_section_point[0][i-1][1])
                    x1[0,i-1] = fpx
                    y1[0,i-1] = fpy
                    z1[0,i-1] = fpz
                elif (fpy<afg.fuse_center_section_point[0][i-1][1] and hw2 ==0):
                    hw2 = abs(fpy-afg.fuse_center_section_point[0][i-1][1])
                    x2[0,i-1] = fpx
                    y2[0,i-1] = fpy
                    z2[0,i-1] = fpz
                    break
        afg.fuse_sec_width[0][i-1] = hw1 + hw2
        hh1 = 0.0
        hh2 = 0.0
        for zeta in np.arange(0.0, 1.0, 0.001):
            (fpx,fpy,fpz) = tigl.fuselageGetPoint(i,k,1.0,zeta)
            if abs(fpy-afg.fuse_center_section_point[0][i-1][1])< 0.01:
                if (fpz>afg.fuse_center_section_point[0][i-1][2]\
                    and hh1 == 0.0):
                    hh1 = abs(fpz-afg.fuse_center_section_point[0][i-1][2])
                elif (fpz<afg.fuse_center_section_point[0][i-1][2]\
                      and hh2 == 0.0):
                    hh2 = abs(fpz-afg.fuse_center_section_point[0][i-1][2])
                    break
        afg.fuse_sec_height[0][i-1] = hh1 + hh2
        afg.fuse_mean_width.append(round(np.mean(afg.fuse_sec_width[:,i-1]),3))

## Evaluating the point at the center of each segment.
    for i in range(int(afg.fuse_nb)):
        for j in range(1, afg.fuse_seg_nb[i-1]+1):
            afg.fuse_center_seg_point[j-1][i-1][0]\
                = (afg.fuse_center_section_point[j-1][i-1][0]\
                   + afg.fuse_center_section_point[j][i-1][0])/2
            afg.fuse_center_seg_point[j-1][i-1][1]\
                = (afg.fuse_center_section_point[j-1][i-1][1]\
                   + afg.fuse_center_section_point[j][i-1][1])/2
            afg.fuse_center_seg_point[j-1][i-1][2]\
                = (afg.fuse_center_section_point[j-1][i-1][2]\
                   + afg.fuse_center_section_point[j][i-1][2])/2

## Evaluating cabin length and volume, nose length and tail_length ------------
    log.info('-----------------------------------------------------------')
    log.info('----------- Analysing cabin dimensions --------------------')
    log.info('-----------------------------------------------------------')
    corr = (1.3) + np.zeros((afg.f_nb))
    c = False
    afg.cabin_nb = np.zeros((afg.f_nb))
    afg.cabin_area = np.zeros((afg.f_nb))
    afg.fuse_cabin_length = np.zeros((afg.f_nb))
    afg.cabin_seg = np.zeros((max_seg_nb,afg.f_nb))
    afg.cabin_length = np.zeros((afg.f_nb))
    afg.fuse_cabin_vol = np.zeros((afg.f_nb))
    afg.fuse_nose_length = np.zeros((afg.f_nb))
    afg.fuse_tail_length = np.zeros((afg.f_nb))
    afg.fuse_fuel_vol = np.zeros((afg.f_nb))

    for i in range(1,afg.f_nb+1):
        ex = False
        cabin_seg = np.zeros((max_seg_nb,1))
        cabin_nb = 0
        cabin_length = 0
        cabin_volume = 0
        nose_length = 0
        tail_length = 0
        if not F_FUEL[i-1]:
            for j in range(1,afg.fuse_seg_nb[i-1]+1):
                if (round(afg.fuse_sec_width[j][i-1],3)\
                    == round(np.amax(afg.fuse_sec_width[:,i-1]),3) and\
                        (h_min <= afg.fuse_sec_height[j,i-1])):
                    cabin_length += afg.fuse_seg_length[j-1,i-1]
                    cabin_volume += afg.fuse_seg_vol[j-1,i-1]
                    cabin_seg[j-1] = 1
                    c = True
                elif not c:
                    nose_length += afg.fuse_seg_length[j-1,i-1]
            if cabin_length >= 0.65 * afg.fuse_length[i-1]:
            # If the aircraft is designed with 1 or more sections with
            # maximum width and the sun of their length is greater the 65%
            # of the total length, the cabin will be considered only in those
            # sections
                tail_length = afg.fuse_length[i-1] - cabin_length - nose_length
                cabin_nb = 1
                ex = True
            while ex is False:
                c = False
                cabin_seg[:] = 0
                nose_length = 0
                tail_length = 0
                cabin_length = 0
                cabin_volume = 0
                for j in range(1,afg.fuse_seg_nb[i-1]+1):
                    if (afg.fuse_sec_width[j][i-1] >= (corr[i-1]\
                        * afg.fuse_mean_width[i-1]) and\
                        (h_min <= afg.fuse_sec_height[j,i-1])):
                        cabin_length += afg.fuse_seg_length[j-1,i-1]
                        cabin_volume += afg.fuse_seg_vol[j-1,i-1]
                        cabin_seg[j-1] = 1
                        c += 1
                    elif c > 1:
                        tail_length += afg.fuse_seg_length[j-1,i-1]
                    else:
                        nose_length += afg.fuse_seg_length[j-1,i-1]
                if corr[i-1] > 0.0 and cabin_length < (0.20 * afg.fuse_length[i-1]):
                    corr[i-1] -= 0.05
                else:
                    ex = True
            afg.fuse_nose_length[i-1] = round(nose_length,3)
            afg.fuse_fuel_vol[i-1] = 0
            afg.fuse_tail_length[i-1] = round(tail_length,3)
            afg.fuse_cabin_length[i-1] = round(cabin_length,3)
            afg.fuse_cabin_vol[i-1] = round(cabin_volume,3)
            afg.cabin_nb[i-1] = cabin_nb
            afg.cabin_seg[:,i-1] = cabin_seg[:,0]
            afg.fuse_cabin_length[i-1] = round(cabin_length,3)
            cabin_area = 0
            for j in range(0,afg.fuse_seg_nb[i-1]):
                if afg.cabin_seg[j,i-1] == 1:
                    (x11,y11,z11) = (x1[j,i-1],y1[j,i-1],z1[j,i-1])
                    (x12,y12,z12) = (x1[j+1,i-1],y1[j+1,i-1],z1[j+1,i-1])
                    (x21,y21,z21) = (x2[j,i-1],y2[j,i-1],z2[j,i-1])
                    (x22,y22,z22) = (x2[j+1,i-1],y2[j+1,i-1],z2[j+1,i-1])
                    cabin_area += (0.5\
                        * abs(x11*y12 + x12*y22 + x22*y21 + x21*y11\
                        - (y11*x12 + y12*x22 + y22*x21 + y21*x11)))
                elif (cabin_area > 0 and afg.cabin_seg[j,i-1] == 0):
                    break
            thick_area = afg.fuse_cabin_length[i-1] * (fuse_thick*2.0)
            afg.cabin_area[i-1] = round((cabin_area-thick_area),3)
        else:
            afg.fuse_fuel_vol[i-1] *= F_FUEL[i-1]/100.0
            afg.fuse_nose_length[i-1] = 0
            afg.fuse_tail_length[i-1] = 0
            afg.fuse_cabin_length[i-1] = 0
            afg.fuse_cabin_vol[i-1] = 0
            afg.cabin_area[i-1] = 0

    close_tixi(tixi, cpacs_in)

# log info display ------------------------------------------------------------
    log.info('-----------------------------------------------------------')
    log.info('---------- Fuselage Geometry Evaluations ------------------')
    log.info('---------- USEFUL INFO ----------------------------------\n'\
             + 'If fuselage number is greater than 1 the\n'\
             + 'informations of each obj are listed in an\n '\
             + 'array ordered progressively')
    log.info('-----------------------------------------------------------')
    log.info('---------- Fuselage Results -------------------------------')
    log.info('Number of fuselage [-]: ' + str(afg.f_nb))
    log.info('Number of fuselage sections [-]: '\
             + str(afg.fuse_sec_nb))
    log.info('Number of fuselage segments [-]: '\
             + str(afg.fuse_seg_nb))
    log.info('Cabin segments array [-]:\n' + str(cabin_seg))
    log.info('Fuse Length [m]:\n' + str(afg.fuse_length))
    log.info('Fuse nose Length [m]:\n' + str(afg.fuse_nose_length))
    log.info('Fuse cabin Length [m]:\n' + str(afg.fuse_cabin_length))
    log.info('Fuse tail Length [m]:\n' + str(afg.fuse_tail_length))
    log.info('Aircraft Length [m]: ' + str(afg.tot_length))
    log.info('Perimeter of each section of each fuselage [m]: \n'\
            + str(afg.fuse_sec_per))
    log.info('Relative distance of each section of each fuselage [m]: \n'\
             + str(afg.fuse_sec_rel_dist))
    log.info('Length of each segment of each fuselage [m]: \n'\
             + str(afg.fuse_seg_length))
    log.info('Mean fuselage width [m]: ' + str(afg.fuse_mean_width))
    log.info('Width of each section of each fuselage [m]: \n'\
             + str(afg.fuse_sec_width))
    log.info('Cabin area [m^2]:\n' + str(afg.cabin_area))
    log.info('Fuselage wetted surface [m^2]:\n' + str(afg.fuse_surface))
    log.info('Volume of all the segmetns of each fuselage [m^3]: \n'\
             + str(afg.fuse_seg_vol))
    log.info('Volume of each cabin [m^3]:\n' + str(afg.fuse_cabin_vol))
    log.info('Volume of each fuselage [m^3]:\n' + str(afg.fuse_vol))
    log.info('Volume of fuel in each fuselage [m^3]:\n'\
             + str(afg.fuse_fuel_vol))
    log.info('-----------------------------------------------------------')

    return(afg)


#==============================================================================
#   MAIN
#==============================================================================

if __name__ == '__main__':
    log.warning('#########################################################')
    log.warning('# ERROR NOT A STANDALONE PROGRAM, RUN balanceuncmain.py #')
    log.warning('#########################################################')
