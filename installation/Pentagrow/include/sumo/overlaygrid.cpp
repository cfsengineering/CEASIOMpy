/* ------------------------------------------------------------------------
 * file:       igesgrid.cpp
 * copyright:  (c) 2010 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Display of a single spline surface
 * ------------------------------------------------------------------------ */

#include "overlaygrid.h"
#include "glew.h"
#include <surf/igesdirentry.h>
#include <surf/polysplinesurf.h>
#include <surf/linearsurf.h>
#include <surf/igesfile.h>
#include <surf/igesentity.h>
#include <surf/iges124.h>
#include <surf/iges144.h>
#include <surf/stepfile.h>
#include <surf/step_ap203.h>
#include <genua/trimesh.h>

using namespace std;

uint OverlayGrid::tesspu = 2;
uint OverlayGrid::tesspv = 2;
bool OverlayGrid::bDrawPolygons = true;

bool OverlayGrid::fromIges(const IgesFile & file, const IgesDirEntry & entry)
{
  // set blank flag
  bVisible = (entry.blank != 1);

  psf.reset();
  if (entry.etype == 128) {
    PolySplineSurf *psurf = new PolySplineSurf();
    if (psurf->fromIges(file, entry)) {
      tesselate(*psurf);
      psf.reset(psurf);
      applyIgesTrafo(file, entry);
      return true;
    }
  } else if (entry.etype == 118) {
    LinearSurf *psurf = new LinearSurf();
    if (psurf->fromIges(file, entry)) {
      tesselate(*psurf);
      psf.reset(psurf);
      applyIgesTrafo(file, entry);
      return true;
    }
  }

  return false;
}

bool OverlayGrid::fromStep(const StepFile & file, const StepEntity *ep)
{
  psf.reset();

  const StepBSplineSurfaceWithKnots *spl(0);
  spl = dynamic_cast<const StepBSplineSurfaceWithKnots*>( ep );
  if (spl != 0) {
    PolySplineSurf *psurf = new PolySplineSurf;
    if (psurf->fromStep(file, spl)) {
      tesselate(*psurf);
      psf.reset(psurf);
      return true;
    }
  }

  return false;
}

void OverlayGrid::applyIgesTrafo(const IgesFile &file, const IgesDirEntry &dir)
{
  // chained transformation
  Mtx44f trafo;
  unity(trafo);

  // extract transformation matrix recursively --
  // transformation matrix entity may be transformed itself
  bool haveTrafo = false;
  int dtf = dir.trafm;
  while (dtf != 0) {

    IgesDirEntry entry;
    file.dirEntry(dtf, entry);
    IgesEntityPtr eptr = file.createEntity(entry);
    IgesTrafoMatrix itf;
    Mtx44f tmp;
    unity(tmp);
    if (IgesEntity::as(eptr, itf)) {
      for (int j=0; j<3; ++j) {
        tmp(j,3) = itf.translation(j);
        for (int i=0; i<3; ++i)
          tmp(i,j) = itf.rotation(i,j);
      }

      // enchain
      trafo = tmp * trafo;
      haveTrafo = true;
    }

    // break infinite recursion
    if (entry.trafm == dtf)
      break;
    dtf = entry.trafm;
  }

  if (haveTrafo) {

    if (psf) {
      Mtx44 rft;
      std::copy(trafo.begin(), trafo.end(), rft.begin());
      psf->setTrafoMatrix(rft);
      psf->apply();
    }

    const int n = pgrid.size();
    for (int i=0; i<n; ++i) {
      Vct3f p = pgrid[i];
      for (int k=0; k<3; ++k)
        pgrid[i][k] =   trafo(k,0)*p[0] + trafo(k,1)*p[1]
                        + trafo(k,2)*p[2] + trafo(k,3);
    }
    for (int i=0; i<n; ++i) {
      Vct3f p = ngrid[i];
      for (int k=0; k<3; ++k)
        ngrid[i][k] = trafo(k,0)*p[0] + trafo(k,1)*p[1] + trafo(k,2)*p[2];
    }

    // need to check that the normal direction is consistent with the
    // quad vertex ordering. if not, flip normals.
    if (pgrid.nrows() > 1 and pgrid.ncols() > 1) {
      Vct3f q0n = cross(pgrid(1,1)-pgrid(0,0), pgrid(0,1)-pgrid(1,0));
      if ( dot(q0n, ngrid(0,0)) < 0.0 ) {
        for (int i=0; i<n; ++i)
          ngrid[i] *= -1.0f;
      }
    }
  }
}

void OverlayGrid::triangles(uint nr, uint nc, Indices & elm)
{
  elm.clear();
  if (nr < 2 or nc < 2)
    return;

  elm.resize( 6*(nr-1)*(nc-1) );
  uint *v = &elm[0];
  uint p1, p2, p3, p4;
  for (uint i=0; i<nr-1; ++i) {
    for (uint j=0; j<nc-1; ++j) {
      p1 = i + j*nr;
      p2 = i+1 + j*nr;
      p3 = i+1 + (j+1)*nr;
      p4 = i + (j+1)*nr;
      if (i%2 == j%2) {
        v[0] = p1; v[1] = p2; v[2] = p3;
        v[3] = p1; v[4] = p3; v[5] = p4;
      } else {
        v[0] = p1; v[1] = p2; v[2] = p4;
        v[3] = p2; v[4] = p3; v[5] = p4;
      }
      v += 6;
    }
  }
}

void OverlayGrid::outline(uint nr, uint nc, Indices & lns)
{
  lns.clear();
  if (nr < 2 or nc < 2)
    return;

  // left side
  lns.reserve( 2*(nr + nc) - 1 );
  for (uint i=0; i<nr; ++i)
    lns.push_back( i );

  // lower side
  for (uint j=1; j<nc-1; ++j)
    lns.push_back( j*(nr) + (nr-1) );

  // right side
  for (uint i=0; i<nr; ++i)
    lns.push_back( (nc-1)*nr + (nr-1-i) );

  // upper side, i = 0
  for (uint j=1; j<nc; ++j)
    lns.push_back( (nc-1-j)*(nr) + 0 );

}

void OverlayGrid::tesselate(const PolySplineSurf & surf)
{
  surf.simpleMesh(pgrid, ngrid, tesspu, tesspv);
  triangles(pgrid.nrows(), pgrid.ncols(), elements);
  outline(pgrid.nrows(), pgrid.ncols(), lines);
  boundingBox();
}

void OverlayGrid::tesselate(const LinearSurf & surf)
{
  surf.simpleMesh(pgrid, ngrid, tesspu, tesspv);
  triangles(pgrid.nrows(), pgrid.ncols(), elements);
  outline(pgrid.nrows(), pgrid.ncols(), lines);
  boundingBox();
}

void OverlayGrid::boundingBox()
{
  // determine bounding box
  bblo = std::numeric_limits<float>::max();
  bbhi = -bblo;
  const int nv = pgrid.size();
  for (int i=0; i<nv; ++i) {
    const Vct3f & p( pgrid[i] );
    for (int k=0; k<3; ++k) {
      bblo[k] = std::min( bblo[k], p[k] );
      bbhi[k] = std::max( bbhi[k], p[k] );
    }
  }
}

void OverlayGrid::drawPrimitives() const
{
  if (not bVisible)
    return;

  const int nr(pgrid.nrows());
  const int nc(pgrid.ncols());
  if (nr*nc == 0)
    return;

  // transfer arrays to GPU
  glVertexPointer(3, GL_FLOAT, 0, pgrid.pointer());
  glNormalPointer(GL_FLOAT, 0, ngrid.pointer());

  if (bDrawPolygons) {
    glColor4ubv( clr.pointer() );
    glDrawElements(GL_TRIANGLES, elements.size(),
                   GL_UNSIGNED_INT, &elements[0]);
  }

  // surface boundaries only
  if (not lines.empty()) {

    Color lineColor(0.8f, 0.8f, 0.8f);
    if (not bDrawPolygons) {
      glLineWidth(2.0f);
      lineColor = clr;
    }

    glColor4ubv( lineColor.pointer() );
    glDrawElements(GL_LINE_STRIP, lines.size(), GL_UNSIGNED_INT, &lines[0]);

    glLineWidth(1.0f);
  }
}

void OverlayGrid::extendBox(float lo[], float hi[]) const
{
  for (int i=0; i<3; ++i) {
    lo[i] = std::min(lo[i], bblo[i]);
    hi[i] = std::max(hi[i], bbhi[i]);
  }
}

void OverlayGrid::collectMesh(TriMesh & tm) const
{
  const int np = pgrid.size();
  PointList<3> pts(np);
  for (int i=0; i<np; ++i)
    ::convert(pgrid[i], pts[i]);

  tm.importMesh(pts, elements);
}


