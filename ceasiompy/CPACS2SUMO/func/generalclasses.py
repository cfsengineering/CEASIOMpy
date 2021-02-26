"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
based on a script from Jan-Niclas Walther (DLR)

General classes for CPACS2SUMO

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2021-02-25
| Last modifiction: 2021-02-26

TODO:

    *

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import math

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


#==============================================================================
#   CLASSES
#==============================================================================

class SimpleNamespace(object):
    """
    Rudimentary SimpleNamespace clone. Works as a record-type object, or
    'struct'. Attributes can be added on-the-fly by assignment. Attributes
    are accesed using point-notation.

    Source:
        * https://docs.python.org/3.5/library/types.html
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        keys = sorted(self.__dict__)
        items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
        return "{}({})".format(type(self).__name__, ", ".join(items))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class Point:
    """
    The Class "Point" store x,y,z value for scaling, rotation and tanlsation,
    because of that unit can differ depending its use.

    Attributes:
        x (float): Value in x [depends]
        y (float): Value in y [depends]
        z (float): Value in z [depends]

    """

    def __init__(self, x=0.0, y=0.0, z=0.0):

        self.x = x
        self.y = y
        self.z = z

    def get_cpacs_points(self, tixi, xpath):
        """ Get x,y,z points (or 2 of those 3) from a given path in the CPACS file

        Args:
            tixi (handles): TIXI Handle of the CPACS file
            xpath (str): xpath to x,y,z value
        """

        coords = ['x','y','z']

        for coord in coords:
            try:
                value = tixi.getDoubleElement(xpath + '/' + coord)
                setattr(self, coord, value)
            except:
                pass


class Transformation:
    """
    The Class "Transformation" store scaling, rotation and tanlsation by
    calling the class "Point"

    Attributes:
        scaling (object): scaling object
        rotation (object): Rotation object
        translation (object): Translation object

    """

    def __init__(self):

        self.scaling = Point(1.0, 1.0, 1.0)
        self.rotation = Point()
        self.translation = Point()

    def get_cpacs_transf(self, tixi, xpath):
        """ Get scaling,rotation and translation from a given path in the
            CPACS file

        Args:
            tixi (handles): TIXI Handle of the CPACS file
            xpath (str): xpath to the tansformations
        """

        try:
            self.scaling.get_cpacs_points(tixi, xpath + '/transformation/scaling')
        except:
            log.warning('No scaling in this transformation!')

        try:
            self.rotation.get_cpacs_points(tixi, xpath + '/transformation/rotation')
        except:
            log.warning('No rotation in this transformation!')

        try:
            self.translation.get_cpacs_points(tixi, xpath + '/transformation/translation')
        except:
            log.warning('No translation in this transformation!')
