
/* ------------------------------------------------------------------------
 * project:    Surf
 * file:       frameprojector.cpp
 * begin:      2011
 * copyright:  (c) 2011 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Search data structure for fitting plane frames to discretized geometry
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#include "frameprojector.h"
#include <surf/product.h>
#include <surf/producttree.h>
#include <genua/cgmesh.h>
#include <genua/timing.h>
#include <genua/plane.h>

#include <iostream> // debugging

using namespace std;

FrameProjector::FrameProjector() : mincosphi(0)
{
  c2s = Mtx44::identity();
  s2c = Mtx44::identity();
}

void FrameProjector::clear()
{
  c2s = Mtx44::identity();
  s2c = Mtx44::identity();
  trees.clear();
}

void FrameProjector::transformation(const Trafo3d & t)
{
  // t is the transformation applied to CAD geometry to move it into
  // point/model space, s2c is its inverse
  t.matrix(c2s);
  Trafo3d::inverse(c2s, s2c);
}

void FrameProjector::buildTree(const Product & prod)
{
  Wallclock clk;
  trees.clear();

  typedef std::pair<CgMeshPtr,Mtx44f> MSet;
  std::vector<MSet> cgm;

  // collect meshes and their respective transformations
  std::vector<ProductTreePtr> stack;
  stack.push_back( prod.rootNode() );
  while (not stack.empty()) {
    ProductTreePtr ptp = stack.back();
    stack.pop_back();
    CgMeshPtr cgr = ptp->cgRep();
    if (cgr) {
      Mtx44f tfm;

      // do not use node transformation for root node, because that transform
      // will be modified interactively and represented by matrix s2c
      if (ptp.get() == prod.rootNode().get())
        unity(tfm);
      else
        ptp->currentTransform().matrix(tfm);
      cgm.push_back( make_pair(cgr,tfm) );
    } else {
      for (uint i=0; i<ptp->nchildren(); ++i)
        stack.push_back(ptp->child(i));
    }
  }

  Vct3f plo, phi;
  plo = std::numeric_limits<float>::max();
  phi = -plo;

  const int ncg = cgm.size();
  trees.clear();
  trees.resize(ncg);
  for (int i=0; i<ncg; ++i) {
    const CgMesh & cgr( *(cgm[i].first) );
    if (cgr.vertices().size() == 0)
      continue;
    trees[i].merge( *(cgm[i].first), cgm[i].second );
    if (trees[i].empty())
      continue;
    const TriTree::DopType & bb( trees[i].dop(0) );
    for (int k=0; k<3; ++k) {
      plo[k] = std::min( plo[k], bb.minCoef(k) );
      phi[k] = std::max( phi[k], bb.maxCoef(k) );
    }
  }

  // scene radius
  mradius = std::sqrt( std::max( sq(plo), sq(phi) ) );
  cout << "Scene radius: " << mradius << endl;

  clk.stop();
  cout << "Projector - tree construction: " << clk.elapsed() << endl;
}

bool FrameProjector::intersect(const Plane & pln,
                               FrameProjector::SegmentArray & seg) const
{
  // determine two directions in the plane
  Vct3 pn = pln.vector();
  Vct3 po = pln.offset() * pn;  // point on plane

  // determine two directions in the plane
  Vct3 xcn = cross( Vct3(1.0, 0.0, 0.0), pn );
  Vct3 ycn = cross( Vct3(0.0, 1.0, 0.0), pn );
  Vct3 zcn = cross( Vct3(0.0, 0.0, 1.0), pn );

  Real sqx = sq(xcn);
  Real sqy = sq(ycn);
  Real sqz = sq(zcn);
  Vct3 axu, axv;
  if (sqx > sqy and sqx > sqz)
    axu = Vct3(xcn);
  else if (sqy > sqx and sqy > sqz)
    axu = Vct3(ycn);
  else
    axu = Vct3(zcn);
  axv = cross(Vct3(pn), axu);

  // scale directions with scene radius
  assert(mradius != 0);
  axu *= float(mradius) / norm(axu);
  axv *= float(mradius) / norm(axv);

  return intersect(po, axu, axv, seg);
}

bool FrameProjector::intersect(const Vct3 &po, const Vct3 &pu, const Vct3 &pv,
                               SegmentArray &seg) const
{
  // transform plane vectors into mesh space
  Vct3f to(po), axu(pu), axv(pv);
  Trafo3d::transformPoint( s2c, to );
  Trafo3d::transformDirection( s2c, axu);
  Trafo3d::transformDirection( s2c, axv);

  // debug
  cout << "origin " << to << endl;
  cout << "axu " << axu << endl;
  cout << "axv " << axv << endl;

  seg.clear();

  // generate two triangles covering the capture rectangle
  PointList<3,float> pvx(4);
  pvx[0] = Vct3f(to) - axu - axv;
  pvx[1] = Vct3f(to) + axu - axv;
  pvx[2] = Vct3f(to) + axu + axv;
  pvx[3] = Vct3f(to) - axu + axv;

  const uint itri[] = {0, 1, 2, 0, 2, 3};
  Indices ptri(itri, itri+6);

  // generate nominal tree
  TriTree planeTree(pvx, ptri);
  TriTree::IndexPairArray pairs;
  const int ncg = trees.size();
  for (int i=0; i<ncg; ++i) {

    // determine pairs of intersecting triangles
    pairs.clear();
    trees[i].intersect(planeTree, pairs, true);

    // compute intersection segments
    PointList<3,float> sf;
    trees[i].segments(planeTree, pairs, sf);
    seg.insert(seg.end(), sf.begin(), sf.end());
  }

  // debug
  cout << seg.size() / 2 << " segments." << endl;

  return (seg.size() > 0);
}

Vct3 FrameProjector::lproject(const SegmentArray & segments,
                              const Vct3 & pt) const
{
  // transform into mesh space
  Vct3f pc(pt);
  Trafo3d::transformPoint(s2c, pc);

  const int ns = segments.size() / 2;
  Vct3f foot, pj(pc);
  float dstmin = huge;
  for (int i=0; i<ns; ++i) {

    const Vct3f & src( segments[2*i+0] );
    const Vct3f & trg( segments[2*i+1] );

    Vct3f d(trg - src);
    float t = dot( pc-src, d ) / dot(d, d);
    t = clamp(t, 0.0f, 1.0f);
    foot = (src + t*d);

    float dst = sq(pc - foot);
    if (dst < dstmin) {
      pj = foot;
      dstmin = dst;
    }
  }

  // back to model space
  Trafo3d::transformPoint(c2s, pj);
  return Vct3(pj);
}

Vct3 FrameProjector::lproject(const SegmentArray & segments,
                              const Vct3 & pt, const Vct3 &) const
{
  return lproject(segments, pt);

  /*

  // transform into mesh space
  Vct3 pc(pt), pnc;
  Trafo3d::transformPoint(s2c, pc);

  // rotate normal
  for (int k=0; k<3; ++k)
    pnc[k] = s2c(k,0)*pn[0] + s2c(k,1)*pn[1] + s2c(k,2)*pn[2];

  const int ns = segments.size();
  Vct3 foot, pj(pc);
  Real dstmin = huge;
  for (int i=0; i<ns; ++i) {
    foot = segments[i].projection(pc);
    Real dst = sq(pc - foot);
    if (dst < dstmin) {
      Vct3 ntri = ftree.face(segments[i].iface).normal();
      if ( fabs(cosarg(pnc, ntri)) > mincosphi ) {
        pj = foot;
        dstmin = dst;
      }
    }
  }

  // back to model space
  Trafo3d::transformPoint(c2s, pj);
  return pj;

  */
}

void FrameProjector::modelSpaceSegments(const SegmentArray & segments,
                                        PointList<3> & pts) const
{
  const int n = segments.size();
  pts.resize(n);
  for (int i=0; i<n; ++i) {
    pts[i] = Vct3(segments[i]);
    Trafo3d::transformPoint(c2s, pts[i]);
  }
}
