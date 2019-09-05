# TODO

## CEASIOMpy project
* Add a recognizable logo
* Make installation easier (Tixi, Tigl, TIGLCreator, sumo, SU2, pyTornado, RCE, conda?)
* Connecting CEASIOMpy with RCE?
* File structure
* Separate code from user working directory ???

## Module dependencies
* Add `__specs__.py` files for each modules
* Add 'type' for input/output in '__specs__.py' ?
* Add General File in/out Class
* Create a function to check consistency (does same variable name are stored a the same xpath, ...)
* Create a function to find in which Module a variable or xpath is used
* Create a function to generate a default /toolspecific node with all the possible XPath

## Documentation
* Automatic syncronisation of CPACS input/output
* Fix docstring translation/formatting
    * https://www.python.org/dev/peps/pep-0257/
    * http://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
* Finish "installation" and "getting_started" pages
* Possible workflow, module order/compatibility
* Create Test Cases
* Continue "How to contribute to CEASIOMpy"
* Example for how to create and add a new module

## Logging
* Fix file permission workaround in `ceasiomlogger.get_logger()` (don't use try-except)
* Do we want one big log file (global) or many small (local for each module)?

## Modules
* To adapt and integrate
    * GUI Edit AeroPerformanceMap
    * SUMO2CPACS
    * SU2CheckConvergence

* To develop
    * StaticStablility
    * DynamicStability
    * FlightModel
    * EngineTool
    * LaTeXReport

* Improve and check all Weight and Balance modules

## Aerodynamics
    * What to do when there is no moment coefficients
    * Calculate and save damping derivatives
    * Calculate and save Controls surface deflections

## Module to Editdata (GUI)
* GUI to create/edit/delete aeroMap from CPACS file
* Add kind of a GUI to enter missing input requirements...?

## RCE Integration
    * Create 'how to install' CEASIOMpy into RCE
    * Small logo for each module

## PyTornado module
Update `specs` file
    * Airfoil
    * Aeroperformance map

## Things to do for each module conversion/updating
    * Add __specs__ file
    * Check if the documentation is correctly auto generated

## Platform compatibility
    * find a solution for '/' in all path  
