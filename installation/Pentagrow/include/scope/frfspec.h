
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
 
#ifndef SCOPE_FRFSPEC_H
#define SCOPE_FRFSPEC_H

#include <genua/defines.h>
#include <genua/mxmesh.h>

/** Data required to assemble forces for a FRF subcase.
  */
struct FRFSubcase
{
  /// state coordinates
  CpxVector xihat;

  /// inertia term \f[ \omega^2 MZ \hat{\xi} \f], real and imaginary part
  Vector finr, fini;

  /// fields in amesh which are used for interpolation, Re/Im alternating
  Indices cpFields;

  /// coefficients for the above fields
  CpxVector cpCoef;

  /// frequency (1/s) for this subcase
  Real f;
};

/** Data required for a frequency-sweep FRF problem.
  */
struct FRFSpec
{
public:

  /// no subcases present?
  bool empty() const {
    return subcase.empty();
  }

  /// clear contents
  void clear() {
    amesh.reset();
    smesh.reset();
    modeMap.clear();
    subcase.clear();
  }

public:

  /// aerodynamic mesh
  MxMeshPtr amesh;

  /// structural mesh
  MxMeshPtr smesh;

  /// mapping between state index and eigenmode field
  Indices modeMap;

  /// subcase specifications
  std::vector<FRFSubcase> subcase;
};

#endif // FRFSPEC_H
