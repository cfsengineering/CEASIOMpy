
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
 #include "topoedge.h"
#include "topoface.h"
#include "topology.h"
#include "topovertex.h"
#include "abstractuvcurve.h"
#include "uvpolyline.h"
#include <genua/pattern.h>
#include <genua/dbprint.h>
#include <genua/mxmesh.h>
#include <genua/smallqr.h>
#include <genua/ioglue.h>

using std::string;

TopoEdge::TopoEdge(const Topology &topo, uint iface, uint a, uint b)
  : m_orig(Specified), m_bInjected(false)
{
  assign(a, b);
  m_faces.push_back( iface );
  m_pcv.push_back( TopoEdge::boundaryCurve(topo, iface, a, b) );
}

Vct3 TopoEdge::eval(uint lfi, Real t) const
{
  assert(m_pcv[lfi]);
  return m_pcv[lfi]->eval(t);
}

AbstractUvCurvePtr TopoEdge::boundaryCurve(const Topology &topo,
                                           uint iface, uint a, uint b)
{
  // locate local indices
  uint ka = topo.vertex(a).findFace(iface);
  assert(ka != NotFound);
  uint kb = topo.vertex(b).findFace(iface);
  assert(kb != NotFound);

  UvPolylinePtr pcv;
  pcv = boost::make_shared<UvPolyline>(topo.face(iface).surface());
  pcv->interpolate( topo.vertex(a).uvpos(ka),
                    topo.vertex(b).uvpos(kb) );
  return pcv;
}

Vct2 TopoEdge::uvpoint(uint kface, uint ipoint) const
{
  assert(kface < m_pcv.size() and m_pcv[kface] != nullptr);
  return m_pcv[kface]->uveval(m_tp[ipoint]);
}

Vct3 TopoEdge::point(uint ipoint) const
{
  Vct3 pt;
  const int nc = m_pcv.size();
  assert(nc > 0);
  if (nc == 1) {
    return m_pcv[0]->eval(m_tp[ipoint]);
  } else {
    for (int i=0; i<nc; ++i)
      pt += m_pcv[i]->eval(m_tp[ipoint]);
    pt /= Real(nc);
    return pt;
  }
}

int TopoEdge::compare(const Topology &topo, const TopoEdge &e, Real tol) const
{
  const TopoVertex & vas = topo.vertex( source() );
  const TopoVertex & vat = topo.vertex( target() );
  const TopoVertex & vbs = topo.vertex( e.source() );
  const TopoVertex & vbt = topo.vertex( e.target() );

  // check whether source and target of the same edge are close to each
  // other, in which case distance measurements cannot be used
  bool adegen = vas.closeTo(vat, tol);
  bool bdegen = vbs.closeTo(vbt, tol);

  if ( not (adegen or bdegen) ) {

    bool ss = vas.closeTo(vbs, tol);
    bool tt = vat.closeTo(vbt, tol);
    if (ss and tt)
      return TopoEdge::ForwardFit;
    else if (ss or tt)
      return TopoEdge::ForwardOverlap;

    bool st = vas.closeTo(vbt, tol);
    bool ts = vat.closeTo(vbs, tol);
    if (st and ts)
      return TopoEdge::ReverseFit;
    else if (st or ts)
      return TopoEdge::ReverseOverlap;

  } else if (adegen and bdegen) {

    dbprint("Both edges are degenerate.");

    // both edges are degenerate in the sense that they start and end
    // at the same 3D point - if this one point per edge is not close to
    // the one point of the other edge, they cannot possibly match.
    bool ss = vas.closeTo(vbs, tol);
    if (not ss) {
      dbprint("Source of edge a is far from source of edge b");
      return TopoEdge::NoMatch;
    }

    // |tangent_a dot tangent_b| must be larger than limit for the
    // two edges to be considered candidates for matching
    const Real mincphi = std::cos( rad(0.5) );

    // compute tangents
    Vct3 asp, asd, bsp, bsd;
    this->curve(0)->tgline(0.0, asp, asd);
    e.curve(0)->tgline(0.0, bsp, bsd);

    Vct3 atp, atd, btp, btd;
    this->curve(0)->tgline(1.0, atp, atd);
    e.curve(0)->tgline(1.0, btp, btd);

    Real css = dot(asd, bsd) / std::sqrt(sq(asd) * sq(bsd));
    Real ctt = dot(atd, btd) / std::sqrt(sq(atd) * sq(btd));

    dbprint("ss Cosine of tangents:",css);
    dbprint("tt Cosine of tangents:",ctt);
    if (css > mincphi and ctt > mincphi)
      return TopoEdge::ForwardFit;

    Real cst = dot(asd, btd) / std::sqrt(sq(asd) * sq(btd));
    Real cts = dot(atd, bsd) / std::sqrt(sq(atd) * sq(bsd));

    dbprint("st Cosine of tangents:",cst);
    dbprint("ts Cosine of tangents:",cts);
    if (cst < -mincphi and cts < -mincphi)
      return TopoEdge::ReverseFit;
  }

  return TopoEdge::NoMatch;
}

void TopoEdge::detach()
{
  m_pcv.clear();
  m_tp.clear();
  m_ftp.clear();
  m_faces.clear();
}

int TopoEdge::connects(uint gfi, const Vct2 &q1, const Vct2 &q2, Real tol) const
{
  const int nf = nfaces();
  for (int j=0; j<nf; ++j) {

    if (m_faces[j] != gfi)
      continue;

    Vct2 qs = m_pcv[j]->uveval(0.0);
    Vct2 qt = m_pcv[j]->uveval(1.0);

    Real stol = sq(tol);
    if ( (sq(qs-q1) < stol) and (sq(qt-q2) < stol) )
      return ForwardFit;
    else if ( (sq(qs-q2) < stol) and (sq(qt-q1) < stol) )
      return ReverseFit;
  }

  return NoMatch;
}

void TopoEdge::split(Real t, uint v, TopoEdge &other)
{
  // adapt vertex indices
  other.m_vix[0] = v;
  other.m_vix[1] = m_vix[1];
  m_vix[1] = v;

  const int nf = m_pcv.size();
  other.m_faces = m_faces;
  other.m_pcv.resize(nf);
  for (int i=0; i<nf; ++i) {
    AbstractUvCurvePair pair = m_pcv[i]->split(t);
    other.m_pcv[i] = pair.second;
    m_pcv[i] = pair.first;
  }

  // split discretization
  if (not m_tp.empty()) {
    Vector::iterator pos = std::lower_bound(m_tp.begin(), m_tp.end(), t);
    other.m_tp.clear();
    if (pos == m_tp.end() or *pos != t)
      other.m_tp.push_back(t);
    other.m_tp.insert(other.m_tp.end(), pos, m_tp.end());
    Vector tmp;
    tmp.insert(tmp.end(), m_tp.begin(), pos);
    tmp.push_back(t);
    m_tp.swap(tmp);
  }

  other.edgeOrigin( m_orig );
}

void TopoEdge::enforcePoint(Real t)
{
  insert_once(m_ftp, t);
  if (not m_tp.empty())
    insert_once(m_tp, t);
}

const Vector & TopoEdge::discretize(const Topology &topo)
{
  m_bInjected = false;
  m_tp = m_ftp;

  const int nf = nfaces();
  dbprint("Meshing edge with",nf,"adjacent faces.");
  for (int i=0; i<nf; ++i) {
    const TopoFace &nbf( topo.face(m_faces[i]) );
    assert(nbf.criterion() != nullptr);
    m_pcv[i]->discretize( *(nbf.criterion()), m_tp );
    dbprint("Side",i,"points:",m_tp.size());
  }

  return m_tp;
}

const Vector & TopoEdge::discretize(const DcMeshCritBase &mcrit)
{
  m_bInjected = false;
  m_tp = m_ftp;
  if (not m_pcv[0])
    return m_tp;

  m_pcv[0]->discretize(mcrit, m_tp);
  return m_tp;
}

bool TopoEdge::injectPoint(uint kf, const Vct2 &p, Real tol)
{
  assert(kf < nfaces());
  const int ntp = m_tp.size();
  if (ntp < 2)
    return false;

  //  const Real sqtol = sq(tol);
  //  Real tbest(-1.0), sqdmin(huge);
  //  for (int i=1; i<ntp; ++i) {
  //    Vct2 p1 = uvpoint(kf, i-1);
  //    Vct2 p2 = uvpoint(kf, i);
  //    Vct2 edir(p2 - p1);
  //    Real st = dot(p - p1, edir) / sq(edir);
  //    if (st < 0 or st > 1)
  //      continue;
  //    Vct2 foot = (1-st)*p1 + st*p2;
  //    Real sqd = sq(p - foot);
  //    if (sqd > sqtol)
  //      continue;
  //    if (sqd < sqdmin) {
  //      tbest = (1-st)*m_tp[i-1] + st*m_tp[i];
  //      sqdmin = sqd;
  //    }
  //  }

  // determine the parameter tbest at which p is closest
  // to any of the segments currently in edge
  Real tbest(-1.0), sqdmin(huge);
  for (int i=1; i<ntp; ++i) {
    Vct2 p1 = uvpoint(kf, i-1);
    Vct2 p2 = uvpoint(kf, i);
    Vct2 edir(p2 - p1);
    Real st = clamp( dot(p - p1, edir) / sq(edir), 0.0, 1.0);
    Vct2 foot = (1-st)*p1 + st*p2;
    Real sqd = sq(p - foot);
    if (sqd < sqdmin) {
      tbest = (1-st)*m_tp[i-1] + st*m_tp[i];
      sqdmin = sqd;
    }
  }

  if (sqdmin > sq(tol)) {
    return false;
  }

  m_bInjected = true;
  insert_once(m_tp, tbest);
  insert_once(m_ftp, tbest);
  dbprint("Injected ",tbest," at ",p);
  return true;
}

void TopoEdge::injectIntersections(const Topology &topo, TopoEdge &e)
{
  // parameter space tolerance
  const Real tol = gmepsilon;

  const int nf = nfaces();
  const int nfe = e.nfaces();

  // parameter values to inject into *this and e
  Vector tinj, tenj;

  PointList2d pi, pj;
  for (int i=0; i<nf; ++i) {
    assert(m_pcv[i] != nullptr);
    const size_t np = m_tp.size();
    const AbstractUvCurve &ci( *m_pcv[i] );
    if (pi.size() != np)
      pi.resize(np);
    std::transform( m_tp.begin(), m_tp.end(), pi.begin(),
                    [&](Real t){ return ci.uveval(t); } );
    for (int j=0; j<nfe; ++j) {
      if (face(i) != e.face(j))
        continue;

      assert(e.m_pcv[j] != nullptr);
      const AbstractUvCurve &cj( *e.m_pcv[j] );
      const size_t npe = e.m_tp.size();
      if (pj.size() != npe)
        pj.resize(npe);
      std::transform( e.m_tp.begin(), e.m_tp.end(), pj.begin(),
                      [&](Real t){ return cj.uveval(t); } );

      // check segments for intersections in (u,v) space of this face
      Mtx22 A;
      Vct2 r;
      for (size_t ki=1; ki<np; ++ki) {
        const Vct2 &a0( pi[ki-1] );
        const Vct2 &a1( pi[ki] );
        for (size_t kj=1; kj<npe; ++kj) {
          const Vct2 &b0( pj[kj-1] );
          const Vct2 &b1( pj[kj] );
          for (int k=0; k<2; ++k) {
            A(k,0) = a1[k] - a0[k];
            A(k,1) = b0[k] - b1[k];
            r[k] = b0[k] - a0[k];
          }

          bool inv = qrlls<2,2>(A.pointer(), r.pointer());
          if (not inv)
            continue;

          // r[0] is parameter on this curve, r[1] on e, if one of
          // them is out of [0,1], then there is no intersection
          if ( r[0] < -tol or r[0] > 1+tol or r[1] < -tol or r[1] > 1+tol )
            continue;

          Real t = (1-r[0])*m_tp[ki-1] + r[0]*m_tp[ki];
          Real te = (1-r[1])*e.m_tp[kj-1] + r[1]*e.m_tp[kj];

          // now that we have an intersection, inject points into curves
          tinj.push_back( clamp(t, 0.0, 1.0) );
          tenj.push_back( clamp(te, 0.0, 1.0) );
          dbprint("Injected ",tinj.back()," and ",tenj.back());
        }
      }

      // processed one curve pair on the same face
      this->inject(topo, i, tinj);
      e.inject(topo, j, tenj);

      tinj.clear();
      tenj.clear();
    }
  }
}

void TopoEdge::toMx(MxMesh &mx) const
{
  const int np = m_tp.size();
  if (np == 0 or (not m_pcv[0]))
    return;

  PointList<3> pts(np);
  for (int i=0; i<np; ++i)
    pts[i] = point(i);
  uint isec = mx.appendSection(pts);

  std::stringstream ss;
  ss << "TopoEdge " << source() << " -> " << target();
  mx.section(isec).rename(ss.str());
}

void TopoEdge::print(uint k, std::ostream &os) const
{
  bool unconnected = m_faces.empty();
  if (unconnected)
    os << "[ ";
  os << "TopoEdge " << k << ": " << source() << " -> " << target();
  if (not m_tp.empty())
    os << ", (" << m_tp.size() << " vertices)";
  if (unconnected)
    os << "]";
  os << endl;
  const int nf = nfaces();
  for (int i=0; i<nf; ++i) {
    os << " - Face " << m_faces[i] << " curve " << m_pcv[i].get();
    os << endl;
  }
}

void TopoEdge::tabulate(const string &fn) const
{
  ofstream os(asPath(fn).c_str());
  const int nf = nfaces();
  const int np = m_tp.size();
  for (int i=0;i < np; ++i) {
    os << m_tp[i];
    for (int kf=0; kf<nf; ++kf)
      os << " " << m_pcv[kf]->uveval(m_tp[i])
         << " " << m_pcv[kf]->eval(m_tp[i]);
    os << endl;
  }
}

static inline Vct2 segment_intersect(const Vct2 &as, const Vct2 &at,
                                     const Vct2 &bs, const Vct2 &bt)
{
  SMatrix<2,2> A;
  SVector<2> x;
  for (int k=0; k<2; ++k) {
    A(k,0) = as[k] - at[k];
    A(k,1) = bt[k] - bs[k];
    x[k] = as[k] - bs[k];
  }
  qrlls<2,2>(A.pointer(), x.pointer());
  return x;
}

bool TopoEdge::intersects(uint fix, const TopoEdge &ea,
                          const TopoEdge &eb, Vct2 &t)
{
  uint ka = ea.findFace(fix);
  if (ka == NotFound)
    return false;
  uint kb = eb.findFace(fix);
  if (kb == NotFound)
    return false;

  const int npa = ea.npoints();
  const int npb = eb.npoints();
  assert(npa > 0 and npb > 0);
  PointList<2> qa(npa), qb(npb);
  Vct2 alo, ahi, blo, bhi;
  alo = blo = std::numeric_limits<Real>::max();
  ahi = bhi = -alo;
  for (int i=0; i<npa; ++i) {
    qa[i] = ea.m_pcv[ka]->uveval(ea.m_tp[i]);
    for (int k=0; k<2; ++k) {
      alo[k] = std::min(alo[k], qa[i][k]);
      ahi[k] = std::min(ahi[k], qa[i][k]);
    }
  }
  for (int i=0; i<npb; ++i) {
    qb[i] = eb.m_pcv[kb]->uveval(eb.m_tp[i]);
    for (int k=0; k<2; ++k) {
      blo[k] = std::min(blo[k], qb[i][k]);
      bhi[k] = std::min(bhi[k], qb[i][k]);
    }
  }

  //  // check whether bounds overlap
  //  for (int k=0; k<2; ++k) {
  //    if (alo[k] > bhi[k])
  //      return false;
  //    if (blo[k] > ahi[k])
  //      return false;
  //  }

  // plain test for intersections
  for (int i=1; i<npa; ++i) {
    const Vct2 & as( qa[i-1] );
    const Vct2 & at( qa[i] );
    alo = Vct2( std::min(as[0], at[0]),  std::min(as[1], at[1]) );
    ahi = Vct2( std::max(as[0], at[0]),  std::max(as[1], at[1]) );
    for (int j=1; j<npb; ++j) {
      const Vct2 & bs( qb[j-1] );
      const Vct2 & bt( qb[j] );
      blo = Vct2( std::min(bs[0], bt[0]),  std::min(bs[1], bt[1]) );
      bhi = Vct2( std::max(bs[0], bt[0]),  std::max(bs[1], bt[1]) );

      //      // check segment bounding boxes first
      //      if ( (blo[0] > ahi[0]) or (blo[1] > ahi[1]) )
      //        continue;
      //      else if ( (alo[0] > bhi[0]) or (alo[1] > bhi[1]) )
      //        continue;

      // compute intersection in (u,v) space
      Vct2 ct = segment_intersect(as, at, bs, bt);
      if ( ct[0] < 0.0 or ct[0] > 1.0 )
        continue;
      if ( ct[1] < 0.0 or ct[1] > 1.0 )
        continue;

      // determine curve parameters
      t[0] = (1.0 - ct[0])*ea.m_tp[i-1] + ct[0]*ea.m_tp[i];
      t[1] = (1.0 - ct[1])*eb.m_tp[j-1] + ct[1]*eb.m_tp[j];
      return true;
    }
  }

  return false;
}

void TopoEdge::inject(const Topology &topo, uint iface, const Vector &ti)
{
  if (ti.empty())
    return;

  // merge tolerance of the appropriate face
  const Real sqtol = topo.face( m_faces[iface] ).sqMergeTolerance();
  const Real uvtol = 1e-4;

  // two curve-parameter points (a,b) are considered the same if
  // |diff(C,t) * (a-b)|^2 < tol at t = (a+b)/2
  const AbstractCurve &uvc( *m_pcv[iface] );
  auto fzy = [&](Real a, Real b) {
    if (std::fabs(a-b) < uvtol)
      return true;
    Real tmid = 0.5*(a + b);
    return sq( uvc.derive(tmid, 1)*(a-b) ) < sqtol;
  };

  // inject all the identified intersection points and clean up
  m_ftp.insert(m_ftp.end(), ti.begin(), ti.end());
  std::sort(m_ftp.begin(), m_ftp.end());
  m_ftp.erase( std::unique(m_ftp.begin(), m_ftp.end(), fzy), m_ftp.end() );

  m_tp.insert(m_tp.end(), m_ftp.begin(), m_ftp.end());
  std::sort(m_tp.begin(), m_tp.end());
  m_tp.erase( std::unique(m_tp.begin(), m_tp.end(), fzy), m_tp.end() );
  m_bInjected = true;
}
