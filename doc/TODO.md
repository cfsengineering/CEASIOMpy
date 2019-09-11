# TODO

## CEASIOMpy project
* Add a recognizable logo
* Make installation easier (Tixi, Tigl, TIGLCreator, sumo, SU2, RCE, conda?)
* Separate code from user working directory ???

## Module dependencies
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
* Create a page "How to use __specs__ file"

## Logging
* Fix file permission workaround in `ceasiomlogger.get_logger()` (don't use try-except)
* Do we want one big log file (global) or many small (local for each module)?

## RCE Integration
    * Create 'how to install' CEASIOMpy into RCE
    * Small logo for each module

## Modules
* To adapt and integrate
    * SUMO2CPACS
    * SU2CheckConvergence

* To develop
    * StaticStablility
    * DynamicStability
    * FlightModel
    * Propulsion
    * LaTeXReport

## Aerodynamics
    * What to do when there is no moment coefficients
    * Calculate and save damping derivatives
    * Calculate and save Controls surface deflections
    * Where and when update 'reference/area' and 'length'

## Module SettingsGUI
* GUI to create/edit/delete aeroMap from CPACS file

## PyTornado module
    * Airfoil
    * Aeroperformance map

## Weight and Balance modules
    * Check input/output, try to simplify
    * Modify the code to make it more CEASIOMpy style
    * Add __specs__ file

## Platform compatibility
    * find a solution for '/' in all path  
