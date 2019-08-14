"""
CEASIOMpy
Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Logging method use by other CEASIOMpy modules

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2018-09-26
| Last modifiction: 2018-09-27

TODO:

    * Do we want one big logfile (global) or many small (local for each module)?

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import logging

#==============================================================================
#   FUNCTIONS
#==============================================================================


def get_logger(name):
    """ Function to create a logger

    Function 'get_logger' create a logger, it sets the format and the level of
    the logfile and console log.

    Args:
        name (str): Logger name

    Returns:
        logger (logger): Logger
    """

    logger = logging.getLogger(name)

    # NOTE: Multiple calls to getLogger() with the same name will return a
    # reference to the same logger object. However, there can be any number of
    # handlers (!) If a logger already as one or more handlers, none will be added
    if len(logger.handlers) > 0:
        return logger

    logger.setLevel(logging.DEBUG)

    # Write logfile
    file_formatter = logging.Formatter('%(asctime)s - %(name)20s \
    - %(levelname)s - %(message)s')

    # Workaround for ReadTheDocs: do not raise an error if we cannot create a log file
    try:
        file_handler = logging.FileHandler(filename=name+'.log', mode='w')
        file_handler.setLevel(logging.DEBUG)     # Level for the logfile
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except PermissionError:
        pass

    # Write log messages on the console
    console_formatter = logging.Formatter('%(levelname)-8s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)   # Level for the console log
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger
