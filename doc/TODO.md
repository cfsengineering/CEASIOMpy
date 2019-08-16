# TODO

## CEASIOMpy project
* Add a recognizable logo
* Make installation easier (Tixi, Tigl, TIGLCreator, sumo, SU2, pyTornado, RCE, conda?)
    * Connecting CEASIOMpy with RCE?
* File structure
    * Separate code from user working directory

## Module dependencies
* Add `__specs__.py` files for each modules
* `_specs.py` better than `__specs__`?
* Add output for `ceasiompy.CLCalculator.__specs__`
* Add General File in/out Class
* Create a function to check consistency (does same variable name are stored a the same xpath, ...)
* Create a function to find in which Module a variable or xpath is used
* Create a function to generate a default /toolspecific field ...
* Add kind of a GUI to enter missing input requirements...?

## Documentation
* Automatic syncronisation of CPACS input/output
* Fix docstring translation/formatting
    * https://www.python.org/dev/peps/pep-0257/
    * http://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
* Make a page for users
* Finish "installation" and "getting_started" pages
* Possible workflow, module order/compatibility
* Create Test Cases and maybe module compatibility
* Continue "How to contribute to CEASIOMpy"
* Example for how to create and add a new module

## Logging

* Fix file permission workaround in `ceasiomlogger.get_logger()` (don't use try-except)
* Do we want one big log file (global) or many small (local for each module)?

## Aerodynamic modules
* How to store results in CPACS (AeroPerformanceMap, damping derivatives, ...)
* Folder structure for the calculation and results

## Modules
* To adapt and integrate
    * PyTornado
    * GUI Edit AeroPerformanceMap
    * SUMO2CPACS
    * CoefCPACS2CSV
    * PlotTool
    * SU2CheckConvergence

* To develop
    * StaticStablility
    * DynamicStability
    * FlightModel
    * EngineTool
    * LaTeXReport

* Improve and check all Weight and Balance modules


## RCE Integration
    * Upload .json file on Github + create 'how to install'
    * Add a script to automatically set the ToolDirectory path of each module
    * Small logo for each module

## PyTornado module
Update `specs` file
    * Airfoil
    * Aeroperformance map

## Things to do for each module conversion/updating
    * Add __specs__ file
    * Check if the documentation is correctly auto generated
