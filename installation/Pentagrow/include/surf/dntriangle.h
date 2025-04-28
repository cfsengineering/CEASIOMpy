
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
 
#ifndef SURF_DNTRIANGLE_H
#define SURF_DNTRIANGLE_H

#include <surf/surface.h>
#include <predicates/predicates.h>
#include "dnvertex.h"
#include "dnedge.h"

/** Triangle in 3D Delaunay triangulation.

  DnTriangle contains indices to its vertices, to three edges,
  and data about its circumsphere.

 \ingroup meshgen
 \sa DnMesh
  */
class DnTriangle
{
  public:
    
    /// create new triangle
    DnTriangle(uint a, uint b, uint c) {
      assert(a != NotFound);
      assert(b != NotFound);
      assert(c != NotFound);
      assert(a != b);
      assert(a != c);
      assert(b != c);
      order(a, b, c);
      nbe[2] = nbe[1] = nbe[0] = NotFound;
    }

    /// change triangle vertices
    void reconnect(uint a, uint b, uint c) {
      assert(a != NotFound);
      assert(b != NotFound);
      assert(c != NotFound);
      assert(a != b);
      assert(a != c);
      assert(b != c);
      order(a, b, c);
      nbe[2] = nbe[1] = nbe[0] = NotFound;
    }

    /// compute circumsphere
    void computeSphere(const Surface &, const DnVertexArray & vtx, bool spt) {
      assert(isValid());
      const Vct3 & p1(vtx[vi[0]].eval());
      const Vct3 & p2(vtx[vi[1]].eval());
      const Vct3 & p3(vtx[vi[2]].eval());      
      pcs = sCircumCenter(vtx);
      if (spt) {
        Real r = norm(pcs - p1);
        Vct3 tn( cross(p2-p1, p3-p1) );
        normalize(tn);
        pcs -= r*tn;
      } 
    }
    
    /// check if triangle is defined
    bool isValid() const {return (vi[0] != NotFound);}

    /// check if triangle has duplicate vertices
    bool hasDuplicates() const {
      if (vi[0] == vi[1])
        return true;
      else if (vi[0] == vi[2])
        return true;
      else if (vi[1] == vi[2])
        return true;
      else
        return false;
    }
    
    /// mark triangle as invalid
    void invalidate() {memset(vi, (int) NotFound, 3*sizeof(uint));}
    
    /// access vertices
    const uint *vertices() const {return vi;}
    
    /// access neighbor edges
    const uint *nbEdges() const {return nbe;}

    /// access neighbor edges
    uint *nbEdges() {return nbe;}
    
    /// reverse normal vector
    void reverse() {
      assert(isValid());
      std::swap(vi[1], vi[2]);
    }

    /// translate vertex indices
    void itranslate(const Indices & repl) {
      order(repl[vi[0]], repl[vi[1]], repl[vi[2]]);
    }

    /// find vertex opposed to edge e
    uint opposedVertex(const DnEdge & e) const {
      const uint s(e.source());
      const uint t(e.target());
      for (uint k=0; k<3; ++k) {
        uint v = vi[k];
        if (v != s and v != t)
          return v;
      }
      return NotFound;
    }

    /// replace a single vertex index
    uint replaceVertex(uint vold, uint vnew) {
      for (uint k=0; k<3; ++k) {
        if (vi[k] == vold) {
          vi[k] = vnew;
          order(vi[0], vi[1], vi[2]);
          return k;
        }
      }
      return NotFound;
    }
    
    /// add edge to neighbor list
    uint attachEdge(uint ei) {
      if (ei == NotFound)
        return NotFound;
      else if (nbe[0] == ei)
        return 0;
      else if (nbe[1] == ei)
        return 1;
      else if (nbe[2] == ei)
        return 2;
      else if (nbe[0] == NotFound) {
        nbe[0] = ei;
        return 0;
      } else if (nbe[1] == NotFound) {
        nbe[1] = ei;
        return 1;
      } else if (nbe[2] == NotFound) {
        nbe[2] = ei;
        return 2;
      } else
        return NotFound;
    }

    /// remove edge from neighbor list
    uint detachEdge(uint ei) {
      if (ei == NotFound)
        return NotFound;
      else if (nbe[0] == ei) {
        nbe[0] = NotFound;
        return 0;
      } else if (nbe[1] == ei) {
        nbe[1] = NotFound;
        return 1;
      } else if (nbe[2] == ei) {
        nbe[2] = NotFound;
        return 2;
      } else
        return NotFound;
    }
  
    /// replace neighbor edge
    uint replaceEdge(uint fold, uint fnew) {
      if (nbe[0] == fold) {
        nbe[0] = fnew;
        return 0;
      } else if (nbe[1] == fold) {
        nbe[1] = fnew;
        return 1;
      } else if (nbe[2] == fold) {
        nbe[2] = fnew;
        return 2;
      } else
        return NotFound;
    }
    
    /// compute normal vector (not normalized)
    Vct3 normal(const DnVertexArray & vtx) const {
      assert(isValid());
      const Vct3 & p1(vtx[vi[0]].eval());
      const Vct3 & p2(vtx[vi[1]].eval());
      const Vct3 & p3(vtx[vi[2]].eval());
      return cross(p2-p1, p3-p1);
    }

    /// center in parametric space
    Vct2 pCenter(const DnVertexArray & vtx) const {
      assert(isValid());
      const Vct2 & q1(vtx[vi[0]].parpos());
      const Vct2 & q2(vtx[vi[1]].parpos());
      const Vct2 & q3(vtx[vi[2]].parpos());
      return (q1+q2+q3) / 3.0;
    }

    /// center in real space
    Vct3 sCenter(const DnVertexArray & vtx) const {
      const Vct3 & p1(vtx[vi[0]].eval());
      const Vct3 & p2(vtx[vi[1]].eval());
      const Vct3 & p3(vtx[vi[2]].eval());
      return (p1+p2+p3) / 3.0;
    }

    /// compute parametric circumcenter
    Vct2 pCircumCenter(const DnVertexArray & vtx) const {
      assert(isValid());
      const Vct2 & q1(vtx[vi[0]].parpos());
      const Vct2 & q2(vtx[vi[1]].parpos());
      const Vct2 & q3(vtx[vi[2]].parpos());

      // compute edge-normal directions
      Vct2 e1( q2-q1 );
      Vct2 e2( q3-q2 );
      Vct2 n1, n2;
      if (e1[1] != 0.0) {
        n1[0] = 1.0;
        n1[1] = -e1[0]/e1[1];
      } else {
        assert(e1[0] != 0.0);
        n1[0] = -e1[1]/e1[0];
        n1[1] = 1.0;
      }
      if (e2[1] != 0.0) {
        n2[0] = 1.0;
        n2[1] = -e2[0]/e2[1];
      } else {
        assert(e2[0] != 0.0);
        n2[0] = -e2[1]/e2[0];
        n2[1] = 1.0;
      }

      // intersect lines through edge midpoints
      Vct2 m1( 0.5*(q1+q2) );
      Vct2 m2( 0.5*(q2+q3) );

      Real a11 = n1[0];
      Real a12 = n1[1];
      Real a21 = -n2[0];
      Real a22 = -n2[1];
      Real det = a11*a22 - a12*a21;
      assert(det != 0.0);
      Real r1 = m2[0] - m1[0];
      Real r2 = m2[1] - m1[1];

      // line through m1 is m1 + s*n1
      Real s = (r1*a22 - r2*a12) / det;
      
      return m1 + s*n1;
    }

    /// compute spatial circumcenter
    Vct3 sCircumCenter(const DnVertexArray & vtx) const {
      assert(isValid());
      const Vct3 & p1(vtx[vi[0]].eval());
      const Vct3 & p2(vtx[vi[1]].eval());
      const Vct3 & p3(vtx[vi[2]].eval());

      // triangle normal and edge-normal directions
      Vct3 tn( cross(p2-p1,p3-p1) );
      Vct3 e1( cross(tn, p2-p1) );
      Vct3 e2( cross(tn, p3-p2) );
      
      // edge midpoints
      Vct3 m1( 0.5*(p1+p2) );
      Vct3 m2( 0.5*(p2+p3) );

      Real a11(0.0), a12(0.0), a21(0.0), a22(0.0);
      Real r1(0.0), r2(0.0);
      for (uint i=0; i<3; i++) {
        a11 +=  sq(e1[i]);
        a12 -= e1[i]*e2[i];
        a22 += sq(e2[i]);
        r1 -= (m1[i] - m2[i])*e1[i];
        r2 += (m1[i] - m2[i])*e2[i];
      }
      a21 = a12;

      // zero means lines are parallel
      Real det = a11*a22 - a12*a21;
      if (det == 0.0) {
        return m1 + huge*e1;
      }

      Real s = (r1*a22 - r2*a12) / det;
      return m1 + s*e1;
    }
    
    /** Check if point is inside triangle.
    Returns 0,1,2 if p is exactly on the corresponding edge, -1 if it is
    inside the triangle, but not on the edge, and -2 if p is outside. */
    int isInside(const DnEdgeArray & edges, const DnVertexArray & vtx,
                 const Vct2 & p) const
    {
      assert(isValid());
      double ort;
      uint v1, v2;      
      for (uint k=0; k<3; ++k) {
        assert(nbe[k] != NotFound);
        const DnEdge & e(edges[nbe[k]]);
        v1 = find(e.source());
        v2 = find(e.target());
        assert(v1 != NotFound and v2 != NotFound);
        if (v1 == 1 and v2 == 0)
          std::swap(v1,v2);
        else if (v1 == 2 and v2 == 1)
          std::swap(v1,v2);
        else if (v1 == 0 and v2 == 2)
          std::swap(v1,v2);
        const Vct2 & q1(vtx[vi[v1]].parpos());
        const Vct2 & q2(vtx[vi[v2]].parpos());
        ort = jrsOrient2d(q1.pointer(), q2.pointer(), p.pointer());
        if (ort < 0)
          return -2;
        else if (ort == 0) {
          Vct2 tmp = q2-q1;
          Real t = dot(p-q1, tmp) / dot(tmp,tmp);
          if (t >= 0.0 and t <= 1.0)
            return k;
          else
            return -2;
        }
      }
      return -1;
    }
    
    /** Check if point is in circumcircle (uv-plane).
    Returns a positive value if i is inside, 0 if on, or negative if i is outside
    the circumcircle of the triangles vertices. */
    int inCircle(const DnVertexArray & vtx, uint i) const {
      const Vct2 & q1(vtx[vi[0]].parpos());
      const Vct2 & q2(vtx[vi[1]].parpos());
      const Vct2 & q3(vtx[vi[2]].parpos());
      const Vct2 & pt(vtx[i].parpos());
      double ict = jrsInCircle(q1.pointer(), q2.pointer(), q3.pointer(), pt.pointer());
      if (ict > 0.0)
        return 1;
      else if (ict < 0.0)
        return -1;    
      else
        return 0;
    }

    /// check if point is inside circumsphere
    int inSphere(const DnVertexArray & vtx, uint i) const {
      assert(isValid());
      const Vct3 & p1(vtx[vi[0]].eval());
      const Vct3 & p2(vtx[vi[1]].eval());
      const Vct3 & p3(vtx[vi[2]].eval());
      const Vct3 & pt(vtx[i].eval());
      double inside = jrsInSphere(p1.pointer(), p2.pointer(), p3.pointer(),
                               pcs.pointer(), pt.pointer());
      if (inside > 0.0)
        return 1;
      else if (inside < 0.0)
        return -1;
      else
        return 0;
    }

    /// compute projection (ut,vt,wt) of a 3D point on triangle
    Vct3 project(const DnVertexArray & vtx, const Vct3 & pt) const {
      const Vct3 & p1( vtx[vi[0]].eval() );
      const Vct3 & p2( vtx[vi[1]].eval() );
      const Vct3 & p3( vtx[vi[2]].eval() );

      Vct3 va, vb, vXi, vEta;
      va = p2 - p1;
      vb = p3 - p1;
      vXi = va - vb*(dot(va,vb)/dot(vb,vb));
      vEta = vb - va*(dot(va,vb)/dot(va,va));

      Vct3 s;
      s[0] = dot(pt-p1, vXi) / dot(vXi,vXi);
      s[1] = dot(pt-p1, vEta) / dot(vEta,vEta);
      s[2] = 1.0 - s[0] - s[1];
      return s;
    }
    
    /// compute projection (u,v) of a 3D point on mesh surface
    Vct2 sProject(const DnVertexArray & vtx, const Vct3 & pt) const {
      const Vct3 & p1( vtx[vi[0]].eval() );
      const Vct3 & p2( vtx[vi[1]].eval() );
      const Vct3 & p3( vtx[vi[2]].eval() );

      Vct3 va, vb, vXi, vEta;
      va = p2 - p1;
      vb = p3 - p1;
      vXi = va - vb*(dot(va,vb)/dot(vb,vb));
      vEta = vb - va*(dot(va,vb)/dot(va,va));

      Real up, vp, wp;
      up = dot(pt-p1, vXi) / dot(vXi,vXi);
      vp = dot(pt-p1, vEta) / dot(vEta,vEta);
      wp = 1.0 - up - vp;
      
      const Vct2 & q1(vtx[vi[0]].parpos());
      const Vct2 & q2(vtx[vi[1]].parpos());
      const Vct2 & q3(vtx[vi[2]].parpos());
      Vct2 qp( wp*q1 + up*q2 + vp*q3 );
      qp[0] = std::min(1.0, std::max(0.0, qp[0]));
      qp[1] = std::min(1.0, std::max(0.0, qp[1]));
      return qp;
    }
    
    /// make sure that the normal direction is correct (u,v space)
    void pFixDirection(const DnVertexArray & vtx) {
      const Vct2 & q1(vtx[vi[0]].parpos());
      const Vct2 & q2(vtx[vi[1]].parpos());
      const Vct2 & q3(vtx[vi[2]].parpos());
      assert(norm(q1-q2) > 0);
      assert(norm(q1-q3) > 0);
      assert(norm(q3-q2) > 0);
      double ot = jrsOrient2d(q1.pointer(), q2.pointer(), q3.pointer());
      if (ot < 0)
        reverse();
      assert(ot != 0);
    }
    
    /// make sure that the normal direction is correct (3-space)
    void sFixDirection(const DnVertexArray & vtx) {
      const Vct3 & n1( vtx[vi[0]].normal() );
      const Vct3 & n2( vtx[vi[1]].normal() );
      const Vct3 & n3( vtx[vi[2]].normal() );
      Vct3 sn( n1+n2+n3 );
      
      const Vct3 & p1( vtx[vi[0]].eval() );
      const Vct3 & p2( vtx[vi[1]].eval() );
      const Vct3 & p3( vtx[vi[2]].eval() );
      Vct3 tn( cross(p2-p1, p3-p1) );
      
      Real s = dot(sn, tn);
      if (s < 0)
        reverse();
      // assert(s != 0);
    }

    /// find index of vertex index v
    uint find(uint v) const {
      for (uint k=0; k<3; ++k)
        if (vi[k] == v)
          return k;
      return NotFound;
    }

    /// find index of edge index e
    uint findEdge(uint e) const {
      for (uint k=0; k<3; ++k)
        if (nbe[k] == e)
          return k;
      return NotFound;
    }

  private:

    /// establish correct ordering
    void order(uint a, uint b, uint c) {
      if (a < b and a < c) {
        vi[0] = a;
        vi[1] = b;
        vi[2] = c;
      } else if (b < a and b < c) {
        vi[0] = b;
        vi[1] = c;
        vi[2] = a;
      } else {
        vi[0] = c;
        vi[1] = a;
        vi[2] = b;
      }
    }

    /// decide if triangle touches a u-boundary with at vertex
    bool touchesUBound(const DnVertexArray & vtx) const {
      assert(isValid());
      for (uint k=0; k<3; ++k) {
        const Vct2 & q(vtx[vi[k]].parpos());
        if (q[0] == 0.0 or q[0] == 1.0)
          return true;
      }
      return false;
    }

  private:
    
    /// point on circumsphere
    Vct3 pcs;
    
    /// vertex indices
    uint vi[3];
    
    /// neighbor edges
    uint nbe[3];
};

#endif
