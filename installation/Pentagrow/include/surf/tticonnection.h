
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
 
#ifndef SURF_TTICONNECTION_H
#define SURF_TTICONNECTION_H

#include <genua/svector.h>
#include <genua/defines.h>

class MeshComponent;
class TTIntersector;

/** Edge-edge connection between surfaces.

  \b Assumptions:
  - Endpoints of connected segments exist in mesh
  - Segments run along patch boundaries

  \ingroup meshgen
  \sa MeshComponent
  */
class TTiConnection
{
public:

  /// undefined connection
  TTiConnection() : acomp(0), bcomp(0) {}

  /// construct connection, general form
  TTiConnection(const MeshComponent *ac, const Vct2 & a1, const Vct2 & a2,
                const MeshComponent *bc, const Vct2 & b1, const Vct2 & b2)
                  : acomp(ac), bcomp(bc), ap1(a1), ap2(a2), bp1(b1), bp2(b2) {}

  /// connect v=1 of a with v=0 of b
  void vconnect(const MeshComponent *ac, const MeshComponent *bc,
                bool samesense=true) {
    acomp = ac;
    bcomp = bc;
    ap1 = vct(0.0, 1.0);
    ap2 = vct(1.0, 1.0);
    if (samesense) {
      bp1 = vct(0.0, 0.0);
      bp2 = vct(1.0, 0.0);
    } else {
      bp1 = vct(1.0, 0.0);
      bp2 = vct(0.0, 0.0);
    }
  }

  /// connect u=1 of a with u=0 of b
  void uconnect(const MeshComponent *ac, const MeshComponent *bc,
                bool samesense=true) {
    acomp = ac;
    bcomp = bc;
    ap1 = vct(1.0, 0.0);
    ap2 = vct(1.0, 1.0);
    if (samesense) {
      bp1 = vct(0.0, 0.0);
      bp2 = vct(0.0, 1.0);
    } else {
      bp1 = vct(0.0, 1.0);
      bp2 = vct(0.0, 0.0);
    }
  }

  /// add intersection segments to intersector, requires sorted faces in tti
  bool appendSegments(TTIntersector & tti);

private:

  struct ConVertex
  {
  public:
    ConVertex() : cmp(0), vix(NotFound) {}
    ConVertex(const MeshComponent *c, Real t, uint v)
      : cmp(c), tc(t), vix(v) {}
    bool operator< (const ConVertex & a) const {return tc < a.tc;}
    bool operator== (const ConVertex & a) const {return tc == a.tc;}
    const Vct3 & pos() const;
  public:
    const MeshComponent *cmp;
    Real tc;                     // edge/border arclength parameter
    uint vix;                    // vertex index
  };

  typedef std::vector<ConVertex> ConVertexArray;

  /// determine all edges of component which are on segment p1,p2
  bool collectCandidates(const MeshComponent *comp,
                         const Vct2 & p1, const Vct2 & p2,
                         Indices & edg);

  /// test a pair of edges for possible connection
  bool connectedPair(uint ae, uint be, Vct3 st[]) const;

  /// find the intersector triangle index from boundary edge
  uint triangleFromEdge(const TTIntersector & tti,
                        const MeshComponent *comp, uint eix) const;

  /// find the intersector triangle index from boundary vertex
  uint triangleFromVertex(const TTIntersector & tti,
                          const MeshComponent *comp, uint vix) const;

  /// find the edge for which the foorpoint of p is nearest p
  uint nearestEdge(const MeshComponent *cmp, const Indices & edges,
                   const Vct3 & p) const;

private:

  /// connected components
  const MeshComponent *acomp, *bcomp;

  /// connections are single linear segments
  Vct2 ap1, ap2, bp1, bp2;

  /// connection vertices
  ConVertexArray bvx;
};

typedef std::vector<TTiConnection> TTiConnectionArray;

#endif // TTICONNECTION_H
