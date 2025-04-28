
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
 
#ifndef TDLSPEC_H
#define TDLSPEC_H

#include <genua/dmatrix.h>
#include <genua/mxmesh.h>

/** Time-domain representation of a single state.


  \sa FlightPath
  */
struct TdlState
{
  enum TdlFlag {Undefined, RigidBody, Elastic, AerodynControl};

  /// default empty construction
  TdlState() : modeindex(NotFound), ctrlindex(NotFound),
               imodefield(NotFound), idcpfield(NotFound), flag(Undefined) {}

  /// state history and its time derivatives
  Vector xi, dxi, ddxi;

  /// inertial force for this mode M_GG*Z_j
  Vector mggz;

  /// eigenmode/basis shape index
  uint modeindex;

  /// control variable index
  uint ctrlindex;

  /// index of the eigenmode / structural basis field
  uint imodefield;

  /// delta-cp field index (NotFound if no aerodynamics associated)
  uint idcpfield;

  /// flag indicates which type of state is represented
  TdlFlag flag;
};

struct TdlSpec
{
  /// aerodynamic mesh
  MxMeshPtr amesh;

  /// structural mesh
  MxMeshPtr smesh;

  /// state time histories
  std::vector<TdlState> states;

  /// time coordinates
  Vector time;

  /// dynamic pressure
  Vector qoo;

  /// reference dimensions used in non-dimensional values
  Real refChord, refSpan, refAlpha, refMach;

  /// index of reference cp field
  uint irefcp;

  /// destroy contents
  void clear() {
    qoo.clear();
    time.clear();
    states.clear();
    amesh.reset();
    smesh.reset();
    irefcp = NotFound;
  }

  /// test whether spec is defined
  bool empty() const {return states.empty();}
};

#endif // TDLSPEC_H
