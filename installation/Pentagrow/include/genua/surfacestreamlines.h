#ifndef GENUA_SURFACESTREAMLINES_H
#define GENUA_SURFACESTREAMLINES_H

#include "trimesh.h"
#include "point.h"
#include <mutex>
#include <atomic>

/** Compute streamlines on a discretized surface.
 *
 * A SurfaceStreamlines is constructed by adding mesh sections or element groups
 * incrementally and finally calling fixate(). All mesh elements thus added to
 * the working set are decomposed into 3-node triangles for the
 * streamline integration algorithm.
 *
 * Once the geometry has thus been defined, a vector field needs to be assigned
 * using extractField(). This step copies field data for the subset of nodes
 * which lie on the previously extrated surfaces.
 *
 * For each field, and arbitrary number (typically ~1000) of streamlines can be
 * integrated. This is done by starting at a prescribed (perhaps randomly
 * chosen) edge index and following the interpolated field vectors across
 * triangles. A new streamline point is generated every time the vector field
 * intersects a triangle edge. In order to avoid too high streamline density,
 * it is possible to cut off streamlines whenever they encounter a triangle
 * edge which has already been intersected n (default 3) times.
 *
 * Streamlines are represented as 4D polylines, where the first 3 coordinates
 * are the point coordinates and the last value is the magnitude of the vector
 * field at that point.
 *
 * The functions computeStreamline() (lock-free) and storeStreamline() (locks)
 * are designed to be called from multiple threads at the same time. The
 * utilities writeRandomLines() and appendRandomLines() are just convenience
 * interfaces which leave the object essentially unmodified.
 *
 * \ingroup mesh
 * \sa MxMesh, MxMeshField
 **/
class SurfaceStreamlines
{
public:

  /// number of times a single mesh edge may be intersected by a streamline
  void permittedCrossings(uint n) {m_maxslice = n;}

  /// extract surface triangles from all surfaces in mesh, return edge count
  uint surfacesFromMesh(const MxMesh &mx);

  /// add mesh section to surface
  void addSection(const MxMeshSection &sec);

  /// call this when all surfaces have been added, returns number of edges
  uint fixate(const MxMesh &mx);

  /// access number of edges
  uint nedges() const {return m_msh.nedges();}

  /// extract vector field on surfaces
  void extractField(const MxMeshField &f);

  /// check how often edge k has already been sliced
  uint edgeSliced(uint k) const;

  /// compute one more random streamline starting at edge istart, thread-safe
  PointList4d computeStreamline(uint istart, Real minSpeed = 0.0);

  /// record streamline internally, thread-safe
  uint storeStreamline(const PointList4d &sln);

  /// number of streamlines stored
  size_t size() const {return m_slines.size();}

  /// clear out all stored lines
  void clear();

  /// access streamline k
  const PointList4d &operator[] (size_t k) const {
    assert(k < m_slines.size());
    return m_slines[k];
  }

  ///@{ Convenience interface

  /// compute and store n random lines enforcing a minimum length
  uint storeRandomLines(uint n, uint minLength=4, Real minSpeed=0.0);

  /// create n random streamlines and write to text files
  void writeRandomLines(uint n, const std::string &baseName,
                        Real minSpeed=0.0);

  /// create n random streamlines and append to mesh as polyline segments
  void appendRandomLines(MxMesh &mx, uint n, const std::string &baseName,
                         Real minSpeed=0.0);

  ///@}

private:

  struct PointOnEdge {
    PointOnEdge() : iedge(NotFound) {}

    uint iedge;   ///< index of edge in m_msh
    Real tpos;    ///< 0: source, 1: target

    bool valid() const {return (iedge != NotFound);}
    Vct3 location(const TriMesh &m) const;
  };

  /// whether edge k has been intersected too many times
  bool forbiddenEdge(uint k) const;

  /// increment edge slice count
  void incSlice(uint k);

  /// start at cur, evaluate
  PointOnEdge walk(const PointOnEdge &cur, bool forward) const;

  /// store point in working streamline
  Real storePoint(const PointOnEdge &p, PointList4d &sln);

  /// compute candidate point on edge (a,b), or return invalid point
  PointOnEdge candidate(const Vct3 &pe,
                        const Vct3 &vf, uint a, uint b) const;

private:

  /// collection of triangles before mesh assembly
  Indices m_pretri;

  /// discrete surface
  TriMesh m_msh;

  /// node indices of the trimesh vertices
  Indices m_idxmap;

  /// vector field values
  PointList3d m_vf;

  /// streamline (or skin friction line, or ...) point coordinates + magnitude
  std::vector<PointList4d> m_slines;

  /// used to protect m_slines from parallel access
  std::mutex m_sline_guard;

  /// number of times an edge has been intersected by a line
  Indices m_edgesliced;

  /// permitted number of edge intersections
  uint m_maxslice = 3;

  /// permitted maximum number of points in half-line
  uint m_maxpoints = 4096;
};

#endif // SURFACESTREAMLINES_H
