
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
 

#ifndef SURF_RBFINTERPOLATOR_H
#define SURF_RBFINTERPOLATOR_H

#include "dispinterpolator.h"
#include <genua/forward.h>
#include <genua/dmatrix.h>
#include <genua/point.h>

/** Interpolate mesh deformation using radial basis functions.

  RbfInterpolator can be used to interpolate displacement
  modes of a coarse structural model to a fine aerodynamic
  mesh. The method employs polyharmonic (pseudo-cubic)
  basis functions and will therefore make use of dense
  linear algebra. Hence, using this method with detailed
  structural meshes with more than a few thousand nodes is
  fairly expensive: Computation time scales with the third
  power of the number of structural nodes and storage needs
  quadratically.

  As the RBF approach has a strong smoothing property, it is
  not advisable to use this strategy for discontinuous displacement
  patterns (mechanisms).

  \ingroup mapping
  \sa DispInterpolator, SurfInterpolator
  */
class RbfInterpolator : public DispInterpolator
{
public:

  /// supported RBF types
  enum RbfType { PolyHarmonic1, PolyHarmonic3, PolyHarmonic5,
                 Multiquadric, InvMultiquadric, WendlandPsi20,
                 WendlandPsi31, WendlandPsi42 };

  /// create empty interpolator
  RbfInterpolator() : DispInterpolator(), m_rtype(PolyHarmonic1),
                      m_beta(1.0), m_mergeThreshold(gmepsilon) {}

  /// set the type of RBF to use and the corresponding shape parameter
  void rbfType(RbfType type, Real epsparam = 1.0) {
    m_rtype = type;
    m_beta = epsparam;
  }

  /// access the RBF type
  RbfType rbfType() const {return m_rtype;}

  /// threshold used to merge structural nodes into centers
  void threshold(Real dst) {m_mergeThreshold = dst;}

  /// clear node index list
  void clearStrNodes() {m_strNodes.clear(); m_ctr.clear();}

  /// identify structural support nodes to use in interpolation
  void useStrNodes(const Indices & nds) {
    m_strNodes.insert(m_strNodes.end(), nds.begin(), nds.end());
  }

  /// add nodes for all sections using one of the specified element types
  void useStrNodes(bool usePoints, bool useBeams, bool useShells);

  /// add a complete mesh section as support nodes
  void useSection(uint isec);

  /// generate a set of RBF centers from point tree
  void centersFromTree(size_t ntarget=1024);

  /// construct RBF approximation basis
  void buildRbfBasis();

  /// compute eigenmode interpolation for aerodynamic mesh
  uint map();

private:

  /// evaluate RBF for mode jm at location p (debugging)
  void eval(uint jm, const Vct3 & p, Vct3 & dx) const;

  /// remove duplicate RBF centers
  uint uniqueCenters();

  /// configurable RBF basis
  double rbf(const Vct3 & x, const Vct3 & c) const
  {
    double rx = x[0] - c[0];
    double ry = x[1] - c[1];
    double rz = x[2] - c[2];
    double t, t1, t2, rsq = (rx*rx + ry*ry + rz*rz);
    switch (m_rtype) {
    case PolyHarmonic1:
      return std::sqrt(rsq);
    case PolyHarmonic3:
      return std::sqrt(rsq)*rsq;
    case PolyHarmonic5:
      return sq(rsq)*std::sqrt(rsq);
    case Multiquadric:
      return std::sqrt(1.0 + m_beta*rsq);
    case InvMultiquadric:
      return 1.0 / (1.0 + m_beta*rsq);
    case WendlandPsi20:
      t = std::sqrt(rsq) / m_beta;
      return (t < 1.0) ? sq(1-t) : 0.0;
    case WendlandPsi31:
      t = std::sqrt(rsq) / m_beta;
      t1 = sq(1-t);
      return (t < 1.0) ? sq(t1)*(4.*t + 1.0) : 0.0;
    case WendlandPsi42:
      t = std::sqrt(rsq) / m_beta;
      t1 = sq(1-t);
      t2 = cb(t1) * (35*sq(t) + 18*t + 3);
      return (t < 1.0) ? t2 : 0.0;
    default:
      return std::sqrt(rsq);
    }
  }

private:

  /// structural nodes used for interpolation
  Indices m_strNodes;

  /// cleaned up point set (RBF centers)
  PointList<3> m_ctr;

  /// RBF coefficients for structural modeshapes
  DMatrix<double> m_wrbf;

  /// flag for type of basis function to use
  RbfType m_rtype;

  /// RBF shape paramter (if any needed)
  Real m_beta;

  /// center merge threshold
  Real m_mergeThreshold;
};

#endif // RBFINTERPOLATOR_H
