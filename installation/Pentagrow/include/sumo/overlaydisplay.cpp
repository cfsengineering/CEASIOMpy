/* ------------------------------------------------------------------------
 * file:       igesdisplay.cpp
 * copyright:  (c) 2010 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * OpenGL display class for collection of IGES surfaces
 * ------------------------------------------------------------------------ */

#include "overlaydisplay.h"
#include "glew.h"
#include <surf/igesfile.h>
#include <surf/iges308.h>
#include <surf/iges144.h>
#include <surf/stepfile.h>
#include <surf/stepentity.h>
#include <surf/step_ap203.h>
#include <surf/multisurfprojector.h>
#include <genua/transformation.h>
#include <genua/timing.h>
#include <genua/trimesh.h>

// debug
#include <iostream>

using namespace std;

OverlayDisplay::OverlayDisplay() : iDisplayList(NotFound),
nVertices(0), bVisible(true)
{
}

OverlayDisplay::~OverlayDisplay()
{
  if (iDisplayList != NotFound)
    glDeleteLists(iDisplayList, 1);
}

void OverlayDisplay::initDisplay()
{
  if (iDisplayList == NotFound) {
    iDisplayList = glGenLists(1);
    compileDisplayList();
  }
}

const Trafo3d & OverlayDisplay::currentTrafo() const
{
  return globTrafo;
}

void OverlayDisplay::applyTrafo(const Trafo3d & tf)
{
  globTrafo = tf;
}

void OverlayDisplay::tesselate(const IgesFile & file)
{
  clear();

  // import all surfaces, set color to grey
  const int ndir = file.nDirEntries();

  // the IGES file is already mapped to memory, it can be accessed
  // (read-only anyway) in parallel
#pragma omp parallel for
  for (int i=0; i<ndir; ++i) {
    IgesDirEntry entry;
    file.dirEntry(2*i+1, entry);

    // look only at geometry entities
    if (entry.useflag != 0)
      continue;

    if (entry.etype != 128 and entry.etype != 118 and entry.etype != 144)
      continue;

    // fromIges() contains the computation of tesselation, which is
    // comparatively expensive -- this is the interesting part
    // for parallel execution
    OverlayGridPtr gp(new OverlayGrid);
    if ( gp->fromIges(file,entry) ) {
      gp->color( Color(.5f, .5f, .5f) );
      gp->id( 2*i+1 );
#pragma omp critical
      {
        grids.push_back( gp );
        nVertices += grids.back()->nvertices();
      }
//    } else {
//#pragma omp critical
//      cerr << "Could not read E" << entry.etype << " at " << 2*i+1 << endl;
    }
  }

  // debug
  cout << "Tesselated " << grids.size() << " surfaces with "
      << nVertices << " vertices." << endl;

  // compute bounding box in local coordinates
  buildBoundingBox();

  // keep them sorted by directory id to speed up
  // patch assignment
  std::sort(grids.begin(), grids.end());

  // reset all patch ids
  const int ng = grids.size();
  patchId.resize(ng);
  fill(patchId.begin(), patchId.end(), NotFound);

  // saturation and lightness for patch colors
  int sat(75), val(130);

  // assign grids to patches
  Color pcol;
  ColorArray patchColors;
  IgesEntityPtr eptr;
  IgesDirEntry entry;
  bool assignedAny = false;
  for (int i=0; i<ndir; ++i) {
    file.dirEntry(2*i+1, entry);
    if (entry.etype == 308) {
      eptr = file.createEntity( entry ) ;
      IgesSubfigure fig;
      if ( IgesEntity::as(eptr, fig) ) {
        cout << "Mapping subfigure " << 2*i+1 << endl;
        uint ipatch = patchNames.size();
        patchNames.push_back( fig.name() );
        pcol.hsv2rgb(rand()%255, sat, val);
        patchColors.push_back( pcol );
        const int n = fig.size();
        for (int j=0; j<n; ++j) {
          int mid = baseSurfaceId( file, fig[j] );
          if (mid == 0)
            continue;
          uint ig = findGrid( mid );
          if (ig != NotFound) {
            assignedAny = true;
            patchId[ig] = ipatch;
            grids[ig]->color(pcol);
          } else {
            // cout << "Entity " << mid << " not found." << endl;
          }
        }
      }
    }
  }
  cout << "Identified " << patchNames.size() << " patches." << endl;

  // when patch identification failed, assign colors by surface id
  if (not assignedAny) {
    const int ng = grids.size();
    for (int i=0; i<ng; ++i) {
      pcol.hsv2rgb(rand()%255, sat, val);
      grids[i]->color( pcol );
    }
  }

  // preset scaling if the IGES file specifies millimeter as units
  if ( file.unitName() == "MM" ) {
    Trafo3d tf;
    tf.scale(0.001, 0.001, 0.001);
    applyTrafo(tf);
  } else if ( file.unitName() == "INCH" ) {
    Trafo3d tf;
    tf.scale(0.0254, 0.0254, 0.0254);
    applyTrafo(tf);
  }

  // enforce rebuilding of a new list if one exists
  clearDisplayList();
}

void OverlayDisplay::tesselate(const StepFile & file)
{
  clear();

  Wallclock c;
  c.start("Parsing STEP file...");

  // collect entities
  std::vector<StepEntity*> surfEnts;

  StepFile::const_iterator itr, last;
  last = file.end();
  for (itr = file.begin(); itr != last; ++itr) {
    const StepEntityPtr & eptr( *itr );
    if (dynamic_cast<const StepBSplineSurfaceWithKnots*>(eptr.get()) != 0) {
      surfEnts.push_back( eptr.get() );
    }
  }

  c.stop("...done.  ");
  c.start("Tesselating surfaces...");

  const int ne = surfEnts.size();
  grids.resize(ne);
#pragma omp parallel for
  for (int i=0; i<ne; ++i) {
    grids[i].reset( new OverlayGrid );
    grids[i]->fromStep( file, surfEnts[i] );
#pragma omp atomic
    nVertices += grids[i]->nvertices();
  }

  c.stop("...done.  ");

  // debug
  cout << "Tesselated " << grids.size() << " surfaces with "
      << nVertices << " vertices." << endl;

  // compute bounding box in local coordinates
  buildBoundingBox();

  // keep them sorted by directory id to speed up
  // patch assignment
  std::sort(grids.begin(), grids.end());

  Color pcol;
  int sat(75), val(130);
  const int ng = grids.size();
  for (int i=0; i<ng; ++i) {
    pcol.hsv2rgb(rand()%255, sat, val);
    grids[i]->color( pcol );
  }

  // enforce rebuilding of a new list if one exists
  clearDisplayList();
}

int OverlayDisplay::baseSurfaceId(const IgesFile & file, int ide) const
{
  IgesDirEntry parent;
  file.dirEntry(ide, parent);

  if (parent.etype == 144) {
    IgesTrimmedSurface its;
    IgesEntityPtr eptr = file.createEntity(parent);
    if ( IgesEntity::as(eptr, its) ) {
      return its.pts;
    } else {
      return 0;
    }
  } else if (parent.etype == 128 or parent.etype == 118) {
    return ide;
  }

  return 0;
}

void OverlayDisplay::clearDisplayList()
{
  if (iDisplayList != NotFound) {
    glDeleteLists(iDisplayList, 1);
    iDisplayList = NotFound;
  }
}

void OverlayDisplay::compileDisplayList()
{
  if (iDisplayList == NotFound) {
    cerr << "IgesDisplay : Display list not created." << endl;
    return;
  }

  glNewList(iDisplayList, GL_COMPILE);

  glEnableClientState(GL_VERTEX_ARRAY);
  glEnableClientState(GL_NORMAL_ARRAY);

  const int n = grids.size();
  for (int i=0; i<n; ++i)
    grids[i]->drawPrimitives();

  glDisableClientState(GL_VERTEX_ARRAY);
  glDisableClientState(GL_NORMAL_ARRAY);

  glEndList();
}

void OverlayDisplay::draw() const
{
  if (not bVisible)
    return;

  // compute current transformation
  Mtx44 tfm;
  globTrafo.matrix( tfm );

  // apply transformation
  glMatrixMode(GL_MODELVIEW);
  glPushMatrix();
  glMultMatrixd(tfm.pointer());
  glCallList(iDisplayList);
  glPopMatrix();
}

void OverlayDisplay::buildBoundingBox()
{
  bblo = std::numeric_limits<float>::max();
  bbhi = -bblo;

  const int n = grids.size();
#pragma omp parallel
  {
    // thread-private private box dimensions
    Vct3f plo, phi;
    plo = std::numeric_limits<float>::max();
    phi = -plo;

    // work on private copies
#pragma omp for
    for (int i=0; i<n; ++i)
      grids[i]->extendBox(plo.pointer(), phi.pointer());

#pragma omp critical
    {
      for (int k=0; k<3; ++k) {
        bblo[k] = std::min(bblo[k], Real(plo[k]));
        bbhi[k] = std::max(bbhi[k], Real(phi[k]));
      }
    } // omp critical
  } // omp parallel

  bblo[3] = bbhi[3] = 1.0;
}

void OverlayDisplay::extendBox(float lo[], float hi[]) const
{
  if (not visible())
    return;

  // transform bounding box corners to global coordinates
  // this guess is good enough for display purposes
  Mtx44 tfm;
  Vct4 qlo, qhi;
  globTrafo.matrix(tfm);
  qlo = tfm * bblo;
  qhi = tfm * bbhi;

  // debug
  // cerr << "Current transformed bb" << endl;
  // cerr << "lo " << qlo << " hi " << qhi << endl;

  for (int k=0; k<3; ++k) {
    lo[k] = std::min( lo[k], float(qlo[k]) );
    hi[k] = std::max( hi[k], float(qhi[k]) );
  }
}

void OverlayDisplay::clear()
{
  bblo = std::numeric_limits<float>::max();
  bbhi = -bblo;
  nVertices = 0;
  grids.clear();
  patchId.clear();
  patchNames.clear();
  globTrafo.identity();
}

void OverlayDisplay::buildProjector(MultiSurfProjector & msp) const
{
  msp.clear();
  for (uint i=0; i<grids.size(); ++i) {
    SurfacePtr psf = grids[i]->surface();
    if (psf)
      msp.append( psf );
  }
  msp.buildTree();
  msp.transformation( globTrafo );
}

void OverlayDisplay::collectMesh(TriMesh & tm) const
{
//  tm.clear();
//  TriMesh sub;
//  const int ng = grids.size();
//  for (int i=0; i<ng; ++i) {
//    sub.clear();
//    grids[i]->collectMesh(sub);
//    sub.faceTag(i);
//    tm.merge(sub);
//  }
//  tm.fixate(true);

  // global mesh
  tm.clear();

#pragma omp parallel
  {
    // thread-private merged mesh and grid submesh
    TriMesh tpm, sub;
    const int ng = grids.size();

#pragma omp for
    for (int i=0; i<ng; ++i) {
      sub.clear();
      grids[i]->collectMesh(sub);
      sub.faceTag(i);
      tpm.merge(sub);
    }

#pragma omp critical
    tm.merge(tpm);
  }
}
