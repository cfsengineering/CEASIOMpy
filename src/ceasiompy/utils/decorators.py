"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Scripts to convert CPACS file geometry into any geometry.


|   Author : Leon Deligny
|   Creation: 2025-Feb-12

"""

# Imports

import time

from functools import wraps

from typing import (
    Dict,
    Tuple,
    Callable,
)

from ceasiompy import log


# Functions

# TODO: Implement CEASIOMpy's own validate function
def validate_call():
    pass


def log_execution(f: Callable) -> Callable:
    """
    Debugging decorator.
    Logs function f and adds time for the function to finish.
    """

    @wraps(f)
    def wrapper(*args: Tuple, **kwargs: Dict):
        start_time = time.time()
        log.info(f"Executing {f.__name__}.")
        result = f(*args, **kwargs)
        end_time = time.time()
        log.info(f"Finished {f.__name__} in {end_time - start_time:.4f} seconds.")
        return result

    return wrapper


def log_test(f: Callable) -> Callable:
    """
    Log Test function decorator
    """

    @wraps(f)
    def wrapper(*args: Tuple, **kwargs: Dict):
        start_time = time.time()
        log.info(f"Testing {f.__name__}.")
        result = f(*args, **kwargs)
        end_time = time.time()
        log.info(f"Finished testing {f.__name__} in {end_time - start_time:.4f} seconds. \n")
        return result

    return wrapper
