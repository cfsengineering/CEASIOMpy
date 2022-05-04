"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to write and append new data to a CEASIOMpy report file (.md)

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2022-05-03

TODO:

    *

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path
from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger()


# =================================================================================================
#   CLASSES
# =================================================================================================


class ReportFile:
    def __init__(self, report_path: Path) -> None:
        pass


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def my_decorator(func):
    def wrapper():
        print("Something is happening before the function is called.")
        __super_func = func
        print(__super_func.__dict__)
        print("Something is happening after the function is called.")

    return wrapper


@my_decorator
def my_function(a=4):
    log.info(f"I'm the function, and I'm now being called! --> {a}")


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":

    print("Nothing to execute")

    my_function()
