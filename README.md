# CEASIOMpy


CEASIOMpy is a Conceptual Aircraft Design Software.

Test1
__________

## Guidelines

### Naming

  - Variable :                  lower_case_with_underscores
  - Function :                  lower_case_with_underscores
  - Classes and Exceptions :    CapWords
  - Package and module :        short, all-lowercase names, no underscore
  - Constants :                 CAPITAL_LETTER_WITH_UNDERSCORE
  - Index in loops:             i,j,k  or lowercase (e.g. alpha, beta,...)

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
__________

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

__________

## Structure of CEASIOMpy Python script

All CEASIOMpy modules should follow (if possible) the same structure for
clarity. A template of this structure can be find here:
https://github.com/cfsengineering/CEASIOMpy/blob/master/lib/ModuleTemplate/mymodule.py

__________

## Logging method

The CEASIOMpy logger can be imported and used as following:

```python
sys.path.append('../')
from utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])
```

Then, you can use the following log in the code:

```python
log.debug('This is for debugging')
log.info('This is for debugging')
log.warning('This is Warnings')
log.error('This is for Error messages')
log.critical('This is for Critical error messages')
```

They will be saved in log file with the same name as you module (.log) and in
the console.

__________

## Tests





__________

## Documentation

If the previous rules are respected, it is possible to generate Doxygen
documention quite easily. At the root of CEASIOMpy project (/CEASIOMpy), you
can use:

```
>>> doxygen doxconf
```

It will generate ...

__________

## RCE Integration

RCE is
It should be possible to integrate every CEASIOMpy script as a RCE module which
could be connected to other RCE modules. Thess module should exchange
(if possible) only CPACS file.

__________
