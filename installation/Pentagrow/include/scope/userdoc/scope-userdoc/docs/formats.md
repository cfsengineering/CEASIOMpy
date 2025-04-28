# Supported File Formats

Scope has built-in support for many file formats. 

## Mesh Data

Mesh files in the following formats can be imported into scope:

- Native .zml files (see below)
- [CGNS](http://cgns.github.io/) version 2.53 based on ADF (not HDF)
- [SU2](https://github.com/su2code/SU2/wiki/Mesh-File) mesh files (.su2)
- NASTRAN bulk data files (most, but not all, element types)
- [TAU](http://elib.dlr.de/90979/) mesh files (tetrahedral and hybrid, .taumesh)
- Legacy VTK format files (.vtk)
- TetGen meshes (.node/.element/.faces)
- EDGE mesh files (.bmesh)
- STL mesh files, both binary and plain text format
- Limited support for Abaqus input files (.inp)

## Computational Results

Mesh files in the following formats can be imported into scope:

- Native .zml files (see below)
- [CGNS](http://cgns.github.io/) version 2.53 based on ADF (not HDF)
- [SU2](http://su2.stanford.edu/) mesh files (.su2)
- NASTRAN punch files (.pch)
- Legacy VTK format files (.vtk)
- EDGE fluid data and boundary deformation data (.bout, .bdis)
- [AEREL](http://www.icas.org/media/pdf/ICAS%20Congress%20General%20Lectures/ICAS%201990%20Stockholm%20-%20proceedings%20content.pdf) results from AERELPLOT 
format files
- Data can be written to the [Ensight Gold](http://www-vis.lbl.gov/NERSC/Software/ensight/doc/OnlineHelp/UM-C11.pdf) file format which is most convenient for importing data into [Paraview](www.paraview.org/). 

## Mass import

There are many situations where a certain mesh file is used for a large number of simulations (or 'subcases'). Some simulation software directly supports writing a single output file containing these many subcases, while others (such as EDGE or SU2) write one output file for each case. With scope, it is possible to load arbitrarily many such result files, optionally [reduce file size](edit.md#mesh-size-reduction) by eliminating volume elements, and store the merged mesh and results in a single native file.

In order to import multiple result runs into a single native file, load first the corresponding mesh *geometry*, e.g. a .bmsh file. Once the mesh is available, scope will permit the selection multiple files in the file selection dialog opened by the **Load** function.

When an automated approach is preferred for use in scripting, the small command-line utility program ```mergefields``` can be called upon to join multiple solution files into a single one. An example command-line call used to merge multiple SU2 solution files (for different angles of attack) in VTK format would look as follows:
 

````
mergefields run1.vtk="Alpha=+1" run3.vtk="Alpha=+3" run5.vtk="Alpha=+5"
````

This call would generate a new file named ```merged.zml``` that contains three subcases with all fields from the three separate solution files. Such a merged file is especially useful when structural loads are to be generated for all of these solutions.

Finally, note that merged CFD files can become very large indeed. Loading and saving such files can be rather slow when accessing mapped network drives on Windows 7, XP, 2008, 2012. This is an inherent limitation of the operating system functions which needs to be [resolved](https://support.microsoft.com/en-us/help/10118/troubleshooting-slow-file-copying-in-windows) by system administration.    

## Native Format

Scope also supports a fairly efficient native binary file format, for which the extension .zml is used. Binary files are compressed (currently using [LZ4](https://cyan4973.github.io/lz4/) or [zlib](http://www.zlib.net/), but that may change) and can be converted to a human-readable and editable plain text XML format, either from within scope (Menu **File**, option **Export**, select **Plain XML**) or using the command-line utility **zml2xml**. Another command-line utility named **zmlprint** can be used to inspect the data structure of a native format file. Typical output of this utility looks like this:

````
Recognized GBF file format; summary: 
Node: MxMesh
Block: 0
2 attributes: 
[0] gbf_format_generator = XmlElement
[1] gbf_format_payload_type = Empty
  Node: MxNote
  Block: 0
  2 attributes: 
  [0] gbf_format_generator = XmlElement
  [1] gbf_format_payload_type = Empty
    Node: NastranGID
    Block: 62872
    5 attributes: 
    [0] gbf_format_generator = XmlElement
    [1] bdata_bytes = 62872
    [2] bdata_type = Int32
    [3] count = 15718
    [4] gbf_format_payload_type = Int32
    End of Node: [NastranGID]
  End of Node: [MxNote]
  Node: MxSolutionTree
  Block: 0
  4 attributes: 
  [0] gbf_format_generator = XmlElement
  [1] children = 2
  [2] name = Results
  [3] gbf_format_payload_type = Empty
    Node: MxNote
    Block: 0
    2 attributes: 
    [0] gbf_format_generator = XmlElement
    [1] gbf_format_payload_type = Empty
    End of Node: [MxNote]
    Node: MxSolutionTree
    Block: 0
    4 attributes: 
    [0] gbf_format_generator = XmlElement
    [1] children = 0
    [2] name = Displacements
    [3] gbf_format_payload_type = Empty
      Node: MxNote
      Block: 0
      2 attributes: 
      [0] gbf_format_generator = XmlElement
      [1] gbf_format_payload_type = Empty
      End of Node: [MxNote]
      Node: Fields
      Block: 256
      5 attributes: 
      [0] gbf_format_generator = XmlElement
      [1] bdata_bytes = 256
      [2] bdata_type = Int32
      [3] count = 64
      [4] gbf_format_payload_type = Int32
      End of Node: [Fields]
    End of Node: [MxSolutionTree]
[...]
 Node: MxMeshField
  Block: 754464
  9 attributes: 
  [0] gbf_format_generator = XmlElement
  [1] bdata_bytes = 754464
  [2] bdata_type = Float64
  [3] class = displacement
  [4] dimension = 6
  [5] name = Displacement 11
  [6] nodal_field = true
  [7] solution_index = 0
  [8] gbf_format_payload_type = Float64
    Node: MxNote
    Block: 0
    2 attributes: 
    [0] gbf_format_generator = XmlElement
    [1] gbf_format_payload_type = Empty
    End of Node: [MxNote]
  End of Node: [MxMeshField]
  Node: MxMeshField
  Block: 754464
  9 attributes: 
  [0] gbf_format_generator = XmlElement
  [1] bdata_bytes = 754464
  [2] bdata_type = Float64
  [3] class = displacement
  [4] dimension = 6
  [5] name = Displacement 12
  [6] nodal_field = true
  [7] solution_index = 0
  [8] gbf_format_payload_type = Float64
    Node: MxNote
    Block: 0
    2 attributes: 
    [0] gbf_format_generator = XmlElement
    [1] gbf_format_payload_type = Empty
    End of Node: [MxNote]
  End of Node: [MxMeshField]
[...]
````
