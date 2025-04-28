
/* Copyright (C) 2015 David Eller <david@larosterna.com>
 * 
 * Commercial License Usage
 * Licensees holding valid commercial licenses may use this file in accordance
 * with the terms contained in their respective non-exclusive license agreement.
 * For further information contact david@larosterna.com .
 *
 * GNU General Public License Usage
 * Alternatively, this file may be used under the terms of the GNU General
 * Public License version 3.0 as published by the Free Software Foundation and
 * appearing in the file gpl.txt included in the packaging of this file.
 */
 
#ifndef BATCHRUN_H
#define BATCHRUN_H

#include <surf/forward.h>
#include <QString>

/** Run sumo in batch mode.
 *  This class is used to run the mesh generation and file conversion
 *  operations offered by sumo in batch mode, i.e. without user intervention
 *  and without opeining a window.
 */
class BatchRun
{
public:

  /// return true if successful, false if no batch processing was requested
  static bool run(int argc, char *argv[]);

private:

  /// look for command-line options
  static bool parseOptions(int argc, char *argv[]);

  /// call tetgen executable
  static bool callTetgen(const std::string &bname);

  /// write short description of command line options to stdout
  static void printHelp();

private:

  /// tetgen option string
  static QString tetgen_opt;

  /// smx file to process
  static QString baseFile;

  /// whether to write IGES output for geometry
  static bool writeIges;

  /// whether to store mesh in EDGE format (default)
  static bool writeEdgeMesh;

  /// whether to store mesh in CGNS format
  static bool writeCgnsMesh;

  /// whether to store mesh in TAU format (only if netcdf available)
  static bool writeTauMesh;

  /// whether to store SU2 mesh
  static bool writeSu2Mesh;

  /// write surface mesh for dwfs
  static bool writeDwfsMesh;
};

#endif // BATCHRUN_H
