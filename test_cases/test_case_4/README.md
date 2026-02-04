<img align="right" height="70" src="../../../documents/logos/CEASIOMpy_banner_main.png">

# CEASIOMpy - Test case 4

## Run a workflow from a command line

It is possible to run a workflow with a simple command line in which you have to describe the CPACS file and the module to run. This is a very fast way to run a workflow but the CPACS file must contain all the parameters required to run the workflow as you will not have the settings modification interface. It is generally recommended to use the CLI to run (or rerun) a workflow that you know already works for a certain CPACS file. Note that if you know what you want to change, you can change the values manually directly in the CPACS file.

To run this test case, you will need to open a terminal and run the following command:

```bash
# To be in the CEASIOMpy Conda environment with all the dependencies
conda activate ceasiompy

# To run the test case 4
ceasiompy_run -m test_files/CPACSfiles/d150.xml PyAVL SkinFriction
```

The following workflow will be executed:

```mermaid
  graph LR;
      D150([D150 CPACS file])-->PyAVL;
      PyAVL-->SkinFriction;
```

When it is over, you can check in the directory `WKDIR/Workflow_0**/Results/AeroCoefficients` (the Workflow number is incremented at every run), you should see a figure named `D150-Alt0.0-Mach0.3.png` which contains some plots of the aerodynamic coefficients. You can also check results from all modules in `WKDIR/Workflow_0**/Results`.

[**<<**](../test_case_3/README.md) Previous test case | [Home](../../README.md#test-cases) | Next test case [**>>**](../test_case_5/README.md)
