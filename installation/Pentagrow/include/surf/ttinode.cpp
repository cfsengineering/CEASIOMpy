
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
 
#include "ttinode.h"
#include "ttintersection.h"
#include "meshcomponent.h"
#include "dnrefine.h"
#include <genua/xcept.h>

using namespace std;

void  TTiNode::average(const uint ctr[])
{
  nrm = 0.0;
  for (int k=0; k<3; ++k) {
    if (ctr[k] > 0) {
      q[k] *= 1.0/ctr[k]; // parametric values summed above!
      nrm += mpp[k]->surface()->normal( q[k][0], q[k][1] );
    }
  }
  normalize(nrm);
}

bool TTiNode::attach(const TTIntersection & sa, const TTIntersection & sb)
{
  Vct2 qa[2], qb[2];
  mpp[0] = sa.firstPatch();
  mpp[1] = sa.secondPatch();
  
  if (sb.firstPatch() != mpp[0] or sb.secondPatch() != mpp[1])
    return false;
  
  Real dist;
  TTIntersection::TTiConTop c = sa.nearestConnection(sb, dist);
  
  switch (c) {
    case TTIntersection::tti_s2s:
      sa.srcParameter(qa[0], qa[1]);
      sb.srcParameter(qb[0], qb[1]);
      q[0] = 0.5*(qa[0] + qb[0]);
      q[1] = 0.5*(qa[1] + qb[1]);
      break;
    case TTIntersection::tti_s2t:
      sa.srcParameter(qa[0], qa[1]);
      sb.trgParameter(qb[0], qb[1]);
      q[0] = 0.5*(qa[0] + qb[0]);
      q[1] = 0.5*(qa[1] + qb[1]);
      break;
    case TTIntersection::tti_t2s:
      sa.trgParameter(qa[0], qa[1]);
      sb.srcParameter(qb[0], qb[1]);
      q[0] = 0.5*(qa[0] + qb[0]);
      q[1] = 0.5*(qa[1] + qb[1]);
      break;
    case TTIntersection::tti_t2t:
      sa.trgParameter(qa[0], qa[1]);
      sb.trgParameter(qb[0], qb[1]);
      q[0] = 0.5*(qa[0] + qb[0]);
      q[1] = 0.5*(qa[1] + qb[1]);
      break;
    case TTIntersection::tti_none:
      return false;
  }
  
  bEnforced = sa.enforced() or sb.enforced();

  return true;
}

Real TTiNode::gap() const
{
  if (mpp[0] == 0 or mpp[1] == 0)
    return 0.0;
  
  Real gp;
  Vct3 p1, p2;
  p1 = mpp[0]->surface()->eval( q[0][0], q[0][1] );
  p2 = mpp[1]->surface()->eval( q[1][0], q[1][1] );
  gp = norm(p2-p1);
  
  if (mpp[2] != 0) {
    Vct3 p3;
    p3 = mpp[2]->surface()->eval( q[2][0], q[2][1] );
    gp += norm(p3-p2) + norm(p3-p1);
  }
  return gp;
}

Real TTiNode::reproject(int niter, Real maxdst, Real dtol)
{
  // implemented for two surfaces
  if ( (not mpp[0]) or (not mpp[1]) )
    return 0.0;
  else if (mpp[2])
    return 0.0;
  
  Vct3 p0, p1, pmid(p), porg(p);
  const Surface & S0( *mpp[0]->surface() );
  const Surface & S1( *mpp[1]->surface() );
  Real cgap(gap()), ngap(cgap);
  Vct2 q0(q[0]), q1(q[1]);
  for (int i=0; i<niter; ++i) {
    Real tol = max(0.25*dtol, 0.125*cgap);
    S0.project(pmid, q0, tol);
    S1.project(pmid, q1, tol);
    p0 = S0.eval(q0[0], q0[1]);
    p1 = S1.eval(q1[0],q1[1]);
    Real ngap = norm(p1 - p0);
    pmid = 0.5*(p0+p1);
    Real dmov = norm(pmid - p);
    if (ngap < cgap and dmov < maxdst) {
      q[0] = q0;
      q[1] = q1;
      p = pmid;
      cgap = ngap;
      
      // debug
      //cout << "Iteration " << i+1 << " gap " << ngap << endl;
      
      if (ngap < dtol)
        break;
    } else {
      break;
    }
  }
  
  return ngap;
}

void TTiNode::mesh2surface()
{
  if (mpp[0] == 0 or mpp[1] == 0)
    return;
  
  Vct3 pmean;
  pmean += mpp[0]->surface()->eval( q[0][0], q[0][1] );
  pmean += mpp[1]->surface()->eval( q[1][0], q[1][1] );
  if (mpp[2] != 0) {
    pmean += mpp[2]->surface()->eval( q[2][0], q[2][1] );
    pmean /= 3.;
  } else {
    pmean *= 0.5;
  }
  p = pmean;
  assert(std::isfinite(dot(p,p)));
}

void TTiNode::snapToBoundary(Real tol)
{
  for (int k=0; k<3; ++k) {
    if (mpp[k] != 0) {
      Real & u( q[k][0] );
      Real & v( q[k][1] );
      if (u < tol)
        u = 0.0;
      else if (u > 1.0-tol)
        u = 1.0;
      if (v < tol)
        v = 0.0;
      else if (v > 1.0-tol)
        v = 1.0;
    }
  }
}

bool TTiNode::onBoundary(Real tol) const
{
  for (int k=0; k<3; ++k) {
    if (mpp[k] == 0)
      return false;
    Real u = q[k][0];
    Real v = q[k][1];
    if (u < tol or u > (1.0 - tol))
      return true;
    if (v < tol or v > (1.0 - tol))
      return true;
  }

  return false;
}

void TTiNode::localCriteria(Real & maxlen, Real & minlen, Real & maxphi) const
{
  maxlen = huge;
  minlen = huge;
  maxphi = huge;
  for (int k=0; k<3; ++k) {
    if (mpp[k] != 0) {
      const DnRefineCriterion & c( *(mpp[k]->criterion()) );
      maxlen = min(maxlen, c.maxLength());
      minlen = min(minlen, c.minLength());
      maxphi = min(maxphi, c.maxPhi());
    }
  }
}

// TTiNode::TTiNode(const TTIntersection & sa, 
//                  const TTIntersection & sb, TTiConnection c)
// {
//   Vct2 qa[2], qb[2];
//   sa.surfaces(psf[0], psf[1]);
//   switch (c) {
//     case tti_s2s:
//       p = 0.5*( sa.srcPoint() + sb.srcPoint() );
//       sa.srcParameter(qa[0], qa[1]);
//       sb.srcParameter(qb[0], qb[1]);
//       q[0] = 0.5*(qa[0] + qb[0]);
//       q[1] = 0.5*(qa[1] + qb[1]);
//       break;
//     case tti_s2t:
//       p = 0.5*( sa.srcPoint() + sb.trgPoint() );
//       sa.srcParameter(qa[0], qa[1]);
//       sb.trgParameter(qb[0], qb[1]);
//       q[0] = 0.5*(qa[0] + qb[0]);
//       q[1] = 0.5*(qa[1] + qb[1]);
//       break;
//     case tti_t2s:
//       p = 0.5*( sa.trgPoint() + sb.srcPoint() );
//       sa.trgParameter(qa[0], qa[1]);
//       sb.srcParameter(qb[0], qb[1]);
//       q[0] = 0.5*(qa[0] + qb[0]);
//       q[1] = 0.5*(qa[1] + qb[1]);
//       break;
//     case tti_t2t:
//       p = 0.5*( sa.trgPoint() + sb.trgPoint() );
//       sa.trgParameter(qa[0], qa[1]);
//       sb.trgParameter(qb[0], qb[1]);
//       q[0] = 0.5*(qa[0] + qb[0]);
//       q[1] = 0.5*(qa[1] + qb[1]);
//       break;
//     case tti_none:
//       throw Error("TTiNode must be attached.");
//   }
// }

