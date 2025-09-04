
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

#ifndef GENUA_TRIMESH_H
#define GENUA_TRIMESH_H

#include <boost/shared_ptr.hpp>
#include <vector>

#include "sparse.h"
#include "xmlelement.h"
#include "point.h"
#include "connectmap.h"
#include "triedge.h"
#include "triface.h"

// to simplify porting
class Triangulation;

class CgnsFile;
class CgnsZone;
class CgnsSection;

typedef std::vector<TriEdge> TriEdgeArray;
typedef std::vector<TriFace> TriFaceArray;

/** Specialized triangular surface mesh.
 *
 * TriMesh serves as a mesh container for triangular surface mesh generation.
 * It supports more advanced face/edge/vertex connectivity queries and permits
 * hence more straightforward iteration through the mesh. Edges and faces are
 * full objects and faces can be assigned tags.
 *
 * For meshes which contain not only triangles, consider MxMesh. When
 * visualization is the primary purpose, perfer CgMesh, which has a smaller
 * memory footprint.
 *
 * \ingroup mesh
 * \sa TriFace, TriEdge, CgMesh, MxMesh
 */
class TriMesh
{
public:
  typedef TriEdgeArray::const_iterator edge_iterator;
  typedef TriFaceArray::const_iterator face_iterator;

  // pattern for triangulation of point grids
  typedef enum
  {
    XPattern,
    QuadPattern,
    BiasedPattern
  } GridPattern;

  class nb_face_iterator
  {
  public:
    nb_face_iterator() {}
    nb_face_iterator(const TriMesh *m, Indices::const_iterator itr) : pos(itr), msh(m) {}
    nb_face_iterator(const nb_face_iterator &a) : pos(a.pos), msh(a.msh) {}
    const nb_face_iterator &operator=(const nb_face_iterator &a)
    {
      if (&a != this)
      {
        msh = a.msh;
        pos = a.pos;
      }
      return *this;
    }
    bool operator==(const nb_face_iterator &a) const
    {
      return (pos == a.pos);
    }
    bool operator!=(const nb_face_iterator &a) const
    {
      return (pos != a.pos);
    }
    bool operator<(const nb_face_iterator &a) const
    {
      return (pos < a.pos);
    }
    const TriFace &operator*() const { return msh->face(*pos); }
    const TriFace *operator->() const { return &msh->face(*pos); }
    const nb_face_iterator &operator++()
    {
      ++pos;
      return *this;
    }
    const nb_face_iterator &operator--()
    {
      --pos;
      return *this;
    }
    uint index() const { return *pos; }
    ptrdiff_t operator-(nb_face_iterator a) { return pos - a.pos; }

  private:
    Indices::const_iterator pos;
    const TriMesh *msh;
  };

  class nb_edge_iterator
  {
  public:
    nb_edge_iterator() {}
    nb_edge_iterator(const TriMesh *m, Indices::const_iterator itr) : pos(itr), msh(m) {}
    nb_edge_iterator(const nb_edge_iterator &a) : pos(a.pos), msh(a.msh) {}
    const nb_edge_iterator &operator=(const nb_edge_iterator &a)
    {
      if (&a != this)
      {
        msh = a.msh;
        pos = a.pos;
      }
      return *this;
    }
    bool operator==(const nb_edge_iterator &a) const
    {
      return (pos == a.pos);
    }
    bool operator!=(const nb_edge_iterator &a) const
    {
      return (pos != a.pos);
    }
    bool operator<(const nb_edge_iterator &a) const
    {
      return (pos < a.pos);
    }
    const TriEdge &operator*() const { return msh->edge(*pos); }
    const TriEdge *operator->() const { return &msh->edge(*pos); }
    const nb_edge_iterator &operator++()
    {
      ++pos;
      return *this;
    }
    const nb_edge_iterator &operator--()
    {
      --pos;
      return *this;
    }
    uint index() const { return *pos; }
    ptrdiff_t operator-(nb_edge_iterator a) { return pos - a.pos; }

  private:
    Indices::const_iterator pos;
    const TriMesh *msh;
  };

  /// create empty mesh
  TriMesh() {}

  /// copy mesh
  TriMesh(const TriMesh &msh);

  /// copy mesh
  TriMesh &operator=(const TriMesh &msh);

  /// destroy mesh
  virtual ~TriMesh() {}

  /// reserve space before adding stuff
  void reserve(size_t nv, size_t nf)
  {
    vtx.reserve(nv);
    faces.reserve(nf);
  }

  /// add a vertex, return its index
  uint addVertex(const Vct3 &p)
  {
    vtx.push_back(p);
    return vtx.size() - 1;
  }

  /// add vertex and normal, return index
  uint addVertex(const Vct3 &p, const Vct3 &n)
  {
    vtx.push_back(p);
    nrm.push_back(n);
    return vtx.size() - 1;
  }

  void removeVertex(uint i)
  {
    vtx.erase(vtx.begin() + i);
    nrm.erase(nrm.begin() + i);
  }

  /// add a triangle, return its index
  uint addFace(uint a, uint b, uint c, int t = 0)
  {
    faces.push_back(TriFace(this, a, b, c));
    faces.back().tag(t);
    return faces.size() - 1;
  }

  /// add a triangle, return its index
  uint addFace(const uint vi[], int t = 0)
  {
    return addFace(vi[0], vi[1], vi[2], t);
  }

  /// triangulate a point matrix
  void triangulate(const PointGrid<3> &pg, GridPattern gpt = XPattern);

  /// add another mesh to this one, do not fixate (!)
  void merge(const TriMesh &msh);

  /// for porting only: merge old triangle mesh object
  void merge(const Triangulation &t);

  /// import mesh data
  void importMesh(const PointList<3> &pts, const Indices &tri,
                  bool udrop = false);

  /// import mesh data, including normal vectors
  void importMesh(const PointList<3> &pts, const PointList<3> &nmv,
                  const Indices &tri, bool udrop = false);

  /// export in simplest form
  void exportMesh(PointList<3> &pts, Indices &tri) const;

  /// export in simplest form, including normal vectors
  void exportMesh(PointList<3> &pts, PointList<3> &nmv, Indices &tri) const;

  /// compute connectivity, optionally drop unreferenced vertices
  void buildConnectivity(bool udrop = false);

  /// compute connectivity and estimate vertex normals if not present
  void fixate(bool udrop = false);

  /// access number of vertices
  uint nvertices() const { return vtx.size(); }

  /// access number of triangles
  uint nfaces() const { return faces.size(); }

  /// access number of edges
  uint nedges() const { return edges.size(); }

  /// access vertex position
  const Vct3 &vertex(uint i) const { return vtx[i]; }

  /// access vertex position
  Vct3 &vertex(uint i) { return vtx[i]; }

  /// access discrete surface normal
  const Vct3 &normal(uint i) const { return nrm[i]; }

  /// access discrete surface normal
  Vct3 &normal(uint i) { return nrm[i]; }

  /// access all vertices
  const PointList<3> &vertices() const { return vtx; }

  /// access all vertices
  PointList<3> &vertices() { return vtx; }

  /// access all normal vectors
  const PointList<3> &normals() const { return nrm; }

  /// access all normal vectors
  PointList<3> &normals() { return nrm; }

  /// access face
  const TriFace &face(uint i) const
  {
    assert(i < faces.size());
    return faces[i];
  }

  /// access face
  TriFace &face(uint i)
  {
    assert(i < faces.size());
    return faces[i];
  }

  /// access edge
  const TriEdge &edge(uint i) const
  {
    assert(i < edges.size());
    return edges[i];
  }

  /// access edge
  TriEdge &edge(uint i)
  {
    assert(i < edges.size());
    return edges[i];
  }

  /// number of edges coincident in vertex i
  uint vdegree(uint i) const
  {
    assert(i < v2f.size());
    return v2e.size(i);
  }

  /// number of faces coincident in edge i
  uint edegree(uint i) const
  {
    assert(i < e2f.size());
    return e2f.size(i);
  }

  /// convenience : fetch three edge indices of a face
  const uint *firstEdgeIndex(uint iface) const
  {
    return f2e.first(iface);
  }

  /// convenience : fetch face indices of an edge
  const uint *firstFaceIndex(uint iedge) const
  {
    return e2f.first(iedge);
  }

  /// collect indices for edges with degree != 2
  void boundaries(Indices &bde) const;

  /// assemble a linear gradient stencil around vertex i
  void gradient(uint i, SpMatrix &gmx) const;

  /// compute surface gradient of x at node i
  Vct3 gradient(uint i, const Vector &x) const;

  /// compute surface gradient of x at node i
  CpxVct3 gradient(uint i, const CpxVector &x) const;

  /// check whether all edges have exactly two neighbor faces
  bool isClosedManifold() const;

  /// presuming *this is manifold, locate points inside the enclosed volume
  bool findInternalPoints(PointList<3> &holes) const;

  /// locate faces which have >= 2 nb faces with opposed normals
  uint findFlippedFaces(Indices &fflip, Real maxphi = PI) const;

  /// compute total area (sum of face areas)
  Real area() const;

  /// compute the enclosed volume (for manifolds)
  Real volume() const;

  /// center of the enclosed volume (for manifolds)
  Vct3 volumeCenter() const;

  /// return length of shortest edge
  Real shortestEdgeLength() const;

  /// compute the solid angle at vertex i
  Real solidAngle(uint i) const;

  /// merge duplicate nodes
  uint mergeNodes(Real threshold = gmepsilon, Real dphimax = M_PI);

  /** Remove duplicate vertices. Check face validity, rebuild
  edge list and connectivity. Does only process identical vertices
  (i.e. where distance smaller threshold) not connected by an edge. */
  uint cleanup(Real threshold = gmepsilon);

  /// merge nodes first, then create patches separated by ridges
  void detectEdges(Real ridgeLimitAngle, Real mergeThreshold = gmepsilon);

  /// change direction of all faces
  void reverse();

  /// change vertex index ordering
  virtual void reorder(const Indices &perm);

  /// swap contents with other mesh
  virtual void swap(TriMesh &a);

  /// compute memory requirements
  virtual Real megabytes() const;

  /// delete all contents
  virtual void clear();

  /// convert to xml representation
  virtual XmlElement toXml(bool share = false) const;

  /// read from xml representation
  virtual void fromXml(const XmlElement &xe);

  /// write to binary stream
  virtual void writeBin(std::ostream &os) const;

  /// read from binary stream
  virtual void readBin(std::istream &is);

  /// save to CGNS file zone
  virtual void toCgns(CgnsFile &file) const;

  /// retrieve from CGNS file section (throws when file incompatible)
  virtual void fromCgns(CgnsZone &zone);

#ifdef HAVE_RPLY

  /// check if a file looks like PLY format
  static bool isPLY(const std::string &fname);

  /// import from PLY file
  bool fromPLY(const std::string &fname);

  /// write to PLY file
  bool toPLY(const std::string &fname, bool binary = true);

#endif // RPLY

  /// write to cgns file
  void writeCgns(const std::string &fname) const;

  /// read from cgns file
  void readCgns(const std::string &fname);

  /// determine whether fname is binary or ascii STL
  void readSTL(const std::string &fname);

  /// read ascii STL file
  void readAsciiSTL(const std::string &fname);

  /// read binary STL
  void readBinarySTL(const std::string &fname);

  /// write binary STL file
  void writeBinarySTL(const std::string &fname) const;

  /// write ascii STL file
  void writeAsciiSTL(const std::string &fname,
                     const std::string &solid = "") const;

  /// iterate over all edges
  edge_iterator edgeBegin() const { return edges.begin(); }

  /// iterate over all edges
  edge_iterator edgeEnd() const { return edges.end(); }

  /// iterate over all faces
  face_iterator faceBegin() const { return faces.begin(); }

  /// iterate over all faces
  face_iterator faceEnd() const { return faces.end(); }

  /// iterate over neighborhood
  nb_face_iterator v2fBegin(uint i) const
  {
    assert(i < v2f.size());
    return nb_face_iterator(this, v2f.begin(i));
  }

  /// iterate over neighborhood
  nb_face_iterator v2fEnd(uint i) const
  {
    assert(i < v2f.size());
    return nb_face_iterator(this, v2f.end(i));
  }

  /// iterate over neighborhood
  nb_face_iterator e2fBegin(uint i) const
  {
    assert(i < e2f.size());
    return nb_face_iterator(this, e2f.begin(i));
  }

  /// iterate over neighborhood
  nb_face_iterator e2fEnd(uint i) const
  {
    assert(i < e2f.size());
    return nb_face_iterator(this, e2f.end(i));
  }

  /// iterate over neighborhood
  nb_edge_iterator v2eBegin(uint i) const
  {
    assert(i < v2e.size());
    return nb_edge_iterator(this, v2e.begin(i));
  }

  /// iterate over neighborhood
  nb_edge_iterator v2eEnd(uint i) const
  {
    assert(i < v2e.size());
    return nb_edge_iterator(this, v2e.end(i));
  }

  /// iterate over neighborhood
  nb_edge_iterator f2eBegin(uint i) const
  {
    assert(i < f2e.size());
    return nb_edge_iterator(this, f2e.begin(i));
  }

  /// iterate over neighborhood
  nb_edge_iterator f2eEnd(uint i) const
  {
    assert(i < f2e.size());
    return nb_edge_iterator(this, f2e.end(i));
  }

  /// bind newly copied faces and edges to this object
  void bind();

  /// estimate vertex normal vectors
  void estimateNormals(bool symmetry = false, Real y0 = 0);

  // For symmetry : normals on the border must be on the plane y=y0
  void fixnormalonborder(Real y0 = 0);

  /// find edge by traversing connectivity
  uint tsearchEdge(uint s, uint t) const
  {
    assert(v2e.size() == vtx.size());
    if (s > t)
      std::swap(s, t);
    assert(s < v2e.size());
    const uint ne(v2e.size(s));
    const uint *nbe(v2e.first(s));
    for (uint i = 0; i < ne; ++i)
    {
      uint idx = nbe[i];
      const TriEdge &e(edges[idx]);
      if (e.source() == s and e.target() == t)
        return idx;
    }
    return NotFound;
  }

  /// find edge in sorted edge array
  uint bsearchEdge(uint s, uint t) const
  {
    TriEdge tmp(this, s, t);
    edge_iterator pos;
    pos = std::lower_bound(edges.begin(), edges.end(), tmp);
    if (pos != edges.end() and *pos == tmp)
      return std::distance(edges.begin(), pos);
    else
      return NotFound;
  }

  /// set tag of all faces to t
  void faceTag(int t);

  /// find all tags in this mesh
  void allTags(Indices &tgs) const;

  /// retrieve name associated with tag t
  std::string tagName(int t) const;

  /// set name associated with tag t
  void tagName(int t, const std::string &s);

  /// create a submesh containing only tag t
  void submesh(int t, TriMesh &sub) const;

  /// find triangles which are enclosed by vertex loop
  bool enclosedTriangles(const Indices &vloop, Indices &t) const;

  /// generate a regular icosahedron with radius r
  void icosahedron(const Vct3 &ctr, Real r);

  /// generate an axis-aligned tetrahedron with radius r
  void tetrahedron(const Vct3 &ctr, Real r);

  /** Generate approximation to sphere with radius r centered at ctr.
    Number of faces will be 20*4^npass */
  void sphere(const Vct3 &ctr, Real r, int nrefp);

  /// generate an axis-aligned half-icosahedron with radius r (in y>0)
  void icosahedron_forsemi(const Vct3 &ctr, Real r);

  /** Generate approximation to a semi-sphere with radius r centered at ctr.
    Number of faces will be a little more than 10*4^npass (bc border) */
  void semisphere(const Vct3 &ctr, Real r, int nrefp);

  // add the y plane between thefarfield and shell to have watertight volume
  void addyplane(PointList<3> vout, Real y0 = 0);

  void writeSTL(const std::string &filename) const;

  /** Generate approximation to sphere by splitting tetrahedron  */
  void tsphere(const Vct3 &ctr, Real r, int nrefp);

  /// quadruple split: divide each triangle in four
  void quadSplit(int npass = 1);

  /// quadruple split: divide each triangle in four, and adapt differently
  /// on the boundary y=0
  void quadSplit_forsemi(const Vct3 &ctr, int npass = 1);

  /// remove triangles which share the same vertices
  void dropDuplicates();

  /// drop triangles which are identified as lying inside a closed manifold
  uint dropInternalTriangles(uint itx, bool usetags = false);

  /// drop triangles which are identified as lying inside a closed manifold
  uint dropInternalTriangles(const Indices &idx, bool usetags = false);

  /// drop triangle which can be reached from a singly connected edge
  uint dropOrphanRidges(const Indices &killtags);

  /// cleanup and drop internals until no triply connected edges remain
  bool mergeAndDrop(uint itx, Real thrstart, Real thrend);

  /// try to join open (singly-connected) edges
  void joinSingleEdges(Real threshold);

  /// try to remove extremely thin (stretched) triangles
  uint dropStretchedTriangles(Real maxstretch, Real maxphi);

  /// remove vertices with edge degree 3
  uint dropTriStars();

  /// split mesh along ridges
  void splitRidges(Indices &ridges, Real cosphi = 0.5);

private:
  /// try to flip edge ei
  bool flipEdge(uint ei, Real mincphi, Indices &vmod);

  /// extend orphan front
  void marchOrphanFront(uint f, const Indices &killtags, Indices &forphan) const;

  /// choose next triangle across edge ei
  uint nextExternalTriangle(uint fcur, uint ei, bool usetags) const;

  /// count the number of multiple edges connected to triangle f
  uint countMultipleEdges(uint fcur) const;

  /// starting from a given edge, find triangles bounded by triple edges
  void findEnclosedGroup(uint fcur, Indices &ftri) const;

  /// determine a point on the inside of triangle fix
  bool triInternalPoint(uint fix, Vct3 &hole) const;

protected:
  typedef std::map<int, std::string> TagMap;

  /// mesh vertices and normal vectors
  PointList<3> vtx, nrm;

  /// vector of triangles
  TriFaceArray faces;

  /// vector of edges
  TriEdgeArray edges;

  /// connectivity data
  ConnectMap v2f, v2e, e2f, f2e;

  /// tag to component name map
  TagMap tagnames;
};

inline void swap(TriMesh &a, TriMesh &b)
{
  a.swap(b);
}

#endif
