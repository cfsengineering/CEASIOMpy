
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
 

#ifndef SURF_LOADIPOL_H
#define SURF_LOADIPOL_H

#include <genua/mxmesh.h>

/** Aerodynamic load interpolator.

  LoadIpol serves as a container for pressure distributions associated with
  state information. The purpose of this class is to act as a frontend for
  aerodynamic load reconstruction from flight simulation data.

  \ingroup mapping
  \sa FsiMesh
*/
class LoadIpol : public MxMesh
{
public:

  /// empty interpolator
  LoadIpol() : iReference(NotFound) {}

  /// number of states
  uint nstate() const {return xlo.size();}

  /// access state
  const std::string & stateInfo(uint i, Real & lo, Real & hi) const {
    lo = xlo[i];
    hi = xhi[i];
    return stateNames[i];
  }

  /// define a new state
  uint newState(const std::string & name, Real lo=0.0, Real hi=1.0) {
    xlo.push_back(lo);
    xhi.push_back(hi);
    iDeriv.push_back(NotFound);
    stateNames.push_back(name);
    return xlo.size()-1;
  }

  /// mark field k as reference solution, provide state
  void markReference(uint k, const Vector & x);

  /// mark field kf as derivative for state kx, will normalize field kf!
  void markDerivative(uint kf, uint kx);

  /// import Cp data from another mesh file (exception on mismatch)
  uint cpimport(const MxMesh & mx, uint ifield);

  /// evaluate pressure coefficient field for given state
  void eval(const Vector & x, Vector & cp) const;

  /// create xml annotation
  void createNote();

  /// extract annotations after MxMesh::fromXml()
  bool extractNote();

private:

  /// compute normalized state
  void normState(const Vector & x, Vector & xn) const {
    const int n = nstate();
    assert(x.size() == size_t(n));
    xn.allocate(n);
    for (int i=0; i<n; ++i)
      xn[i] = (x[i] - xlo[i]) / (xhi[i] - xlo[i]);
  }

protected:

  /// names of the model states
  StringArray stateNames;

  /// lower limits for state variables (used for normalization)
  Vector xlo;

  /// upper limits for state variables (used for normalization)
  Vector xhi;

  /// normalized reference state for linearization
  Vector xnref;

  /// index of the field containing Cp for reference state
  uint iReference;

  /// index of the field which contains derivative, if applicable
  Indices iDeriv;
};

#endif // LOADIPOL_H
