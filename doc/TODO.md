# TODO

## CEASIOMpy project
* Make installation easier
    * External dependencies
        * Sumo
        * SU2
        * RCE
        * PyTornado
        * Conda?
    * Script for automatic installation?
* Separate code from user working directory ???

## Module dependencies
* Create a function to check consistency (does same variable name are stored a the same xpath, ...)

## Documentation
* Fix `gen_module_interface_pages.py`: Script does not run on ReadTheDocs because Tigl/Tixi import fails
* Fix docstring translation/formatting
    * https://www.python.org/dev/peps/pep-0257/
    * http://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
* Continue with documentation

## Modules
* To adapt and integrate
    * SUMO2CPACS

* To develop
    * Propulsion
    * DynamicStability
    * FlightModel
    * LaTeXReport
    * Beam model generator (automatic sizing)

### Aerodynamics
* Calculate and save controls surface deflections
* SU2CheckConvergence (maybe integrate with SU2Run)

### Module SettingsGUI
* Find a way to detect active modules in RCE

### Weight and Balance modules
* Check input/output, try to simplify
* Modify the code to make it more CEASIOMpy style
* Add missing `__specs__` file

### AeroFrame
* Get OptiMale test case to work (A/C with multiple wings) with SU2
* How deal with wing symmetries?
* Getting analysis settings from CPACS file
    * Choose e.g. PyTornado or SU2
* File path handling (where store temp files, results, etc.)
* Save intermediate results (i.e. results from each iteration)
* Add test case (make sure it runs)
* What should be stored in CPACS?
    * Maximum deflections at the end of the loop?
    * Or max. absolute difference versus iteration number

## Tests
* Create test function for every module

### Platform compatibility
* Try to install on different platform

## Miscellaneous
* Where and when update 'reference/area' and 'length'? (e.g. after changing A/C geometry)
