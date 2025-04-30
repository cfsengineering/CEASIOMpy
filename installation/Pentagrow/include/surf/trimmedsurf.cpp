
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
 
#include "trimmedsurf.h"
#include "polysplinesurf.h"
#include "rationalsplinesurface.h"
#include "igesfile.h"
#include "iges144.h"
#include "iges142.h"
#include "dnmesh.h"
#include "dnrefine.h"
#include "uvmapdelaunay.h"
#include "dcmeshcrit.h"
// #include <predicates/predicates.h>
#include <genua/basicedge.h>
#include <genua/ndpointtree.h>
#include <genua/cgmesh.h>
#include <genua/dbprint.h>
#include <genua/pattern.h>

// debug
#include <genua/mxmesh.h>

using namespace std;

TrimmedSurf *TrimmedSurf::clone() const
{
  return (new TrimmedSurf(*this));
}

void TrimmedSurf::curveBounds(const PointList<2> &bnd,
                              Vct2 &plo, Vct2 &phi) const
{
  plo = std::numeric_limits<Real>::max();
  phi = -plo;
  const int np = bnd.size();
  for (int i=0; i<np; ++i) {
    for (int k=0; k<2; ++k) {
      Real pk = bnd[i][k];
      plo[k] = std::min(plo[k], pk);
      phi[k] = std::max(phi[k], pk);
    }
  }
}

void TrimmedSurf::dimStats(Surface::DimStat &stat) const
{
  if (not base)
    return;

  // let base surface set values
  base->dimStats(stat);

  // determine bounding range for external constraint
  Vct2 plo, phi;
  curveBounds(extPoly, plo, phi);

  const int nu = std::max(2, stat.nu);
  const int nv = std::max(2, stat.nv);
  PointGrid<3> ptg(nu,nv);
  for (int i=0; i<nu; ++i) {
    Real tu = Real(i)/(nu-1);
    Real u = (1.0 - tu)*plo[0] + tu*phi[0];
    for (int j=0; j<nv; ++j) {
      Real tv = Real(j)/(nv-1);
      Real v = (1.0 - tv)*plo[1] + tu*phi[1];
      ptg(i,j) = eval(u, v);
      for (int k=0; k<3; ++k) {
        Real pk = ptg(i,j)[k];
        stat.bbhi[k] = std::max(pk, stat.bbhi[k]);
        stat.bblo[k] = std::min(pk, stat.bblo[k]);
      }
    }
  }

  stat.area = 0.0;
  for (int i=1; i<nu; ++i) {
    for (int j=1; j<nv; ++j) {
      Real w = norm(ptg(i,j) - ptg(i-1,j)) + norm(ptg(i,j-1) - ptg(i-1,j-1));
      Real h = norm(ptg(i,j) - ptg(i,j-1)) + norm(ptg(i-1,j) - ptg(i-1,j-1));
      stat.area += 0.25*w*h;
    }
  }
}

void TrimmedSurf::meshCurves()
{
  Vector t;
  if (extBound) {
    extBound->initGrid(t);
    const int n = t.size();
    extPoly.reserve(n);
    for (int i=0; i<n; ++i) {
      Vct3 p = extBound->eval(t[i]);
      // extPoly[i][0] = clamp(p[0], 0.0, 1.0);
      // extPoly[i][1] = clamp(p[1], 0.0, 1.0);
      Vct2 q;
      q[0] = clamp(p[0], 0.0, 1.0);
      q[1] = clamp(p[1], 0.0, 1.0);
      if (extPoly.empty() or sq(q - extPoly.back()) > 1e-8)
        extPoly.push_back(q);
    }
    refineCurve(extPoly);
  }

  intPoly.resize( intBound.size() );
  for (uint j=0; j<intBound.size(); ++j) {
    intBound[j]->initGrid(t);
    const int n = t.size();
    intPoly[j].reserve(n);
    for (int i=0; i<n; ++i) {
      Vct3 p = intBound[j]->eval(t[i]);
      // assert(p[0] >= 0.0 and p[0] <= 1.0);
      // assert(p[1] >= 0.0 and p[1] <= 1.0);
      //      intPoly[j][i][0] = clamp(p[0], 0.0, 1.0);
      //      intPoly[j][i][1] = clamp(p[1], 0.0, 1.0);
      Vct2 q;
      q[0] = clamp(p[0], 0.0, 1.0);
      q[1] = clamp(p[1], 0.0, 1.0);
      if (intPoly[j].empty() or sq(q - intPoly[j].back()) > 1e-8)
        intPoly[j].push_back(q);
    }
    refineCurve(intPoly[j]);
  }
}

void TrimmedSurf::refineCurve(PointList<2> &q) const
{
  // use tangent change criterion
  const Real mincphi = cos( rad(30.) );
  const Real maxdqs = sq(0.05);
  const Real mindqs = sq(1e-4);
  const uint nmax = 4096;

  PointList<2> tmp;
  tmp.reserve(q.size());
  int nin = 0;
  do {
    nin = 0;
    tmp.clear();
    Vct3 S1, S2, S1u, S2u, S1v, S2v;
    const int n = q.size();
    base->plane(q[0][0], q[0][1], S1, S1u, S1v);
    tmp.push_back( q.front() );
    for (int i=1; i<n; ++i) {
      Real dqs = sq(q[i] - q[i-1]);
      base->plane(q[i][0], q[i][1], S2, S2u, S2v);
      if (dqs > maxdqs) {
        tmp.push_back( 0.5*(q[i-1] + q[i]) );
        ++nin;
      } else if (dqs > mindqs) {
        if (cosarg(S1u, S2u) < mincphi or cosarg(S1v, S2v) < mincphi) {
          tmp.push_back( 0.5*(q[i-1] + q[i]) );
          ++nin;
        }
      }
      tmp.push_back(q[i]);
      S1u = S2u;
      S1v = S2v;
    }
    q.swap(tmp);
  } while ((nin > 0) and (q.size() < nmax));

  // make sure the constraint is closed
  Vct2 jn = 0.5 * (q.front() + q.back());
  q.front() = q.back() = jn;
}

void TrimmedSurf::projectConstraint(const PointList<2> &c,
                                    std::set<Real> &uset, std::set<Real> &vset) const
{
  const int n = c.size();
  for (int i=0; i<n; i+=2) {
    uset.insert( c[i][0] );
    vset.insert( c[i][1] );
  }
}

uint TrimmedSurf::insertPoints(const TrimmedSurf::PointTree & ptree,
                               PointList<2> &c) const
{
  PointList<2> con(c);
  Indices inear;
  const int n = c.size();
  uint nin = 0;
  for (int i=1; i<n; ++i) {
    inear.clear();
    const Vct2 & src( c[i-1] );
    const Vct2 & trg( c[i] );
    Vct2 cd(trg - src);
    Real len = normalize(cd);
    ptree.find(src, len, inear);
    ptree.find(trg, len, inear);
    const int nnp = inear.size();
    for (int j=0; j<nnp; ++j) {
      const Vct2 & pj( ptree.point(inear[j]) );
      if (sq(pj-src) < gmepsilon)
        continue;
      if (sq(pj-trg) < gmepsilon)
        continue;
      // Real sds = jrsOrient2d(src, trg, pj);
      // if (sds != 0.0)
      //  continue;

      Real t = dot(pj - src, cd);
      if (t <= gmepsilon or t >= 1-gmepsilon)
        continue;
      Vct2 foot = (1-t)*src + t*trg;
      Real dls = sq( pj - foot );
      if (dls < gmepsilon) {
        cout << "between " << con[nin+i-1] << " and " << con[nin+i] << endl;
        con.insert(con.begin()+i+nin, pj);
        // debug
        cout << t << " Inserting " << pj << endl;

        ++nin;
        break;
      }
    }
  }

  if (nin > 0)
    con.swap(c);

  return nin;
}

void TrimmedSurf::tessellate(CgMesh &cgm, uint maxtri) const
{
  // cgRepDN(cgm);
  //   return;

  PointList<2> pg;
  Indices tri;
  trimmedGrid(maxtri, pg, tri);

  if (tri.size() == 0) {
    cgm.clearMesh();
    dbprint("No triangles left after trimming: ", name());
    return;
  }

  // find boundary vertices
  Indices bv;
  findBoundaries(tri, bv);

  // project mesh boundary vertices onto constraints
  const int nib = intPoly.size();
  const int nbv = bv.size();
  Vector parc(nbv);
  Indices pjbound(nbv);

  for (int i=0; i<nbv; ++i) {

    uint ibound(NotFound), bvi = bv[i];
    Vct2 ptmp = pg[bvi];
    Real arc, dstmin = std::numeric_limits<Real>::max();
    arc = pointToBoundary(extPoly, ptmp, dstmin);

    for (int k=0; k<nib; ++k) {
      Vct2 pp = pg[bvi];
      Real tarc = pointToBoundary(intPoly[k], pp, dstmin);
      if ( tarc >= 0.0 ) {
        ptmp = pp;
        arc = tarc;
        ibound = k;
      }
    }

    pjbound[i] = ibound;
    parc[i] = arc;
    pg[bvi] = ptmp;
  }

  // add corner triangles
  fillCorners(NotFound, bv, parc, pjbound, pg, tri);
  // for (int k=0; k<nib; ++k)
  //   fillCorners(k, bv, parc, pjbound, pg, tri);

  // evaluate surface for used vertices only
  Indices iused(tri);
  sort_unique(iused);
  const int nu = iused.size();

  // construct vertex index mapping
  const int nall = pg.size();
  Indices vmap(nall, NotFound);
  for (int i=0; i<nu; ++i)
    vmap[iused[i]] = i;

  Vct3 S, Su, Sv;
  PointList<3,float> cgv(nu), cgn(nu);
  for (int i=0; i<nu; ++i) {
    Vct2 p = pg[iused[i]];
    base->plane(p[0], p[1], S, Su, Sv);
    cgv[i] = Vct3f( S );
    cgn[i] = Vct3f( cross(Su,Sv) );
  }

  // remap triangle vertices to used vertices
  const int ntv = tri.size();
  for (int i=0; i<ntv; ++i) {
    tri[i] = vmap[tri[i]];
    assert(tri[i] != NotFound);
  }

  cgm.importMesh(nu, cgv.pointer(), cgn.pointer(), ntv/3, &tri[0]);

  // add boundaries as lines
  linesFromBoundary(extPoly, cgm);
  for (int k=0; k<nib; ++k)
    linesFromBoundary(intPoly[k], cgm);
  cgm.expandStrips();
}

void TrimmedSurf::linesFromBoundary(const PointList<2> &bnd, CgMesh &cgm) const
{
  const int np = bnd.size();
  PointList<3,float> pln(np);
  for (int i=0; i<np; ++i)
    pln[i] = Vct3f(base->eval(bnd[i][0], bnd[i][1]));
  cgm.appendLine(pln);
}

void TrimmedSurf::findBoundaries(const Indices &tri, Indices &bv) const
{
  const int ntri = tri.size() / 3;
  BasicEdgeSet edset;
  for (int i=0; i<ntri; ++i) {
    const uint *vk = &tri[3*i];
    for (int k=0; k<3; ++k) {
      BasicEdge e( vk[k], vk[(k+1)%3] );
      if (edset.count(e) == 0)
        edset.insert(e);
      else
        edset.erase(e);
    }
  }

  bv.clear();
  bv.reserve(edset.size()*2);
  BasicEdgeSet::const_iterator itr, last = edset.end();
  for (itr = edset.begin(); itr != last; ++itr) {
    bv.push_back( itr->source() );
    bv.push_back( itr->target() );
  }

  sort_unique(bv);
}

void TrimmedSurf::cgRepDN(CgMesh &cgm) const
{
  // 2D Delaunay mesh generator
  SurfacePtr self( (Surface*) this, null_deleter() );
  DnMesh gnr(self, DnPlane);

  // start with rectangular grid
  Vector up, vp;
  base->initGridPattern(up, vp);

  // At this point, we know that there will be constraints to insert
  // which will badly affect mesh quality -- hence, the initial triangle
  // mesh should be reasonably fine. This is assured by projecting the
  // constraint polylines onto the u/v pattern vectors in order to generate
  // a suitable initial grid-type mesh.

  std::set<Real> uset(up.begin(), up.end()), vset(vp.begin(), vp.end());
  projectConstraint(extPoly, uset, vset);
  for (uint ic=0; ic<intPoly.size(); ++ic)
    projectConstraint(intPoly[ic], uset, vset);

  almost_equal<Real> pred(1e-3);
  up.clear();
  vp.clear();
  std::unique_copy(uset.begin(), uset.end(), back_inserter(up), pred);
  std::unique_copy(vset.begin(), vset.end(), back_inserter(vp), pred);

  if (up.front() != 0.0)
    up.insert(up.begin(), 0.0);
  if (up.back() != 1.0)
    up.insert(up.end(), 1.0);
  if (vp.front() != 0.0)
    vp.insert(vp.begin(), 0.0);
  if (vp.back() != 1.0)
    vp.insert(vp.end(), 1.0);

  // smooth pattern once
  {
    const int n = up.size();
    for (int i=1; i<n-1; ++i)
      up[i] = 0.5*up[i] + 0.25*(up[i-1] + up[i+1]);
  }
  {
    const int n = vp.size();
    for (int i=1; i<n-1; ++i)
      vp[i] = 0.5*vp[i] + 0.25*(vp[i-1] + vp[i+1]);
  }

  gnr.init(up, vp);

  //  // insert premesh points, especially on the boundary, into constraints
  //  if (gnr.nvertices() > 0) {
  //    PointList<2> uvp;
  //    {
  //      Indices tri;
  //      gnr.exportMesh(uvp, tri);
  //    }

  //    TrimmedSurf::PointTree ptree;
  //    ptree.allocate(uvp, true, 4);
  //    ptree.sort();

  //    PointList<2> cxp(extPoly);
  //    uint ni(0);
  //    do {
  //      ni = insertPoints(ptree, cxp);
  //    } while (ni > 0);
  //  }

  // insert external boundary constraints, if present
  Indices icon = gnr.addConstraint(extPoly, true);

  // abort tesselation if constraint insertion failed
  bool extrimmed = true;
  if (extPoly.size() != icon.size()) {
    extrimmed = false;
    clog << name() << " not trimmed along external boundary." << endl;
    clog << gnr.lastError() << endl;
  }

  // dbprint("Inserted constraint:", extPoly.size(),
  //         sq(extPoly.front() - extPoly.back()));

  // insert internal boundary constraints
  vector<bool> intrimmed(intPoly.size(), extrimmed);
  if (extrimmed) {
    for (uint j=0; j<intPoly.size(); ++j) {
      icon = gnr.addConstraint(intPoly[j], true);
      if ((not intPoly[j].empty()) and icon.empty()) {
        clog << name() << " internal boundary trimming failed." << endl;
        intrimmed[j] = false;
      }
    }
  }

  // erase external and hole triangles
  // cout << "Trimming (" << gnr.nfaces() << ")..." << endl;
  if (extrimmed) {
    addHole(extPoly, false, gnr);
    for (uint j=0; j<intPoly.size(); ++j) {
      if (intrimmed[j])
        addHole(intPoly[j], true, gnr);
    }
  }

  // export to CgMesh
  Indices triangles;
  PointList<3> mvtx, mnrm;
  PointList<2> pp;
  gnr.exportMesh(pp, mvtx, mnrm, triangles);

  if (not mvtx.empty())
    cgm.importMesh(mvtx.size(), mvtx.pointer(), mnrm.pointer(),
                   triangles.size()/3, &triangles[0]);

  return;

  // -----

  //  // start with rectangular grid
  //  Vector up, vp;
  //  base->initGridPattern(up, vp);

  //  // create mapped Delaunay mesh generator
  //  SurfacePtr self( (Surface*) this, null_deleter());


  //  // UvMapDelaunay gnr(self, up, vp);
  //  UvMapDelaunay gnr(self, equi_pattern(4), equi_pattern(4));

  //  // test h-criterion
  //  const Real htol = std::max(0.001, 0.01*base->typLength());
  //  DcMeshHeightCrit crit;
  //  crit.npass(8);
  //  crit.maxNodes( 20000 );
  //  crit.tolerance(htol);

  //  gnr.twoQuads();
  //  //gnr.initMesh(up, vp);
  // // gnr.dbgDump( name() );
  ////  abort();

  //  gnr.refineBoundaries(crit);
  //  gnr.refineInternal(crit);

  //  // insert external boundary constraints, if present
  //  // gnr.addConstraint(extPoly, true);
  //  // dbprint("Inserted constraint:", extPoly.size(),
  //  //         sq(extPoly.front() - extPoly.back()));

  ////  // insert internal boundary constraints
  ////  for (uint j=0; j<intPoly.size(); ++j) {
  ////    gnr.addConstraint(intPoly[j], true);
  ////  }

  ////  // erase external and hole triangles
  ////  // cout << "Trimming (" << gnr.nfaces() << ")..." << endl;
  ////  addHole(extPoly, false, gnr);
  ////  for (uint j=0; j<intPoly.size(); ++j) {
  ////    addHole(intPoly[j], true, gnr);
  ////  }

  //  // export to CgMesh
  //  Indices tri;
  //  gnr.triangles(tri);

  //  const PointList<3> & mvtx( gnr.xyzVertices() );
  //  const PointList<3> & mnrm( gnr.xyzNormals() );
  //  if (not tri.empty())
  //    cgm.importMesh( mvtx.size(), mvtx.pointer(), mnrm.pointer(),
  //                   tri.size()/3, &tri[0]);
}

void TrimmedSurf::trimmedGrid(uint maxtri,
                              PointList<2> &pg, Indices &tri) const
{
  // start with rectangular grid
  Vector up, vp;
  base->initGridPattern(up, vp);

  // determine parametric range of external boundary
  if (not extPoly.empty()) {
    Vct2 plo, phi;
    curveBounds(extPoly, plo, phi);

    // reduce range to bounding box of external boundary
    Vector tmp;
    Vector::iterator p1, p2;
    p1 = std::lower_bound(up.begin(), up.end(), plo[0]);
    p2 = std::upper_bound(up.begin(), up.end(), phi[0]);
    if (p1 != up.begin())
      --p1;
    if (p2 != up.end())
      ++p2;
    tmp = Vector(p1, p2);
    up.swap(tmp);

    p1 = std::lower_bound(vp.begin(), vp.end(), plo[1]);
    p2 = std::upper_bound(vp.begin(), vp.end(), phi[1]);
    if (p1 != vp.begin())
      --p1;
    if (p2 != vp.end())
      ++p2;
    tmp = Vector(p1, p2);
    vp.swap(tmp);
  }

  {
    std::set<Real> uset(up.begin(), up.end());
    std::set<Real> vset(vp.begin(), vp.end());
    projectConstraint(extPoly, uset, vset);
    for (uint ic=0; ic<intPoly.size(); ++ic)
      projectConstraint(intPoly[ic], uset, vset);

    almost_equal<Real> pred(1e-3);
    up.clear();
    vp.clear();
    std::unique_copy(uset.begin(), uset.end(), back_inserter(up), pred);
    std::unique_copy(vset.begin(), vset.end(), back_inserter(vp), pred);
  }

  // impose a limit on refinement
  {
    Real freduce = sqrt(0.5*Real(maxtri) / (up.size() * vp.size()));
    if (freduce < 1) {
      Vector tmp;
      interpolate_pattern(up, freduce*up.size(), tmp);
      tmp.swap(up);
      tmp.clear();
      interpolate_pattern(vp, freduce*vp.size(), tmp);
      tmp.swap(vp);
    }
  }

  const int nu = up.size();
  const int nv = vp.size();

#undef LIX
#define LIX(i,j)  (((j)*nu) + (i))

  pg.resize(nu*nv);
  for (int j=0; j<nv; ++j)
    for (int i=0; i<nu; ++i)
      pg[ LIX(i,j) ] = Vct2( up[i], vp[j] );

  // check whether vertices are inside or trimmed away
  std::vector<bool> vInside(nu*nv);
  const int ni = intPoly.size();
  for (int i=0; i<(nu*nv); ++i) {
    const Vct2 & p = pg[i];
    bool include = point_in_polygon(extPoly, p);
    for (int k=0; k<ni; ++k)
      include &= (not point_in_polygon(intPoly[k], p));
    vInside[i] = include;
  }

  // create all grid triangles which have at least 2 vertices inside
  tri.clear();
  uint v[6];
  for (int j=0; j<nv-1; ++j) {
    for (int i=0; i<nu-1; ++i) {

      uint p1 = LIX(i, j);
      uint p2 = LIX(i+1, j);
      uint p3 = LIX(i+1, j+1);
      uint p4 = LIX(i, j+1);

      int b1 = vInside[p1];
      int b2 = vInside[p2];
      int b3 = vInside[p3];
      int b4 = vInside[p4];

      v[0] = p1;
      v[1] = p2;
      v[2] = p3;
      v[3] = p1;
      v[4] = p3;
      v[5] = p4;

      // if just one vertex is outside, try to bring the internal edge
      // close to the probable boundary -- the ordering above is good if
      // p2 or p4 is outside, otherwise, the internal edge is swapped
      int bsum = b1+b2+b3+b4;
      if (bsum == 4) {
        // all vertices inside, assumed common case
        tri.insert(tri.end(), v, v+6);
      } else if (bsum == 3) {
        if (b1 == 0) {
          v[3] = p2;
          tri.insert(tri.end(), v+3, v+6);
        } else if (b3 == 0) {
          v[2] = p4;
          tri.insert(tri.end(), v, v+3);
        } else if (b2 == 0) {
          tri.insert(tri.end(), v+3, v+6);
        } else { // p4 outside
          tri.insert(tri.end(), v, v+3);
        }
      }

      //      else if (bsum > 1) {

      //        // in the case of two vertices outside, we cannot know which edge
      //        // ordering is best, so we simply use all triangles which have 2
      //        // vertices inside
      //        if ((b1+b2+b3) > 1)
      //          tri.insert(tri.end(), v, v+3);
      //        if ((b1+b3+b4) > 1)
      //          tri.insert(tri.end(), v+3, v+6);
      //      }

    }
  }

#undef LIX
}

Real TrimmedSurf::pointToBoundary(const PointList<2> &bnd,
                                  Vct2 &p, Real & dstmin) const
{
  Vct2 pp(p);

  Real arcFoot(-1.0), arcLength = 0;
  const int nb = bnd.size();
  for (int i=1; i<nb; ++i) {
    const Vct2 & src( bnd[i-1] );
    const Vct2 & trg( bnd[i] );
    Vct2 cd(trg - src);
    Real cl = normalize(cd);
    Real t = dot(p - src, cd) / cl;
    arcLength += cl;
    if (t < 0.0 or t > 1.0)
      continue;
    Vct2 foot = (1-t)*src + t*trg;
    Real dst = sq(p - foot);
    if (dst < dstmin) {
      pp = foot;
      dstmin = dst;
      arcFoot = arcLength + t*cl;
    }
  }
  if (arcFoot >= 0)
    p = pp;

  return arcFoot;
}

bool TrimmedSurf::findCorners(const PointList<2> &bnd, Indices &cix,
                              Vector &carc) const
{
  cix.clear();
  carc.clear();
  const Real mincosphi = 0.707;
  const int np = bnd.size();
  if (np < 3)
    return false;

  Real arc = 0.0;
  for (int i=1; i<np-1; ++i) {
    arc += norm(bnd[i] - bnd[i-1]);
    Real cphi = cosarg( bnd[i]-bnd[i-1], bnd[i+1]-bnd[i] );
    if (cphi < mincosphi) {
      cix.push_back(i);
      carc.push_back(arc);
    }
  }

  // first/last point may be a corner
  return (cosarg(bnd[1]-bnd[0], bnd[np-1]-bnd[np-2]) < mincosphi);
}

void TrimmedSurf::fillCorners(uint ibnd, const Indices & bv,
                              const Vector &parc,
                              const Indices &ibound,
                              PointList<2> & pg, Indices &tri) const
{
  Indices cix;
  Vector carc;
  bool startCorner = false;
  const PointList<2> *pbnd = 0;
  if (ibnd == NotFound)
    pbnd = &extPoly;
  else
    pbnd = &(intPoly[ibnd]);
  assert(pbnd != 0);

  const PointList<2> & bnd( *pbnd );
  startCorner = findCorners(bnd, cix, carc);

  const int nbv = parc.size();
  if (startCorner) {

    uint lowestNonZero(NotFound), highestNotMax(NotFound);
    Real nonzero(huge), notmax(-huge);

    // compute full arclength
    Real maxArc = 0.0;
    const int np = bnd.size();
    for (int i=1; i<np; ++i)
      maxArc += norm(bnd[i] - bnd[i-1]);

    // find first projected point which is not at 0
    // and last projected point which is below full arclength
    for (int i=0; i<nbv; ++i) {
      if (ibound[i] != ibnd)
        continue;
      Real arc = parc[i];
      if ((arc > 0) and (arc < nonzero)) {
        nonzero = arc;
        lowestNonZero = i;
      } else if ((arc < maxArc) and (arc > notmax)) {
        highestNotMax = i;
        notmax = arc;
      }
    }

    // create corner triangle
    if (highestNotMax != NotFound and lowestNonZero != NotFound) {
      uint v[3], icv = pg.size();
      pg.push_back( bnd.front() );
      v[0] = bv[highestNotMax];
      v[1] = icv;
      v[2] = bv[lowestNonZero];
      tri.insert(tri.end(), v, v+3);
    }
  }

  const int nc = cix.size();

  for (int j=0; j<nc; ++j) {

    uint highestBelow(NotFound), lowestAbove(NotFound);
    Real sbelow(-huge), sabove(huge);

    for (int i=0; i<nbv; ++i) {
      if (ibound[i] != ibnd)
        continue;
      Real arc = parc[i];
      if ((arc < carc[j]) and (arc > sbelow)) {
        sbelow = arc;
        highestBelow = i;
      } else if ((arc > carc[j]) and (arc < sabove)) {
        sabove = arc;
        lowestAbove = i;
      }
    }

    if (highestBelow != NotFound and lowestAbove != NotFound) {
      uint v[3], icv = pg.size();
      pg.push_back( bnd[cix[j]] );
      v[0] = bv[highestBelow];
      v[1] = icv;
      v[2] = bv[lowestAbove];
      tri.insert(tri.end(), v, v+3);
    }
  }
}

bool TrimmedSurf::inside(const Vct2 &p) const
{
  if (extPoly.empty())
    return true;

  bool inb = point_in_polygon(extPoly, p);
  if (not inb)
    return false;

  const int nhole = intPoly.size();
  for (int i=0; i<nhole; ++i) {
    bool inh = point_in_polygon(intPoly[i], p);
    if (inh)
      return false;
  }

  return true;
}

void TrimmedSurf::addHole(const PointList<2> & poly,
                          bool innerBound, DnMesh & gnr) const
{
  const int n = poly.size();
  for (int i=1; i<n; ++i) {
    const Vct2 & src( poly[i-1] );
    const Vct2 & trg( poly[i] );
    Vct2 crs, px[2];
    crs[0] = trg[1] - src[1];
    crs[1] = src[0] - trg[0];

    px[0] = 0.5*(src + trg + crs);
    px[1] = 0.5*(src + trg - crs);

    for (int k=0; k<2; ++k) {
      Real u = px[k][0];
      if (u <= 0.0 or u >= 1.0)
        continue;
      Real v = px[k][1];
      if (v <= 0.0 or v >= 1.0)
        continue;
      if (innerBound == point_in_polygon(poly, px[k])) {
        uint nkill = gnr.addHole(px[k]);
        if (nkill != 0 and innerBound)
          return;
      }
    }
  }
}

void TrimmedSurf::addHole(const PointList<2> & poly,
                          bool innerBound, UvMapDelaunay & gnr) const
{
  const int n = poly.size();
  for (int i=1; i<n; ++i) {
    const Vct2 & src( poly[i-1] );
    const Vct2 & trg( poly[i] );
    Vct2 crs, px[2];
    crs[0] = trg[1] - src[1];
    crs[1] = src[0] - trg[0];

    px[0] = 0.5*(src + trg + crs);
    px[1] = 0.5*(src + trg - crs);

    for (int k=0; k<2; ++k) {
      Real u = px[k][0];
      if (u <= 0.0 or u >= 1.0)
        continue;
      Real v = px[k][1];
      if (v <= 0.0 or v >= 1.0)
        continue;
      if (innerBound == point_in_polygon(poly, px[k])) {
        uint nkill = gnr.punchHole(px[k]);
        if (nkill != 0) {
          return;
        }
      }
    }
  }
}

bool TrimmedSurf::fromIges(const IgesFile &file, const IgesDirEntry &entry,
                           SurfacePtr baseSurf)
{
  *this = TrimmedSurf();

  if (entry.etype != 144)
    return false;

  IgesTrimmedSurface e144;
  if (not file.createEntity(entry, e144))
    return false;

  // untrimmed base surface
  IgesDirEntry echild, ecurve;
  file.dirEntry(e144.pts, echild);
  if (baseSurf)
    base = baseSurf;
  else
    base = Surface::createFromIges(file, echild);
  if (not base)
    return false;

  // external boundary, if present
  if (e144.pto == 0) {
    extBound.reset();
  } else {
    file.dirEntry(e144.pto, echild);
    IgesCurveOnSurface e142;
    if (not file.createEntity(echild, e142))
      return false;

    // using only parametric space representations
    if (e142.bptr == 0) {
      dbprint("TrimmedSurf requires trim curves in parameter space.");
      return false;
    } else if (e142.sptr != e144.pts) {
      dbprint("TrimmedSurf : Trim curve not on trimmed surface.");
      return false;
    }

    file.dirEntry(e142.bptr, ecurve);
    extBound = AbstractCurve::createFromIges(file, ecurve);
    if (not extBound)
      return false;
  }

  // internal boundaries
  const int nib = e144.n2;
  intBound.resize(nib);
  for (int i=0; i<nib; ++i) {
    file.dirEntry(e144.pti[i], echild);
    IgesCurveOnSurface e142;
    if (not file.createEntity(echild, e142))
      return false;

    // using only parametric space representations
    if (e142.bptr == 0) {
      dbprint("TrimmedSurf requires trim curves in parameter space.");
      return false;
    } else if (e142.sptr != e144.pts) {
      dbprint("TrimmedSurf : Trim curve not on trimmed surface.");
      return false;
    }

    file.dirEntry(e142.bptr, ecurve);
    intBound[i] = AbstractCurve::createFromIges(file, ecurve);
    if (not intBound[i])
      return false;
  }

  if (intBound.size() != (uint) nib) {
    dbprint("Expected ",nib," internal boundaries, found", intBound.size());
    return false;
  }

  applyIgesTrafo(file, entry);

  // map boundary curves into new parameter space [0,1]x[0,1]
  const PolySplineSurf *pss(0);
  const RationalSplineSurf *rss(0);
  pss = dynamic_cast<const PolySplineSurf *>( base.get() );
  rss = dynamic_cast<const RationalSplineSurf *>( base.get() );
  if (pss != 0) {
    if (extBound)
      pss->knotScale( *extBound );
    for (int i=0; i<nib; ++i)
      pss->knotScale( *(intBound[i]) );
  } else if (rss != 0) {
    if (extBound)
      rss->knotScale( *extBound );
    for (int i=0; i<nib; ++i)
      rss->knotScale( *(intBound[i]) );
  }

  meshCurves();

  return true;
}

XmlElement TrimmedSurf::toXml(bool share) const
{
  XmlElement xe("TrimmedSurf");
  xe["nexternal"] = extBound ? "1" : "0";
  xe["ninternal"] = str(intBound.size());
  xe["name"] = name();

  {
    XmlElement xb("BaseSurface");
    xb.append( base->toXml(share) );
    xe.append(std::move(xb));
  }

  if (extBound) {
    XmlElement xb( extBound->toXml(share) );
    xb["trim_boundary"] = "external";
    xe.append(std::move(xb));
  }

  for (uint i=0; i<intBound.size(); ++i) {
    XmlElement xb( intBound[i]->toXml(share) );
    xb["trim_boundary"] = "internal";
    xe.append(std::move(xb));
  }

  return xe;
}

void TrimmedSurf::fromXml(const XmlElement &xe)
{
  *this = TrimmedSurf();

  assert(xe.name() == "TrimmedSurf");
  const uint neb = Int( xe.attribute("nexternal") );
  const uint nib = Int( xe.attribute("ninternal") );
  rename( xe.attribute("name") );

  XmlElement::const_iterator itr, ilast = xe.end();
  for (itr = xe.begin(); itr != ilast; ++itr) {
    if (itr->name() == "BaseSurface") {
      assert(itr->begin() != itr->end());
      base = Surface::createFromXml( *(itr->begin()) );
      if (not base)
        throw Error("No base surface specified for TrimmedSurf.");
    } else if (itr->hasAttribute("trim_boundary")) {
      AbstractCurvePtr acp = AbstractCurve::createFromXml(*itr);
      if (acp) {
        if (itr->attribute("trim_boundary") == "external")
          extBound = acp;
        else
          intBound.push_back( acp );
      }
    }
  }

  if (intBound.size() != nib)
    throw Error("TrimmedSurf : did not find external boundary.");
  if ( (extBound and (neb == 0)) or ((not extBound) and (neb != 0)))
    throw Error("TrimmedSurf : No external boundary in XML rep.");

  meshCurves();
}




