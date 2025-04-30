
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
 
#include "multisurfprojector.h"

#include <iostream>
using namespace std;

MultiSurfProjector::MultiSurfProjector() : pjtol(1e-6), uvtol(1e-6)
{
  unity(c2s);
  unity(s2c);
}

void MultiSurfProjector::transformation(const Trafo3d & t)
{
  // t is the transformation applied to CAD geometry to move it into
  // point/model space, s2c is its inverse
  t.matrix(c2s);
  Trafo3d::inverse(c2s, s2c);
}

void MultiSurfProjector::append(SurfacePtr psf, const PointList<2> & uv)
{
  if (not psf)
    return;

  surfaces.push_back(psf);
  parpos.insert(parpos.end(), uv.begin(), uv.end());

  Indices idx(uv.size(), surfaces.size()-1);
  surfidx.insert(surfidx.end(), idx.begin(), idx.end());
}

void MultiSurfProjector::append(SurfacePtr psf)
{
  if (not psf)
    return;

//  // debug
//  PointGrid<2> pgrid;
//  psf->initGrid(100, 0.1, rad(40.), pgrid);
//  PointList<2> plist;
//  plist.insert(plist.end(), pgrid.begin(), pgrid.end());
//  append(psf, plist);

  Vector up, vp;
  psf->initGridPattern(up, vp);

  const int nu = up.size();
  const int nv = vp.size();
  PointList<2> uv(nu*nv);

  for (int j=0; j<nv; ++j)
    for (int i=0; i<nu; ++i)
      uv[j*nu + i] = vct(up[i], vp[j]);

  append(psf, uv);
}

void MultiSurfProjector::buildTree()
{
  const int n = parpos.size();
  PointList<3> pts(n);

#pragma omp parallel for schedule(static)
  for (int i=0; i<n; ++i) {
    const Vct2 & q( parpos[i] );
    const SurfacePtr & psf( surfaces[surfidx[i]] );
    pts[i] = psf->eval( q[0], q[1] );
  }

  btree = BSearchTree(pts);
}

void MultiSurfProjector::clear()
{
  unity(c2s);
  unity(s2c);
  surfaces.clear();
  surfidx.clear();
  parpos.clear();
  btree = BSearchTree();
}

Vct3 MultiSurfProjector::project(const Vct3 & p) const
{
  // p is in model space, transform point to CAD surface space
  Vct3 pcad(p);
  Trafo3d::transformPoint(s2c, pcad);

  // debug
  cout << "Incoming: " << p << endl << "CAD space: " << pcad << endl;

  uint inear = btree.nearest(pcad);
  SurfacePtr psf = surfaces[surfidx[inear]];

//  // debug
//  {
//    const int np = btree.size();
//    uint ibest(0);
//    Real dstmin(huge);
//    for (int i=0; i<np; ++i) {
//      Real dst = sq(btree.vertex(i) - pcad);
//      if (dst < dstmin) {
//        dstmin = dst;
//        ibest = i;
//      }
//    }
//    cout << "Linear search: " << ibest << " at " << btree.vertex(ibest) << endl;
//    cout << "Tree search:   " << inear << " at " << btree.vertex(inear) << endl;
//  }

  // debug
  Vct3 tmp = btree.vertex(inear);
  // Trafo3d::transformPoint(c2s, tmp);
  cout << "Nearest vertex: " << tmp << " dst " << norm(tmp - pcad) << endl;

  Vct2 q = parpos[inear];

  cout << "Projection init: " << q << " surface: "
       << psf->eval(q[0], q[1]) << endl;
  bool pjok = psf->project(pcad, q, pjtol, uvtol);

  cout << "Projection status: " << pjok << " result: " << q << endl;


  // evaluate result and transform into model space
  pcad = psf->eval(q[0], q[1]);
  Trafo3d::transformPoint(c2s, pcad);

  // debug
  cout << "Projected: " << pcad << " dst " << norm(pcad - p) << endl;

  return pcad;
}
