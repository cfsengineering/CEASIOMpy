# Contributing to CEASIOMpy

- [Documentation/installation](#documentation--installation)
- [Development guidelines](#development-guidelines)
  - [Git/Github](#git--github)
  - [Python](#python)
    - [Conda](#conda)
    - [Formatting](#formatting)
    - [Naming conventions](#naming-conventions)
    - [Logging](#logging)
    - [Testing and coverage](#testing-and-coverage)
    - [Learn Python](#learn-python)
  - [CPACS](#cpacs)
  - [Other](#other)
- [How to contribute](#how-to-contribute)
  - [Reporting bugs](#reporting-bugs)
  - [Writing a new module](#writing-a-new-module)
  - [Writing specs file](#writing-specs-file)

## Documentation / Installation

The CEASIOMpy documentation is included in the [Github repository](./README.md) in Markdown files as this one. You can follow the links to find the information that you are looking for.

### Installation

To install CEASIOMpy please refer to the [installation page](./installation/INSTALLATION.md), it will guide you through the installation process depending on your system.

If you have some trouble to install CEASIOMpy on your computer, please use the following [Github Discussion page](https://github.com/cfsengineering/CEASIOMpy/discussions/categories/installation-issues). If your problem is something that could be reproduced it will be transformed into an issues.

## Development guidelines

### Git / Github

If you want to participate in the development of CEASIOMpy, it is a good thing if you have a basic understanding of how the version control system [Git](https://git-scm.com/) and the Github platform work.

- [Learn Git Branching](https://learngitbranching.js.org/?locale=en_EN) : online tutorials to learn how to use Git

- [Git Tutorials YouTube playlist](https://www.youtube.com/playlist?list=PL-osiE80TeTuRUfjRe54Eea17-YfnOOAx) by [Corey Schafer](https://www.youtube.com/channel/UCCezIgC97PvUuR4_gbFUs5g)

- [Official Github documentation](https://docs.github.com/en/get-started/quickstart/hello-world)

You could then fork the CEASIOMpy repository and create pull request when you think your work is ready to be reviewed.

### Python

#### Conda

It is highly recommended to use conda (or miniconda) for CEASIOMpy. Some libraries could be complicated to install without it. If you install the default environment as explain in the [installation procedure](./installation/INSTALLATION.md) you should then have all the requirements you need to run and develop CEASIOMpy.

#### Formatting

We try to use [Black](https://github.com/psf/black) as a formatting tool. It should be installed in the CEASIOMpy conda environment, if not, you can install it with:

```sh
pip install black
```

Then, you could either set it as the your default formatting tool in your IDE and set it to 'run on save' or run the following command when you want to lint your code:

```sh
black -l 99 name_of_your_file.py
```

#### Naming conventions

We try to follow the following naming conventions in CEASIOMpy:

- Variables : lower_case_with_underscores
- Functions : lower_case_with_underscores
- Classes and Exceptions : CapWords
- Packages and modules : short, all-lowercase names, no underscore
- Constants : CAPITAL_LETTER_WITH_UNDERSCORE
- Index in loops: i,j,k or lowercase (e.g. alpha, beta,…) or more explicit (i_fus, i_wing, i_eng)

Quotes:

- `" "` simple quotes are used for strings, e.g. `print("Test1")`
- `"""Docstring"""` triple-double quotes are used for docstring (documentation)
- Variable name should be explicit, with in first position the object
   it represents, then detail about its type, e.g:
  - aircraft_name
  - engine_nb
  - wing_span
  - controlsurf_deflection_angle

These guidelines have been adapted from:

- <https://www.python.org/dev/peps/pep-0008/#naming-conventions>
- <https://gist.github.com/sloria/7001839>
- <https://www.python.org/dev/peps/pep-0008/>

#### Logging

Logging the output of a module can be very useful to understand what happens during its execution or debugging it.  The CEASIOMpy logger can be imported and used as following:

```python
from lib.utils.ceasiomlogger import get_logger
log = get_logger()
```

Then, you can use the following logging function anywhere in the code of the module:

```python
log.debug('This is for debugging messages')
log.info('This is for information messages')
log.warning('This is for warning messages')
log.error('This is for error messages')
log.critical('This is for critical error messages')
```

The log file is saved at the root of CEASIOMpy (CEASIOMpy/ceasiompy.log) and printed in the console during the execution. In the log file, the second column is the level of the message and the third column is the module from which the message comes from.

#### Testing and coverage

If possible, new functions should have corresponding [pytest](https://docs.pytest.org/en/latest/getting-started.html).

Pytest, [flake8](https://flake8.pycqa.org/en/latest/) and [codecov](https://about.codecov.io/) are included in our [Github action CI](https://github.com/cfsengineering/CEASIOMpy/blob/main/.github/workflows/pytest.yml) and will run automatically for each push and pull request to the main branch.

You could also run the CI manually with on your machine with:

```bash
cd CEASIOMpy
./run_ci.sh
```

#### Learn Python

If you are new to Python we recommend some material that could help you (you can also find many other resources online):

- Website with Python tutorials:

  - [learnpython.org](https://www.learnpython.org/)

- On YouTube, videos by [Corey Schafer](https://www.youtube.com/channel/UCCezIgC97PvUuR4_gbFUs5g):
  - [Python Programming Beginner Tutorials playlist](https://www.youtube.com/playlist?list=PL-osiE80TeTskrapNbzXhwoFUiLCjGgY7)
  - [Python Object-Oriented Tutorial playlist](https://www.youtube.com/playlist?list=PL-osiE80TeTsqhIuOqKhwlXsIBIdSeYtc)

### CPACS

[CPACS](https://www.cpacs.de) is a Common Parametric Aircraft Configuration Schema [[1]](#Alder20). It is a data definition for the air transportation system. CPACS enables engineers to exchange information between their tools. CPACS is the default format to define aircrafts geometry in CEASIOMpy.

- [CPACS official website](https://www.cpacs.de)
- [CPACS Github repository](https://github.com/DLR-SL/CPACS)
- [CPACS documentation](https://www.cpacs.de/documentation/CPACS_3_3_0_Docs/html/89b6a288-0944-bd56-a1ef-8d3c8e48ad95.htm)
- Related libraries:
  - [TIXI](https://github.com/DLR-SC/tixi) A simple XML interface library
  - [TiGL](https://github.com/DLR-SC/tigl) Geometry Library to process aircraft geometries [[2]](#Sigg19)
  - [cpacspy](https://github.com/cfsengineering/cpacspy) A Python package to work with CPACS file and AeroMaps

### Other

Other resources that could the useful.

#### PyTornado

- [PyTornado website](https://pytornado.readthedocs.io/en/latest/)
- [Github repository](https://github.com/airinnova/pytornado)

#### SUMO

- [SUMO website](https://www.larosterna.com/products/open-source)

#### SU2

- [SU2 website](https://su2code.github.io/)
- [SU2 Configuration template file](https://github.com/su2code/SU2/blob/master/config_template.cfg)

## How to contribute

### Reporting bugs

If you find a bug, please report it on the [Github issues page](https://github.com/cfsengineering/CEASIOMpy/issues)

### Writing a new module

We highly encourage and appreciate any contributions to the CEASIOMpy codebase. If you have an idea for a new module, it could be a good thing to contact the CEASIOMpy team which could help you to write the module and be sure it is coherent with the rest of the project. You can also check the [CEASIOMpy project board](https://github.com/cfsengineering/CEASIOMpy/projects/1) to see what is the development status of the project.
If you want to write a new module, you can use the [Module Template](https://github.com/cfsengineering/CEASIOMpy/tree/main/ceasiompy/ModuleTemplate) to help you. Normally, all modules follow the same file structure:

```text
.
├── files               <- Files related to this module
│   ├── doc1.pdf
│   └── module_logo.png
├── func                <- Module subfunction import by the main one.
│   ├── subfunc1.py
│   └── subfunc2.py
├── tests               <- Test function for this module.
│   ├── cpacsfile_for_test.xml
│   ├── test_subfunc1.py
│   ├── test_subfunc2.py
│   └── test_moduletemplate.py
├── __specs__.py        <- Specification of the module.
├── moduletemplate.py   <- Main module of the module.
└── README.md           <- Readme for the module.
```

To develop a new module you should follow the above steps.:

- Create a fork of the CEASIOMpy repository
- On your fork, create a new branch
- On this branch, write your module and its test functions
- Create a pull request on the CEASIOMpy repository
- Ask for a review of the pull request
- If the pull request is accepted, the module will be merged into the CEASIOMpy repository

### Writing specs file

The `__specs__.py` file is a python file that contains the specification of the module. It is used to define your module input and output. It is also used to automatically create a tab in the SettingsGUI module with the correct input and default values.

The `__specs__.py` file should look like this:

```python
from ceasiompy.utils.moduleinterfaces import CPACSInOut
from ceasiompy.utils.xpath import FUSELAGES_XPATH, WINGS_XPATH
# Hint: you can check the file /ceasiompy/utils/xpath.py to find all the XPath which are already defined. If you use a new XPath, you can add it in the file.

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()


# ----- Input -----

# In the following example we add three (!) new entries to 'cpacs_inout'
# Try to use (readable) loops instead of copy-pasting three almost same entries
for direction in ["x", "y", "z"]:
    cpacs_inout.add_input(
        var_name=direction,
        var_type=float,
        default_value=None,
        unit="1",
        descr=f"Fuselage scaling on {direction} axis",
        xpath=FUSELAGES_XPATH + f"/fuselage/transformation/scaling/{direction}",
        gui=True,
        gui_name=f"{direction.capitalize()} scaling",
        gui_group="Fuselage scaling",
    )

# You can add input for different types of variables. In this case a string.
cpacs_inout.add_input(
    var_name="test",
    var_type=str,
    default_value="This is a test",
    unit=None,
    descr="This is a test of description",
    xpath="/cpacs/toolspecific/CEASIOMpy/test/myTest",
    gui=True,
    gui_name="My test",
    gui_group="Group Test",
)

# You can also provide a list of possible values for the input. In SettingsGUI, it will appear as a combobox.
cpacs_inout.add_input(
    var_name="other_var",
    var_type=list,
    default_value=[2, 33, 444],
    unit="[unit]",
    xpath="/cpacs/toolspecific/CEASIOMpy/test/myList",
    gui=True,
    gui_name="Choice",
    gui_group="My Selection",
)

# For a selection a aeromaps (amongst those in the CPACS file) you should use the following syntax:
cpacs_inout.add_input(
    var_name='aeromap_uid_select',
    var_type=list,
    default_value=None,
    xpath='/cpacs/toolspecific/CEASIOMpy/test/aeroMapUIDSelecton',
    gui=True,
    gui_name='__AEROMAP_SELECTION',
)

# For a checkbox selection of aeromaps (amongst those in the CPACS file) you should use the following syntax:
cpacs_inout.add_input(
    var_name='aeromap_uid_cb',
    var_type=list,
    default_value=None,
    xpath='/cpacs/toolspecific/CEASIOMpy/test/aeroMapCheckBoxSelction',
    gui=include_gui,
    gui_name='__AEROMAP_CHECHBOX',
)

# ----- Output -----

cpacs_inout.add_output(
    var_name="output",
    default_value=None,
    unit="1",
    descr="Description of the output",
    xpath="/cpacs/toolspecific/CEASIOMpy/test/myOutput",
)

```

## References

<!-- How to cite a reference [[1]](#Alder20) -->

<a id="Alder20">[1]</a> M. Alder, E. Moerland, J. Jepsen and B. Nagel. Recent Advances in Establishing a Common Language for Aircraft Design with CPACS. Aerospace Europe Conference 2020, Bordeaux, France, 2020. <https://elib.dlr.de/134341/>  

<a id="Sigg19">[2]</a> Siggel, M. and Kleinert, J. and Stollenwerk, T. and Maierl, R.: TiGL: An Open Source Computational Geometry Library for Parametric Aircraft Design. Mathematics in Computer Science (2019). [10.1007/s11786-019-00401-y](https://link.springer.com/article/10.1007/s11786-019-00401-y)  
