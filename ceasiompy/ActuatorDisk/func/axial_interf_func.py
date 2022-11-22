"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This function calculate axial interference factor

Args:
        lagrangian_moltiplicator (float): Lagrangian moltiplicator [-]
        non_dimensional_radius (float): Non dimensional radius [-]

Returns:
    axial_interference_factor (float):  Axial interference factor[-]

Python version: >=3.8

| Author: Giacomo Benedetti
| Creation: 2022-11-22

TODO:

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================


# =================================================================================================
#   FUNCTION
# =================================================================================================


def axial_interference_function(lagrangian_moltiplicator, non_dimensional_radius):

    axial_interference_factor = (lagrangian_moltiplicator * non_dimensional_radius**2) / (
        non_dimensional_radius**2 + (1 + lagrangian_moltiplicator) ** 2
    )
    return axial_interference_factor
