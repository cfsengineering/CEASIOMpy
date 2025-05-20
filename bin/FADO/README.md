# FADO
Framework for Aerostructural Design Optimization

## Motivation
Q: "What is my purpose?"

A: "You run other codes."

More seriously, the typical use case is:
you have a simulation code (CFD, FEA, etc.) that reads/writes its inputs/outputs from/to text file(s),
you want to wrap the execution of that code, for example to use it in an optimization,
but that code does not have a Python interface quite like what you would like...

FADO provides abstractions to make this job easier than writing specialized scripts for each application,
scripting is still required, but the resulting scripts should be easier to maintain/adapt/modify.

The design of the framework is centered around large scale applications (10k+ variables) and functions that are expensive to evaluate (compared to the cost of preparing input files).

## Abstractions
From the top down (and not a replacement for the docs):

- **Driver**: The class of objects used to wrap the execution steps required to evaluate functions and their gradients in a way that conforms to the interface of particular optimizers. Drivers can evaluate all their functions simultaneously (i.e. in parallel).
- **Function**: An entity with one scalar output and any number of input "variables". Functions are further defined by the steps ("evaluations") required to obtain their value and possibly their gradient.
- **Variable**: The scalar or vector inputs of functions that are exposed to the optimizers.
- **Evaluation**: These wrap the calls to the external codes, they are configured with the input and data files, and the instructions, required to execute the code. "Parameters" can be associated with evaluations to introduce small changes to the input files (e.g. change a boundary condition in a multipoint optimization).
- **Parameter**: A numeric or text variable that is not exposed to the optimizer, they are useful to introduce small modifications to the input files to make a small number of template input files applicable to as many evaluations as possible.

**Note**: The calls to external codes from `FADO.ExternalRun` evaluations are made with `subprocess.call(..., shell=True)`, don't run optimizations as root, or in system directories, etc.

## Interfacing with files
Function, Variable, and Parameter need ways to be written and read to or from files.
Any object implementing `write(file,values)` and/or `read(file) -> values` can be used, five classes are provided that should cover most scenarios:

- **LabelReplacer**: Replaces any occurrence of a label (a string) with the value of a scalar variable or parameter.
- **ArrayLabelReplacer**: Does the same for array-like values.
- **PreStringHandler**: Reads(writes) a list of values separated by a configurable delimiter from(in) front of a label defining the start of a line (i.e. the line must start with the label).
- **TableReader/Writer**: Reads or writes to a section of a delimited table, rows outside of the table range do not need to be in table format, but those inside are expected to have the same number of columns, the examples should make it clear how to use these classes.
- **LabeledTableReader**: Reads values from CSV-type files based on column name and range of rows.

## Installation
Make the parent directory of FADO reachable to Python, usually via PYTHONPATH, `from FADO import *` should then work (provided the name of the directory was not changed).

## Dependencies
Hard dependency on NumPy, ndarrays are used throughout the code.
The ExteriorPenaltyDriver was designed around the [SciPy.optimize.minimize](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html) interface, but a simple implementation of the Fletcher-Reeves method is available (see example2_SU2).
The ScipyDriver was designed with the constrained optimization methods in mind (especially SLSQP) but does not strictly require SciPy to be used.
To use the IpoptDriver you need [IPyOpt](https://github.com/g-braeunlich/IPyOpt) and [Ipopt](https://github.com/coin-or/Ipopt), the latter can be installed with apt-get.

## Usage
Have a look at the examples, "examples/rosenbrock" is a contrived example using the Rosenbrock function, the others are realistic uses of [SU2](https://su2code.github.io/) (version > 7.1.0).
All the important classes and methods have Python documentation strings, these can be printed using the utility function `printDocumentation`, e.g. `FADO.printDocumentation(FADO.TableReader)`, for classes this will print the documentation for all their methods.
In general, undocumented methods are meant for FADO's internal use, and should not be called by users.

## License
[LGPL-3.0](https://www.gnu.org/licenses/lgpl-3.0.html)

