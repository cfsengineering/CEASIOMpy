
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

#ifndef SURF_TOPOEDGE_H
#define SURF_TOPOEDGE_H

#include "forward.h"
#include <genua/point.h>

/** Topological edge, connecting two or more faces.
 *
 * A topological edge can be the boundary of an isolated face. However, when
 * the full model is a two-manifold, then each edge must have exactly two
 * adjacent faces.
 *
 * \ingroup meshgen
 * \sa TopoFace, TopoVertex, Topology
 */
class TopoEdge
{
public:

  enum MatchResult { NoMatch, ForwardFit, ReverseFit,
                     ForwardOverlap, ReverseOverlap };

  enum Origin { Unknown, Specified, Intersection };

  /// create empty edge
  TopoEdge() : m_orig(Unknown), m_bInjected(false) {}

  /// create edge between existing vertices, not attached yet
  TopoEdge(uint a, uint b) : m_orig(Specified), m_bInjected(false) {
    assign(a,b);
  }

  /// initialize boundary edge with vertex indices
  TopoEdge(const Topology &topo, uint iface, uint a, uint b);

  /// assign vertices
  void assign(uint a, uint b) {
    if (a < b) {
      m_vix[0] = a;
      m_vix[1] = b;
    } else {
      m_vix[0] = b;
      m_vix[1] = a;
    }
  }

  /// determine how edge was created
  int edgeOrigin() const {return m_orig;}

  /// change origin flag
  void edgeOrigin(Origin flag) {m_orig = flag;}

  /// access source vertex
  uint source() const {return m_vix[0];}

  /// access target vertex
  uint target() const {return m_vix[1];}

  /// compare edges
  bool operator< (const TopoEdge & e) const {
    if (source() < e.source())
      return true;
    else if (e.source() > source())
      return false;
    else
      return target() < e.target();
  }

  /// edge equality
  bool operator== (const TopoEdge & e) const {
    return (source() == e.source()) and (target() == e.target());
  }

  /// evaluate curve underlying this edge
  Vct3 eval(uint lfi, Real t) const;

  /// compare geometry with another edge
  int compare(const Topology &topo, const TopoEdge &e,
              Real tol=gmepsilon) const;

  /// a circular edge starts and ends at the same vertex
  bool circular() const {return source() == target();}

  /// number of connected faces
  uint nfaces() const {return m_faces.size();}

  /// access face i
  uint face(uint i) const {
    assert(i < m_faces.size());
    return m_faces[i];
  }

  /// access face i
  uint & face(uint i) {
    assert(i < m_faces.size());
    return m_faces[i];
  }

  /// access curve with local index k
  AbstractUvCurvePtr curve(uint k) const {
    assert(k < m_pcv.size());
    return m_pcv[k];
  }

  /// return local index of face i
  uint findFace(uint fix) const {
    const int nf = m_faces.size();
    for (int i=0; i<nf; ++i)
      if (m_faces[i] == fix)
        return i;
    return NotFound;
  }

  /// connect with curve cv on face fix
  uint attachFace(uint fix, AbstractUvCurvePtr pcv) {
    // one edge can contain same face multiple times (with different curves)
    m_faces.push_back(fix);
    m_pcv.push_back(pcv);
    return m_faces.size() - 1;
  }

  /// drop face with global index fix from connectivity
  bool detachFace(uint gfi) {
    uint k = findFace(gfi);
    if (k == NotFound)
      return false;
    m_faces.erase( m_faces.begin()+k );
    m_pcv.erase( m_pcv.begin()+k );
    return true;
  }

  /// detach edge from all faces
  void detach();

  /// check whether this edge connects two points on global face gfi
  int connects(uint gfi, const Vct2 &q1, const Vct2 &q2, Real tol=gmepsilon) const;

  /// split edge by inserting vertex v, make this the edge (a,v) and other (v,b)
  void split(Real t, uint v, TopoEdge &other);

  /// enforce a point to be present in discretization
  void enforcePoint(Real t);

  /// discretize while satisfying mesh refinement criteria on all faces
  const Vector & discretize(const Topology &topo);

  /// discretize using simple criteria on first face
  const Vector & discretize(const DcMeshCritBase &mcrit);

  /// enforce discretization
  void discretize(const Vector &t) {m_tp = t; m_bInjected = false;}

  /// access discretization pattern
  const Vector &pattern() const {return m_tp;}

  /// change discretization to include point p
  bool injectPoint(uint kf, const Vct2 &p, Real tol=gmepsilon);

  /// make compatible with another edge - inject intersections
  void injectIntersections(const Topology &topo, TopoEdge &e);

  /// determine whether a point was injected into edge after discretization
  bool pointInjected() const {return m_bInjected;}

  /// reset injection status
  void pointInjected(bool flag) {m_bInjected = flag;}

  /// number of points on discretized edge
  uint npoints() const {return m_tp.size();}

  /// retrieve discrete points in (u,v) space of face k
  Vct2 uvpoint(uint kface, uint ipoint) const;

  /// retrieve discrete point in 3D space
  Vct3 point(uint ipoint) const;

  /// generate lines for debugging
  void toMx(MxMesh &mx) const;

  /// plain text output for debugging
  void print(uint k, std::ostream &os) const;

  /// write plain text table for debugging
  void tabulate(const std::string &fn) const;

  /// create default curve, straight in parameter space
  static AbstractUvCurvePtr boundaryCurve(const Topology &topo,
                                          uint iface, uint a, uint b);

  /// test two edges for intersection in space of face index fix
  static bool intersects(uint fix, const TopoEdge &ea,
                         const TopoEdge &eb, Vct2 &t);

private:

  /// inject a set of parameter values
  void inject(const Topology &topo, uint iface, const Vector &ti);

private:

  /// continuous geometry representation in parameter space
  AbstractUvCurveArray m_pcv;

  /// discretization in curve parameter space
  Vector m_tp;

  /// curve parameter points enforced in discretization
  Vector m_ftp;

  /// faces connected to this edge
  Indices m_faces;

  /// vertex indices
  uint m_vix[2];

  /// tag which indicates how this edge was created
  Origin m_orig;

  /// flag indicating whether point was inserted on edge
  bool m_bInjected;
};

#endif // TOPOEDGE_H
