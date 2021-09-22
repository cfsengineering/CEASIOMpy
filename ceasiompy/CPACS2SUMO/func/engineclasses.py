"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerlands

Classes to save engine/nacelle value for CPACS2SUMO

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2021-02-25
| Last modifiction: 2021-09-22

TODO:

    * Improve docstring

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import math

from cpacspy.cpacsfunctions import get_float_vector 

from ceasiompy.utils.generalclasses import SimpleNamespace, Point, Transformation
from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


#==============================================================================
#   CLASSES
#==============================================================================

class Engine:
    """TODO docstring for Engine."""

    def __init__(self, tixi, xpath):

        self.xpath = xpath
        self.uid = tixi.getTextAttribute(xpath, 'uID')

        self.transf = Transformation()
        self.transf.get_cpacs_transf(tixi,self.xpath)

        self.sym = False
        if tixi.checkAttribute(self.xpath, 'symmetry'):
            if tixi.getTextAttribute(self.xpath, 'symmetry') == 'x-z-plane':
                self.sym = True

        if tixi.checkElement(self.xpath + '/parentUID'):
            self.parent_uid = tixi.getTextElement(self.xpath + '/parentUID')
            log.info('The parent UID is: ' + self.parent_uid)

        if tixi.checkElement(self.xpath + '/engineUID'):
            engine_uid = tixi.getTextElement(self.xpath + '/engineUID')
            log.info('The engine UID is: ' + engine_uid)
        else:
            log.error('No engine UID found!')

        # In cpacs engine are "stored" at two different place
        # The main at /cpacs/vehicles/aircraft/model/engines
        # It contains symetry and translation and the UID to the engine definition
        # stored at /cpacs/vehicles/engines/ with all the carateristic of the nacelle
        nacelle_xpath = tixi.uIDGetXPath(engine_uid) + '/nacelle'

        self.nacelle = Nacelle(tixi,nacelle_xpath)


class Nacelle:
    """
    The Class "Nacelle" saves all the parameter to create the entiere nacelle in SUMO.

    Attributes:
        TODO

    """

    def __init__(self,tixi,xpath):

        self.xpath = xpath
        self.uid = tixi.getTextAttribute(xpath, 'uID')

        self.fancowl = NacellePart(tixi,self.xpath + '/fanCowl')

        self.corecowl = NacellePart(tixi,self.xpath + '/coreCowl')

        self.centercowl = Cone(tixi,self.xpath + '/centerCowl')


class NacellePart:
    """
    The Class "NacellePart" saves all the parameter to create fan/core/center
    of and engine in SUMO.

    Attributes:
        TODO

    """

    def __init__(self,tixi,xpath):

        self.isengpart = False
        self.iscone = False

        if tixi.checkElement(xpath):
            self.xpath = xpath
            self.uid = tixi.getTextAttribute(xpath, 'uID')

            self.isengpart = True

            # Should have only 1 section
            self.section = NacelleSection(tixi, xpath + '/sections/section[1]')


class Cone():
    """
    The Class "Cone" saves all the parameter to create cone of and engine in SUMO.

    Attributes:
        TODO

    """

    def __init__(self,tixi,xpath):

        self.isengpart = False
        self.iscone = False

        if tixi.checkElement(xpath):

            self.xpath = xpath
            self.uid = tixi.getTextAttribute(xpath, 'uID')

            self.isengpart = True
            self.iscone = True

            self.xoffset = tixi.getDoubleElement(xpath+'/xOffset')

            self.curveUID = tixi.getTextElement(xpath+'/curveUID')
            self.curveUID_xpath =  tixi.uIDGetXPath(self.curveUID)

            self.pointlist = PointList(tixi, self.curveUID_xpath + '/pointList')


class NacelleSection:
    """
    The Class "NacelleSection" saves information relative to the section to
    constructuce the nacelle parts

    Attributes:
        TODO

    """

    def __init__(self, tixi, xpath):

        self.xpath = xpath
        self.uid = tixi.getTextAttribute(xpath, 'uID')

        self.transf = Transformation()
        self.transf.get_cpacs_transf(tixi, self.xpath)

        self.profileUID = tixi.getTextElement(self.xpath + '/profileUID')

        self.profileUID_xpath =  tixi.uIDGetXPath(self.profileUID)

        self.pointlist = PointList(tixi, self.profileUID_xpath + '/pointList')


class PointList(object):
    """
    The Class "PointList" saves list of points for profile/airfoil

    Attributes:
        TODO

    """

    def __init__(self, tixi, xpath):
        self.xpath = xpath

        self.xlist = get_float_vector(tixi,self.xpath+'/x')
        self.ylist = get_float_vector(tixi,self.xpath+'/y')
