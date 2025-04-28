
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
 
#include <iostream>
#include <sstream>
#include <genua/pattern.h>
#include <genua/xcept.h>
#include <genua/point.h>
#include "curve.h"
#include "initgrid.h"
#include "dnmesh.h"
#include "linearsurf.h"
#include "igesfile.h"
#include "igesdirentry.h"
#include "iges118.h"
#include "iges126.h"
#include "iges124.h"

using namespace std;

// ---------------- local scope --------------------------------------------

//static inline bool uless(const Vct2 & a, const Vct2 & b)
//{
//  return a[0] < b[0];
//}

// -------------------------------------------------------------------------

LinearSurf::LinearSurf(const LinearSurf & a) : Surface(a)
{
  init(a.curves);
}

Vector LinearSurf::init(const CurvePtr &ca, const CurvePtr &cb)
{
  CurvePtrArray cva(2);
  cva[0] = ca;
  cva[1] = cb;
  return init(cva);
}

Vector LinearSurf::init(const CurvePtrArray & cv)
{
  // clone curves, but store only the spline part
  const uint nc(cv.size());
  curves.resize(nc);
  for (uint i=0; i<nc; ++i) 
    curves[i] = CurvePtr(new Curve(*cv[i]));
  
  uint nid = Curve::arclenParamet(curves, vp);
  if (nid != 0) {
    throw Error("LinearSurf '"+name()+"': Curves intersect/coincide.\n");
  }
  
  return vp;
}

uint LinearSurf::segment(Real v) const
{
  Vector::const_iterator pos;
  pos = std::lower_bound(vp.begin(), vp.end(), v);

  // handle out-of range cases
  if (pos == vp.begin())
    return 1;
  else if (pos == vp.end())
    return vp.size()-1;
  else
    return std::distance(vp.begin(), pos);
}

Vct3 LinearSurf::eval(Real u, Real v) const
{
  // find segment
  assert(u >= 0);
  assert(u <= 1);
  assert(v >= 0);
  assert(v <= 1);
  uint sg = segment(v);
  Real  t = (v - vp[sg-1])/(vp[sg] - vp[sg-1]);
  t = min(1.0, max(0.0,t));
  return (1-t)*curves[sg-1]->eval(u) + t*curves[sg]->eval(u);
}

Vct3 LinearSurf::derive(Real u, Real v, uint ku, uint kv) const
{
  assert(u >= 0);
  assert(u <= 1);
  assert(v >= 0);
  assert(v <= 1);
  if (ku == 0 and kv == 0)
    return eval(u,v);
  else if (kv > 1)
    return vct(0,0,0);
  else {
    uint sg = segment(v);
    if (kv == 1) {
      Vct3 xdv = curves[sg]->derive(u,ku) - curves[sg-1]->derive(u,ku);
      return xdv / (vp[sg] - vp[sg-1]);
    } else {
      Real t = (v - vp[sg-1]) / (vp[sg] - vp[sg-1]);
      t = min(1.0, max(0.0,t));
      return (1-t)*curves[sg-1]->derive(u,ku) + t*curves[sg]->derive(u,ku);
    }
  }
}

void LinearSurf::plane(Real u, Real v, Vct3 & S, Vct3 & Su, Vct3 & Sv) const
{
  assert(u >= 0);
  assert(u <= 1);
  assert(v >= 0);
  assert(v <= 1);
  uint sg = segment(v);
  Real idv = 1.0 / (vp[sg] - vp[sg-1]);
  Real  t = (v - vp[sg-1]) * idv;
  t = min(1.0, max(0.0,t));
  
  Vct3 c1, c1du, c2, c2du;
  curves[sg-1]->tgline(u, c1, c1du);
  curves[sg]->tgline(u, c2, c2du);
  
  S = (1-t)*c1 + t*c2;
  Sv = (c2 - c1) * idv;
  Su = (1-t)*c1du + t*c2du;
}

void LinearSurf::apply()
{
  // transform associated sections
  Mtx44 m(RFrame::trafoMatrix());
  for (uint i=0; i<curves.size(); ++i) {
    curves[i]->setTrafoMatrix(m);
    curves[i]->apply();
  }
  RFrame::clear();
}

void LinearSurf::initGridPattern(Vector & upi, Vector & vpi) const
{
  Vector tmp, up;
  for (uint i=0; i<curves.size(); ++i) {
    const Vector & kts( curves[i]->knots() );
    // tmp.insert(tmp.end(), kts.begin(), kts.end());
    const uint nu = std::min(size_t(32), std::max(size_t(8), kts.size()));
    AbstractCurve::gridFromKnots(nu, kts, up);
    tmp.insert(tmp.end(), up.begin(), up.end());
  }
  std::sort(tmp.begin(), tmp.end());

  almost_equal<Real> cmp(1e-3);
  tmp.erase( std::unique(tmp.begin(), tmp.end(), cmp), tmp.end() );
  // upi.swap(tmp);

  if (tmp.size() < 32u and tmp.size() > 8u) {
    upi.swap(tmp);
  } else {
    const uint nu = std::min(size_t(32), std::max(size_t(8), tmp.size()));
    interpolate_pattern(tmp, nu, upi);
  }

  vpi = vp;
}

void LinearSurf::dimStats(DimStat &stat) const
{
  Surface::dimStats(stat);

  uint nucp = 10;
  const int nc = curves.size();
  for (int i=0; i<nc; ++i)
    nucp = std::max(nucp, curves[i]->controls().size());

  stat.nControlU = nucp;
  stat.nControlV = vp.size();
}
    
void LinearSurf::isSymmetric(bool & usym, bool & vsym) const
{
  usym = false;
  vsym = false;
}

void LinearSurf::initMesh(const DnRefineCriterion & c, DnMesh & gnr) const
{
  Surface::initMesh(c, gnr);
  gnr.markKinks( 0.25*PI );
}

void LinearSurf::simpleMesh(PointGrid<3,float> & pgrid,
                            PointGrid<3,float> & ngrid,
                            uint pu, uint pv) const
{
  pu = std::max(pu, 1u);
  pv = std::max(pv, 1u);

  // determine a suitable set of parameters
  almost_equal<Real> pred(1e-4);

  Vector k, upt, vpt;
  const int nc = curves.size();
  for (int i=0; i<nc; ++i) {
    const Vector & kni( curves[i]->knots() );
    k.insert(k.end(), kni.begin(), kni.end());
  }

  std::sort(k.begin(), k.end());
  k.erase(std::unique(k.begin(), k.end(), pred), k.end());
  const int nu = (k.size() - 1)*pu + 1;
  upt.allocate(nu);
  interpolate_pattern(k, nu, upt);

  k = vp;
  std::sort(k.begin(), k.end());
  k.erase(std::unique(k.begin(), k.end(), pred), k.end());
  const int nv = (k.size() - 1)*pv + 1;
  vpt.allocate(nv);
  interpolate_pattern(k, nv, vpt);

  // start with grid, then convert to trimesh
  pgrid.resize(nu, nv);
  ngrid.resize(nu, nv);
  Vct3 S, Su, Sv, pn;
  for (int j=0; j<nv; ++j) {
    for (int i=0; i<nu; ++i) {
      plane(upt[i], vpt[j], S, Su, Sv);
      pn = cross(Su, Sv).normalized();
      convert(S, pgrid(i,j));
      convert(pn, ngrid(i,j));
    }
  }
}

/*
void LinearSurf::initGrid(Real lmax, Real phimax, PointGrid<2> & pts) const
{
  uint nu, nv;
  InitGrid ig(this);
  if (pts.size() < 100) {
    nu = 37;
  } else {
    nu = pts.nrows();
  }
  ig.initPattern( equi_pattern(nu), vp );
  ig.vRefineByLength(lmax);
  ig.uAdapt(lmax, phimax);
    
  Real stretch;
  nv = ig.ncols();
  do {
    nv += 8;
    stretch = ig.vRefineByStretch(nv, 100.);
  } while (stretch > 100.);
  ig.smooth(1);
  ig.collect(pts);
}*/

XmlElement LinearSurf::toXml(bool) const
{
  XmlElement xe("LinearSurf");
  xe["name"] = ids;
  xe["ncurves"] = str(curves.size());
  for (uint i=0; i<curves.size(); ++i)
    xe.append(curves[i]->toXml());

  return xe;
}

void LinearSurf::fromXml(const XmlElement & xe)
{
  if (xe.name() != "LinearSurf")
    throw Error("LinearSurf: incompatible XML representation.");

  rename(xe.attribute("name"));
  curves.clear();
  XmlElement::const_iterator itr;
  for (itr = xe.begin(); itr != xe.end(); ++itr) {
    CurvePtr cp = Curve::createFromXml(*itr);
    if (cp)
      curves.push_back(cp);
  }

  init(curves);
}

bool LinearSurf::fromIges(const IgesFile & file, const IgesDirEntry & dir)
{
  if (dir.etype != 118)
    return false;

  // retrieve curve representations
  IgesEntityPtr eptr = file.createEntity(dir);
  IgesRuledSurface isf;
  if ( IgesEntity::as(eptr, isf) ) {

    IgesDirEntry entry;

    CurvePtr pc0(new Curve());
    file.dirEntry(isf.firstCurve(), entry);
    if (not pc0->fromIges(file, entry))
      return false;

    CurvePtr pc1(new Curve());
    file.dirEntry(isf.secondCurve(), entry);
    if (not pc1->fromIges(file, entry))
      return false;

    curves.resize(2);
    curves[0] = pc0;
    curves[1] = pc1;

    vp.resize(2);
    vp[0] = 0.0;
    vp[1] = 1.0;

    setIgesName(file, isf);

  } else {
    return false;
  }

  return true;
}

int LinearSurf::toIges(IgesFile & igfile, int tfi) const
{
  // add all constituent curves first 
  const int n(curves.size());
  if (n < 2)
    return 0;
  
  Indices cvi(n);
  for (int i=0; i<n; ++i) 
    cvi[i] = curves[i]->toIges(igfile);
  
  // generate multiple surfaces 
  int ilast(0);
  for (int i=0; i<n-1; ++i) {
    IgesRuledSurface igs;
    igs.setup(cvi[i], cvi[i+1]);
    igs.direction(0);
    igs.form(1);
    igs.trafoMatrix( tfi );
    igs.label("LINR_SRF");
    igs.subscript( i+1 );
    ilast = igs.append(igfile);
  }

  return ilast;
}
