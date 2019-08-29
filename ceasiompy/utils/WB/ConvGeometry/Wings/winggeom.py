"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

This file will analyse the wing geometry from cpacs file.

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

def check_segment_connection(wing_plt_area_xz, wing_plt_area_yz, ag, tigl):
    """ The function checks for each segment the start and end section index
        and to reorder them.

    ARGUMENTS
    (float) wing_plt_area_xz    --Arg.: Wing area on the xz plane [m^2].
    (float) wing_plt_area_yz    --Arg.: Wing area on the yz plane [m^2].
    (class) ag     --Arg.: AircraftGeometry class.
    ##======= Class are defined in the InputClasses folder =======##
    (char) tigl    --Arg.: Tigl handle.

    RETURN
    (int) sec_nb            --Out.: Number of sections for each wing.
    (int) start_index       --Out.: Start section index for each wing.
    (float-array) seg_sec_reordered -- Out.: Reordered segments with
                                             respective start and end section
                                             for each wing.
    (float_array) sec_index --Out.: List of section index reordered.
    """
    log.info('---------------------------------------------')
    log.info('---- Checking wings segments connection -----')
    log.info('---------------------------------------------')

    # Initialising arrays
    nbmax = np.amax(ag.wing_seg_nb)
    seg_sec = np.zeros((nbmax,ag.w_nb,3))
    seg_sec_reordered = np.zeros(np.shape(seg_sec))
    sec_index = np.zeros((nbmax,ag.w_nb))
    start_index = []
    sec_nb = []

    # First, for each segment the start and end sections are found. Then
    # they are reordered considering that the end section of a segment
    # is the start section of the next one.
    # The first section is the one that has the lowest y,
    # for horizontal wings, or z, for vertical wings position
    # The code works if a section is defined and not used and if the segments
    # are not define with a consequential order.
    # WARNING The code does not work if a segment is defined
    #         and then not used.
    #         The aircraft should be designed along the x-axis
    #         and on the x-y plane

    for i in range(1,ag.w_nb+1):
        wing_sec_index = []
        for j in range(1,ag.wing_seg_nb[i-1]+1):
            (s0,e) = tigl.wingGetInnerSectionAndElementIndex(i,j)
            (s1,e) = tigl.wingGetOuterSectionAndElementIndex(i,j)
            seg_sec[j-1,i-1,0] = s0
            seg_sec[j-1,i-1,1] = s1
            seg_sec[j-1,i-1,2] = j
        (slpx,slpy,slpz) = tigl.wingGetChordPoint(i,1,0.0,0.0)
        seg_sec_reordered[0,i-1,:] = seg_sec[0,i-1,:]
        start_index.append(1)
        for j in range(2,ag.wing_seg_nb[i-1]+1):
            (x,y,z) = tigl.wingGetChordPoint(i,j,1.0,0.0)
            if (ag.wing_plt_area[i-1] > wing_plt_area_xz[i-1]\
		and ag.wing_plt_area[i-1] > wing_plt_area_yz[i-1]):
                if y < slpy:
                    (slpx,slpy,slpz) = (x,y,z)
                    start_index.append(j)
                    seg_sec_reordered[0,i-1,:] = seg_sec[j-1,i-1,:]
            else:
                if z < slpz:
                    (slpx,slpy,slpz) = (x,y,z)
                    start_index.append(j)
                    seg_sec_reordered[0,i-1,:] = seg_sec[j-1,i-1,:]
        for j in range(2,ag.wing_seg_nb[i-1]+1):
            end_sec = seg_sec_reordered[j-2,i-1,1]
            start_next = np.where(seg_sec[:,i-1,0] == end_sec)
            seg_sec_reordered[j-1,i-1,:] = seg_sec[start_next[0],i-1,:]
        wing_sec_index.append(seg_sec_reordered[0,0,0])
        for j in range(2,ag.wing_seg_nb[i-1]+1):
            if (seg_sec_reordered[j-1,i-1,0] in wing_sec_index) == False:
                wing_sec_index.append(seg_sec_reordered[j-1,i-1,0])
        if (seg_sec_reordered[j-1,i-1,1] in wing_sec_index) == False:
            wing_sec_index.append(seg_sec_reordered[j-1,i-1,1])
        nb = np.shape(wing_sec_index)
        if nb[0] > nbmax:
            nbmax = nb[0]
        sec_index.resize(nbmax,ag.w_nb)
        sec_index[0:nb[0],i-1] = wing_sec_index[0:nb[0]]
        sec_nb.append(nb[0])

    return(sec_nb, start_index, seg_sec_reordered, sec_index)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

def get_wing_segment_length(ag, wing_center_section_point):
    """ The function evaluates the length of each segment of each wing,
        also considering the ones defined using symmetry.
        The function will upload the aircraft geometry class.

    ARGUMENTS
    (class) ag  --Arg.: AircraftGeometry class.
    ##======= Class are defined in the InputClasses folder =======##
    (float_array) wing_center_section_point   --Arg.: Central point of each
                                                      segment defined at 1/4
                                                      of the chord [m, m, m].
    RETURN
    (class) ag  --Out.: AircraftGeometry class updated.
    """

    log.info('---------------------------------------------')
    log.info('----- Evaluating wings segments length ------')
    log.info('---------------------------------------------')
    max_seg_nb = np.amax(ag.wing_seg_nb)
    ag.wing_seg_length = np.zeros((max_seg_nb,ag.wing_nb))

    # To evaluate the length of each segment, the ditance of central point
    # of the start and end section of each segment is computed

    a = 0
    for i in range(1,ag.w_nb+1):
        for j in range(1,ag.wing_seg_nb[i-1]+1):
            (x1,y1,z1) = wing_center_section_point[j-1,i-1,:]
            (x2,y2,z2) = wing_center_section_point[j,i-1,:]
            ag.wing_seg_length[j-1][i+a-1]\
                = (math.sqrt((x1-x2)**2+(y1-y2)**2+(z1-z2)**2))
        if ag.wing_sym[i-1] != 0:
            ag.wing_seg_length[:,i+a] = ag.wing_seg_length[:,i+a-1]
            a += 1

    return(ag)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

def wing_geom_eval(ag, cpacs_in):
    """ Main function to evaluate the wings geometry

    ARGUMENTS
    (class) ag         --Arg.: AircraftGeometry class.
    ##======= Class are defined in the InputClasses folder =======##
    (char) cpacs_in    -- Arg.: Cpacs xml file location.

    RETURN
    (class) ag  --Out.: AircraftGeometry class updated.
    """

##===========================================================================##
    log.info('---------------------------------------------')
    log.info('---------- Analysing wing geometry ----------')
    log.info('---------------------------------------------')

    # Opening tixi and tigl
    tixi = open_tixi(cpacs_in)
    tigl = open_tigl(tixi)

## ----------------------------------------------------------------------------
## COUNTING 1 -----------------------------------------------------------------
## Counting wing number without symmetry --------------------------------------
## ----------------------------------------------------------------------------

    w_nb = tixi.getNamedChildrenCount('/cpacs/vehicles/aircraft\
                                      /model/wings','wing')

## ----------------------------------------------------------------------------
## INITIALIZATION 1 -----------------------------------------------------------
## ----------------------------------------------------------------------------

    ag.w_nb = w_nb
    ag.wing_nb = w_nb
    wing_plt_area_xz = []
    wing_plt_area_yz = []
    wingUID = []

## ----------------------------------------------------------------------------
## COUNTING 2 -----------------------------------------------------------------
## Counting sections and segments----------------------------------------------
## ----------------------------------------------------------------------------

    b = 0
    for i in range(1,w_nb + 1):
        double = 1
        ag.wing_sym.append(tigl.wingGetSymmetry(i))
        if ag.wing_sym[i-1] != 0:
            double = 2  # To consider the real amount of wing
                        # when they are defined using symmetry
            ag.wing_nb += 1
        ag.wing_sec_nb.append(tigl.wingGetSectionCount(i))
        ag.wing_seg_nb.append(tigl.wingGetSegmentCount(i))
        ag.wing_vol.append(tigl.wingGetVolume(i) * double)
        # x-y plane
        ag.wing_plt_area.append(tigl.wingGetReferenceArea(i,1)*double)
        # x-z plane
        wing_plt_area_xz.append(tigl.wingGetReferenceArea(i,2)*double)
        # y-z plane
        wing_plt_area_yz.append(tigl.wingGetReferenceArea(i,3)*double)
        ag.wing_tot_vol = ag.wing_tot_vol + ag.wing_vol[i-1]
        wingUID.append(tigl.wingGetUID(i))
        ag.wing_span.append(tigl.wingGetSpan(wingUID[i-1]))
        a = np.amax(ag.wing_span)
        # Evaluating the index that corresponds to the main wing
        if a > b:
            ag.main_wing_index = i
            b = a

## Checking segment and section connection and reordering them
    (ag.wing_sec_nb, start_index, seg_sec, wing_sec_index)\
      = check_segment_connection(wing_plt_area_xz, wing_plt_area_yz,\
                                 ag, tigl)

## ----------------------------------------------------------------------------
## INITIALIZATION 2 -----------------------------------------------------------
## ----------------------------------------------------------------------------

    max_wing_sec_nb = np.amax(ag.wing_sec_nb)
    max_wing_seg_nb = np.amax(ag.wing_seg_nb)
    wing_center_section_point = np.zeros((max_wing_sec_nb, w_nb, 3))
    ag.wing_center_seg_point = np.zeros((max_wing_seg_nb, ag.wing_nb, 3))
    ag.wing_seg_vol = np.zeros((max_wing_seg_nb, w_nb))
    ag.wing_fuel_seg_vol = np.zeros((max_wing_seg_nb, w_nb))
    ag.wing_fuel_vol = 0
    ag.wing_mac = np.zeros((4, w_nb))
    ag.wing_sec_thicknes = np.zeros((max_wing_sec_nb+1, w_nb))

##===========================================================================##
## ----------------------------------------------------------------------------
## WING ANALYSIS --------------------------------------------------------------
## ----------------------------------------------------------------------------
# Main wing plantform area

    ag.wing_plt_area_main = ag.wing_plt_area[ag.main_wing_index-1]

## Wing: MAC,chords,thicknes,span,plantform area ------------------------------

    for i in range(1,w_nb+1):
        mac = tigl.wingGetMAC(wingUID[i-1])
        (wpx,wpy,wpz) = tigl.wingGetChordPoint(i,1,0.0,0.0)
        (wpx2,wpy2,wpz2) = tigl.wingGetChordPoint(i,1,0.0,1.0)
        ag.wing_max_chord.append(np.sqrt((wpx2-wpx)**2 + (wpy2-wpy)**2\
                                 + (wpz2-wpz)**2))
        (wpx,wpy,wpz) = tigl.wingGetChordPoint(i,ag.wing_seg_nb[i-1],1.0,0.0)
        (wpx2,wpy2,wpz2) = tigl.wingGetChordPoint(i,ag.wing_seg_nb[i-1],\
                                                  1.0,1.0)
        ag.wing_min_chord.append(np.sqrt((wpx2-wpx)**2 + (wpy2-wpy)**2\
                                 + (wpz2-wpz)**2) )
        for k in range(1,5):
            ag.wing_mac[k-1][i-1] = mac[k-1]
        for jj in range(1,ag.wing_seg_nb[i-1]+1):
            j = int(seg_sec[jj-1,i-1,2])
            cle = tigl.wingGetChordPoint(i,j,0.0,0.0)
            ag.wing_seg_vol[j-1][i-1] = tigl.wingGetSegmentVolume(i,j)
            lp = tigl.wingGetLowerPoint(i,j,0.0,0.0)
            up = tigl.wingGetUpperPoint(i,j,0.0,0.0)
            if np.all(cle == lp) == True:
                L = 0.25
            else:
                L = 0.75
            if np.all(cle == up) == True:
                U = 0.25
            else:
                U = 0.75
            (wplx, wply, wplz) = tigl.wingGetLowerPoint(i,j,0.0,L)
            (wpux, wpuy, wpuz) = tigl.wingGetUpperPoint(i,j,0.0,U)
            wing_center_section_point[j-1][i-1][0] = (wplx+wpux) / 2
            wing_center_section_point[j-1][i-1][1] = (wply+wpuy) / 2
            wing_center_section_point[j-1][i-1][2] = (wplz+wpuz) / 2
            ag.wing_sec_thicknes[j-1][i-1] = np.sqrt((wpux-wplx)**2\
                + (wpuy-wply)**2 + (wpuz-wplz)**2)
        j = int(seg_sec[ag.wing_seg_nb[i-1]-1,i-1,2])
        (wplx, wply, wplz) = tigl.wingGetLowerPoint(\
            i,ag.wing_seg_nb[i-1],1.0,L)
        (wpux, wpuy, wpuz) = tigl.wingGetUpperPoint(\
            i,ag.wing_seg_nb[i-1],1.0,U)
        ag.wing_sec_thicknes[j][i-1] = np.sqrt((wpux-wplx)**2\
            + (wpuy-wply)**2 + (wpuz-wplz)**2)
        wing_center_section_point[ag.wing_seg_nb[i-1]][i-1][0] = (wplx+wpux)/2
        wing_center_section_point[ag.wing_seg_nb[i-1]][i-1][1] = (wply+wpuy)/2
        wing_center_section_point[ag.wing_seg_nb[i-1]][i-1][2] = (wplz+wpuz)/2
        ag.wing_sec_mean_thick.append(np.mean(\
            ag.wing_sec_thicknes[0:ag.wing_seg_nb[i-1]+1,i-1]))
        # Evaluating wing fuel tank volume in the main wings
        if abs(round(ag.wing_plt_area[i-1],3) - ag.wing_plt_area_main)\
           < 0.001:
            tp_ratio = ag.wing_min_chord[i-1]/ag.wing_max_chord[i-1]
            ratio = round(tp_ratio * ag.wing_plt_area[i-1]/100,1)
            if ratio >= 1.0:
                 ag.wing_fuel_vol = round(ag.wing_vol[i-1]*0.8,2)
            elif ratio >= 0.5:
                 ag.wing_fuel_vol = round(ag.wing_vol[i-1]*0.72,2)
            else:
                 ag.wing_fuel_vol = round(ag.wing_vol[i-1]*0.5,2)
            for j in seg_sec[:,i-1,2]:
                if j == 0.0:
                    break
                ag.wing_fuel_seg_vol[int(j)-1][i-1]\
                    = round((ag.wing_seg_vol[int(j)-1][i-1]\
                            /(sum(ag.wing_vol))) * ag.wing_fuel_vol,2)
        if ag.wing_plt_area[i-1] > wing_plt_area_xz[i-1] and\
            ag.wing_plt_area[i-1] > wing_plt_area_yz[i-1]:
            ag.is_horiz.append(True)
            if ag.wing_sym[i-1] != 0:
                ag.is_horiz.append(True)
        else:
            ag.is_horiz.append(False)
            if ag.wing_sym[i-1] != 0:
                ag.is_horiz.append(False)

    # Wing segment length evaluatin function
    ag = get_wing_segment_length(ag,wing_center_section_point)

    # Evaluating the point at the center of each segment, the center
    # is placed at 1/4 of the chord, symmetry is considered.

    a = 0
    c = False
    for i in range(1,int(ag.wing_nb)+1):
        if c:
            c = False
            continue
        for jj in range(1,ag.wing_seg_nb[i-a-1]+1):
            j = int(seg_sec[jj-1,i-a-1,2])
            ag.wing_center_seg_point[j-1][i-1][0]\
                = (wing_center_section_point[j-1][i-a-1][0]\
                + wing_center_section_point[j][i-a-1][0])/2
            ag.wing_center_seg_point[j-1][i-1][1]\
                = (wing_center_section_point[j-1][i-a-1][1]\
                + wing_center_section_point[j][i-a-1][1])/2
            ag.wing_center_seg_point[j-1][i-1][2]\
                = (wing_center_section_point[j-1][i-a-1][2]\
                + wing_center_section_point[j][i-a-1][2])/2
        if ag.wing_sym[i-1-a] != 0:
            if ag.wing_sym[i-1-a] == 1:
                symy = 1
                symx = 1
                symz = -1
            if ag.wing_sym[i-1-a] == 2:
                symy = -1
                symx = 1
                symz = 1
            if ag.wing_sym[i-1-a] == 3:
                symy = 1
                symx = -1
                symz = 1
            ag.wing_center_seg_point[:,i,0]\
                = ag.wing_center_seg_point[:,i-1,0] * symx
            ag.wing_center_seg_point[:,i,1]\
                = ag.wing_center_seg_point[:,i-1,1] * symy
            ag.wing_center_seg_point[:,i,2]\
                = ag.wing_center_seg_point[:,i-1,2] * symz
            c = True
            a += 1

    ag.w_seg_sec = seg_sec
    close_tixi(tixi, cpacs_in)

# log info display ------------------------------------------------------------
    log.info('---------------------------------------------')
    log.info('--------------- Wing Results ----------------')
    log.info('Number of Wings [-]: ' + str(ag.wing_nb))
    log.info('Wing symmetry plane [-]: ' + str(ag.wing_sym))
    log.info('Number of wing sections (not counting symmetry) [-]: '\
             + str(ag.wing_sec_nb))
    log.info('Number of wing segments (not counting symmetry) [-]: '\
             + str(ag.wing_seg_nb))
    log.info('Wing Span [m]: ' + str(ag.wing_span))
    log.info('Wing MAC length [m]: ' + str(ag.wing_mac[0,]))
    log.info('Wing MAC x,y,z coordinate [m]: \n' + str(ag.wing_mac[1:4,]))
    log.info('Wings sections thicknes [m]: ' + str(ag.wing_sec_thicknes))
    log.info('Wings sections mean thicknes [m]: '\
            + str(ag.wing_sec_mean_thick))
    log.info('Wing segments length [m]: ' + str(ag.wing_seg_length))
    log.info('Wing max chord length [m]: ' + str(ag.wing_max_chord))
    log.info('Wing min chord length [m]: ' + str(ag.wing_min_chord))
    log.info('Main wing plantform area [m^2]: ' + str(ag.wing_plt_area_main))
    log.info('Wings plantform area [m^2]: '\
             + str(ag.wing_plt_area))
    log.info('Volume of each wing [m^3]: ' + str(ag.wing_vol))
    log.info('Total wing volume [m^3]: ' + str(ag.wing_tot_vol))
    log.info('Wing volume for fuel storage [m^3]: '\
             + str(ag.wing_fuel_vol))
    log.info('---------------------------------------------')

    return(ag)


#==============================================================================
#   MAIN
#==============================================================================

if __name__ == '__main__':
    log.warning('##########################################################')
    log.warning('############# ERROR NOT A STANDALONE PROGRAM #############')
    log.warning('##########################################################')
