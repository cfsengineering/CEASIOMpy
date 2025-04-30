
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
 
#include "abstractcurve.h"
#include "mappedcurve.h"
#include "curve.h"
#include "circulararc.h"
#include "airfoil.h"
#include "symframe.h"
#include "openframe.h"
#include "ellipframe.h"
#include "eggframe.h"
#include "compositecurve.h"
#include "polysplinecurve.h"
#include "linecurve.h"
#include "rationalsplinecurve.h"
#include "igesfile.h"
#include "igesdirentry.h"
#include "iges406.h"
#include "iges100.h"
#include "iges124.h"
#include "iges126.h"
#include "dcmeshcrit.h"
#include <genua/defines.h>
#include <genua/pattern.h>
#include <genua/dbprint.h>
#include <genua/cgmesh.h>
#include <genua/smallqr.h>

void AbstractCurve::tgline(Real t, Vct3 & c, Vct3 & dc) const
{
  // default implementation
  c = this->eval(t);
  dc = this->derive(t, 1);
}

bool AbstractCurve::project(const Vct3 &pt, Real &s, Real stol, Real ttol) const
{
//  const Real sqst = sq(stol);
//  const Real sqtt = sq(ttol);
//  Vct3 b, c, dc;
//  for (int i=0; i<16; ++i) {
//    tgline(t, c, dc);
//    b = pt - c;
//    if (sq(b) < sqst)
//      return true;
//    qrlls<3,1>(dc.pointer(), b.pointer());
//    t += b[0];
//    if (sq(b[0]) < sqtt)
//      return true;
//    t = clamp(t, 0.0, 1.0);
//  }
//  return false;

  Vct3 pc, tc;
  const int nbs = 64;
  for (int i=0; i<nbs; ++i) {
    this->tgline(s, pc, tc); // local lin is pc + s*tc
    Vct3 d = pt - pc;
    Real r = dot(d, tc);
    Real ds = r / sq(tc);
    if ((std::fabs(r) < stol) or (std::fabs(ds) < ttol))
      return true;
    s = clamp(s+ds, 0.0, 1.0);
  }
  return false;
}

bool AbstractCurve::pierce(const Vct3 &pn, Real dp, Real &s, Real stol) const
{
  Vct3 p, tg;
  const int nbs = 64;
  for (int i=0; i<nbs; ++i) {

    // local linearization of curve is p + ds*tg
    this->tgline(s, p, tg);
    Real r = dp - dot(pn, p);
    Real ds = r / dot(tg, pn);
    s = clamp(s+ds, 0.0, 1.0);

    if ((std::fabs(r) < stol*dp) or (std::fabs(ds) < stol))
      return true;
  }
  return false;
}

Real AbstractCurve::curvature(Real t) const
{
  assert(t >= 0);
  assert(t <= 1);

  // need first and second derivative
  Vct3 dc = derive(t, 1);
  Vct3 ddc = derive(t, 2);

  Real  x1(dc[0]),  y1(dc[1]),  z1(dc[2]);
  Real x2(ddc[0]), y2(ddc[1]), z2(ddc[2]);
  Real t1 = sq(z2*y1 - y2*z1);
  Real t2 = sq(x2*z1 - z2*x1);
  Real t3 = sq(y2*x1 - x2*y1);
  Real t4 = cb( sqrt(sq(x1) + sq(y1) + sq(z1)) );
  return sqrt(t1 + t2 + t3) / t4;
}

void AbstractCurve::initGrid(Vector &t) const
{
  // subclasses must implement something better!
  t = equi_pattern(32);
}

void AbstractCurve::tessellate(CgMesh &cgr) const
{
  Vector t;
  initGrid(t);

  const int n = t.size();
  PointList<3,float> pts(n);
  for (int i=0; i<n; ++i)
    pts[i] = Vct3f( eval(t[i]) );

  // append polyline
  cgr.clearMesh();
  cgr.appendLine(pts);
  cgr.expandStrips();
}

XmlElement AbstractCurve::toXml(bool) const
{
  XmlElement xe("AbstractCurve");
  return xe;
}

void AbstractCurve::fromXml(const XmlElement &) {}

int AbstractCurve::toIges(IgesFile &, int) const
{
  return 0;
}

bool AbstractCurve::fromIges(const IgesFile &, const IgesDirEntry &)
{
  return false;
}

void AbstractCurve::gridFromKnots(uint n, const Vector &kts, Vector &t,
                                  Real tstart, Real tend)
{
  // used to eliminate multiple knots
  const Real tol = 1e-4;
  almost_equal<Real> pred(tol);

  // eliminate duplicate values
  Vector k(kts); // knot vector is always sorted
  k.erase(std::unique(k.begin(), k.end(), pred), k.end());

  if (tstart == 0.0 and tend == 1.0) {

    interpolate_pattern(k, n, t);

  } else {

    assert(tstart >= 0.0);
    assert(tend <= 1.0);

    // locate tstart and tend in knot vector
    Vector::iterator pstart = std::lower_bound(k.begin(), k.end(), tstart);
    assert(pstart != k.end());
    if (pstart > k.begin() and *pstart < tstart)
      --pstart;

    Vector::iterator pend = std::lower_bound(k.begin(), k.end(), tend);

    // refine
    if ( std::distance(pstart,pend) > 1 ) {

      // sub-segment of knot vector spanning tstart-tend
      Vector ksub(pstart, pend);
      interpolate_pattern(ksub, n, t);

      // remap to [0,1] because calling parameter is in that domain
      for (uint i=0; i<n; ++i)
        t[i] = (t[i] - tstart) / (tend - tstart);

      if (t.front() <= tol)
        t.front() = 0.0;
      else
        t.insert(t.begin(), 0.0);
      if (t.back() >= 1.0-tol)
        t.back() = 1.0;
      else
        t.insert(t.end(), 1.0);

    } else {
      t = equi_pattern(n);
    }
  }
}

uint AbstractCurve::discretize(const DcMeshCritBase &mcrit, Vector &t) const
{
  uint nmin(4);
  if (t.empty()) {
    t = equi_pattern(nmin);
  } else {
    insert_once(t, 0.0);
    insert_once(t, 1.0);
  }

  Vector tin, tmp;
  PointList<3> pts, tng;
  do {

    tin.clear();
    const int np = t.size();
    pts.resize(np);
    tng.resize(np);
    for (int i=0; i<np; ++i)
      tgline(t[i], pts[i], tng[i]);

    for (int i=1; i<np; ++i) {
      if ( mcrit.splitEdge(pts[i-1], pts[i], tng[i-1], tng[i]) ) {
        Real tmid = 0.5*(t[i] + t[i-1]);
        tin.push_back(tmid);
        continue;
      }
    }

    if (not tin.empty()) {
      tmp.resize(t.size() + tin.size());
      std::merge(t.begin(), t.end(), tin.begin(), tin.end(), tmp.begin());

      // smooth point distribution a little
      const Real omega = 0.3;
      const int ntp = tmp.size();
      t.resize(ntp);
      t.front() = tmp.front();
      t.back() = tmp.back();
      for (int i=1; i<ntp-1; ++i)
        t[i] = (1.0-omega)*tmp[i] + 0.5*omega*(tmp[i-1] + tmp[i+1]);
    }

  } while (not tin.empty());

  return t.size();
}

AbstractCurvePtr AbstractCurve::createFromXml(const XmlElement & xe)
{
  if (xe.name() == "Curve") {
    Curve *cp = new Curve("Unknown");
    cp->fromXml(xe);
    return AbstractCurvePtr(cp);
  } else if (xe.name() == "OpenFrame") {
    OpenFrame *cp = new OpenFrame("Unknown");
    cp->fromXml(xe);
    return AbstractCurvePtr(cp);
  } else if (xe.name() == "Airfoil") {
    Airfoil *cp = new Airfoil("Unknown");
    cp->fromXml(xe);
    return AbstractCurvePtr(cp);
  } else if (xe.name() == "SymFrame") {
    SymFrame *cp = new SymFrame("Unknown");
    cp->fromXml(xe);
    return AbstractCurvePtr(cp);
  } else if (xe.name() == "EllipFrame") {
    EllipFrame *cp = new EllipFrame("Unknown");
    cp->fromXml(xe);
    return AbstractCurvePtr(cp);
  } else if (xe.name() == "EggFrame") {
    EggFrame *cp = new EggFrame("Unknown");
    cp->fromXml(xe);
    return AbstractCurvePtr(cp);
  } else if (xe.name() == "CompositeCurve") {
    CompositeCurve *cp = new CompositeCurve("Unknown");
    cp->fromXml(xe);
    return AbstractCurvePtr(cp);
  } else if (xe.name() == "CircularArc") {
    CircularArc *cp = new CircularArc("Unknown");
    cp->fromXml(xe);
    return AbstractCurvePtr(cp);
  } else if (xe.name() == "PolySplineCurve") {
    PolySplineCurve *cp = new PolySplineCurve();
    cp->fromXml(xe);
    return AbstractCurvePtr(cp);
  } else if (xe.name() == "LineCurve") {
    LineCurve *cp = new LineCurve();
    cp->fromXml(xe);
    return AbstractCurvePtr(cp);
  } else if (xe.name() == "RationalSplineCurve") {
    RationalSplineCurve *cp = new RationalSplineCurve();
    cp->fromXml(xe);
    return AbstractCurvePtr(cp);
  } else if (xe.name() == "MappedCurve") {
    MappedCurve *cp = new MappedCurve();
    cp->fromXml(xe);
    return AbstractCurvePtr(cp);
  } else
    return AbstractCurvePtr();
}

AbstractCurvePtr AbstractCurve::createFromIges(const IgesFile & file,
                                               const IgesDirEntry & entry)
{
  AbstractCurvePtr acp;

  // spline curves
  if (entry.etype == 126) {

    IgesSplineCurve ispl;
    if (file.createEntity(entry, ispl)) {
      if (ispl.polynomial) {
        PolySplineCurve *psp = new PolySplineCurve;
        if (psp->fromIges(file, entry))
          acp = AbstractCurvePtr(psp);
      } else {  // rational
        RationalSplineCurve *rsp = new RationalSplineCurve;
        if (rsp->fromIges(file, entry))
          acp = AbstractCurvePtr(rsp);
      }
    }

  } else if (entry.etype == 100) {

    CircularArc *ccp = new CircularArc;
    if (ccp->fromIges(file, entry))
      acp = AbstractCurvePtr(ccp);

  } else if (entry.etype == 102) {

    CompositeCurve *ccp = new CompositeCurve;
    if (ccp->fromIges(file, entry))
      acp = AbstractCurvePtr(ccp);

  } else if (entry.etype == 110) {

    LineCurve *ccp = new LineCurve;
    if (ccp->fromIges(file, entry))
      acp = AbstractCurvePtr(ccp);

  } else {
    dbprint("AbstractCurve cannot create entity type ", entry.etype);
  }

//  if (acp and acp->name().empty()) {
//    std::string s = strip( entry.label() );
//    if (not s.empty())
//      acp->rename(s);
//  }

  return acp;
}

void AbstractCurve::setIgesName(const IgesFile & file,const IgesEntity & e)
{
  IgesDirEntry entry;
  IgesEntityPtr ep;
  IgesNameProperty e406;
  const int np = e.nPropRef();

  // use 8-char label if no name property defined
  rename( strip(e.label()) );

  // look for name property
  for (int i=0; i<np; ++i) {
    file.dirEntry( e.propRef(i), entry );
    if (entry.etype == 406) {
      ep = file.createEntity(entry);
      if (IgesEntity::as(ep, e406))
        rename( e406.str() );
    }
  }

  // if name is still empty, use entity name
  if (name().empty()) {
    rename( str(e.pindex()) + "P" );
  }
}

void AbstractCurve::setIgesTransform(const IgesFile & file,
                                     const IgesDirEntry & entry)
{
  int tfi = entry.trafm;
  if (tfi == 0)
    return;

  // fetch transformation entry
  IgesTrafoMatrix itf;
  if (file.createEntity(tfi, itf)) {
    Mtx44 tfm;
    itf.toMatrix(tfm);
    setTrafoMatrix(tfm);
    apply();
  }
}

uint AbstractCurve::arclenParamet(const AbstractCurveArray & cpa, Vector & vp)
{
  const int nc(cpa.size());
  if (nc == 0)
    return 0;

  // evaluate curves at nt points around the circumference
  const int nt(8);
  Real dt = 1.0/nt;
  PointGrid<3> pts(nt,nc);
  for (int j=0; j<nc; ++j) {
    const AbstractCurve & cv(*cpa[j]);
    for (int i=0; i<nt; ++i) {
      Real t = 0.5*dt + i*dt;
      pts(i,j) = cv.eval(t);
    }
  }

  // compute a mean parametrization
  uint nid(0);
  vp.resize(nc);
  vp[0] = 0.0;
  for (int j=1; j<nc; ++j) {
    vp[j] = vp[j-1];
    for (int i=0; i<nt; ++i) {
      vp[j] += norm(pts(i,j) - pts(i,j-1));
    }
    if (vp[j] == vp[j-1])
      ++nid;
  }

  // normalize to 0..1
  vp -= vp.front();
  vp /= vp.back();

  // strange, sometimes vp.back() ends up as 0.99998
  vp.front() = 0.0;
  vp.back() = 1.0;

  return nid;
}

/*
typedef std::pair<Vct3, Vct3> PointPair;
typedef std::vector<PointPair> PairArray;

enum Joining { HT=0, TH=1, HH=2, TT=3 };

static int ppdistance(const PairArray &p, uint a, uint b, Real d[])
{
  int imin = HT;
  d[HT] = sq(p[a].first - p[b].second);
  d[TH] = sq(p[a].second - p[b].first);
  if (d[TH] < d[imin])
    imin = TH;
  d[HH] = sq(p[a].first - p[b].first);
  if (d[HH] < d[imin])
    imin = HH;
  d[TT] = sq(p[a].second - p[b].second);
  if (d[TT] < d[imin])
    imin = TT;
  return imin;
}

static AbstractCurvePtr reverse_curve(AbstractCurvePtr acp)
{
  return boost::make_shared<MappedCurve>(acp, -1.0, 1.0);
}

AbstractCurvePtr AbstractCurve::joinCurves(AbstractCurveArray &crv)
{
  const size_t nc = crv.size();
  if (nc < 2)
    return AbstractCurvePtr();

  PairArray pts(nc);
  Indices headTail(2*nc, NotFound);
  for (size_t i=0; i<nc; ++i)
    pts[i] = std::make_pair( crv[i]->eval(0.0),
                             crv[i]->eval(1.0) );


  for (size_t i=0; i<nc; ++i) {
    for (size_t j=i+1; j<nc; ++j) {

    }
  }

  AbstractCurveArray sgm;

  return AbstractCurvePtr(),
}
*/

