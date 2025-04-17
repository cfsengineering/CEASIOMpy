<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_main.png">

# CEASIOMpy - Test case 5

## Run a workflow from a configuration file

A CEASIOMpy configuration file is a text file (saved as `*.cfg`) which contains the information necessary to run CEASIOMpy. To store and re-execute workflows that you run often, it may be worthwhile to store them in a configuration file. The file should contain at least two lines, one to give the path to the CPACS file and one to give the modules to be executed.

For the test case you must first create and save a file named `my_ceasiompy_config_file.cfg` in `WKDIR`. Then, write the following lines in it:

```text
% This is an example of config file for ceasiompy
CPACS_TOOLINPUT = ../test_files/CPACSfiles/D150_simple.xml
MODULE_TO_RUN = ( PyAVL, SkinFriction, SaveAeroCoefficients )
```

You can now run it with the following command:

```bash
ceasiompy_run --cfg my_ceasiompy_config_file.cfg
```

It will create a new `Workflow_0**` (the number will increase at each run) directory in which you can found the results.

[**<<**](../test_case_4/README.md) Previous test case | [Home](../../README.md#test-cases) |
