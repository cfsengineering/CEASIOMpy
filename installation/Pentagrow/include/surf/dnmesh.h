
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
 
#ifndef SURF_DNMESH_H
#define SURF_DNMESH_H

#include <vector>
#include <set>
#include <genua/boxsearchtree.h>
#include <genua/rsearchtree.h>
#include <genua/xmlelement.h>
#include <surf/surface.h>
#include "dnvertex.h"
#include "dnedge.h"
#include "dntriangle.h"

typedef enum {DnPlane, DnSpatial} DnType;

struct DnTriangleShape;
class DnRefineCriterion;

/** Mesh generation engine.

  DnMesh implements generation of unstructured surface meshes using 
  Delaunay triangulation. Both plane Delaunay triangulation and Chew's
  variant for curved surfaces are supported. For three-dimensional 
  surfaces, Chew's algorithm yields vastly superior meshes, but puts 
  stringent requirements on the initial state if used for refinement.

  *Note:* This is the legacy surface mesh generator still used in sumo
  but to be replaced by DelaunayCore in the future.

  \ingroup meshgen
  \sa DelaunayCore
  */ 
class DnMesh
{
  public:    

    /// create generator for surface s
    DnMesh(SurfacePtr s, DnType t);

    /// evaluate the surface
    Vct3 eval(Real u, Real v) const {return psf->eval(u,v);}
    
    /// initialize with an equidistant mesh spaced nu x nv
    void init(uint nu, uint nv);

    /// initialize with structured mesh
    void init(const Vector & up, const Vector & vp);
    
    /// initialize with arbitrary point grid
    void init(const PointGrid<2> & pg);

    /// initialize point grid and cascade to remove stretched triangles
    void init(const PointGrid<2> & pg, Real maxstretch, uint kins=9);
    
    /// start with (optionally constrained) boundary, return true on success
    bool initBoundary(const PointList<2> & pts);
    
    /// fill a polygonal boundary for initialization
    bool initPolygon(const PointList<2> & pts);
    
    /// import a triangular mesh
    uint importMesh(const PointList<2> & pts, const Indices & qtri);
    
    /// export a triangular mesh (2D)
    uint exportMesh(PointList<2> & pts, Indices & qtri) const;
    
    /// export a triangular mesh (3D)
    uint exportMesh(PointList<2> & pp, PointList<3> & vtx, 
                    PointList<3> & nrm, Indices & qtri) const;
    
    /// current number of vertices
    uint nvertices() const {return vertices.size();}

    /// current number of edges
    uint nedges() const {return edges.size()-iDeadEdges.size();}

    /// current number of triangles
    uint nfaces() const {return triangles.size()-iDeadTriangles.size();}

    /// number of triangles, including invalid ones (!)
    uint nAllTriangles() const {return triangles.size();}

    /// access parametric vertex position
    const Vct2 & parpos(uint i) const {
      assert(i < vertices.size());
      return vertices[i].parpos();
    }

    /// access 3D space position of vertex i
    const Vct3 & position(uint i) const {
      assert(i < vertices.size());
      return vertices[i].eval();
    }
    
    /// access surface normal of vertex i
    const Vct3 & normal(uint i) const {
      assert(i < vertices.size());
      return vertices[i].normal();
    }

    /// access vertex indices of triangle k, may return 0 for invalid triangle
    const uint *triangleVertices(uint k) const {
      assert(k < triangles.size());
      const DnTriangle & t( triangles[k] );
      return t.isValid() ? t.vertices() : 0;
    }

    /// change triangulation mode (hope that you know what you are doing)
    void switchMode(DnType t) {type = t;}
    
    /// does not work yet
    uint elimNeedles(Real maxstretch, Real maxphi);
    
    /** Add constrained segments, return indices of constrained vertices.
    This method returns an empty set if insertion failed because of colliding
    constraints. */
    Indices addConstraint(const PointList<2> & pts, bool allowSplit = false);
    
    /// constrain an edge if it separates components with a normal jump between them
    void markKinks(Real dphi);
    
    /// disable splitting of boundary edges
    void disableBoundarySplit();
    
    /// enable splitting of boundary edges
    void enableBoundarySplit();
    
    /// insert vertex, sustain Delaunay property
    uint insertVertex(const Vct2 & p, bool & onBoundary);

    /// insert a point into a boundary edge
    uint insertBoundaryVertex(const Vct2 & p, Real ptol=gmepsilon);
    
    /// place a hole at p and remove affected triangles
    uint addHole(const Vct2 & p);

    /// remove stretched triangles
    void destretch(uint nmax, Real maxstretch);
    
    /// refine according to criteria (queue-based procedure)
    uint refine(const DnRefineCriterion & c);
    
    /// refine according to criteria (plain loop)
    void iterativeRefine(const DnRefineCriterion & c);
    
    /// split triangles near vertices in vlist
    void refineAround(const Indices & vlist, const DnRefineCriterion & c);
    
    /// plain laplacian smoothing (all unconstrained vertices)
    void smooth(uint niter = 1, Real omega = 1.0);
    
    /// smooth using vertex subset
    void smooth(const Indices & idx, uint niter, Real omega = 1.0);

    /// smooth only vertices in stretched triangles
    void smoothStretched(Real maxstretch);
    
    /// smooth stretched inside boxes only 
    void smoothStretched(Real maxstretch, std::vector<BndRect> & bxs);
    
    /// write 3D mesh to xml representation (MeshFields)
    XmlElement toXml() const;
    
    /// parameter space mesh to xml
    XmlElement pToXml() const;
    
    /// recompute all connectivity
    void fixate();

    /// set interruption flag to stop refinement 
    void setAbortFlag(bool flag) {bAbort = flag;}
    
    /// merge vertices closer than threshold
    void cleanup(Real xyzt, Real uvt);
    
    /// access error message
    const std::string & lastError() const {return errmsg;}
    
  private:

    /// add edge to triangulation, return index (no connectivity updates)
    uint addEdge(uint a, uint b);
    
    /// add triangle to triangulation, return index (no connectivity updates)
    uint addTriangle(uint a, uint b, uint c);

    /// try to add two triangles for the quad a-d, intelligently
    void addQuad(uint a, uint b, uint c, uint d);
    
    /// fix direction of triangle normal
    void fixDirection(DnTriangle & t) {
      if (type == DnSpatial)
        t.sFixDirection(vertices);
      else
        t.pFixDirection(vertices);
    }
    
    /// find edge index, requires sorted edge array
    uint findEdgeSorted(uint a, uint b) const {
      DnEdge etest(a,b);
      DnEdgeArray::const_iterator pos;
      pos = std::lower_bound(edges.begin(), edges.end(), etest);
      if (pos != edges.end() and *pos == etest)
        return std::distance(edges.begin(), pos);
      else
        return NotFound;
    }

    /// find edge index by topological search
    uint findEdgeTopo(uint a, uint b) const;

    /// check if edge may be flipped
    bool canFlip(uint i) const {
      return (not binary_search(iNoFlip.begin(), iNoFlip.end(), i));
    }

    /// check if edge is on kink
    bool isKink(uint i) const {
      return binary_search(iKinkEdge.begin(), iKinkEdge.end(), i);
    }
    
    /// check if edge may be split
    bool canSplit(uint i) const {
      return (not binary_search(iNoSplit.begin(), iNoSplit.end(), i));
    }
    
    /// register edge i as non-flippable
    void forbidFlip(uint i) {
      Indices::iterator pos;
      pos = std::lower_bound(iNoFlip.begin(), iNoFlip.end(), i);
      if (pos == iNoFlip.end() or *pos != i)
        iNoFlip.insert(pos, i);
    }
    
    /// register edge i as non-flippable
    void forbidSplit(uint i) {
      Indices::iterator pos;
      pos = std::lower_bound(iNoSplit.begin(), iNoSplit.end(), i);
      if (pos == iNoSplit.end() or *pos != i)
        iNoSplit.insert(pos, i);
    }
    
    /// locate triangle which contains position vertex p (2D algorithm)
    int locateTriangle(const Vct2 & p, uint vnear, uint & ti) const;
    
    /// locate triangle which contains vertex ni (flexible algorithm)
    int locateTriangle(uint ni, uint vnear, uint & ti) const;
    
    /// delete triangle, detach from vertices
    void killTriangle(uint ti);

    /// delete edge (no connectivity updates)
    void killEdge(uint ei);

    /// split one triangle into three
    void splitTriangle(uint ti, uint ni);

    /// split two triangles into four
    bool splitEdge(uint ei, uint ni);
    
    /// insert new vertex at midpoint if possible
    bool refineEdge(uint ei, Real minlen);
    
    /// find point to insert when refining edge ei
    uint findDivider(uint ei, Real minlen);
    
    /// determine if and how to refine triangle t 
    bool refineTriangle(uint tix, Real mxs, Real minlen);
    
    /// move v to its barycenter, if legal
    void smoothVertex(uint v);
    
    /// flip edge
    bool flipEdge(uint ei);

    /// recusively flip edges to establish Delauny property
    bool legalizeEdge(uint ei, uint v);

    /// make sure that edge a,b occurs in triangulation
    uint enforceEdge(uint a, uint b);
    
    /// compute edge neighborhood
    uint findNeighborhood(uint ei, uint v[4], uint nbe[4], uint nbf[2]) const;

    /// collect all edges which run into vertex i
    void collectNbEdges(uint i, Indices & edg, bool allEdges=false) const;

    /// kill triangles starting from ti until constrained edges are encountered
    uint recursiveErase(uint ti);

    /// collect triangles to erase
    uint carveHole(uint ti);

    /// insert edge which cannot be inserted using edge flips alone
    uint insertSegment(uint a, uint b);

    /// suitable orientation test sepending on mesh type
    Real orientation(uint a, uint b, uint c) const {
      if (type == DnSpatial) 
        return sOrientation(a, b, c);
      else
        return pOrientation(a, b, c);
    }
    
    /// orientation test in 2D
    Real pOrientation(uint a, uint b, uint c) const;
    
    /// orientation test in 3D
    Real sOrientation(uint a, uint b, uint c) const;
    
    /// test if vertex ni is inside triangle ti
    int isInside(uint ti, uint ni) const {
      if (type == DnSpatial)
        return sIsInside(ti, ni);
      else 
        return pIsInside(ti, ni);
    }
    
    /// test if vertex ni is inside triangle ti
    int sIsInside(uint ti, uint ni) const;
    
    /// special case of vertex on wrapped boundary
    int sIsOnBoundaryEdge(uint ti, uint ni) const;
    
    /// test if vertex ni is inside triangle ti
    int pIsInside(uint ti, uint ni) const;
    
    /// test if edge ei intersects line a-b
    bool intersects(uint ei, uint a, uint b) const {
      if (type == DnSpatial)
        return sIntersects(ei, a, b);
      else
        return edges[ei].pIntersects(vertices, a, b);
    }
    
    /// test if a and b lie on different side of ei (intersection)
    bool sIntersects(uint ei, uint a, uint b) const;
    
    /// triangulate the polygon above the edge ei
    bool triangulatePolygon(uint ei, const Indices & v);

    /// compute edge lengths, return triangle area
    void classify(uint ti, Real maxstretch, DnTriangleShape & shp) const;
    
    /// try to merge source and target of eshort
    bool collapseEdge(uint eshort);
    
    /// change vdrop to vkeep in all faces connected to vdrop
    void fuseVertices(uint vdrop, uint vkeep);
    
    /// refine a triangle with one long side and a large angle
    bool destroyHat(uint ti, uint elong);
    
    /// check if the neighborhood v is convex
    bool isConvexSet(uint v[4]) const;
    
    /// displace a vertex to the barycenter of its ring-1 neighborhood
    void centerVertex(uint i, Real omega = 1.0);
    
    /// collect the surrounding polygon for an interior point
    void constructPolygon(uint v, Indices & ip) const;
    
    /// check if pt is inside polygon determined by ip
    bool ptInPolygon(const Vct2 & pt, const Indices & ip) const;
    
    /// check if vertex v can be moved to pt without tangling the mesh
    bool vertexCanMove(uint v, const Vct2 & pt) const;
    
    /// debugging : check local connectivity for consistency (aborts on error)
    uint checkConnectivity(uint v, Indices & nbv) const;
    
    /// delete everything
    void clear();
    
    /// prepare list of changed triangles
    uint nntriangles() {
      sort_unique(newTriangles);
      if ((not newTriangles.empty()) and newTriangles.back() == NotFound)
        newTriangles.pop_back();
      return newTriangles.size();
    }
    
    /// prepare list of changed edges
    uint nnedges() {
      sort_unique(newEdges);
      if ((not newEdges.empty()) and newEdges.back() == NotFound)
        newEdges.pop_back();
      return newEdges.size();
    }

  private:

    /// Delaunay algorithm used
    DnType type;
    
    /// underlying continuous surface
    SurfacePtr psf;
    
    /// vertex array
    DnVertexArray vertices;

    /// edge array
    DnEdgeArray edges;

    /// triangle array
    DnTriangleArray triangles;

    /// point search tree
    RSearchTree btree;

    /// dead edges and triangles
    Indices iDeadEdges, iDeadTriangles;

    /// edges which may not be flipped or split
    Indices iNoFlip, iKinkEdge, iNoSplit;

    /// newly created edges or modified triangles
    Indices newEdges, newTriangles;

    /// flag which indicates if geometry is wrapped in u-direction
    bool uwrap, depinsert, nowrefining;
    
    /// refinement is interrupted if this flag is set to true 
    bool bAbort;
    
    /// error message
    std::string errmsg;
};

#endif
