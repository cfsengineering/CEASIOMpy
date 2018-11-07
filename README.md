# CEASIOMpy

CEASIOMpy is a Conceptual Aircraft Design Software.

TEST1

## Installation

To use CEASIOMpy you just have to download or clone this repository in the Install directory of your choice. Then, you have to add it to your PYTHONPATH.

If use Windows, you have to add the following line, in your autoexec.bat file.
```
set PYTHONPATH=%PYTHONPATH%;\InstalDir\CEASIOMpy
```
 Alternatively, if you edit the system variable through the System Properties (My Computer > Properties > Advanced System Settings > Environment Variables) it should also worked.

If you use Linux in BASH you have to add the following line, in your .bashrc file
```
export PYTHONPATH="$PYTHONPATH: /InstalDir/CEASIOMpy/"
```

If you use Linux in TCSH you have to add the following line, in your .tcshrc file
```
setenv PYTHONPATH ${PYTHONPATH}: /InstalDir/CEASIOMpy/
```

### TIXI and TIGL Installation

From source or via Conda ...


## Guidelines

### Naming

  - Variable :                  lower_case_with_underscores
  - Function :                  lower_case_with_underscores
  - Classes and Exceptions :    CapWords
  - Package and module :        short, all-lowercase names, no underscore
  - Constants :                 CAPITAL_LETTER_WITH_UNDERSCORE
  - Index in loops:             i,j,k  or lowercase (e.g. alpha, beta,...) <br />
                                or more explicit (i_fus, i_wing, i_eng)

### Quotes
  - '  '    simple quote are used for string, e.g. print('Test1')
  - """ """ triple double quote are used for docstring (documentation)

### Variable
  - Variable name should be explicit, with in first position the object it
    represents, then detail about its type, if needed. <br />
        - aircraft_name <br />
        - engine_nb <br />
        - wing_span <br />
        - controlsurf_deflection_angle <br />

These Guidelines have been adapted from: https://gist.github.com/sloria/7001839
and https://www.python.org/dev/peps/pep-0008/



## Folder Structure

CEASIOMpy <br />
├── docs <br />
├── lib <br />
│   ├── ModuleTemplate <br />
│   │   ├── ToolInput <br />
│   │   ├── ToolOutut <br />
│   │   ├── docs <br />
│   │   ├── mymodule.log <br />
│   │   └── mymodule.py <br />
│   ├── OtherModule <br />
│   └── ... <br />
├── test <br />
│   ├── benchmarks <br />
│   ├── integration <br />
│   └── ... <br />
├── temp <br />
├── LICENSE <br />
├── README.md <br />
└── ... <br />



## Structure of CEASIOMpy Python script

All CEASIOMpy modules should follow (if possible) the same structure for clarity. A template of this structure can be find here:
https://github.com/cfsengineering/CEASIOMpy/blob/master/lib/ModuleTemplate/mymodule.py



## Logging method

The CEASIOMpy logger can be imported and used as following:

```python
from lib.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])
```

Be careful, if you did not add the paht to the CEASIOMpy folder in your 'PYTHONPATH' the logger will not be found.

Then, you can use the following log in the code:

```python
log.debug('This is for debugging messages')
log.info('This is for information messages')
log.warning('This is for warning messages')
log.error('This is for error messages')
log.critical('This is for critical error messages')
```

They will be saved in log file with the same name as your module (.log) and in the console.



## Tests

Each new module added should have corresponding test module, which allow to verify
all the main functionality of this module.

Structure of testing procedure ...



## Documentation

If the previous rules are respected, it is possible to generate Doxygen
documention quite easily. At the root of CEASIOMpy project (/CEASIOMpy), you
can use:

```
>>> doxygen doxconf
```

It will generate ...



## CPACS

The Common Parametric Aircraft Configuration Schema (CPACS) is a data definition for the air transportation system. CPACS enables engineers to exchange information between their tools. It is therefore a driver for multi-disciplinary and multi-fidelity design in distributed environments. CPACS describes the characteristics of aircraft, rotorcraft, engines, climate impact, fleets and mission in a structured, hierarchical manner. Not only product but also process information is stored in CPACS. The process information helps in setting up workflows for analysis modules. Due to the fact that CPACS follows a central model approach, the number of interfaces is reduced to a minimum.

CPACS Github : https://github.com/DLR-LY/CPACS



## RCE Integration

RCE is a distributed, workflow-driven integration environment developed by DLR. It is used by engineers and scientists to analyze, optimize, and design complex systems (e.g., aircraft, ships, or satellites) by using and integrating their own design and simulation tools.

RCE website: http://rcenvironment.de

It should be possible to integrate every CEASIOMpy module as a RCE module. Then, they could be connected to each other and exchange only CPACS files (if possible).
