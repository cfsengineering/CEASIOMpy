/* ------------------------------------------------------------------------
 * file:       igesdisplay.h
 * copyright:  (c) 2010 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * OpenGL display class for collection of IGES surfaces
 * ------------------------------------------------------------------------ */

#ifndef SUMO_IGESDISPLAY_H
#define SUMO_IGESDISPLAY_H

#include "overlaygrid.h"
#include <genua/transformation.h>

class IgesFile;
class StepFile;
class MultiSurfProjector;
class TriMesh;

/** Display 3D geometry from IGES file.

  \sa IgesGrid
  */
class OverlayDisplay
{
public:

  /// empty display
  OverlayDisplay();

  /// release display resources
  ~OverlayDisplay();

  /// must be called after GL initialization
  void initDisplay();

  /// access current transformation
  const Trafo3d & currentTrafo() const;

  /// change display transformation
  void applyTrafo(const Trafo3d & tf);

  /// move in IGES model to display
  void tesselate(const IgesFile & file);

  /// move in STEP model to display
  void tesselate(const StepFile & file);

  /// draw (immediate mode for display list)
  void draw() const;

  /// extend bounding box (if visible)
  void extendBox(float lo[], float hi[]) const;

  /// visibility
  bool visible() const {return bVisible;}

  /// enable/disable display
  void visible(bool flag) {bVisible = flag;}

  /// number of parts/patches identified
  uint nparts() const {return patchNames.size();}

  /// number of IGES surfaces successfully read
  uint nsurfaces() const {return grids.size();}

  /// number of vertices currently displayed
  uint nvertices() const {return nVertices;}

  /// construct projector
  void buildProjector(MultiSurfProjector & msp) const;

  /// collect all surfaces into a global mesh
  void collectMesh(TriMesh & tm) const;

  /// enforce rebuild of display list (next draw call)
  void clearDisplayList();

  /// clear out all data
  void clear();

protected:

  /// locate grid by directoy entry
  uint findGrid(uint idir) const {
    OverlayGridArray::const_iterator pos;
    pos = std::lower_bound(grids.begin(), grids.end(), idir);
    if (pos != grids.end() and (*pos)->id() == idir)
      return std::distance(grids.begin(), pos);
    else
      return NotFound;
  }

  /// retrieve the underlying surface object directory id from a trimmed surface
  int baseSurfaceId(const IgesFile & file, int ide) const;

  /// determine bounding box in original coordinates
  void buildBoundingBox();

  /// build a local-coordinate display list
  void compileDisplayList();

private:

  /// grids to display
  OverlayGridArray grids;

  /// patch ids for all grids
  Indices patchId;

  /// patch names (if found)
  StringArray patchNames;

  /// global display transformation
  Trafo3d globTrafo;

  /// cached bounding box in local coordinates
  Vct4 bblo, bbhi;

  /// OpenGL display list
  uint iDisplayList;

  /// statistics
  uint nVertices;

  /// hide/show
  bool bVisible;
};

#endif // IGESDISPLAY_H
