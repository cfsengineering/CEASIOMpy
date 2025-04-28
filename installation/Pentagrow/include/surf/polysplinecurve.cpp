
/* Copyright (C) 2017 David Eller <david@larosterna.com>
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

#include "polysplinecurve.h"
#include "igesfile.h"
#include "iges126.h"
#include "iges406.h"
#include "stepfile.h"
#include "step_ap203.h"
#include <genua/dbprint.h>
#include <iostream>

using namespace std;

Vector PolySplineCurve::createPolyline(const PointList3d &pts)
{
  const int np = pts.size();
  Vector u(np);
  for (int i=1; i<np; ++i) {
    u[i] = u[i-1] + norm(pts[i] - pts[i-1]);
  }

  // to alleviate the situation where there are multiples of input point,
  // add a small degree of uniform parameterization to the vector u
  Real usum = u.back();
  Real ueps = std::max(1e-2 * (usum / np), 1e-6*usum);
  for (int i=1; i<np; ++i) {
    u[i] += i*ueps;
  }

  u /= u.back();
  createPolyline(u, pts);

  return u;
}

void PolySplineCurve::createPolyline(const Vector &upar, const PointList3d &pts)
{
  ub.init(1, upar);
  cp = pts;
}

Vct3 PolySplineCurve::eval(Real u) const
{
  u = tmap(u);
  assert(u >= 0);
  assert(u <= 1);

  Real fu[8];
  const int uspan = ub.lleval(u, fu);

  Vct3 pt;
  const int pu = ub.degree();
  for (int i=0; i<pu+1; ++i)
    pt += fu[i] * cp[uspan-pu+i];

  return pt;
}

Vct3 PolySplineCurve::derive(Real u, uint ku) const
{
  Vct3 pt;
  int uspan;
  if (ku == 0) {
    return eval(u);
  } else {
    u = tmap(u);
    assert(u >= 0);
    assert(u <= 1);
    const int pu = ub.degree();
    Matrix fu(ku+1, pu+1);
    uspan = ub.derive(u, ku, fu);
    for (int i=0; i<pu+1; ++i)
      pt += (tend - tstart)*fu(ku,i) * cp[uspan-pu+i];
  }

  return pt;
}

void PolySplineCurve::tgline(Real t, Vct3 &c, Vct3 &dc) const
{
  c = 0.0;
  dc = 0.0;

  Real u = tmap(t);
  assert(u >= 0);
  assert(u <= 1);

  const int pu = ub.degree();
  Matrix fdu(2, pu+1);
  const int uspan = ub.derive(u, 1, fdu);

  Real fu[8];
  ub.lleval(u, fu);

  for (int i=0; i<pu+1; ++i) {
    const Vct3 & cpi = cp[uspan-pu+i];
    dc += (tend - tstart)*fdu(1,i) * cpi;
    c += fu[i] * cpi;
  }
}

void PolySplineCurve::apply()
{
  PointGrid<3>::iterator itr;
  for (itr = cp.begin(); itr != cp.end(); ++itr)
    *itr = forward(*itr);
  RFrame::clear();
}

void PolySplineCurve::initGrid(Vector &t) const
{
  const int nps = std::max(2u, ub.degree() / 2);
  const int ntv = 2 + (cp.size()-1)*nps;
  AbstractCurve::gridFromKnots( ntv, ub.getKnots(), t, tstart, tend);
}

XmlElement PolySplineCurve::toXml(bool share) const
{
  XmlElement xe("PolySplineCurve");
  xe["name"] = name();
  xe["tstart"] = str(tstart);
  xe["tend"] = str(tend);
  xe["kfront"] = str(kfront);
  xe["kback"] = str(kback);
  xe.append(ub.toXml());

  XmlElement xcp("ControlPoints");
  xcp.attribute("count") = str(cp.size());
  xcp.asBinary(3*cp.size(), cp.pointer(), share);
  xe.append(std::move(xcp));

  return xe;
}

void PolySplineCurve::fromXml(const XmlElement & xe)
{
  *this = PolySplineCurve();

  assert(xe.name() == "PolySplineCurve");
  tstart = xe.attr2float("tstart", 0.0);
  tend = xe.attr2float("tend", 1.0);
  kfront = xe.attr2float("kfront", 0.0);
  kback = xe.attr2float("kback", 1.0);
  rename( xe.attribute("name") );
  XmlElement::const_iterator itr, last;
  last = xe.end();
  for (itr = xe.begin(); itr != last; ++itr) {
    if (itr->name() == "SplineBasis") {
      ub.fromXml(*itr);
    } else if (itr->name() == "ControlPoints") {
      uint n = Int( itr->attribute("count") );
      cp.resize(n);
      itr->fetch(3*cp.size(), cp.pointer());
    }
  }
}

bool PolySplineCurve::fromIges(const IgesFile & file,
                               const IgesDirEntry & entry)
{
  if (entry.etype != 126)
    return false;

  *this = PolySplineCurve();
  IgesEntityPtr eptr = file.createEntity(entry);
  IgesSplineCurve ssf;
  if (IgesEntity::as(eptr, ssf)) {

    // intercept case of too high polynomial order
    if (ssf.degree() > 7) {
      dbprint("Spline curve degree exceeds 7.");
      return false;
    }
    if (not ssf.isPolynomial()) {
      dbprint("Cannot handle rational spline curves yet.");
      return false;
    }

    // normalize knot vector to range 0,1
    Vector knots( ssf.knotVector() );
    kfront = knots.front();
    kback = knots.back();
    knots -= kfront;
    knots /= kback - kfront;

    // subregion mapping, transformed to (0,1)
    tstart = (ssf.ustart - kfront) / (kback - kfront);
    tend = (ssf.uend - kfront) / (kback - kfront);

    assert(tstart >= 0.0);
    assert(tend <= 1.0);

    ub = SplineBasis(ssf.degree(), knots);
    cp = ssf.ctrlPoints();

  } else {
    return false;
  }

  setIgesName(file, ssf);
  setIgesTransform(file, entry);

  return true;
}

int PolySplineCurve::toIges(IgesFile & file, int tfi) const
{
  const Vector & ukts(ub.getKnots());
  if (ukts.empty())
    return 0;

  int inp = 0;
  if ( not name().empty() ) {
    IgesNameProperty np(name());
    inp = np.append(file);
  }

  IgesSplineCurve igs;
  igs.setup(cp.size(), ub.degree(), ukts.pointer(), cp.pointer());
  igs.trafoMatrix(tfi);
  igs.label("PSPL_CRV");
  if (inp != 0)
    igs.addPropRef(inp);
  return igs.append( file );
}

size_t PolySplineCurve::writeGCode(std::ostream &os) const
{
  if (ub.degree() == 2 or ub.degree() == 3) {
    const Vector & kts = ub.getKnots();
    const size_t nctrl = cp.size();
    const size_t q = ub.degree();
    os << "G64 BSPLINE SD=" << ub.degree() << std::endl;
    for (size_t i=0; i<nctrl; ++i) {
      const Vct3 &p = cp[i];
      os << "X=" << p[0] << " Y=" << p[1] << " Z=" << p[2]
         << " PL="<< kts[q+i] - kts[q+i-1] << std::endl;
    }
    return nctrl;
  } else if (ub.degree() == 1) {
    os << "G01" << std::endl;
    for (const Vct3 & p : cp)
      os << "X=" << p[0] << " Y=" << p[1] << " Z=" << p[2] << std::endl;
    return cp.size();
  }

  // TODO
  // order 4,5 -> hack into polynomial segments and write POLY blocks
  // order > 5 -> approximate using 5th degree polynomial segments

  return 0;
}

bool PolySplineCurve::fromStep(const StepFile & file,
                               const StepBSplineCurveWithKnots *ep)
{
  if ( ep->degree > 7 )
    return false;

  // if (not ep->name.empty())
  //   rename( ep->name );

  // extract knot vectors, basis function spec
  assert(ep->knots.size() == ep->knot_multiplicities.size());
  ub.init( ep->degree, ep->knots.size(),
           &(ep->knots[0]), &(ep->knot_multiplicities[0]) );

  // gather control points
  const StepCartesianPoint *pp = 0;
  const int ncp = ep->control_points_list.size();
  cp.resize(ncp);
  for (int j=0; j<ncp; ++j) {
    bool ok = file.as( ep->control_points_list[j], &pp );
    if (not ok)
      return false;
    for (int k=0; k<3; ++k)
      cp[j][k] = pp->coordinates[k];
  }

  return true;
}

PolySplineCurve *PolySplineCurve::clone() const
{
  return (new PolySplineCurve(*this));
}
