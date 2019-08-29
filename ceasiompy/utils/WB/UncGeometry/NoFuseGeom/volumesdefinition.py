"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script evaluates the unconventional aircraft wings geometry .

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-12-07
| Last modifiction: 2019-08-29 (AJ)
"""


#=============================================================================
#   IMPORTS
#=============================================================================

import numpy as np
import math

from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.cpacsfunctions import open_tixi,open_tigl, close_tixi

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================

"""All classes are defined inside the classes folder and in the
   InputClasses/Unconventional folder."""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def wing_check_thickness(h_min, awg, cpacs_in, TP, FUEL_ON_CABIN=0):
    """ The fuction subdivides the main wing into nodes and defines
        the fuel and cabin volumes.

        INPUT
        (float) h_min    --Arg.: Minimum height for the fuselage [m].
        (class) awg      --Arg.: AircraftWingGeometry class look at
                                 aircraft_geometry_class.py in the
                                 classes folder for explanation.

        (char) cpacs_in  --Arg.: Relative position of the xml file.
        (boolean) TP            --Arg.: True if the aircraft is a turboprop.
        (float) FUEL_ON_CABIN --Arg.: Percentage of the cabin volume
                                      used for fuel storaging instead
                                      for passengers. (default 0%)
        OUTPUT
        (float-array) wing_nodes    --Out.: 3D array containing the
                                            nodes coordinates (x,y,z)
                                            [m,m,m].
        (class) awg      --Arg.: AircraftWingGeometry class look at
                                 aircraft_geometry_class.py in the
                                 classes folder for explanation.
    """

    log.info('-----------------------------------------------------------')
    log.info('----------- Evaluating fuselage and wing volume -----------')
    log.info('-----------------------------------------------------------')

    tixi = open_tixi(cpacs_in)
    tigl = open_tigl(tixi)

    SPACING = 0.1
    subd_c = 30  # Number of subdivisions along the perimeter
                   # on eachsurface, total number of points for each section
                   # subd_c * 2
    DEN = 0.0
    w = awg.main_wing_index - 1
    wing_nodes  = 0
    c = False

    for d in range(1,subd_c+2):
        DEN += d
    zeta = 1.0/DEN
    for i in awg.w_seg_sec[:,w,2]:
        if i == 0.0:
            break
        w_temp=np.zeros((2,subd_c+2,3))
        #Number of subdivisions along the longitudinal axis
        subd_l = math.ceil((awg.wing_seg_length[int(i)-1][w]/SPACING))
        if subd_l == 0:
            subd_l = 1
        eta = 1.0/subd_l
        et = 0.0
        (xc,yc,zc) = awg.wing_center_seg_point[int(i)-1][w][:]
        for j in range(0,int(subd_l)-1):
            (xle,yle,zle) =  tigl.wingGetLowerPoint(w+1,int(i),et,0.0)
            (xle2,yle2,zle2) =  tigl.wingGetLowerPoint(w+1,int(i),et,1.0)
            if xle < xle2:
                ZLE = 0.0
                ze = 0.0
            else:
                ZLE = 1.0
                ze = 1.0
            for k in range(0,subd_c+2):
                if ZLE == 0.0:
                    ze += float(k)*zeta
                elif ZLE == 1.0:
                    ze -= float(k)*zeta
                (xl,yl,zl) =  tigl.wingGetLowerPoint(w+1,int(i),et,ze)
                (xu,yu,zu) =  tigl.wingGetUpperPoint(w+1,int(i),et,ze)
                w_temp[0, k, :] = (xu,yu,zu)
                w_temp[1, k, :] = (xl,yl,zl)
            if c is False:
                wing_nodes = w_temp
                c = True
            else:
                wing_nodes = np.concatenate((wing_nodes, w_temp), axis=0)
            et = j * eta
    (rows, columns, pages) = wing_nodes.shape

    # wing_nodes 3D matrix: the even rows and the zero row correspond
    # to the upper profile of the wing, while all the odd rows correspond
    # to the lower profile. The columns contain the coordinates of each nodes.
    # The page 0,1 and 2 contain respectively the x,y and z coordinate.
    h_max = []
    h_mean = []
    y_sec = []

    for r in range(0,rows-1,2):
        h_max_temp = 0
        z_min = 9999
        z_max = 0
        h = []
        for c in range(0,columns):
            (xu, yu, zu) = wing_nodes[r,c,:]
            (xl, yl, zl) = wing_nodes[r+1,c,:]
            h.append(abs(zu-zl))
            if abs(zu-zl) > h_max_temp:
                h_max_temp = abs(zu-zl)
            if r == 0:
                if zl < z_min:
                    (x13, y13, z13) = (xl, yl, zl)
                    z_min = zl
                if zu > z_max:
                    (x14, y14, z14) = (xu, yu, zu)
                    z_max = zu
            else:
                if zl < z_min:
                    (x23_t,y23_t,z23_t) = (xl,yl,zl)
                    z_min = zl
                if zu > z_max:
                    (x24_t,y24_t,z24_t) = (xu,yu,zu)
                    z_max = zu
        h_max.append(h_max_temp)
        h_mean.append(np.mean(h))
        y_sec.append(yl)
        if np.mean(h) >= h_min:
            h_mean_cabin = np.mean(h_mean)
            awg.y_max_cabin = yl
            seg = r
            if r != 0:
                (x23,y23,z23) = (x23_t,y23_t,z23_t)
                (x24,y24,z24) = (x24_t,y24_t,z24_t)
        else:
            (x11, y11, z11) =  wing_nodes[0,0,:]
            (x12, y12, z12) =  wing_nodes[0,-1,:]
            (x21, y21, z21) =  wing_nodes[seg,0,:]
            (x22, y22, z22) =  wing_nodes[seg,-1,:]
            break

    for c in range(0, columns):
        (xu,yu,zu) = wing_nodes[0,c,:]
        (xl,yl,zl) = wing_nodes[1,c,:]
        if abs(zu-zl) >= h_min:
            xs1 = xu
            zs1u = zu
            zs1l = zl
            yse1 = yl
            break
    for c in range(0, columns):
        (xu,yu,zu) = wing_nodes[seg,c,:]
        (xl,yl,zl) = wing_nodes[seg+1,c,:]
        if abs(zu-zl) >= h_min:
            xs2 = xu
            zs2u = zu
            zs2l = zl
            yse2 = yl
            break
    for c in range(columns-1, -1, -1):
        (xu,yu,zu) = wing_nodes[0,c,:]
        (xl,yl,zl) = wing_nodes[1,c,:]
        if abs(zu-zl) >= h_min:
            xe1 = xu
            ze1u = zu
            ze1l = zl
            break
    for c in range(columns-1, -1, -1):
        (xu,yu,zu) = wing_nodes[seg,c,:]
        (xl,yl,zl) = wing_nodes[seg+1,c,:]
        if abs(zu-zl) >= h_min:
            xe2 = xu
            ze2u = zu
            ze2l = zl
            break

    awg.cabin_area = 0.5 * abs(xs1*yse2 + xs2*yse2 + xe2*yse1 + xe1*yse1\
                               - xs2*yse1 - xe2*yse2 - xe1*yse2 - xs1*yse1)
    fuse_plt_area = 0.5 * abs(x11*y21 + x21*y22 + x22*y12 + x12*y11\
                              - x21*y11 - x22*y21 - x12*y22 - x11*y12)
    fuse_frontal_area = 0.5 * abs(y24*z23 + y23*z13 + y13*z14 + y14*z24\
                                  - z24*y23 - z23*y13 - z13*y14 -z14*y24)
    c1 = math.sqrt((x11-x12)**2 + (y11-y12)**2 + (z11-z12)**2)
    c2 = math.sqrt((x21-x22)**2 + (y21-y22)**2 + (z21-z22)**2)

    awg.cabin_span = abs(awg.y_max_cabin-y11)

    awg.fuse_vol = (0.95 * fuse_frontal_area) * (fuse_plt_area/(awg.cabin_span))\
                    / (math.sqrt(1+(c2/c1)))

    if awg.wing_sym[w-1] != 0:
        awg.fuse_vol *= 2
        awg.cabin_area *= 2

    awg.cabin_vol = (awg.cabin_area * h_min)
    delta_vol = (awg.fuse_vol - awg.cabin_vol)
    awg.fuse_fuel_vol = (float(FUEL_ON_CABIN)/100.0)*delta_vol
    if TP:
        t = 0.5
    else:
        t = 0.55
    awg.wing_fuel_vol = t * (awg.wing_vol[w] - awg.fuse_vol)
    awg.fuel_vol_tot = awg.fuse_fuel_vol + awg.wing_fuel_vol

# log info display ------------------------------------------------------------
    log.info('--------------------- Main wing Volumes -------------------')
    log.info('Wing volume [m^3]: ' + str(awg.wing_vol[w]))
    log.info('Cabin volume [m^3]: ' + str(awg.cabin_vol))
    log.info('Volume of the wing as fuselage [m^3]: ' + str(awg.fuse_vol))
    log.info('Volume of the remaining portion of the wing [m^3]: '\
             + str(awg.wing_vol[w] - awg.fuse_vol))
    log.info('Fuel volume in the fuselage [m^3]: ' + str(awg.fuse_fuel_vol))
    log.info('Fuel volume in the wing [m^3]: ' + str(awg.wing_fuel_vol))
    log.info('Total fuel Volume [m^3]: ' + str(awg.fuel_vol_tot))
    log.info('-----------------------------------------------------------')

    return(awg, wing_nodes)


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('#########################################################')
    log.warning('# ERROR NOT A STANDALONE PROGRAM, RUN balanceuncmain.py #')
    log.warning('#########################################################')
