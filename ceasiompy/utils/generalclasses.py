"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

General classes to get transformation from any part of a CPACS file

Python version: >=3.8

| Author: Aidan Jungo
| Creation: 2021-02-25

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================


from ceasiompy import log
from tixi3.tixi3wrapper import Tixi3Exception

# =================================================================================================
#   CLASSES
# =================================================================================================

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
        """Get x,y,z points (or 2 of those 3) from a given path in the CPACS file

        Args:
            tixi (handles): TIXI Handle of the CPACS file
            xpath (str): xpath to x,y,z value
        """

        coords = ["x", "y", "z"]
        if tixi.checkElement(xpath):
            for coord in coords:
                try:
                    value = tixi.getDoubleElement(xpath + "/" + coord)
                    setattr(self, coord, value)
                except Tixi3Exception:
                    pass
        else:
            log.warning(f"xpath {xpath} do not exist!")


class Transformation:
    """
    The Class "Transformation" store scaling, rotation and translation by
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
        """
        Get scaling, rotation and translation
        from a given path in the CPACS file

        Args:
            tixi (handles): TIXI Handle of the CPACS file
            xpath (str): xpath to the tansformations
        """

        self.tixi = tixi
        self.xpath = xpath

        self.scaling.get_cpacs_points(tixi, xpath + "/transformation/scaling")
        self.rotation.get_cpacs_points(tixi, xpath + "/transformation/rotation")
        self.translation.get_cpacs_points(tixi, xpath + "/transformation/translation")

        # Find type of reference: absGlobal, absLocal or nothing
        # TODO: check if it correct to get parent when absLocal is used..?
        ref_type = ""
        try:
            ref_type = self.tixi.getTextAttribute(
                self.xpath + "/transformation/translation", "refType"
            )
        except Tixi3Exception:
            log.info("No refType attribute")

        if ref_type != "absGlobal":
            self.get_parent_transformation()

    def get_parent_transformation(self):

        if self.tixi.checkElement(self.xpath + "/parentUID"):
            parent_uid = self.tixi.getTextElement(self.xpath + "/parentUID")
            log.info("The parent UID is: " + parent_uid)

            self.xpath = self.tixi.uIDGetXPath(parent_uid)

            # Get parent transformation
            transf = Transformation()
            transf.get_cpacs_transf(self.tixi, self.xpath)

            # Sum translation
            self.translation.x += transf.translation.x
            self.translation.y += transf.translation.y
            self.translation.z += transf.translation.z


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    log.info("Nothing to execute!")
