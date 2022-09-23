<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_main.png">

# CEASIOMpy - Test case 2

## Create and run a workflow with the GUI

In this second test case, you will learn how to create a CEASIOMpy workflow with the help of the Graphical User Interface (GUI).
To run this test case, you will need to open a terminal and run the following command (:warning: Working directory for this test case will be written where you are running the command):

```bash
# To be in the CEASIOMpy Conda environment with all the dependencies
conda activate ceasiompy

# To run the test case 2
ceasiompy_run --testcase 2
```

By running the above command, a new tab should appear in your default web browser, it should look like this:

![CEASIOMpy GUI](./testcase2_gui_main-page.png)

From that page you can select a working directory,by using the arrows and the list to navigate in your folder. All your results will be saved in this directory.

Then, select a CPACS file by clicking on the `Browse files` button, you can choose the `D150_simple.xml`. CPACS is a file format which contain the aircraft geometry and many other information.

Use now the sidebar on the left to select the next page `Workflow`.

We will try to build the following workflow:

```mermaid
  graph LR;
<<<<<<< HEAD
      CPACSCreator-->PyTornado;
      PyTornado-->WeightConventional;
      WeightConventional-->PlotAeroCoefficients;
||||||| parent of af67f93 (Replace new module name everywhere)
      D150([D150 CPACS file])-->CPACSCreator;
      CPACSCreator-->CPACS2GMSH;
      CPACS2GMSH-->SU2Run;
      SU2Run-->PlotAeroCoefficients;
=======
      D150([D150 CPACS file])-->CPACSCreator;
      CPACSCreator-->CPACS2GMSH;
      CPACS2GMSH-->SU2Run;
      SU2Run-->SaveAeroCoefficients;
>>>>>>> af67f93 (Replace new module name everywhere)
```

You can create this workflow by selecting the module in list and add them one by one.

TODO: add a gif of the workflow creation

On the side bar you can now go to the `Run workflow` page and click on `Run`.

A `CPACSCreator` window will open.

<p align="center">
<img height="580" src="testcase2_cpacscreator.png">
</p>
<p align="center">
CPACSCreator Interface
</p>

With CPACSCreator, you can modify the geometry of the aircraft. You will not do that in this tutorial, but you can check the following links for more information:

* [CPACSCreator tutorial](https://dlr-sc.github.io/tigl/doc/cpacscreator-0.1/tuto.html#tuto_create_from_scratch)

* [CPACSCreator video tutorial](https://www.youtube.com/watch?v=M5ryc7HT3uA)

In this case, you can just save the file and close the window. The next step will run automatically. You should be able to see what is happening in the logfile section (just bellow the `Run` button) or in the the terminal window.

When the calculation is over, you can click on the `Results` page (on the sidebar). You can select the aeromap `???` and choose what you want to plot on the x and y axis of the graph. You can also use the two filter plot only some part of the results.

TODO: add gif of selecting results

[**<<**](../test_case_1/README.md) Previous test case | [Home](../../README.md#test-cases) | Next test case [**>>**](../test_case_3/README.md)
