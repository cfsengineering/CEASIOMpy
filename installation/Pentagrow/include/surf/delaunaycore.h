
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
 
#ifndef SURF_DELAUNAYCORE_H
#define SURF_DELAUNAYCORE_H

#include "dcedge.h"
#include "dcface.h"
#include <boost/pool/object_pool.hpp>

class DcGeometry;
class ConnectMap;

/** Delaunay triangulations.

  This class encapsulates some of the core algorithms needed for
  constructing and refining constrained Delaunay triangulations. DelaunayCore
  stores the triangulation connectivity data using a butterfly edge data
  structure kept in a hash table, but no vertex geometry; it is therefore
  restricted to purely topological operations.

  Geometric functions such as an encroachment predicate or a triangle location
  function must therefore be supplied as function objects.

  This class is meant to supersede DnMesh once it supports the same
  functionality.

  \ingroup meshgen
  \sa DcEdge, DcFace, DcGeometry
*/
class DelaunayCore
{
public:

  enum InsertionFlag {NotInserted, EdgeSplit, FaceSplit,
                      VertexPresent, ExtendedOutward};

  enum StatusCode { StatusOk = 0,
                    ConstraintIntersection,
                    UnhandledMixedConstraint,
                    CannotEnforceEdge,
                    InconsistentTopology,
                    InsertPointOutOfDomain,
                    InsertCannotSplitEdge,
                    InsertTriangledNotFound,
                    ProtectedConstraintEncroached,
                    NumberOfStatusCodes };

  typedef std::pair<DcEdge*, uint> EncPair;
  typedef std::vector<EncPair> FlipStack;

  /// empty triangulation
  DelaunayCore(DcGeometry & geom, size_t reserveEdges=8192);

  /// enable/disable mesh extension when vertex inserted beyond current mesh
  void enableExtension(bool flag) { bInsertExtend = flag; }

  /// add a new face
  uint addFace(uint a, uint b, uint c);

  /// add multiple faces, will not check orientation (!)
  void addFaces(const Indices & tri);

  /// compute edges from faces, update connectivity; call only in initialization
  void fixate();

  /// erase edges which are not connected to any faces any more
  void eraseDetachedEdges();

  /// export triangles
  void triangles(Indices & tri) const;

  /// export constrained line segments
  void constrainedEdges(Indices &lns) const;

  /// compute vertex-to-face connectivity
  void vertexMap(uint nv, ConnectMap & v2f) const;

  /// number of faces, inclusing invalid ones
  uint nAllFaces() const {return faces.size();}

  /// number of valid faces
  uint nValidFaces() const {return faces.size() - invalidFaces.size();}

  /// access face f
  const DcFace & face(uint f) const {
    assert(f < faces.size());
    return faces[f];
  }

  /** Vertex insertion.
   Attempts to insert vertex c, return flag (InsertionFlag) indicating whether
  edge or face was split or vertex was found present in mesh. Optionally enforce
  Delaunay property by flipping edges. */
  int insertVertex(uint c, bool legalizeEdges=true);

  /** Constraint insertion.
  Insert constrained edges along not-yet inserted vertices c. Returns c.size()
  if operation successfull; returns zero if all vertices could be inserted but
  an edge enforcement failed, or n < c.size() if vertex n could not be inserted
  at all (lying on non-splittable edge, outside the domain etc.). */
  uint insertConstraint(const Indices & c,
                        int flags = DcEdge::Constrained,
                        bool legalizeEdges=true);

  /// change internal treatment of special edges by setting flag bits
  void setEdgeFlags(int pattern, int flags);

  /// change internal treatment of special edges by un-setting flag bits
  void unsetEdgeFlags(int pattern, int flags);

  /// protect constrained edges by ball where insertions are forbidden
  void protectConstraints(bool flag) { bProtectConstraints = flag; }

  /// split edge a-b, insert new vertex c in the middle
  bool splitEdge(DcEdge *pab, uint c, bool legalizeEdges=true);

  /// split face f, insert vertex x
  bool splitFace(uint f, uint x, bool legalizeEdges=true);

  /// extend triangulation : construct triangle using pab and vertex c
  void addExternalVertex(DcEdge *pab, uint c, bool legalizeEdges=true);

  /// access list of vertices inserted into constrained edges
  const Indices & verticesOnConstraints() const {return vinConEdges;}

  /// access list of vertices inserted into constrained edges
  Indices & verticesOnConstraints() {return vinConEdges;}

  /// flip edge, update connectivity
  bool flipEdge(DcEdge *pe);

  /// eat triangles away, starting at face f, stop at constraints
  uint eatHole(uint f);

  /// erase all faces connected to any of the sorted vertices in idx
  uint eraseFacesTouching(const Indices &idx);

  /// locate edge, return 0 if not found
  DcEdge *findEdge(uint s, uint t) const {
    if (s != t) {
      DcEdge etest(s, t);
      DcEdgeItr pos = edges.find(&etest);
      return (pos != edges.end()) ? *pos : nullptr;
    }
    return nullptr;
  }

  /// construct edge
  DcEdge *constructEdge(uint s, uint t) {
    assert(s != t);
    DcEdge *ep = (DcEdge *) edgePool.malloc();
    assert(ep != 0);
    return (new(ep) DcEdge(s, t));  // placed at ep
  }

  /// collect vertex diamond for edge pe
  bool diamond(DcEdge *pe, uint v[]) const;

  /// test whether a four-node neighborhood is convex
  bool isConvex(const uint v[]) const;

  /// mark all constrained vertices
  void constrainedVertices(std::vector<bool> & cvx,
                           int edgeflag = DcEdge::Constrained) const;

  /// mark boundary vertices
  void boundaryVertices(std::vector<bool> & bvx) const;

  /// remove all contents, release memory
  void clear();

  /// access status code (set when operation not successful)
  int lastStatusCode() const {return status;}

protected:

  /// copy construct edge
  DcEdge *constructEdge(const DcEdge & e) {
    assert(e.source() != e.target());
    DcEdge *ep = (DcEdge *) edgePool.malloc();
    assert(ep != 0);
    return (new(ep) DcEdge(e));  // placed at ep
  }

  /// erase edge from set and cache
  void eraseEdge(DcEdge *pe) {
    edges.erase(pe);
    if (pe != 0)
      pe->invalidate();
    //    for (int i=0; i<edge_cache_size; ++i)
    //      if (edgeCache[i] == pe)
    //        edgeCache[i] = 0;
  }

  /// given two adjacent faces, return vertex of topo not in t (Anglada 1997)
  uint angOpposedVertex(uint t, uint topo) const {
    assert(t < faces.size());
    assert(topo < faces.size());
    const uint *vtopo = faces[topo].vertices();
    for (int k=0; k<3; ++k)
      if ( faces[t].find(vtopo[k]) == NotFound )
        return vtopo[k];
    return NotFound;
  }

  /// return face adjacent to t which does not contain v
  uint angOpposedFace(uint t, uint p) const {
    assert(t < faces.size());
    const uint *vi = faces[t].vertices();
    for (int k=0; k<3; ++k) {
      const uint src = vi[k];
      const uint trg = vi[(k+1)%3];
      if (src == p or trg == p)
        continue;
      const DcEdge *pe = findEdge( src, trg );
      assert(pe != 0);
      assert(pe->left() == t or pe->right() == t);
      if (pe->left() == t)
        return pe->right();
      else
        return pe->left();
    }
    return NotFound;
  }

  /// triangulate the polygon given by a sorted vertex set (vbeg,vend]
  void triangulatePolygon(uint bs, uint bt,
                          Indices::const_iterator vbeg,
                          Indices::const_iterator vend);

  /// invalidate face
  void eraseFace(uint k);

  /// detach reference to face k from the edges of k
  void detachFace(uint k);

  /// legalize edge pe with respect to vertex v
  void legalizeEdge(uint src, uint trg, uint v);

  /// legalize edge pe with respect to vertex v
  void legalizeEdge(DcEdge *pe, uint v);

  /// search face cache for edge which may be flipped to obtain (s,t)
  DcEdge *searchCacheForFlip(uint s, uint t) const;

  /// extend face cache with immediate neighbor elements
  bool extendCache();

  /// enforce the presence of edge (src,trg) by erasing and retriangulating
  DcEdge *imprintIntersectingEdge(uint csrc, uint ctrg);

  /// enforce the presence of (src,trg) when it overlaps existing edges
  DcEdge *imprintOverlappingEdge(uint csrc, uint ctrg);

  /// called by both edge imprinting routines
  void carveAndTriangulate(uint src, uint trg, const Indices &ifaces,
                           Indices &vleft, Indices &vright);

  /// process an edge flip stack
  void legalizeStack(FlipStack & stack);

  /// start caching new faces
  void startFaceCaching() {
    faceCache.clear();
    bCacheFaces = true;
  }

  /// stop caching new faces
  void stopFaceCaching() {
    bCacheFaces = false;
  }

private:

  /// geometry evaluator
  DcGeometry & geo;

  /// pool allocator for edges
  boost::pool<> edgePool;

  /// edges
  DcEdgeHash edges;

  /// faces
  DcFaceArray faces;

  /// list of invalid faces
  Indices invalidFaces;

  /// keeps track of inserted faces
  Indices faceCache;

  /// vertices inserted on constrained edges
  Indices vinConEdges;

  /// code set when error occurs
  StatusCode status;

  /// forbid insertion inside ball around constrained edges?
  bool bProtectConstraints;

  /// flag indicating whether new faces should be cached
  bool bCacheFaces;

  /// is mesh extension by vertex insertion allowed?
  bool bInsertExtend;
};

#endif // DELAUNAYCORE_H
