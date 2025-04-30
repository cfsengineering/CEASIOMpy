
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
 
#ifndef SURF_TOPOFACE_H
#define SURF_TOPOFACE_H

#include "forward.h"
#include "surface.h"
#include "uvmapping.h"
#include "uvmapdelaunay.h"
#include <genua/trimesh.h>

/** Topological face.
 *
 * TopoFace represents a single surface which is bounded and constrained by
 * a number of TopoEdges.
 *
 * Mesh generation concept:
 * As a precondition, each face must be bounded by one or more edges which
 * define the outer boundary of the domain to discretize. Mesh generation starts
 * with tesselating all edges (from Topology) in a manner which conforms to
 * the mesh quality criteria defined on all faces which share the edge. Then,
 * the segments which represent the edges are inserted into the face meshes
 * which are, at first, initialized trivially. The next phase is the generation
 * of a first mesh on each face, followed by the computation and processing of
 * intersection lines in TopoSegmChain. The result of the face intersection
 * process is a set of new edges which represent the intersection lines, which
 * may be remeshed for a better local parameterization.
 *
 * Starting anew, each face mesh is cleared and the new set of edges, including
 * intersection lines, are enforced to be present in each face mesh.
 *
 * Faces which are meshed by an external procedure can import a predefined mesh
 * and set the keepExplicitMesh flag to avoid running the internal mesh
 * generation and injection of edges. With this flag set, intersections hitting
 * such surfaces can naturally not be handled.
 *
 * \ingroup meshgen
 * \sa Topology, TopoEdge, Surface
 **/
class TopoFace
{
public:

  enum MgBackend { DcMeshGen, JrsTriangle };

  /// create undefined face
  TopoFace();

  /// initialize face with surface
  explicit TopoFace(SurfacePtr psf, uint id);

  /// access surface
  SurfacePtr surface() const {return m_psf;}

  /// copy (!) discretization criterion, will be modified locally
  void criterion(DcMeshCritBasePtr pmc);

  /// access point merge tolerance
  Real sqMergeTolerance() const;

  /// change id
  void iid(uint id) {m_iid = id;}

  /// access discretization criterion
  DcMeshCritBasePtr criterion() const {return m_pmc;}

  /// edges connected to this
  const Indices & edges() const {return m_edges;}

  /// evaluate surface
  Vct3 eval(Real u, Real v) const { assert(m_psf); return m_psf->eval(u,v); }

  /// evaluate point and derivatives on surface
  void plane(Real u, Real v, Vct3 &S, Vct3 &Su, Vct3 &Sv) const {
    assert(m_psf);
    m_psf->plane(u, v, S, Su, Sv);
  }

  /// connect to edge e
  uint appendEdge(uint e, bool isHole = false) {
    uint ke = findEdge(e);
    if (ke == NotFound) {
      m_edges.push_back(e);
      m_edgeIsHole.push_back(isHole);
      return m_edges.size() - 1;
    } else {
      m_edgeIsHole[ke] = isHole;
      return ke;
    }
  }

  /// replace edge a with b, return true if successful
  bool replaceEdge(uint a, uint b) {
    const int ne = m_edges.size();
    for (int i=0; i<ne; ++i) {
      if (m_edges[i] == a) {
        m_edges[i] = b;
        return true;
      }
    }
    return false;
  }

  /// find local index of edge e
  uint findEdge(uint e) const {
    const int ne = m_edges.size();
    for (int i=0; i<ne; ++i)
      if (m_edges[i] == e)
        return i;
    return NotFound;
  }

  /// eliminate edge with global index e from connectivity
  uint detachEdge(uint e);

  /// identify the edge (global index) of this face which connects q1 and q2
  uint findConnection(const Topology &topo, const Vct2 &q1,
                      const Vct2 &q2, Real tol=gmepsilon) const;

  /// clear stored mesh, initialize (u,v) mapping if necessary
  void clearMesh();

  /// insert edge constraints into (u,v) mesh
  uint insertEdges(const Topology &topo, bool allowSplit = true);

  /// propagate constraint splitting to topological edges
  void pushSplitsToEdges(Topology &topo) const;

  /// indicates whether face wants to retain an externally generated mesh
  bool keepExplicitMesh() const {return m_keepExplicitMesh;}

  /// create mesh on face, accounting for discretized edges
  uint generateMesh(const Topology &topo);

  /// create mesh on face, starting with prescribed initial vertices
  uint generateMesh(const Topology &topo, const PointList<2> &pini);

  /// alternatively, import a mesh generated explicitly (call replaceEdgeNodes!)
  void importMesh(const PointList<2> &uvp, const Indices &tri,
                  bool keepExplicit=true);

  /// replace edge vertices in order to make edge nodes match exactly
  void replaceEdgeNodes(const Topology &topo, bool isecOnly=true);

  /// access mesh (once it has been generated)
  const TriMesh & mesh() const;

  /// access mesh (once it has been generated)
  TriMesh & mesh();

  /// access mesh coordinates in (u,v) space
  const PointList<2> & uvVertices() const;

  /// split edges which are intersected by newly introduced intersections
  void splitBoundaries(Topology &topo);

  /// debugging : write mesh and boundaries in (u,v) space
  void uvDump(const Topology &topo, const std::string &fname) const;

  /// plain-text debugging output
  void print(uint k, std::ostream &os) const;

  /// change backend to use for mesh generation
  static void backend(int b);

private:

  /// create internal mesh generator instance
  void constructMeshGen();

  /// remove triangles within internal hole edge k
  bool carveHole(const TopoEdge &e);

private:

  /// each face is backed by exactly one surface
  SurfacePtr m_psf;

  /// edges on this face
  Indices m_edges;

  /// indicates whether an edge is an internal boundary (a hole)
  std::vector<bool> m_edgeIsHole;

  /// criterion used for meshing
  DcMeshCritBasePtr m_pmc;

  /// dispatches to DC or JRS mesh generation
  MeshGeneratorPtr m_mg;

  /// integer id (index in Topology)
  uint m_iid;

  /// if true, keep externally/explicitely generated mesh
  bool m_keepExplicitMesh;

  /// mesh generator backend to use
  static int s_backend;
};

#endif // TOPOFACE_H
