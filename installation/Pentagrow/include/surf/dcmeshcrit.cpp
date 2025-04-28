
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
 
#include "dcmeshcrit.h"
#include "surface.h"
#include "sides.h"
#include "abstractuvcurve.h"
#include <genua/xmlelement.h>
#include <genua/dbprint.h>
#include <iostream>

using namespace std;

// ------------------------- DcMeshCritBase -----------------------------------

void DcMeshCritBase::assign(const Surface *srf,
                            const PointList<2> *uv, const PointList<2> *st,
                            const PointList<3> *xy, const PointList<3> *nm)
{
  psf = srf;
  ppuv = uv;
  ppst = st;
  ppxy = xy;
  ppnm = nm;
}

bool DcMeshCritBase::splitEdge(const AbstractUvCurve &cuv,
                               Real ts, Real tt) const
{
  Vct3 ps, pt, tgs, tgt;
  cuv.tgline(ts, ps, tgs);
  cuv.tgline(tt, pt, tgt);
  return splitEdge(ps, pt, tgs, tgt);
}

//static inline bool has_edge(const uint tri[], uint a, uint b)
//{
//  int hit(0);
//  for (int k=0; k<3; ++k) {
//    if (tri[k] == a or tri[k] == b)
//      ++hit;
//  }
//  return (hit == 2);
//}

int DcMeshCritBase::checkGrowthRatio(const uint va[], const uint vb[]) const
{
  Real sqa = sq(cross( pxy(va[1]) - pxy(va[0]), pxy(va[2]) - pxy(va[0]) ));
  Real sqb = sq(cross( pxy(vb[1]) - pxy(vb[0]), pxy(vb[2]) - pxy(vb[0]) ));
  if ( sqa <= sqb*maxGrowth )
    return NoSplit;

  // ok, need to split, but how?
  // check whether one edge is much longer than
  const uint a(va[0]), b(va[1]), c(va[2]);
  const Real len[3] = { sq(pxy(a) - pxy(b)),
                        sq(pxy(b) - pxy(c)),
                        sq(pxy(c) - pxy(a)) };

  int s = NoSplit;
  Real lmax(0.0), lmin = std::numeric_limits<Real>::max();
  for (int k=0; k<3; ++k) {
    // never split edge shared by both triangles because that cannot
    // improve growth ratio
    // if ( has_edge(vb, va[k], va[(k+1)%3]) )
    //  continue;
    if (len[k] > lmax) {
      lmax = len[k];
      s = SplitEdge1 + k;
    }
    lmin = std::min(lmin, len[k]);
  }

  if (lmax > lmin*maxGrowth)
    return s;
  else
    return InsertTriCenter;
}

// ------------------------- DcMeshCrit ---------------------------------------

DcMeshCrit::DcMeshCrit() : DcMeshCritBase()
{
  const Real lmax = std::numeric_limits<Real>::max();
  smaxLenXY = lmax;
  sminLenXY = 0.0;
  smaxLenUV = lmax;
  sminLenUV = 0.0;
  pmaxU = lmax;
  minCosPhi = -1.0;
  maxCosBeta = 1.0;
  minCosBeta = -1.0;
  maxGrowth = NotDouble;
  std::fill( uBiasFactor, uBiasFactor+3, 1.0 );
  std::fill( vBiasFactor, vBiasFactor+3, 1.0 );
  std::fill( uBiasWidth, uBiasWidth+3, 0.25 );
  std::fill( vBiasWidth, vBiasWidth+3, 0.25 );
  checkOrthogonal = false;
}

bool DcMeshCrit::splitEdge(const AbstractUvCurve &cuv, Real ts, Real tt) const
{
  // compute tangent of curve in surfaces (u,v) plane
  Vct2 uvs, uvt, ds, dt;

  cuv.uvtgline(ts, uvs, ds);
  cuv.uvtgline(tt, uvt, dt);

  Vct2 qmid(0.5*(uvs + uvt));
  Real bf = sq(biasReduction(qmid));
  Real sql = sq(uvt - uvs);
  if ( sql > smaxLenUV*bf )
    return true;
  else if ( sql < sminLenUV*bf )
    return false;

  // check if projected distance in u-direction is too long
  if ( sq(uvt[0] - uvs[0]) > sq(pmaxU)*bf )
    return true;

  // evaluate surface metric at edge midpoint
  Vct3 S, Su, Sv;
  const Surface & srf( *(cuv.surface()) );
  srf.plane(qmid[0], qmid[1], S, Su, Sv);

  // check whether the length of the edge in parameter plane corresponds
  // to a larger than permissible length in the spatial domain
  Vct2 qed(uvt - uvs);
  if (sq(Su*qed[0] + Sv*qed[1]) > smaxLenXY*bf) {
    //dbprint("Edge split: Su*qed[0] + Sv*qed[1]");
    return true;
  }

  // check length criterion in the direction orthogonal to edge
  if (checkOrthogonal) {
    if (sq(Su*qed[1] - Sv*qed[0]) > smaxLenXY*bf) {
      //dbprint("Edge split: Su*qed[1] - Sv*qed[0]");
      return true;
    }
  }

  if (minCosPhi > -1.0) {

    // determine normalized cross-edge direction
    ds = Vct2( -ds[1], ds[0] );
    dt = Vct2( -dt[1], dt[0] );
    Vct2 tx = (ds + dt).normalized();

    // factor to ensure that |pr - pl| = sqrt(3)*edge_len
    Real slt = sq(Su*tx[0] + Sv*tx[1]);  // sqlen of unit step across edge
    Real sll = sq(Su*tx[1] - Sv*tx[0]);  // sqlen of unit step along edge
    Real tff = sll / slt;

    // compute (u,v) points to the left and right of edge
    Real dx = std::sqrt(3.0* sql * tff);
    Vct2 ql = qmid + dx*tx;
    Vct2 qr = qmid - dx*tx;
    ql = Vct2( clamp(ql[0], 0.0, 1.0), clamp(ql[1], 0.0, 1.0) );
    qr = Vct2( clamp(qr[0], 0.0, 1.0), clamp(qr[1], 0.0, 1.0) );

    // determine difference in surface normal direction between left and right
    Real cphi = cosarg( srf.normal(ql[0], ql[1]), srf.normal(qr[0], qr[1]) );
    if (cphi < minCosPhi) {
      // dbprint("Edge split: transverse normal angle.");
      return true;
    }
  }

  Vct3 ps, pt, tgs, tgt;
  cuv.tgline(ts, ps, tgs);
  cuv.tgline(tt, pt, tgt);
  return this->splitEdge(ps, pt, tgs, tgt, bf);
}

bool DcMeshCrit::splitEdge(const Vct3 &ps, const Vct3 &pt,
                           const Vct3 &tgs, const Vct3 &tgt, Real bf) const
{
  Vct3 edi = pt - ps;
  Real sql = sq(edi);
  if ( sql > smaxLenXY*bf )
    return true;
  else if ( sql < sminLenXY*bf )
    return false;

  //dbprint("Edge bias ",bf,sql);

  Real ltg = sq(tgs);
  if ((ltg < 0.0) or (minCosPhi > -1.0)) {

    Real cphi = cosarg(tgs, tgt);
    if (cphi < minCosPhi)
      return true;

    cphi = cosarg(edi, tgs);
    if (cphi < minCosPhi)
      return true;

    cphi = cosarg(edi, tgt);
    if (cphi < minCosPhi)
      return true;

  }

  return false;
}

bool DcMeshCrit::splitEdge(uint s, uint t) const
{
  Real bf = sq(biasReduction(0.5*(puv(s) + puv(t))));
  if ( sq(puv(s) - puv(t)) > smaxLenUV*bf )
    return true;
  else if ( sq(pxy(s) - pxy(t)) > smaxLenXY*bf )
    return true;
  else if ( cosarg(pnm(s), pnm(t)) < minCosPhi )
    return true;
  return false;
}

int DcMeshCrit::splitFace(uint a, uint b, uint c) const
{
  const Real tooLarge = std::numeric_limits<Real>::max();
  Real len[3], lmax(0.0), lmin(tooLarge);
  int s = NoSplit;

  // bias
  Vct2 qmid = (puv(a) + puv(b) + puv(c)) / 3.0;
  Real bf = sq(biasReduction( qmid ));

  // maximum edge length criterion (uv)
  if (smaxLenUV < tooLarge) {
    len[0] = sq(puv(a) - puv(b));
    len[1] = sq(puv(b) - puv(c));
    len[2] = sq(puv(c) - puv(a));
    for (int k=0; k<3; ++k) {
      if (len[k] > lmax) {
        lmax = len[k];
        s = SplitEdge1 + k;
      }
    }
    if (lmax > smaxLenUV*bf)
      return s;
  }

  // don't split if triangle is already too small in (u,v) space
  if (lmax < sminLenUV*bf)
    return TooSmall;

  // check projected length in u
  if ( pmaxU < tooLarge ) {
    len[0] = sq(puv(a)[0] - puv(b)[0]);
    len[1] = sq(puv(b)[0] - puv(c)[0]);
    len[2] = sq(puv(c)[0] - puv(a)[0]);
    for (int k=0; k<3; ++k) {
      if (len[k] > lmax) {
        lmax = len[k];
        s = SplitEdge1 + k;
      }
    }
    if (lmax > sq(pmaxU)*bf)
      return s;
  }

  // maximum edge length criterion (xyz)
  len[0] = sq(pxy(a) - pxy(b));
  len[1] = sq(pxy(b) - pxy(c));
  len[2] = sq(pxy(c) - pxy(a));

  lmax = 0.0;
  for (int k=0; k<3; ++k) {
    if (len[k] > lmax) {
      lmax = len[k];
      s = SplitEdge1 + k;
    }
    lmin = std::min(lmin, len[k]);
  }

  // when even the longest edge is too short, don't even consider splitting
  if (lmax < sminLenXY*bf)
    return TooSmall;

  // keep split flag for longest edge around
  const int slmax = s;
  // const int ccslm = InsertCircumCenterE1 + s - int(SplitEdge1);

  // flag indicating that the triangle is obtuse - one large,
  // two small internal angles
  const Real ccr = ccRadius(len);
  bool obtuse = (2*ccr > lmax);
  bool pointed = (lmax > 8*lmin);
  bool irregular = obtuse or pointed;

  if (lmax > smaxLenXY*bf)
    return irregular ? s : InsertTriCenter;

  // maximum normal angle criterion
  if (minCosPhi > -1.0) {
    int sc = slmax;
    Real cphi[3], mincphi(1.0);
    cphi[0] = cosarg( pnm(a), pnm(b) );
    cphi[1] = cosarg( pnm(b), pnm(c) );
    cphi[2] = cosarg( pnm(c), pnm(a) );
    for (int k=0; k<3; ++k) {
      if (cphi[k] < mincphi) {
        mincphi = cphi[k];
        if (mincphi < minCosPhi and len[k] > sminLenXY)
          sc = SplitEdge1 + k;
      }
    }
    if (mincphi < minCosPhi)
      return irregular ? sc : InsertTriCenter;

    // check normal criterion between triangle and surface
    sc = slmax;
    Vct3 fn = cross(pxy(b) - pxy(a), pxy(c) - pxy(a));
    cphi[0] = cosarg( pnm(a), fn );
    cphi[1] = cosarg( pnm(b), fn );
    cphi[2] = cosarg( pnm(c), fn );
    for (int k=0; k<3; ++k) {
      if (cphi[k] < mincphi) {
        mincphi = cphi[k];
        if (mincphi < minCosPhi and len[k] > sminLenXY)
          sc = SplitEdge1 + (k + 1)%3;  // select opposed edge for split
      }
    }
    if (mincphi < minCosPhi)
      return irregular ? sc : InsertTriCenter;
  }

  // maximum apex angle criterion
  if (minCosBeta > -0.999 or maxCosBeta < 0.999) {
    Vct3 edv[3];
    edv[0] = ( pxy(b) - pxy(a) );
    edv[1] = ( pxy(c) - pxy(b) );
    edv[2] = ( pxy(a) - pxy(c) );
    Real mincbeta(1.0), maxcbeta(-1.0);
    const int ea[3] = {2, 0, 1};
    const int eb[3] = {0, 1, 2};
    for (int k=0; k<3; ++k) {
      Real cbeta = cosarg( -edv[ea[k]], edv[eb[k]] );
      mincbeta = std::min(mincbeta, cbeta);
      maxcbeta = std::max(maxcbeta, cbeta);
    }

    // always split longest edge
    if ((mincbeta < minCosBeta) or (maxcbeta > maxCosBeta))
      return slmax;
  }

  return NoSplit;
}

void DcMeshCrit::importLegacy(const XmlElement &xe)
{
  smaxLenXY = sq(xe.attr2float("maxlen", sqrt(smaxLenXY)));
  sminLenXY  = sq(xe.attr2float("minlen", sqrt(sminLenXY)));

  Real maxPhi = std::acos(minCosPhi);
  minCosPhi = std::cos( rad(xe.attr2float("maxphi", deg(maxPhi))) );
  nMaxNodeCount = xe.attr2int("nvmax", std::numeric_limits<int>::max());

  // translate strech ratio into minimum permitted beta angle
  Real stretch = std::numeric_limits<Real>::max();
  if (maxCosBeta < 1)
    stretch = 1.0 / std::tan( std::acos(maxCosBeta) );
  stretch = xe.attr2float("maxstretch", stretch);
  if (stretch < std::numeric_limits<Real>::max())
    maxCosBeta = std::cos( std::atan(1.0 / stretch) );
}

// -------------------- DcMeshHeightCrit -------------------------------------

bool DcMeshHeightCrit::splitEdge(const Vct3 &ps, const Vct3 &pt,
                                 const Vct3 &tgs, const Vct3 &tgt, Real) const
{
  // estimate maximum expected height error
  // using tan(phi) \approx phi for small angles
  Vct3 edi = pt - ps;
  Real eln = norm(pt - ps);

  // exploit tan( acos(x) ) = sqrt(1 - sq(x)) / x
  // Real phis = arg(edi, tgs);
  // Real phit = arg(edi, tgt);
  Real cphis = cosarg(edi, tgs);
  Real cphit = cosarg(edi, tgt);
  if (cphis <= 0.0 or cphit <= 0.0)
    return true;

  Real bs = std::sqrt( 1.0 - sq(cphis) ) / cphis;
  Real bt = std::sqrt( 1.0 - sq(cphit) ) / cphit;
  Real hmax = 0.5*eln*std::max(bs, bt);
  return sq(hmax) > smaxHeight;
}

bool DcMeshHeightCrit::splitEdge(uint s, uint t) const
{
  Vct2 qmid = 0.5*( puv(s) + puv(t) );
  Vct3 pmid = 0.5*( pxy(s) + pxy(t) );
  return sq( psf->eval(qmid[0], qmid[1]) - pmid ) > smaxHeight;
}

int DcMeshHeightCrit::splitFace(uint a, uint b, uint c) const
{
  Vct2 qmid = ( puv(a) + puv(b) + puv(c) ) / 3.0;
  Vct3 pmid = ( pxy(a) + pxy(b) + pxy(c) ) / 3.0;
  if ( sq( psf->eval(qmid[0], qmid[1]) - pmid ) > smaxHeight ) {
    Real l1 = sq(pxy(a) - pxy(b));
    Real l2 = sq(pxy(b) - pxy(c));
    Real l3 = sq(pxy(c) - pxy(a));
    if (l1 > l2 and l1 > l3)
      return DcMeshCritBase::SplitEdge1;
    else if (l2 > l1 and l2 > l3)
      return DcMeshCritBase::SplitEdge2;
    else
      return DcMeshCritBase::SplitEdge3;
  } else {
    return DcMeshCritBase::NoSplit;
  }
}

// --------------------- DcMeshSourceCrit ------------------------------------

bool DcMeshSourceCrit::splitEdge(const Vct3 &ps, const Vct3 &pt,
                                 const Vct3 &, const Vct3 &, Real) const
{
  Real f = factor(ps, pt);
  Real sql = sq(pt - ps);
  return (sql*m_gisl > f);
}

bool DcMeshSourceCrit::splitEdge(uint s, uint t) const
{
  const Vct3 &ps( pxy(s) );
  const Vct3 &pt( pxy(t) );
  Real f = factor(ps, pt);
  Real sql = sq(pt - ps);
  return (sql*m_gisl > f);
}

int DcMeshSourceCrit::splitFace(uint a, uint b, uint c) const
{
  Vct3 p[3] = { pxy(a), pxy(b), pxy(c) };
  Real f = 1.0, slmax = 0.0;
  Real sql[3];
  int ilmax = 0;
  const int nps = m_points.size();
  for (int i=0; i<3; ++i) {
    const int s = i;
    const int t = (i+1)%3;
    sql[i] = sq(p[t] - p[s]);
    for (int j=0; j<nps; ++j) {
      f = std::max(f, pointSource(j, p[s]));
      f = std::max(f, pointSource(j, p[t]));
    }
    if (sql[i] > slmax) {
      ilmax = i;
      slmax = sql[i];
    }
  }

  if (slmax*m_gisl < f)
    return NoSplit;

  Real len[3];
  for (int k=0; k<3; ++k)
    len[k] = sqrt(sql[k]);
  Real ccr = ccRadius(len);
  bool obtuse = (2*ccr > len[ilmax]);

  if (obtuse)
    return SplitEdge1 + ilmax;
  else
    return InsertTriCenter;

  return NoSplit;
}

Real DcMeshSourceCrit::factor(const Vct3 &pa, const Vct3 &pb) const
{
  Real f = 1.0;
  const int nps = m_points.size();
  for (int i=0; i<nps; ++i) {
    f = std::max(f, pointSource(i, pa));
    f = std::max(f, pointSource(i, pb));
  }

  const int nls = m_lines.size() / 2;
  for (int i=0; i<nls; ++i) {
    f = std::max(f, lineSource(i, pa));
    f = std::max(f, lineSource(i, pb));
  }

  return f;
}

void DcMeshSourceCrit::factors(const Vct3 p[], Real f[]) const
{
  f[0] = f[1] = f[2] = 1.0;
  const int nps = m_points.size();
  for (int i=0; i<nps; ++i) {
    for (int k=0; k<3; ++k)
      f[k] = std::max(f[k], pointSource(i, p[k]));
  }

  const int nls = m_lines.size() / 2;
  for (int i=0; i<nls; ++i) {
    for (int k=0; k<3; ++k)
      f[k] = std::max(f[k], lineSource(i, p[k]));
  }
}

// --------------------- DcMeshMultiCrit ------------------------------------

DcMeshCritBasePtr DcMeshMultiCrit::clone() const
{
  DcMeshMultiCritPtr p = boost::make_shared<DcMeshMultiCrit>(*this);
  for (size_t i=0; i<m_crits.size(); ++i)
    p->m_crits[i] = m_crits[i]->clone();
  return p;
}

void DcMeshMultiCrit::append(DcMeshCritBasePtr pmc)
{
  m_crits.push_back(pmc);
}

void DcMeshMultiCrit::assign(const Surface *srf,
                             const PointList<2> *uv,
                             const PointList<2> *st,
                             const PointList<3> *xy,
                             const PointList<3> *nm)
{
  DcMeshCritBase::assign(srf, uv, st, xy, nm);
  for (size_t i=0; i<m_crits.size(); ++i)
    m_crits[i]->assign(srf, uv, st, xy, nm);
}

bool DcMeshMultiCrit::splitEdge(const Vct3 &ps, const Vct3 &pt,
                                const Vct3 &tgs, const Vct3 &tgt, Real bf) const
{
  for (size_t i=0; i<m_crits.size(); ++i) {
    if ( m_crits[i]->splitEdge(ps, pt, tgs, tgt, bf) )
      return true;
  }
  return false;
}

bool DcMeshMultiCrit::splitEdge(const AbstractUvCurve &cuv,
                                Real ts, Real tt) const
{
  for (size_t i=0; i<m_crits.size(); ++i) {
    if ( m_crits[i]->splitEdge(cuv, ts, tt) )
      return true;
  }
  return false;
}

bool DcMeshMultiCrit::splitEdge(uint s, uint t) const
{
  for (size_t i=0; i<m_crits.size(); ++i) {
    if ( m_crits[i]->splitEdge(s, t) )
      return true;
  }
  return false;
}

int DcMeshMultiCrit::splitFace(uint a, uint b, uint c) const
{
  for (size_t i=0; i<m_crits.size(); ++i) {
    int flag = m_crits[i]->splitFace(a, b, c);
    if (flag != NoSplit)
      return flag;
  }
  return NoSplit;
}

