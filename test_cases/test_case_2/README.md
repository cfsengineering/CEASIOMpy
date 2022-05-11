<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_main.png">

# CEASIOMpy - Test case 2

In this second test case, we will learn how to create a CEASIOMpy workflow with the help of the Graphical User Interface (GUI). 
To run this test case, you will need to open a terminal and run the following command (:warning: Working directory for this test case will be written where you are running the command):

```bash
# To be in the CEASIOMpy Conda environment with all the dependencies
conda activate ceasiompy

# To run the test case 2
ceasiompy_run --testcase 2
```

By running the above command, you will see the following output:

<!-- <p align="center">
<img height="300" src="../../documents/figures/D150.png">
</p>
<p align="center">
3D view of the D150 aircraft
</p> -->

With this GUI, we will try to build the following workflow:

```mermaid
  graph LR;
      D150(D150 CPACS file)-->CPACSCreator;
      CPACSCreator-->CPACS2GMSH;
      CPACS2GMSH-->SU2Run;
      SU2Run-->PlotAeroCoefficients;
```


[**<<**](../test_case_1/README.md) Previous test case | [Home](../../README.md#test-cases) | Next test case [**>>**](../test_case_3/README.md)
