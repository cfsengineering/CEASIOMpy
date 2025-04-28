
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
 
#ifndef SURF_TOPOLOGY_H
#define SURF_TOPOLOGY_H

#include "forward.h"
#include "topoedge.h"
#include "topoface.h"
#include "topovertex.h"

/** Container for topology information.
 *
 * Class Topology stores faces and edges along with vertex data.
 *
 * \ingroup meshgen
 * \sa TopoVertex, TopoEdge, TopoFace
 */
class Topology
{
public:

  /// create empty topology object
  Topology() {}

  /// number of faces defined
  uint nfaces() const {return m_faces.size();}

  /// number of edges defined
  uint nedges() const {return m_edges.size();}

  /// add surface, generate four boundary edges by default
  uint appendFace(SurfacePtr psf, bool uperiodic=false, bool vperiodic=false);

  /// append an existing face
  uint appendFace(const TopoFace &f);

  /// generate a plain edge between vertices a,b
  uint appendEdge(uint iface, uint a, uint b);

  /// append an existing edge
  uint appendEdge(const TopoEdge &edg);

  /// add a topological vertex
  uint appendVertex(uint iface, const Vct2 &uvp);

  /// add a topological vertex
  uint appendVertex(uint ifa, const Vct2 &uva,
                    uint ifb, const Vct2 &uvb);

  /// test whether face i is adjacent to face j
  bool shareEdge(uint i, uint j) const;

  /// introduce connections between face fa and edge ea
  void connectEdge(uint fa, uint ea,
                   AbstractUvCurvePtr pcv, bool isHole=false);

  /// connect face fa with face fb along edge ea/eb, return true on success
  bool connectFaces(uint a, uint b, uint ea, uint eb, Real tol=gmepsilon);

  /// try to connect two faces by searching for matching edges
  bool connectFaces(uint fa, uint fb, Real tol=gmepsilon);

  /// connect v = 1 of a to v = 0 of b
  bool vEnchain(uint a, uint b, Real tol=gmepsilon);

  /// add a set of faces and connect them in v-direction
  bool vEnchain(const SurfaceArray &surfaces);

  /// construct a plane closing surface inside a closed-curve edge, return face index
  uint fillPlaneBoundary(uint ebound);

  /// access vertex by index
  const TopoVertex &vertex(uint k) const {
    assert(k < m_vertices.size());
    return m_vertices[k];
  }

  /// access vertex by index
  TopoVertex &vertex(uint k) {
    assert(k < m_vertices.size());
    return m_vertices[k];
  }

  /// linear search for vertex
  uint findVertex(uint iface, const Vct2 & uvp);

  /// find global index of edge connecting pa and pb on face i
  uint findConnection(uint iface, const Vct2 &pa, const Vct2 &pb,
                      Real tol = gmepsilon) const
  {
    return face(iface).findConnection(*this, pa, pb, tol);
  }

  /// find global index of edge identified by tag on face i
  uint findConnection(uint iface, uint sideTag, Real tol = gmepsilon) const;

  /// access face by index
  const TopoFace &face(uint k) const {
    assert(k < m_faces.size());
    return m_faces[k];
  }

  /// access face by index
  TopoFace &face(uint k) {
    assert(k < m_faces.size());
    return m_faces[k];
  }

  /// access edge by index
  const TopoEdge &edge(uint k) const {
    assert(k < m_edges.size());
    return m_edges[k];
  }

  /// access edge by index
  TopoEdge &edge(uint k) {
    assert(k < m_edges.size());
    return m_edges[k];
  }

  /// discretize all edges
  void meshEdges();

  /// discretize all faces
  void meshFaces(bool allowConstraintSplit=false);

  /// merge meshes of all faces into one global mesh
  void mergeFaceMeshes(TriMesh &globMesh) const;

  /// compute intersections between faces which do not share an edge
  void intersect(TopoIsecArray &segm) const;

  /// join face meshes for debugging
  void toMx(MxMesh &mx) const;

  /// plain text output for debugging
  void print(std::ostream &os) const;

private:

  /// topological vertices
  std::vector<TopoVertex> m_vertices;

  /// faces (one for each surface)
  std::vector<TopoFace> m_faces;

  /// edges
  std::vector<TopoEdge> m_edges;
};

#endif // TOPOLOGY_H
