
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
 
#include "dnmesh.h"
#include "dnrefine.h"
#include "planarmesh.h"

using namespace std;

void PlanarMesh::init(const PointList<3> & pts)
{
  const int n = pts.size();
  psf.reset( new PlaneSurface("PlanarMeshSurface") );
  psf->init(pts);
  
  cbound.resize(n);
  for (int i=0; i<n; ++i)
    psf->project(pts[i], cbound[i], 0, 0);
}

uint PlanarMesh::punch(const PointList<3> & h)
{
  if (not psf)
    return 0;
  
  const int n = h.size();
  PointList<2> chole(n);
  Vct2 hmarker;
  for (int i=0; i<n; ++i) {
    psf->project(h[i], chole[i], 0, 0);
    hmarker += chole[i];
  }
  hmarker *= 1.0 / n;
  
  holemarker.push_back(hmarker);
  choles.push_back(chole);
  return choles.size()-1;
}

uint PlanarMesh::enforce(const PointList<3> & h)
{
  if (not psf)
    return 0;
  
  const int n = h.size();
  PointList<2> con(n);
  for (int i=0; i<n; ++i) 
    psf->project(h[i], con[i], 0, 0);
  
  cforce.push_back(con);
  return cforce.size()-1;
}

void PlanarMesh::delaunay(Real maxaspect, int npass)
{
  if (not psf)
    return;
  
  // mesh quality criterion
  Real maxlen(0.0), minlen(huge);
  const int np = cbound.size();
  for (int i=1; i<np; ++i) {
    Real len = norm( psf->eval(cbound[i][0], cbound[i][1]) 
        - psf->eval(cbound[i-1][0], cbound[i-1][1]) );
    maxlen = max(maxlen, len);
    minlen = min(minlen, len);
  }
  
  // initialize mesh generator
  DnMesh gnr(psf, DnSpatial);
  gnr.init(10,10);
  gnr.addConstraint(cbound);
    
  const int nh = choles.size();
  for (int i=0; i<nh; ++i) {
    if (not choles[i].empty())
      gnr.addConstraint(choles[i]);
  }
  
  const int nc = cforce.size();
  for (int i=0; i<nc; ++i) {
    if (not cforce[i].empty())
      gnr.addConstraint(cforce[i]);
  }
  
  DnRefineCriterion mc(&gnr);
  mc.setCriteria(maxlen, minlen, PI, maxaspect);
  for (int i=0; i<npass; ++i) {
    gnr.refine(mc);
    gnr.smooth(3, 0.5);
  }
  
  // eat away external triangles
  gnr.addHole(vct(0.01,0.01));
  
  for (int i=0; i<nh; ++i) {
    if (not choles[i].empty())
      gnr.addHole(holemarker[i]);
  }
  
  // export result mesh
  PointList<2> qts;
  Indices qtri;
  gnr.exportMesh(qts, qtri);
  
  const int nep = qts.size();
  PointList<3> pts(nep);
  for (int i=0; i<nep; ++i)
    pts[i] = psf->eval(qts[i][0], qts[i][1]);
    
  msh.clear();
  msh.importMesh(pts, qtri);
  msh.cleanup();
  msh.dropTriStars();
}








