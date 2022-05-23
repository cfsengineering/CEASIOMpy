"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions and variables for CPACS2GMSH

Python version: >=3.7

| Author : Tony Govoni
| Creation: 2022-02-04

TODO:

"""

# Define mesh color for GMSH, only use in GUI (red, green, blue, brightness)
MESH_COLORS = {
    "farfield": (255, 200, 0, 100),
    "symmetry": (153, 255, 255, 100),
    "wing": (0, 200, 200, 100),
    "fuselage": (255, 215, 0, 100),
    "pylon": (255, 15, 255, 100),
    "engine": (127, 0, 255, 100),
    "bad_surface": (255, 0, 0, 255),
    "good_surface": (0, 255, 0, 100),
}
