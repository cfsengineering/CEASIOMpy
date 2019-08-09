Guidelines
==========

Naming
------

-  Variable : lower_case_with_underscores
-  Function : lower_case_with_underscores
-  Classes and Exceptions : CapWords
-  Package and module : short, all-lowercase names, no underscore
-  Constants : CAPITAL_LETTER_WITH_UNDERSCORE
-  Index in loops: i,j,k or lowercase (e.g. alpha, beta,…) or more
   explicit (i_fus, i_wing, i_eng)

Quotes
------

-  ’ ’ simple quote are used for string, e.g. print(‘Test1’)
-  """ """ triple double quote are used for docstring (documentation)

Variable
--------

-  Variable name should be explicit, with in first position the object
   it represents, then detail about its type, if needed. - aircraft_name
   - engine_nb - wing_span - controlsurf_deflection_angle

These Guidelines have been adapted from:
https://gist.github.com/sloria/7001839 and
https://www.python.org/dev/peps/pep-0008/

Folder Structure
----------------

TODO

Structure of CEASIOMpy Python script
------------------------------------

All CEASIOMpy modules should follow (if possible) the same structure for
clarity. A template of this structure can be find here:
https://github.com/cfsengineering/CEASIOMpy/blob/master/lib/ModuleTemplate/mymodule.py

Logging method
--------------

The CEASIOMpy logger can be imported and used as following:

.. code:: python

   from lib.utils.ceasiomlogger import get_logger
   log = get_logger(__file__.split('.')[0])

Be careful, if you did not add the paht to the CEASIOMpy folder in your
‘PYTHONPATH’ the logger will not be found.

Then, you can use the following log in the code:

.. code:: python

   log.debug('This is for debugging messages')
   log.info('This is for information messages')
   log.warning('This is for warning messages')
   log.error('This is for error messages')
   log.critical('This is for critical error messages')

They will be saved in log file with the same name as your module (.log)
and in the console.

Tests
-----

Each new module added should have corresponding test module, which allow
to verify all the main functionality of this module.

Structure of testing procedure ...
