
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
 
#include "wakecomponent.h"
#include "wakesurf.h"
#include "dnrefine.h"
#include <genua/pattern.h>
#include <genua/dbprint.h>

using namespace std;

void WakeComponent::premesh(const PointGrid<2> &)
{
  anyPremesh();
}

void WakeComponent::premesh(const PointList<2> &, const Indices &)
{
  anyPremesh();
}

void WakeComponent::anyPremesh()
{
  clear();

  // adapt() will make constraint node indices meaningless, so
  // clear constraints here
  clearConstraints();

  adapt();
  dbStoreMesh(psf->name()+"Init.msh");

  bFreshMesh = true;
}

void WakeComponent::ppt2mg()
{
  const int nf = TriMesh::nfaces();
  Indices triangles(3*nf);
  for (int i=0; i<nf; ++i) {
    const uint *vi = TriMesh::face(i).vertices();
    for (int k=0; k<3; ++k)
      triangles[3*i+k] = vi[k];
  }

  mg = DnMesh(MeshComponent::psf, DnSpatial);
  mg.importMesh(MeshComponent::ppt, triangles);
}

void WakeComponent::adapt()
{
  // must have exactly one parent component
  assert(nParents() == 1);

  // extract seed points along wing trailing edge
  const MeshComponent & parent( *(MeshComponent::parents.front()) );
  Indices ibound;
  parent.boundary(west, ibound);

  const int nb = ibound.size();
  m_tedge.resize(nb);
  for (int i=0; i<nb; ++i) {
    const Vct2 & uv = parent.parameter(ibound[i]);
    m_tedge[i] = uv[1];
  }

  // generate default wake mesh from seed points
  wakeMesh();

  // wakeMesh updates mg, so we can refine and smooth here
  mg.refine( *(criterion()) );
  mg.smooth(2);
  mg.refine( *(criterion()) );

  // debug
  string pname = parent.surface()->name();
  dbprint("Adapting wake mesh for "+pname, nb, "boundary points.");
  dbStoreMesh(pname+"WakeAdapted.msh");

  // enforce intersection constraints, should there be any
  reconstrain();
  transfer();
}

void WakeComponent::wakeMesh()
{
  // taken 1:1 from testing/wake/initwake.cpp

  TriMesh::clear();

  // surface object must be a wake surface
  WakeSurfPtr wsp;
  wsp = boost::dynamic_pointer_cast<WakeSurf>(MeshComponent::surface());
  assert(wsp);

  // if parent mesh does not exist yet, use another seed
  if (m_tedge.empty())
    m_tedge = equi_pattern(41, 0.0, 1.0);

  wsp->paramap(m_tedge, m_wedge);

  // rebuild wake surface to match wing mesh
  // wsp->reattach(m_vedge);

  // determine typical edge length along trailing edge
  const int nte = m_wedge.size();
  PointList<3> pte(nte);
  for (int i=0; i<nte; ++i)
    pte[i] = wsp->eval(0.0, m_wedge[i]);

  // determine span and TE discretization size
  Real wspan = 0.0;
  for (int i=1; i<nte; ++i)
    wspan += norm(pte[i] - pte[i-1]);
  Real minlen = 1.5 * wspan / (nte - 1);

  // determine approximate streamwise extent
  Real swlen = norm(wsp->eval(0.0, 0.5) - wsp->eval(1.0, 0.5));
  Real sw2span = swlen / wspan;

  // algorithm parameters
  const Real maxlen = MeshComponent::criterion()->maxLength();
  // const Real stretch = MeshComponent::criterion()->maxStretch();
  const int nMinSpanwise = 12;
  const int nMinStreamwise = 20;
  const int nMaxStreamwise = 128;

  // generate parametrization in streamwise direction
  // expansion factor f (streamwise direction) is set such that the streamwise
  // length of the last row of triangles is approximately maxlen.

  // this will not work well if the wake is nor parametrized uniformly in the
  // streamwise direction, so we need to correct for the parametrization
  // difference
  Vct3 Tle = wsp->derive(0.0, 0.5, 1, 0);
  Vct3 Tte = wsp->derive(1.0, 0.5, 1, 0);
  Real upFactor = sqrt( sq(Tle) / sq(Tte) );
  dbprint("Ration of streamwise tangent lengths: ", upFactor);

  const int nsw = min(nMaxStreamwise, max(nMinStreamwise, nte/2));
  Real f = pow(upFactor*sw2span*maxlen/minlen, 1.0/(nsw-1));
  Vector up(nsw);
  expand_pattern(nsw, f, up);

  // create elements
  Indices itriangles;
  Vector vlo(m_wedge), vhi;

  // add first row of vertices
  uint nlo(vlo.size()), nhi;
  uint loffset = 0, hoffset = nlo;
  MeshComponent::ppt.resize(nlo);
  for (uint i=0; i<nlo; ++i)
    MeshComponent::ppt[i] = vct(0.0, vlo[i]);

  Real ncw = nte;
  for (int i=1; i<nsw; ++i) {

    // create a new row of wake mesh vertices
    nlo  = vlo.size();
    ncw /= f;
    nhi  = max(nMinSpanwise, int(ncw));
    nhi += (m_wedge.size() & 1) ^ (nhi & 1);

    interpolate_pattern(vlo, nhi, vhi);

    // append new row of vertices
    for (uint j=0; j<nhi; ++j)
      ppt.push_back( vct(up[i], vhi[j]) );

    // walk along the row and add triangles
    uint ihi(0), ilo(0), vi[3];
    while (ihi < nhi-1 or ilo < nlo-1) {
      vi[0] = hoffset + ihi;
      vi[1] = loffset + ilo;
      if (ilo == nlo-1) {
        ++ihi;
        vi[2] = hoffset + ihi;
      } else if (ihi == nhi-1) {
        ++ilo;
        vi[2] = loffset + ilo;
      } else {
//        Real ll = sq( psf->eval( ppt[vi[0]][0], ppt[vi[0]][1] )
//                    - psf->eval( ppt[loffset+ilo][0], ppt[loffset+ilo][1] ) );
//        Real lh = sq( psf->eval( ppt[vi[1]][0], ppt[vi[1]][1] )
//                    - psf->eval( ppt[hoffset+ihi][0], ppt[hoffset+ihi][1] ) );
//        if (ll < lh) {
//          ++ilo;
//          vi[2] = loffset + ilo;
//        } else {
//          ++ihi;
//          vi[2] = hoffset + ihi;
//        }
        Real tlo = vlo[ilo+1];
        Real thi = vhi[ihi+1];
        if (tlo < thi) {
          ++ilo;
          vi[2] = loffset + ilo;
        } else {
          ++ihi;
          vi[2] = hoffset + ihi;
        }
      }
      itriangles.insert(itriangles.end(), vi, vi+3);
    }

    // start next row downstream of ulo
    vlo.swap(vhi);
    loffset = hoffset;
    hoffset = ppt.size();
  }

  const int nv = ppt.size();
  TriMesh::vtx.resize(nv);
  for (int i=0; i<nv; ++i)
    TriMesh::vtx[i] = wsp->eval(ppt[i][0], ppt[i][1]);

  // import faces
  const int nf = itriangles.size() / 3;
  for (int i=0; i<nf; ++i) {
    const uint *vi = &itriangles[3*i];
    TriMesh::addFace(vi);
  }

  ppt2mg();
}

void WakeComponent::transfer()
{
  MeshComponent::transfer();

  // replace vertices along wing TE
  const int nbp = m_wedge.size();

  WakeSurfPtr wsp;
  wsp = boost::dynamic_pointer_cast<WakeSurf>(MeshComponent::surface());
  assert(wsp);
  SurfacePtr wingSurf = wsp->parentWing();

  // search wake boundary nodes in 3D space
  BSearchTree btree( TriMesh::vertices() );
  int nrepl = 0;
  for (int i=0; i<nbp; ++i) {
    Vct3 pWake = wsp->eval(0.0, m_wedge[i]);
    uint inear = btree.nearest(pWake);
    if (sq(pWake - btree.vertex(inear)) < gmepsilon) {
      Vct3 pWing = wingSurf->eval(0.0, m_tedge[i]);
      TriMesh::vertex(inear) = pWing;
      ++nrepl;
    }
  }

  if (nrepl != nbp)
    dbprint("Did not replace all trailing edge nodes: ", nrepl, "/", nbp);
}


