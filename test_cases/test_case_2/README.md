<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_main.png">

# CEASIOMpy - Test case 2

## Create and run a workflow with the GUI

In this second test case, you will learn how to create a CEASIOMpy workflow with the help of the Graphical User Interface (GUI).
To run this test case, you will need to open a terminal and run the following command:

```bash
# To be in the CEASIOMpy Conda environment with all the dependencies
conda activate ceasiompy

# To run the test case 2
ceasiompy_run --testcase 2
```

By running the above command, a new tab should appear in your default web browser, it should look like this:

![CEASIOMpy GUI](./testcase2_gui_main-page.png)

From that page you can select a working directory, by using the arrows and the list to navigate in your folder. All your results will be saved in this directory.

Then, select a CPACS file by clicking on the `Browse files` button, you can choose the `D150_simple.xml` (it could be found in /CEASIOMpy/test_files/CPACSfiles/D150_simple.xml). CPACS is a file format which contain the aircraft geometry and many other information.

We can now use now the sidebar on the left to select the next tab, that is to say `Workflow`.

We will try to build the following workflow:

```mermaid
  graph LR;
      D150([D150 CPACS file])-->CPACSCreator;
      CPACSCreator-->CPACS2GMSH;
      CPACS2GMSH-->SU2Run;
      SU2Run-->SaveAeroCoefficients;
```

You can create this workflow by selecting the module in list and add them one by one, as demonstrate bellow.

<p align="center">
<img height="480" src="testcase2_workflow_creation.gif">
</p>
<p align="center">
Creation of a workflow with CEASIOMpy GUI
</p>

On the side bar you can now go to the `Run workflow` tab, for now we will skip the `Settings` tab.
Once arrived on the page, you can just click on `Run` to execute the workflow.

<p align="center">
<img height="380" src="testcase2_run_workflow.png">
</p>
<p align="center">
Run workflow page
</p>

When the first module is executed, you should see a `CPACSCreator` window that pops up.

<p align="center">
<img height="580" src="testcase2_cpacscreator.png">
</p>
<p align="center">
CPACSCreator Interface
</p>

With CPACSCreator, you can modify the geometry of the aircraft. We will not do that in this tutorial, but you can check the following links for more information:

* [CPACSCreator tutorial](https://dlr-sc.github.io/tigl/doc/cpacscreator-0.1/tuto.html#tuto_create_from_scratch)

* [CPACSCreator video tutorial](https://www.youtube.com/watch?v=M5ryc7HT3uA)

In this case, you can just save the file and close the window. The next modules will run automatically. You should be able to see what is happening in the logfile section (just bellow the `Run` button) or in the the terminal window. It could take a few minutes depending on your computer because it will create a mesh with [GMSH](https://gmsh.info/) and run it with [SU2](https://su2code.github.io/).

When the calculation is over, you can click on the `Results` tab (on the sidebar). In the results part there are tabs corresponding to the different module used during the workflow, you can explore the results.

<p align="center">
<img height="480" src="testcase2_results.gif">
</p>
<p align="center">
Creation of a workflow with CEASIOMpy GUI
</p>

All the results can also be found in the working directory you chose at the beginning of the testcase.

[**<<**](../test_case_1/README.md) Previous test case | [Home](../../README.md#test-cases) | Next test case [**>>**](../test_case_3/README.md)
