# CEASIOMpy Test Cases

CEASIOMpy test cases are there to learn how to use CEASIOMpy. They can also be used to check that everything is installed and works as expected.

- [Test case 1](#test-case-1) : Run a simple existing workflow
- [Test case 2](#test-case-2) : Create and run a workflow with the Graphical User Interface
- [Test case 3](#test-case-3) : Create and run a workflow with a configuration file 

## Test case 1

:x: Not implemented yet

As a first test case, we will run a simple workflow which is already set up, you will just run it ans observe the results.

For this workflow, we will use the D150 (D150_simple.xml) file which is a simple A320-like aircraft.

To run this test case, you will need to open a terminal and run the following command:

```bash
# To be in the CEASIOMpy Conda environment with all the dependencies
conda activate ceasiompy

# To run the test case 1
ceasiompy_run --testcase 1
```

<!-- TODO: Where to save it ?? -->

This workflow will take as input the CPACS file of the aircraft (D150_simple.xml), it will run the PyTornado module, and it will plot the aerodynamic coefficients.

```mermaid
  graph LR;
      D150(D150 CPACS file)-->PyTornado;
      PyTornado-->PlotAeroCoefficients;
```






## Test case 2

:x: Not implemented yet

## Test case 3

:x: Not implemented yet