/* ------------------------------------------------------------------------
 * file:       igesgrid.h
 * copyright:  (c) 2010 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * 3D View widget for surfaces
 * ------------------------------------------------------------------------ */

#ifndef SUMO_IGESGRID_H
#define SUMO_IGESGRID_H

#include <surf/surface.h>
#include <genua/color.h>
#include <genua/point.h>
#include <boost/shared_ptr.hpp>

class IgesFile;
struct IgesDirEntry;
class StepFile;
class StepEntity;
class PolySplineSurf;
class LinearSurf;
class TriMesh;

/** Draws a single spline surface.

  This is a low-level object used by IgesDisplay to display a single spline
  surface imported from IGES files.

  \sa IgesDisplay
*/
class OverlayGrid
{
public:

  /// empty grid
  OverlayGrid() : iEntry(NotFound), bVisible(true) {}

  /// change minimum number of tesselation points between knots
  static void vertexDensity(uint pu, uint pv) {
    tesspu = pu;
    tesspv = pv;
  }

  /// enable/disable polygon display
  static void drawPolygons(bool flag) { bDrawPolygons = flag; }

  /// number of vertices (for statistics)
  uint nvertices() const {return pgrid.size();}

  /// access extracted surface
  SurfacePtr surface() const {return psf;}

  /// change polygon color
  void color(const Color & c) {clr = c;}

  /// assign directory entry id
  void id(uint k) {iEntry = k;}

  /// retrieve directory entry id
  uint id() const {return iEntry;}

  /// create grid from IGES surface
  bool fromIges(const IgesFile & file, const IgesDirEntry & entry);

  /// create grid from STEP spline surface
  bool fromStep(const StepFile & file, const StepEntity *ep);

  /// extend display bounding box
  void extendBox(float lo[], float hi[]) const;

  /// draw (immediate mode for display list)
  void drawPrimitives() const;

  /// merge visualization triangles into mesh
  void collectMesh(TriMesh & tm) const;

  /// create triangles from grid
  static void triangles(uint nrow, uint ncol, Indices & elm);

  /// create grid outline
  static void outline(uint nrow, uint ncol, Indices & lns);

private:

  /// tesselate polynomial spline surface
  void tesselate(const PolySplineSurf & surf);

  /// tesselate linear (ruled) surface
  void tesselate(const LinearSurf & surf);

  /// extract transformation from IGES entity
  void applyIgesTrafo(const IgesFile & file, const IgesDirEntry & dir);

  /// compute bounding box
  void boundingBox();

private:

  /// surface recovered from IGES/STEP file
  SurfacePtr psf;

  /// display data : vertices
  PointGrid<3,float> pgrid;

  /// display data : normals
  PointGrid<3,float> ngrid;

  /// elements for polygon display
  Indices elements;

  /// lines for wireframe display
  Indices lines;

  /// display bounding box
  Vct3f bblo, bbhi;

  /// color to use
  Color clr;

  /// IGES directory entry for this surface
  uint iEntry;

  /// IGES file visibility flag
  bool bVisible;

  /// tesselation parameters
  static uint tesspu, tesspv;

  /// whether to draw polygons or just boundaries
  static bool bDrawPolygons;
};

typedef boost::shared_ptr<OverlayGrid> OverlayGridPtr;
typedef std::vector<OverlayGridPtr> OverlayGridArray;

inline bool operator< (const OverlayGridPtr & a, const OverlayGridPtr & b)
{
  return (a->id() < b->id());
}

inline bool operator< (uint aid, const OverlayGridPtr & b)
{
  return (aid < b->id());
}

inline bool operator< (const OverlayGridPtr & a, uint bid)
{
  return (a->id() < bid);
}

#endif // IGESGRID_H
