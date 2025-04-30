
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

#include "uvmapdelaunay.h"
#include "dcmeshcrit.h"
#include "surface.h"
#include "sides.h"
#include <genua/mxmesh.h>
#include <genua/pattern.h>
#include <genua/dbprint.h>

#include <iostream>
using namespace std;

UvMapDelaunay::UvMapDelaunay(SurfacePtr psf)
  : srf(psf), geo(0.0, 1.0), core(geo)
{
  Vector up, vp;
  srf->initGridPattern(up, vp);
  if (up.size() < 4)
    up = equi_pattern(4);
  if (vp.size() < 4)
    vp = equi_pattern(4);

  init(psf, up, vp);
}

UvMapDelaunay::UvMapDelaunay(SurfacePtr psf, const UvMapping &uvmap, Real mergeTol)
  : geo(0.0, 1.0), core(geo)
{
  init(psf, uvmap, mergeTol);
}

UvMapDelaunay::UvMapDelaunay(SurfacePtr psf, const Vector &up,
                             const Vector &vp, Real mergeTol)
  : srf(psf), geo(0.0, 1.0), core(geo), uvm(*psf, up, vp)
{
  Real tmin, tmax;
  uvm.boundaries(tmin, tmax);
  tmin = std::min(0.0, tmin) - 0.125;
  tmax = std::max(1.0, tmax) + 0.125;
  geo.quantRange(tmin, tmax);
  geo.pointTolerance( sq(mergeTol) );
}

void UvMapDelaunay::init(SurfacePtr psf, const UvMapping &uvmap, Real mergeTol)
{
  srf = psf;
  uvm = uvmap;

  Real tmin, tmax;
  uvm.boundaries(tmin, tmax);
  tmin = std::min(0.0, tmin) - 0.125;
  tmax = std::max(1.0, tmax) + 0.125;
  geo.quantRange(tmin, tmax);
  geo.pointTolerance( sq(mergeTol) );
}

void UvMapDelaunay::init(SurfacePtr psf, const Vector &up, const Vector &vp,
                         Real mergeTol)
{
  srf = psf;

  Real tmin, tmax;
  uvm.init(*srf, up, vp);
  uvm.boundaries(tmin, tmax);
  tmin = std::min(0.0, tmin) - 0.125;
  tmax = std::max(1.0, tmax) + 0.125;
  geo.quantRange(tmin, tmax);
  geo.pointTolerance( sq(mergeTol) );
}

void UvMapDelaunay::clear()
{
  core.clear();
  geo.clear();
  puv.clear();
  pxy.clear();
  pnm.clear();
  virtVertices.clear();
}

uint UvMapDelaunay::append(const Vct2 &uv)
{
  assert(srf);
  Vct3 S, Su, Sv;
  srf->plane(uv[0], uv[1], S, Su, Sv);
  pxy.push_back( S );
  pnm.push_back( cross(Su,Sv) );
  puv.push_back(uv);
  return geo.stInsertVertex( uvm.eval(uv) );
}

uint UvMapDelaunay::stAppend(const Vct2 &st)
{
  pxy.push_back( Vct3() );
  pnm.push_back( Vct3() );
  puv.push_back( Vct2() );
  uint nvi = geo.stInsertVertex(st);
  virtVertices.push_back(nvi);
  return nvi;
}

void UvMapDelaunay::twoQuads()
{
  clear();
  uint c1 = append( vct(0.0, 0.0) );
  uint c2 = append( vct(1.0, 0.0) );
  uint c3 = append( vct(1.0, 1.0) );
  uint c4 = append( vct(0.0, 1.0) );
  core.addFace(c1, c2, c3);
  core.addFace(c1, c3, c4);
  core.fixate();
}

void UvMapDelaunay::initEnclosing()
{
  clear();

  // find extremal values generated when inserting corner points
  Real tmin(0.0), tmax(1.0);
  {
    Real u[] = {0.0, 1.0, 1.0, 0.0};
    Real v[] = {0.0, 0.0, 1.0, 1.0};
    for (int k=0; k<4; ++k) {
      Real t = uvm.eval(u[k], v[k]);
      tmin = std::min( tmin, t - 1e-6 );
      tmax = std::max( tmax, t + 1e-6 );
    }
  }

  // the corner points may not generate the most extreme t-values;
  // hence, look for the extremal values of the control points
  Real tbmin, tbmax;
  uvm.boundaries(tbmin, tbmax);
  tmin = std::min( tmin, tbmin ) - 0.1;
  tmax = std::max( tmax, tbmax ) + 0.1;

  uint c1 = stAppend( vct(-0.1, tmin) );
  uint c2 = stAppend( vct(1.1,  tmin) );
  uint c3 = stAppend( vct(1.1, tmax) );
  uint c4 = stAppend( vct(-0.1, tmax) );
  core.addFace(c1, c2, c3);
  core.addFace(c1, c3, c4);
  core.fixate();
}

void UvMapDelaunay::removeOutsideCorners()
{
  sort_unique(virtVertices);
  // uint nf = core.eraseFacesTouching(virtVertices);
  // dbprint("Erased ",nf,"outside faces");

  const int nf = core.nAllFaces();
  for (int i=0; i<nf; ++i) {
    if (not core.face(i).valid())
      continue;
    const uint *vi = core.face(i).vertices();
    bool doErase = false;
    for (int k=0; k<3; ++k)
      doErase |= std::binary_search(virtVertices.begin(),
                                    virtVertices.end(), vi[k]);
    if (doErase)
      core.eatHole(i);
  }

  dbprint(srf->name()," removeOutsideCorners() of ",nf,
          ", faces left:",nfaces());
}

void UvMapDelaunay::enableConstraintSplitting(bool flag)
{
  if (flag)
    core.unsetEdgeFlags( DcEdge::Constrained, DcEdge::NeverSplit );
  else
    core.setEdgeFlags( DcEdge::Constrained, DcEdge::NeverSplit );
}

void UvMapDelaunay::initMesh(const PointList<2> &uv, const Indices &tri)
{
  clear();
  const int n = uv.size();
  geo.reserve(n);
  puv.reserve(n);
  pxy.reserve(n);
  pnm.reserve(n);
  for (int i=0; i<n; ++i)
    append(uv[i]);
  core.addFaces(tri);
  core.fixate();
}

void UvMapDelaunay::initMesh(const Vector &up, const Vector &vp)
{
  const int nu = up.size();
  const int nv = vp.size();

  PointList<2> uv(nu*nv);
  for (int j=0; j<nv; ++j)
    for (int i=0; i<nu; ++i)
      uv[j*nu + i] = Vct2( up[i], vp[j] );

  const int ntri = 2*(nu-1)*(nv-1);
  Indices tri(3*ntri);
  uint p1, p2, p3, p4, fi1, fi2;
  for (int j=0; j<nv-1; ++j) {
    for (int i=0; i<nu-1; ++i) {
      p1 = i + j*nu;
      p2 = i+1 + j*nu;
      p3 = i+1 + (j+1)*nu;
      p4 = i + (j+1)*nu;
      fi1 = 2*(nv-1)*i + 2*j;
      fi2 = fi1 + 1;
      tri[3*fi1+0] = p1; tri[3*fi1+1] = p2; tri[3*fi1+2] = p3;
      tri[3*fi2+0] = p1; tri[3*fi2+1] = p3; tri[3*fi2+2] = p4;
    }
  }

  initMesh(uv, tri);
}

uint UvMapDelaunay::insertConstraint(const Indices &cvi,
                                     int edgeflags, bool legalizeEdges)
{
  uint ninsert = core.insertConstraint( cvi, edgeflags, legalizeEdges );
#ifndef NDEBUG
  if (ninsert != cvi.size() ) {
    dbgDump(srf->name()+"InsertFailure");
    assert(!"Constraint insertion failed.");
  }
#endif
  return ninsert;
}

uint UvMapDelaunay::insertConstraint(const PointList<2> &uvc,
                                     int edgeflags, bool legalizeEdges)
{
  Indices cvi;
  return insertConstraint(uvc, cvi, edgeflags, legalizeEdges);
}

uint UvMapDelaunay::insertConstraint(const PointList<2> &uvc, Indices &cvi,
                                     int edgeflags, bool legalizeEdges)
{
  const int np = uvc.size();
  if (np == 0)
    return 0;

  cvi.clear();
  cvi.resize(np, NotFound);
  for (int i=0; i<np-1; ++i)
    cvi[i] = append( uvc[i] );

  if ( sq(uvc.back() - uvc.front()) <= geo.pointTolerance() )
    cvi[np-1] = cvi[0];
  else
    cvi[np-1] = append( uvc.back() );

  uint ninsert = core.insertConstraint( cvi, edgeflags, legalizeEdges );
#ifndef NDEBUG
  if (ninsert != cvi.size() ) {
    dbgDump(srf->name()+"InsertFailure");
    assert(!"Constraint insertion failed.");
  }
#endif
  return ninsert;
}

uint UvMapDelaunay::refineBoundaries(DcMeshCritBase &c)
{
  const PointList<2> & pst( geo.stVertices() );
  c.assign(srf.get(), &puv, &pst, &pxy, &pnm);
  const int npass = c.npass();
  uint nref = 0;
  for (int j=0; j<npass; ++j) {
    uint nsplit = 0;
    const int nface = core.nAllFaces();
    for (int i=0; i<nface; ++i) {
      if (not core.face(i).valid())
        continue;
      const uint *vi = core.face(i).vertices();
      bool didSplit = false;
      for (int k=0; k<3; ++k) {
        uint s = vi[k];
        uint t = vi[ (k+1)%3 ];
        if (c.splitEdge(s,t)) {
          DcEdge *pe = core.findEdge(s,t);
          if (pe->degree() == 1) {
            uint cin = append( 0.5*(puv[s] + puv[t]) );
            core.splitEdge(pe, cin);
            didSplit = true;
            ++nsplit;
          }
        }
        if (didSplit)
          break;
      } // k-edge
    } // i-face

    nref += nsplit;
    if (nsplit < 1)
      break;

  } // j-pass

  return nref;
}

uint UvMapDelaunay::refineInternal(DcMeshCritBase &c)
{
  // clear list of vertices which are injected into constrained edges
  core.verticesOnConstraints().clear();

  const PointList<2> & pst( geo.stVertices() );
  c.assign(srf.get(), &puv, &pst, &pxy, &pnm);
  const int npass = c.npass();
  uint nref(0), nskip = c.nSkipSmooth();
  for (int j=0; j<npass; ++j) {
    uint nsplit = 0;
    const int nface = core.nAllFaces();
    for (int i=0; i<nface; ++i) {
      const DcFace & fi( core.face(i) );
      if (puv.size() > c.maxNodes())
        break;
      if (not fi.valid())
        continue;

      const uint *vi = fi.vertices();
      int esp = c.splitFace(vi);
      if (esp == DcMeshCrit::TooSmall)
        continue;

      //      // if single-triangle geometry says don't split, it may still be necessary
      //      // to split in order to achieve moderate area growth ratio
      //      if (esp == DcMeshCrit::NoSplit) {
      //        if (c.maxGrowthRatio() != NotDouble) {
      //          for (int k=0; k<3; ++k) {
      //            DcEdge *pe = core.findEdge( fi.esource(k), fi.etarget(k) );
      //            if (pe != 0 and pe->degree() == 2) {
      //              uint fopp = pe->otherFace(i);
      //              assert(fopp != NotFound); // since degree == 2
      //              esp = c.checkGrowthRatio(vi, core.face(fopp).vertices());
      //              if (esp != DcMeshCrit::NoSplit)
      //                break;
      //            } // valid edge
      //          } // edge loop
      //        }
      //      }

      if (esp == DcMeshCrit::NoSplit)
        continue;

      if ( (esp >= DcMeshCrit::InsertCircumCenter) and
           (esp <= DcMeshCrit::InsertCircumCenterE3) ) {
        Vct2 uvc;
        if (uvCircumCenter(i, uvc)) {
          int itc = append( uvc );
          nsplit += (core.insertVertex(itc) != DelaunayCore::NotInserted);
          continue;
        } else {
          dbprint("[i] Failed to project circumcenter at "+str(uvc));

          // if longest edge indicator embedded, fall through to SplitEdge
          if (esp > DcMeshCrit::InsertCircumCenter)
            esp = esp - DcMeshCrit::InsertCircumCenterE1 + DcMeshCrit::SplitEdge1;
        }
      }

      if (esp <= DcMeshCrit::SplitEdge3) {
        int ke = esp - DcMeshCrit::SplitEdge1;
        uint s = fi.esource(ke);
        uint t = fi.etarget(ke);
        DcEdge *pe = core.findEdge(s,t);
        if (pe != 0) {
          if (pe->degree() == 2) {
            uint cin = append( 0.5*(puv[s] + puv[t]) );
            int inv = core.insertVertex(cin);
            // int inv = core.splitEdge(pe, cin);
            nsplit += (inv != DelaunayCore::NotInserted);
          } else {
            // pe is a boundary edge, split explicitly
            uint cin = append( 0.5*(puv[s] + puv[t]) );
            nsplit += core.splitEdge(pe, cin);
          }
        }
      } else if (esp == DcMeshCrit::InsertTriCenter) {
        Vct2 uvc = (puv[vi[0]] + puv[vi[1]] + puv[vi[2]]) / 3.0;
        int itc = append(uvc);
        nsplit += (core.insertVertex(itc) != DelaunayCore::NotInserted);
      }


    } // i-face

    nref += nsplit;
    if (nsplit < 3)
      break;

    // smooth every nskip'th pass
    if ((j+1)%nskip == 0)
      smooth(2, 0.25);

    if (puv.size() > c.maxNodes())
      break;
  } // j-pass

  return nref;
}

void UvMapDelaunay::smooth(uint niter, Real omega)
{
  // vertex-to-face connectivity
  ConnectMap v2f;
  const int nvx = puv.size();
  core.vertexMap(nvx, v2f);

  const int staticflag = DcEdge::Constrained |
      DcEdge::Feature | DcEdge::SurfaceIntersection;
  std::vector<bool> cvx(nvx, false);
  core.constrainedVertices(cvx, staticflag);

  for (uint iter=0; iter<niter; ++iter) {
    for (int i=0; i<nvx; ++i) {
      uint ki = (iter & 1) ? (nvx-1-i) : i;
      if (not cvx[ki])
        smoothVertex(ki, v2f.size(ki), v2f.first(ki), omega);
    }
  }

  geo.remapFaces(core);
}

void UvMapDelaunay::smoothVertex(uint iv, uint nnb,
                                 const uint *nbf, Real omega)
{
  if (nnb == 0 or omega <= 0.0)
    return;

  // determine barycenter bcu in (u,v)-space and bcx in (x,y,z)-space
  Vct3 bcx;
  Vct2 bcu;
  Real area(0);
  for (uint i=0; i<nnb; ++i) {
    assert(core.face(nbf[i]).valid());
    // Real cbeta = core.face( nbf[i] ).cosApexAngle(pxy, iv);
    // Real wgt = std::pow(cbeta+1.0, 3.0); // 1.0 / ( gmepsilon + (1.0 - cbeta) );
    const uint *vi = core.face( nbf[i] ).vertices();
    const Vct3 & p0( pxy[vi[0]] );
    const Vct3 & p1( pxy[vi[1]] );
    const Vct3 & p2( pxy[vi[2]] );
    Real ar = 0.5*norm(cross(p1-p0, p2-p0));
    assert(ar > 0);
    bcx += ar/3. * (p0 + p1 + p2);
    area += ar;
    const Vct2 & q0( puv[vi[0]] );
    const Vct2 & q1( puv[vi[1]] );
    const Vct2 & q2( puv[vi[2]] );
    bcu += ar/3. * (q0 + q1 + q2);
  }

  assert(area > 0);
  bcu /= area;
  bcx /= area;

  Vct2 uv, st;
  bool legalMove = true;
  do {

    Vct3 pnew = (1.0 - omega)*pxy[iv] + omega*bcx;

    // project barycenter onto surface to find (u,v)
    uv = (1.0 - omega)*puv[iv] + omega*bcu;
    uv[0] = clamp(uv[0], 0.0, 1.0);
    uv[1] = clamp(uv[1], 0.0, 1.0);
    srf->project( pnew, uv );
    st = uvm.eval(uv);

    // determine if all the triangles to be modified will remain legal
    legalMove = true;
    for (uint i=0; i<nnb; ++i) {
      const uint *vi = core.face( nbf[i] ).vertices();
      int ori = geo.orientChanged( vi, iv, st );
      legalMove &= (ori == DcGeometry::CounterClockwise);
    }

    // reduce smoothing parameter, abort smoothing operation if omega
    // becomes too small to be worthwhile
    omega *= 0.5;
    if (omega < 0.125)
      return;

  } while (not legalMove);

  assert(legalMove);

  Vct3 S, Su, Sv;
  srf->plane(uv[0], uv[1], S, Su, Sv);
  pxy[iv] = S;
  pnm[iv] = cross(Su,Sv);
  puv[iv]= uv;
  geo.stVertex(iv) = st;
}

bool UvMapDelaunay::uvCircumCenter(uint fi, Vct2 &uv) const
{
  const uint *vi = core.face(fi).vertices();

  // circumcenter in (s,t)-space
  Vct2 st = geo.circumCenter( vi );

  // compute guess to start projection
  uv = geo.circumCenter( puv, vi );
  uv[0] = clamp(uv[0], 0.0, 1.0);
  uv[1] = clamp(uv[1], 0.0, 1.0);

  const Real tol = 1e-4;
  return uvm.invert(st, uv, tol);
}

uint UvMapDelaunay::punchHole(const Vct2 &phole)
{
  dbprint("[i] Punching hole at ",phole);
  uint v = append(phole);
  uint fnear = NotFound;
  int loc = geo.locateTriangle(core, v, fnear);
  if (loc == DcGeometry::Inside) {
    uint n = core.eatHole(fnear);
    core.eraseDetachedEdges();
    dbprint("[i] Eliminated triangles: ",n);
    return n;
  } else {
    dbprint("[i] No triangles to erase here.");
    return 0;
  }
}

void UvMapDelaunay::sortedBoundary(Indices &bvx) const
{
  bvx.clear();
  const int nv = pxy.size();
  std::vector<bool> bflag( nv, false );
  core.boundaryVertices( bflag );
  for (int i=0; i<nv; ++i) {
    if (bflag[i] and whichside(puv[i]) != none) {
      bvx.push_back(i);
    }
  }

  // sort along boundary
  CcwCompare cmp( puv );
  std::sort(bvx.begin(), bvx.end(), cmp);
}

void UvMapDelaunay::dbgDump(const std::string & fname) const
{
  Indices tri, lns;
  core.triangles(tri);
  core.constrainedEdges(lns);
  {
    MxMesh mx;
    mx.appendNodes( xyzVertices() );
    mx.appendSection(Mx::Tri3, tri);
    mx.appendSection(Mx::Line2, lns);
    mx.toXml(true).zwrite(fname + "_xy.zml");
  }

  {
    const PointList<2> & pst(geo.stVertices());
    PointList<3> psm(pst.size());
    for (uint i=0; i<psm.size(); ++i) {
      psm[i] = vct(  pst[i][0], pst[i][1], 0.0 );
      // cout << i << " uv " << puv[i] << " st " << pst[i] << endl;
    }

    MxMesh mx;
    mx.appendNodes( psm );
    mx.appendSection(Mx::Tri3, tri);
    mx.appendSection(Mx::Line2, lns);
    mx.toXml(true).zwrite(fname + "_st.zml");
  }

  {
    PointList<3> psm(puv.size());
    for (uint i=0; i<psm.size(); ++i) {
      psm[i] = vct(  puv[i][0], puv[i][1], 0.0 );
      // cout << i << " uv " << puv[i] << " st " << pst[i] << endl;
    }

    MxMesh mx;
    mx.appendNodes( psm );
    mx.appendSection(Mx::Tri3, tri);
    mx.appendSection(Mx::Line2, lns);
    mx.toXml(true).zwrite(fname + "_uv.zml");
  }
}


