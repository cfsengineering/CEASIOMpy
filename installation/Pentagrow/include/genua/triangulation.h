
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
 
#ifndef GENUA_TRIANGULATION_H
#define GENUA_TRIANGULATION_H

#include <deque>
#include <list>
#include <map>
#include <set>

#include "svector.h"
#include "trafo.h"
#include "bounds.h"
#include "edgeface.h"
#include "plane.h"
#include "xmlelement.h"
#include "sparse.h"

// container typedefs
typedef std::list<Edge> EdgeList;
typedef std::list<Face> FaceList;
typedef std::map<uint, EdgeList> EdgeMap;
typedef std::map<uint, FaceList> FaceMap;
typedef std::map<Edge, std::set<Face> > CrossMap;

/** Triangular surface.

  A triangulation consists of a collection of vertices (accessible in constant
  time) and connectivity information stored in classes Edge and Face, which use
  vertex indices as references. Triangulations in GTS format can be read with
  correct normal vector orientation, according to the convention used in GTS.

  Vertex normals are computed on initialization by averaging the face normals of
  adjacent triangles. Face fold angles (angle between face normals) can be
 computed
  with edgeTransAngle(), the solid angle at a vertex (between all adjacent
 faces)
  with solidAngle().

  \deprecated
  \ingroup mesh
  \sa TriMesh, CgMesh
  */
class Triangulation : public RFrame
{
  public:

    // iterator typedefs
    typedef PointList<3>::const_iterator vertex_iterator;
    typedef FaceList::const_iterator face_iterator;
    typedef EdgeList::const_iterator edge_iterator;

    /// empty construction
    Triangulation() {}

    /// copy construction: change triangulation pointers in faces
    Triangulation(const Triangulation & tg);

    /// virtual destructor
    virtual ~Triangulation() {}

    /// iterator access
    vertex_iterator vertex_begin() const
      {return vtx.begin();}

    /// iterator access
    vertex_iterator vertex_end() const
      {return vtx.end();}

    /// iterator access
    face_iterator face_begin() const
      {return faces.begin();}

    /// iterator access
    face_iterator face_end() const
      {return faces.end();}

    /// iterator to list of face which share vertex i
    face_iterator nb_face_begin(uint i) const;

    /// iterator to list of face which share vertex i
    face_iterator nb_face_end(uint i) const;

    /// iterator access
    edge_iterator edge_begin() const
      {return edges.begin();}

    /// iterator access
    edge_iterator edge_end() const
      {return edges.end();}

    /// iterator to list of edges which share vertex i
    edge_iterator nb_edge_begin(uint i) const;

    /// iterator to list of edges which share vertex i
    edge_iterator nb_edge_end(uint i) const;

    /// number of edges connected to vertex i
    uint degree(uint i) const;

    /// transform vertices
    void apply();

    /// information
    uint nvertices() const
      {return vtx.size();}

    /// information
    uint nedges() const
      {return edges.size();}

    /// information
    uint nfaces() const
      {return faces.size();}

    /// const access
    const Vct3 & vertex(uint i) const
      {assert(vtx.size() > i); return vtx[i];}

    /// mutable access
    Vct3 & vertex(uint i)
      {assert(vtx.size() > i); return vtx[i];}

    /// return reference to vertex list
    const PointList<3> & vertices() const {return vtx;}

    /// return reference to vertex list
    PointList<3> & vertices() {return vtx;}

    /// const access
    const Vct3 & normal(uint i) const
      {assert(nrm.size() > i); return nrm[i];}

    /// mutable access
    Vct3 & normal(uint i)
      {assert(nrm.size() > i); return nrm[i];}

    /// return reference to normal list
    const PointList<3> & normals() const {return nrm;}
    
    /// return neighbour vertices
    std::set<uint> nbVertices(uint idx) const;

    /// access face map
    FaceList nbFaces(uint idx) const;

    /// access face map
    std::set<Face> nbFaces(const Edge & e) const;

    /// access edge map
    const EdgeList & nbEdges(uint idx) const;

    /// compute solid angle at vertex idx
    virtual Real solidAngle(uint idx) const;

    /** compute ridge/valley criterion.
      Returns the angle between normals of the two faces meeting at e, signed
      positive if the edge is a 'ridge', i.e. its center lies above the CoG of
      the neighbor faces, and negative in the opposite case. */
    Real ridgeCriterion(const Edge & e) const;

    /// area center of face neighborhood of vertex i
    Vct3 barycenter(uint i) const;

    /// compute area (of the dual mesh cell) assigned to this vertex
    Real vertexArea(uint i) const;

    /// compute angle between faces containing e
    Real edgeAngleTrans(const Edge & e) const;

    /// compute angle between edge end vertices
    Real edgeAngleLong(const Edge & e) const;

    /// determine if e is on a surface boundary
    bool onBoundary(const Edge & e) const;

    /// triangulate point matrix
    void triangulate(const PointGrid<3> & pg);

    /// eat other surface (cleanup yourself)
    void merge(const Triangulation & tg);

    /// find vertex index closest to p (consider hint argument)
    uint nearest(const Vct3 & p, int pos=-1) const;

    /// determine closest vertex for each of the points in pts
    Indices nearest(const PointList<3> & pts) const;
    
    /// determine bounding box
    BndBox bbox() const;

    /// add vertex to list, return its index
    uint addVertex(const Vct3 & v)
      {vtx.push_back(v); return vtx.size()-1;}

    /// add (externally computed) normal vector
    uint addNormal(const Vct3 & nm)
      {nrm.push_back(nm.normalized()); return nrm.size()-1;}

    /// add a new face to triangulation (vertices must exist)
    void addFace(const Face & f);

    /// insert face in suitable place and update connectivity
    void insertFace(const Face & f);

    /// recreate edge list
    void rebuildEdgeList();

    /// update neighbourhood lists
    void updateNeighbours();
    
    /// recompute normal vectors only
    virtual void recompNormals();
    
    /// after adding all faces, recompute neighbours, normals, etc.
    void fixate();

    /// check consistency
    std::ostream & check(std::ostream & os) const;

    /** Remove duplicate vertices. Check face validity, rebuild
      edge list and connectivity. Does only process identical vertices
      (i.e. where distance < threshold) not connected by an edge.
    */
    void cleanup(Real threshold = gmepsilon, bool bonly = false);

    /// geometric relaxation - smoothes out sharp edges
    void relax(uint ni);

    /// split single edge, add new vertex and normal
    virtual void splitEdge(const Edge & e, bool ipol=true);

    /// collapse single edge, delete neighbor faces
    virtual void collapseEdge(const Edge & e);

    /// find edges which intersect plane and corresponding parameters
    Vector intersectingEdges(const Plane & pln, EdgeList & el) const;

    /// compute total area (sum of face areas)
    Real area() const;

    /// compute the enclosed volume (for manifolds)
    Real volume() const;

    /// return length of shortest edge
    Real shortestEdgeLength() const;

    /// simple estimation of curvature in direction s
    Real estimCurvature(uint i, const Vct3 & s) const;

    /// reverse normal direction of all faces
    void reverse();
    
    /// compute gradient matrix using angular averaging
    SpMatrix gradient(uint i) const;
    
    /// evaluate gradient of scalar surface field at i
    Vct3 gradient(uint i, const Vector & x) const;
    
    /// read a GTS surface
    virtual std::istream & readGTS(std::istream & is);

    /// write GTS-compatible output
    std::ostream & writeGTS(std::ostream & os) const;

    /// write visualization
    virtual std::ostream & writeOogl(std::ostream & os) const;

    /// write STL representation
    virtual std::ostream & writeSTL(std::ostream & os) const;

    /// write tecplot triangulation
    virtual std::ostream & writeTec(std::ostream & os) const;

    /// write in OBJ format (Alias wavefront)
    virtual std::ostream & writeObj(std::ostream & os) const;
    
    /// write to binary stream
    void writeBin(std::ostream & os) const;

    /// read from binary stream
    void readBin(std::istream & is);
    
    /// create XML representation
    virtual XmlElement toXml() const;

    /// create from XML representation
    virtual void fromXml(const XmlElement & xe);

    /// delete all vertices and faces
    void clear();
    
    /// compute memory requirements
    Real megabytes() const;
    
  protected:

    /// validity predicate for faces
    bool invalidFace(const Face & f) const;

    /// validity predicate for edges
    bool invalidEdge(const Edge & e) const;



    /// make vertex list unique
    void unify(Real threshold, bool bonly);

    /// rename indices
    virtual void rename(const Indices & idx);

    /// erase face from lists
    void removeFace(const Face & f);

    /// erase edge from lists
    void removeEdge(const Edge & e);

  protected:
  
    /// collection of vertices and normals
    PointList<3> vtx, nrm;
    
    /// compatible faces
    FaceList faces;
    
    /// polyheder edges
    EdgeList edges;
  
    /// maps vertex indices to edges
    EdgeMap v2e;
    
    /// maps vertex indices to faces
    FaceMap v2f;    
    
    /// maps edges to faces
    CrossMap e2f;

    friend class Edge;
    friend class Face;
};

#endif


