
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
 
#ifndef SURF_FSIELEMENT_H
#define SURF_FSIELEMENT_H

#include <genua/defines.h>
#include <genua/dvector.h>
#include <genua/point.h>

class FsiMesh;

/** Element wrapper for fluid-structure mapping.

  \sa mapping
  \sa FsiMesh
  */
class FsiElement
{
public:

  enum {max_nodes = 16};

  /// initialize
  FsiElement(const FsiMesh & m, uint gix);

  /// base class
  virtual ~FsiElement() {}

  /// access vertices
  uint nvertices() const {return nv;}

  /// access vertices
  const uint *vertices() const {return vi;}

  /// determine shape function value, return |J|
  virtual Real shapeFunction(Real u, Real v, Real N[]) const = 0;

  /// evaluate integrand at u, v with weight wgt
  void eval(const Vector & pf, Real u, Real v, Real wgt, Vct3 npf[]) const;

  /// evaluate integrand at u, v with weight wgt
  void eval(const Vector & pf, Real u, Real v, Real wgt, Vct6 npf[]) const;

  /// evaluate at single integration pont for multiple pressure fields
  void eval(const Matrix & mpf, Real u, Real v, Real wgt,
            PointList<3> & psn, PointGrid<6> & enf) const;

  /// return fluid elements nearest to integration points
  uint nearestFluidElement(Real u, Real v, Vct2 & fuv) const;

  /// integrate nodal force vector components
  void integrate(const Vector & pf, uint nip, const Real u[], const Real v[],
                 const Real wgt[], PointList<3,Real> & gnf) const;

  /// apply a tensor-product integration rule
  void tpIntegrate(const Vector & pf, uint nip, const Real u[], const Real wgt[],
                   PointList<3,Real> & gnf) const;

  /// integrate nodal force and moment components
  void integrate(const Vector & pf, uint nip, const Real u[], const Real v[],
                 const Real wgt[], PointList<6,Real> & gnf) const;

  /// apply a tensor-product integration rule
  void tpIntegrate(const Vector & pf, uint nip, const Real u[], const Real wgt[],
                   PointList<6,Real> & gnf) const;

  /// integrate nodal forces for multiple pressure fields
  void integrate(uint nip, const Real u[], const Real v[],
                 const Real wgt[], const Matrix & mpf,
                 PointGrid<6,Real> & gnf) const;

protected:

  /// reference to mesh object
  const FsiMesh & msh;

  /// mean element normal set by constructor
  Vct3 meanNormal;

  /// pointer to element indices
  const uint *vi;

  /// element section and local index
  uint nv, isec, lix;
};

/** Wrapper for 3-node triangles in FSI problems.
  \ingroup mapping
  \sa FsiMesh
  */
class FsiTri3 : public FsiElement
{
public:

  /// precompute constant element properties
  FsiTri3(const FsiMesh & m, uint gix);

  /// for validation
  Real area() const {return 0.5*detJ;}

  /// determine shape function value, return |J|
  Real shapeFunction(Real u, Real v, Real N[]) const {
    N[0] = 1.0 - u - v;
    N[1] = u;
    N[2] = v;
    return detJ;
  }

private:

  /// precomputed element area
  Real detJ;
};

/** Wrapper for 4-node quadrilaterals in FSI problems.
  \ingroup mapping
  \sa FsiMesh
  */
class FsiQuad4 : public FsiElement
{
public:

  /// precompute constant element properties
  FsiQuad4(const FsiMesh & m, uint gix);

  /// for validation
  Real area() const {return detJ;}

  /// determine shape function value, return |J|
  Real shapeFunction(Real u, Real v, Real N[]) const {

    // debug
    u = 0.5*(u + 1.0);
    v = 0.5*(v + 1.0);

    N[0] = (1.0 - u)*(1.0 - v);
    N[1] = u*(1.0 - v);
    N[2] = u*v;
    N[3] = (1.0 - u)*v;
    return detJ;
  }

private:

  /// precomputed element area
  Real detJ;
};

#endif // FSIELEMENT_H
