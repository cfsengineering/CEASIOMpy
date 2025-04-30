
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
 
#include "airfoilfitter.h"
#include "airfoil.h"

#include <genua/point.h>
#include <genua/eig.h>
#include <genua/pattern.h>
#include <genua/transformation.h>
#include <genua/ioglue.h>

using std::string;

// ------------------------- local --------------------------------------------

static bool largestPositive(Vct3 & a)
{
  Real x = std::fabs(a[0]);
  Real y = std::fabs(a[1]);
  Real z = std::fabs(a[2]);
  bool flipped = false;
  if (x > y and x > z) {
    if (a[0] < 0.0) {
      a *= -1.0;
      flipped = true;
    }
  } else if (y > x and y > z) {
    if (a[1] < 0.0) {
      a *= -1.0;
      flipped = true;
    }
  } else if (a[2] < 0.0) {
    a *= -1.0;
    flipped = true;
  }
  return flipped;
}

// ------------------------- AirfoilFitter ------------------------------------

AirfoilPtr AirfoilFitter::fitSegments(const PointList<3> &segm)
{
  if (segm.empty())
    return AirfoilPtr();

  assert(segm.size()%2 == 0);
  toLocal(segm);

  // generate a thicker airfoil with large TE gap to wrap around the current
  // set of coordinates
  Airfoil wrapfoil("WrappedFoil");
  wrapfoil.naca4(0.0, 0.3, 1.25*m_tcest, false);
  wrapfoil.closeTrailingEdge( std::min(0.5*m_tcest, 0.02) );

  // blow up the wrap airfoil and move it slightly forward
  wrapfoil.scale(1.02);
  wrapfoil.translate(-0.01, 0.0, 0.0);
  wrapfoil.apply();

  // generate a decently distributed set of sampling points to be
  // projected onto segments
  const int nsp = std::min(512u, std::max(128u, segm.size()));
  Vector usp;
  airfoil_pattern( nsp, 0.5, 1.3, 1.1, usp );
  PointList<2> pjp(nsp);
  for (int i=0; i<nsp; ++i) {
    Vct3 pw = wrapfoil.eval(usp[i]);
    Vct2 pt( pw[0], pw[2] );
    nearestSegment(pt, pjp[i]);
  }

  // remove duplicate points resulting from projection
  PointList<2> tmp;
  tmp.reserve(nsp);
  tmp.push_back(pjp.front());
  Real mindst(1e-6);
  for (int i=1; i<nsp; ++i) {
    if (sq(pjp[i]-tmp.back()) > sq(mindst))
      tmp.push_back(pjp[i]);
  }
  pjp.swap(tmp);

  // make sure that ordering is consistent
  reorder(pjp);

  AirfoilPtr afp(new Airfoil("Approximation", pjp));
  return afp;
}

uint AirfoilFitter::nearestSegment(const Vct2 &p, Vct2 &ps) const
{
  const int nseg = m_crd.size() / 2;

  Vct2 ppi;
  Real dsq, mindsq = std::numeric_limits<Real>::max();
  uint bestSeg = NotFound;
  for (int i=0; i<nseg; ++i) {
    dsq = project(i, p, ppi);
    if (dsq < mindsq) {
      mindsq = dsq;
      bestSeg = i;
      ps = ppi;
    }
  }

  return bestSeg;
}

Real AirfoilFitter::project(uint k, const Vct2 &p, Vct2 &ps) const
{
  const Vct2 &s1( m_crd[2*k+0] );
  const Vct2 &s2( m_crd[2*k+1] );
  Vct2 r(p - s1), s(s2 - s1);
  Real ts, sqs = sq(s);
  if (sqs <= 0.0)
    ts = 0.0;
  else
    ts = clamp(dot(r, s) / sqs, 0.0, 1.0);
  ps = (1-ts)*s1 + ts*s2;
  return sq(p - ps);
}

void AirfoilFitter::estimatePrincipal(const PointList<3> &pts)
{
  const int np = pts.size();

  // determine center of point set
  Vct3 ctr;
  for (int i=0; i<np; ++i)
    ctr += pts[i];
  ctr /= Real(np);

  // compute covariance matrix
  Mtx33 cov;
  for (int i=0; i<np; ++i) {
    Vct3 r = pts[i] - ctr;
    cov += dyadic(r, r);
  }
  cov /= Real(np);

  // eigenvalues of covariance matrix
  Vct3 lambda;
  sym_eig3(cov, lambda);

  // extract eigenvectors for largest eigenvalue
  extract_eigenvector(cov, lambda[2], m_guide);
  extract_eigenvector(cov, lambda[0], m_pln);
  largestPositive(m_guide);
  normalize(m_guide);
  normalize(m_pln);
}

void AirfoilFitter::toLocal(const PointList<3> &pts)
{
  const int np = pts.size();
  if (sq(m_guide) < gmepsilon)
    estimatePrincipal(pts);

  // determine center of point set
  Vct3 ctr;
  for (int i=0; i<np; ++i)
    ctr += pts[i];
  ctr /= Real(np);

  // determine coordinate transformation
  Real gmax = -std::numeric_limits<Real>::max();
  uint imax, ile;
  imax = ile = NotFound;
  for (int i=0; i<np; ++i) {
    Vct3 r( pts[i] - ctr );
    Real g = dot(m_guide, r);
    if (g > gmax) {
      imax = i;
      gmax = g;
    }
  }
  assert(imax != NotFound);
  cout << "TE at " << pts[imax] << endl;

  // mark point farthest from gmax as LE
  Real maxdst = 0.0;
  for (int i=0; i<np; ++i) {
    Real dsq = sq( pts[i] - pts[imax] );
    if (dsq > maxdst) {
      maxdst = dsq;
      ile = i;
    }
  }
  assert(ile != NotFound);
  cout << "LE at " << pts[ile] << endl;

  m_ple = pts[ile];
  m_xax = pts[imax] - pts[ile];
  m_chord = normalize(m_xax);

  // derive remaining axes
  m_zax = m_pln;
  m_zax -= dot(m_pln, m_xax)*m_xax;
  normalize(m_zax);
  m_yax = cross(m_xax, m_zax).normalized();

  // determine local coordinates
  m_crd.resize(np);
  Real ich = 1.0 / m_chord;
  for (int i=0; i<np; ++i) {
    Vct3 r = pts[i] - m_ple;
    m_crd[i][0] = dot(m_xax, r) * ich;
    m_crd[i][1] = dot(m_yax, r) * ich;
  }

  // estimate thickness ratio
  Real ymin, ymax;
  ymin = std::numeric_limits<Real>::max();
  ymax = -ymin;
  for (int i=0; i<np; ++i) {
    ymax = std::max( m_crd[i][1], ymax );
    ymin = std::min( m_crd[i][1], ymin );
  }
  m_tcest = ymax - ymin;
  cout << "AirfoilFitter: t/c = " << m_tcest << endl;
}

void AirfoilFitter::rotation(Vct3 &rot) const
{
  // assemble rotation matrix from coordinate directions
  Mtx33 m;
  for (int i=0; i<3; ++i) {
    m(i,0) = m_xax[i];
    m(i,1) = m_zax[i];
    m(i,2) = m_yax[i];
  }

  // debug
  cout << "Local basis: " << endl << m << endl;

  Trafo3d::findRotation(m, rot);
}

void AirfoilFitter::transform(const PointList<2> &crd, PointList<3> &pts) const
{
  const int np = crd.size();
  pts.resize(np);
  for (int i=0; i<np; ++i) {
    Real x = crd[i][0];
    Real y = crd[i][1];
    pts[i] = m_ple + (x*m_xax + y*m_yax)*m_chord;
  }
}

void AirfoilFitter::reorder(PointList<2> &pts)
{
  Vct2 ctr;
  const int np = pts.size();
  for (int i=0; i<np; ++i)
    ctr += pts[i];
  ctr /= Real(np);

  Real sum(0);
  for (int i=1; i<np; ++i) {
    const Vct2 & r1( pts[i-1] - ctr );
    const Vct2 & r2( pts[i] - ctr );
    sum += r1[0]*r2[1] - r1[1]*r2[0];
  }
  if (sum < 0)
    std::reverse( pts.begin(), pts.end() );
}

void AirfoilFitter::normalizeCoordinates()
{
  // move LE point to (0,0) and rescale
  const int np = m_crd.size();
  Real xmin, xmax;
  xmin = std::numeric_limits<Real>::max();
  xmax = -xmin;
  uint ile(np/2), ite(0);
  for (int i=0; i<np; ++i) {
    Real x = m_crd[i][0];
    if (x > xmax) {
      xmax = x;
      ite = i;
    }
    if (x < xmin) {
      xmin = x;
      ile = i;
    }
  }
  Vct2 cle = m_crd[ile];
  m_ple += m_chord * (cle[0]*m_xax + cle[1]*m_yax);

  Real dx = xmax - xmin;
  m_chord *= dx;
  for (int i=0; i<np; ++i)
    m_crd[i] = (m_crd[i] - cle) / dx;

  // TODO:
  // derotate such that trailing edge point is at (1,0)
}
