"""
CEASIOMpy
Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Logging method use by other CEASIOMpy modules

| Works with Python 2.7/3.6
| Author : Aidan Jungo
| Creation: 2018-09-26
| Last modifiction: 2018-09-27

TODO:

* Create at test file

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import logging.config
from logging.handlers import RotatingFileHandler

#==============================================================================
#   FUNCTIONS
#==============================================================================


def get_logger(name):
    """ Function to create a logger

    Function 'get_logger' create a logger, it sets the format and the level of
    the logfile and console log.

    Source : -

    ARGUMENTS
    (str)           name            -- Logger name

    RETURNS
    (logger)        logger          -- Logger
    """

    # Set logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Write logfile
    file_formatter = logging.Formatter('%(asctime)s - %(name)20s \
    - %(levelname)s - %(message)s')
    file_handler = RotatingFileHandler(name+'.log', 'a', 1000000, 1)
    file_handler.setLevel(logging.DEBUG)     # Level for the logfile
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Write log messages on the console
    console_formatter = logging.Formatter('%(levelname)-8s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)   # Level for the console log
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger
