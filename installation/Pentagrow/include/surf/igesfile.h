
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

#ifndef SURF_IGESFILE_H
#define SURF_IGESFILE_H

#include "forward.h"
#include "igessection.h" 
#include "igesentity.h"

/** Main interface to IGES files.
 *
 * This class is employed both to import existing IGES 5.3 files and to
 * assemble compliant files from geometry objects. Note that each object
 * to be written to file generates a directory entry (IgesDirEntry) and
 * a block of parameter data (IgesEntity).
 *
 * \ingroup interop
 * \sa IgesDirEntry, IgesEntity
 */
class IgesFile
{
public:

  /// empty IGES file
  IgesFile() {}

  /// check if the file 'fname' looks like IGES format
  static bool isIges(const std::string & fname);

  /// set start section content
  void startContent(const std::string & s) {
    startSec.setContent( s );
  }

  /// change product name
  void productName(const std::string & s) {
    globalSec.productName( s );
  }

  /// access model tolerance
  double modelTolerance() const {return globalSec.modelTolerance();}

  /// change model tolerance
  void modelTolerance(double tol) {
    globalSec.modelTolerance( tol );
  }

  /// change file name in global section
  void fileName(const std::string & s) {
    globalSec.fileName( s );
  }

  /// change native system name in global section
  void nativeSystem(const std::string & s) {
    globalSec.nativeSystem(s);
  }

  /// change preprocessor version in global section
  void preprocessorVersion(const std::string & s) {
    globalSec.preprocessorVersion(s);
  }

  /// access length unit name
  const std::string & unitName() const {return globalSec.unitnames;}

  /// set unit name
  void unitName(const std::string & s) {
    globalSec.unitnames = s;
  }

  /// number of directory entries currently present
  int nDirEntries() const {return dirSec.nlines()/2;}

  /// access directory entry by iges index
  void dirEntry(uint de, IgesDirEntry & entry) const;

  /// create entity corresponding to to entry
  IgesEntityPtr createEntity(const IgesDirEntry & entry) const;

  /// create entity corresponding to to entry index
  IgesEntityPtr createEntity(uint de) const;

  /// convenience function
  template <class EntityType>
  bool createEntity(const IgesDirEntry &entry, EntityType &et) const {
    IgesEntityPtr ep = createEntity(entry);
    return IgesEntity::as(ep, et);
  }

  /// convenience function
  template <class EntityType>
  bool createEntity(uint de, EntityType &et) const {
    IgesEntityPtr ep = createEntity(de);
    return IgesEntity::as(ep, et);
  }

  /// access directory
  IgesDirectorySection & directory() {return dirSec;}

  /// access directory
  const IgesDirectorySection & directory() const {return dirSec;}

  /// access parameter section
  IgesParameterSection & parameters() {return parSec;}

  /// access parameter section
  const IgesParameterSection & parameters() const {return parSec;}

  /// write to file
  void write(const std::string & fname);

  /// read sections from file
  void read(const std::string & fname);

private:

  /// start section with user-readable header
  IgesStartSection startSec;

  /// global section with file-wide parameters
  IgesGlobalSection globalSec;

  /// entity directory section
  IgesDirectorySection dirSec;

  /// parameter data section
  IgesParameterSection parSec;
};

#endif
