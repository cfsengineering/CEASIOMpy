
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
 
#ifndef SURF_DNEDGE_H
#define SURF_DNEDGE_H

/** Edge in a Delaunay triangulation.

  An edge is represented by its source and target vertices. Since all edges
  are undirected (i.e s-t is the same as t-s), indices are ordered so that
  source() is always smaller than target(). Additionally, an edge can be
  connected to two triangles, whose indices are stored.

  \ingroup meshgen
  \sa DnMesh
  */
class DnEdge
{
  public:
    
    /// construct new edge
    DnEdge(uint a, uint b) {
      reconnect(a,b);
    }

    /// connect edge to different vertices
    void reconnect(uint a, uint b) {
      assert(a != NotFound);
      assert(b != NotFound);
      if (a < b) {
        vi[0] = a;
        vi[1] = b;
      } else {
        vi[0] = b;
        vi[1] = a;
      }
      nbf[1] = nbf[0] = NotFound;
    }
    
    /// check if edge is defined
    bool isValid() const {return vi[0] != NotFound;}
    
    /// mark edge as invalid
    void invalidate() {vi[0] = vi[1] = NotFound;}
    
    /// access source vertex index
    uint source() const {return vi[0];}
    
    /// access target vertex index
    uint target() const {return vi[1];}
    
    /// count number of neighbor triangles
    uint nNeighbors() const {
      uint nnb(2);
      if (nbf[0] == NotFound)
        --nnb;
      if (nbf[1] == NotFound)
        --nnb;
      return nnb;
    }

    /// access neighbor triangle indices
    uint nbTriangle(uint i) const {
      assert(i < 2);
      return nbf[i];
    }

    /// access triangle which is opposed to triangle with index ti
    uint opposed(uint ti) const {
      if (nbf[0] == ti)
        return nbf[1];
      else if (nbf[1] == ti)
        return nbf[0];
      else
        return NotFound;
    }

    /// check if edge has vertex i
    uint find(uint i) const {
      if (vi[0] == i)
        return 0;
      else if (vi[1] == i)
        return 1;
      else
        return NotFound;
    }
    
    /// add triangle to neighbor list
    uint attachTriangle(uint fi) {
      if (nbf[0] == fi)
        return 0;
      else if (nbf[1] == fi)
        return 1;
      else if (nbf[0] == NotFound) {
        nbf[0] = fi;
        return 0;
      } else if (nbf[1] == NotFound) {
        nbf[1] = fi;
        return 1;
      } else
        return NotFound;
    }
    
    /// remove triangle from neighbor list
    uint detachTriangle(uint fi) {
      if (nbf[0] == fi) {
        nbf[0] = NotFound;
        return 0;
      } else if (nbf[1] == fi) {
        nbf[1] = NotFound;
        return 1;
      } else
        return NotFound;
    }

    /// replace a connection with another
    uint replaceTriangle(uint fold, uint fnew) {
      if (nbf[0] == fold) {
        nbf[0] = fnew;
        return 0;
      } else if (nbf[1] == fold) {
        nbf[1] = fnew;
        return 1;
      } else
        return NotFound;
    }

    /// define a unique ordering for edges
    bool operator< (const DnEdge & a) const {
      if (vi[0] < a.vi[0])
        return true;
      else if (vi[0] > a.vi[0])
        return false;
      else if (vi[1] < a.vi[1])
        return true;
      else
        return false;
    }

    /// define edge identity
    bool operator== (const DnEdge & a) const {
      if (vi[0] != a.vi[0])
        return false;
      else if (vi[1] != a.vi[1])
        return false;
      else
        return true;
    }

    /// compute where *this intersects (a,b) in the parameter domain
    Real pIntersect(const DnVertexArray & vtx, uint a, uint b) const {
      assert(isValid());
      const Vct2 & p1(vtx[vi[0]].parpos());
      const Vct2 & p2(vtx[vi[1]].parpos());
      const Vct2 & pa(vtx[a].parpos());
      const Vct2 & pb(vtx[b].parpos());      
      Real a11 = p2[0] - p1[0];
      Real a21 = p2[1] - p1[1];
      Real a12 = pa[0] - pb[0];
      Real a22 = pa[1] - pb[1];
      Real det = a11*a22 - a12*a21;
      if (fabs(det) < gmepsilon)
        return huge;
      Real r1 = pa[0] - p1[0];
      Real r2 = pa[1] - p1[1];
      Real s = (r1*a22 - r2*a12) / det;
      return s;
    }

    /// test if *this intersects (a,b) in the parameter domain
    bool pIntersects(const DnVertexArray & vtx, uint a, uint b) const {
      assert(isValid());
      const Vct2 & p1(vtx[vi[0]].parpos());
      const Vct2 & p2(vtx[vi[1]].parpos());
      const Vct2 & pa(vtx[a].parpos());
      const Vct2 & pb(vtx[b].parpos());      
      Real a11 = p2[0] - p1[0];
      Real a21 = p2[1] - p1[1];
      Real a12 = pa[0] - pb[0];
      Real a22 = pa[1] - pb[1];
      Real det = a11*a22 - a12*a21;
      if (fabs(det) < gmepsilon)
        return false;
      Real r1 = pa[0] - p1[0];
      Real r2 = pa[1] - p1[1];
      Real s = (r1*a22 - r2*a12) / det;
      if (s < 0.0 or s > 1.0)
        return false;
      Real t = (a11*r2 - a21*r1) / det;
      if (t < 0.0 or t > 1.0)
        return false;
      else 
        return true;
    }
    
    /// test if *this overlaps (a,b) in 3D space with small distance
    bool sIntersects(const Surface & srf, const DnVertexArray & vtx, uint a, uint b) const {
      assert(isValid());
      const Vct3 & p1(vtx[vi[0]].eval());
      const Vct3 & p2(vtx[vi[1]].eval());
      const Vct3 & pa(vtx[a].eval());
      const Vct3 & pb(vtx[b].eval());      
      
      // minimize distance between *this and line (a,b)
      Real a11(0.0), a12(0.0), a22(0.0);
      Real d1, d2, d3, r1(0.0), r2(0.0);
      for (uint k=0; k<3; ++k) {
        d1 = p2[k] - p1[k];
        d2 = pb[k] - pa[k];
        d3 = p1[k] - pa[k];
        a11 += d1*d1;
        a12 -= d1*d2;
        a22 += d2*d2;
        r1  -= d1*d3;
        r2  += d2*d3; 
      }
      Real a21 = a12;
      Real det = a11*a22 - a12*a21;
      if (fabs(det) < gmepsilon)
        return false;
      Real s = (r1*a22 - r2*a12) / det;
      if (s < 0.0 or s > 1.0)
        return false;
      Real t = (a11*r2 - a21*r1) / det;
      if (t < 0.0 or t > 1.0)
        return false;
      
      // compute line-line distance in 3D space
      Vct3 pself( (1.-s)*p1 + s*p2 );
      Vct3 pother( (1.-t)*pa + t*pb );
      Real lldst = norm(pself - pother);
      if (lldst < gmepsilon)
        return true;
      
      // at the point where the two lines are nearest, compute
      // the distance of the projection point on each line to the surface
      Vct2 qself( (1.-s)*vtx[vi[0]].parpos() + s*vtx[vi[1]].parpos() );
      Real sgap = norm(pself - srf.eval(qself[0], qself[1]));
      Vct2 qother( (1.-t)*vtx[a].parpos() + t*vtx[b].parpos() );
      Real tgap = norm(pother - srf.eval(qother[0], qother[1]));
      
      // lines are considered intersecting if their distance is smaller
      // than the gap between the lines and the surface
      if (lldst < 2*std::max(sgap,tgap))
        return true;
      else
        return false;  
    }
    
    /// edge length in parameter space
    Real pLength(const DnVertexArray & vtx) const {
      return norm(vtx[vi[0]].parpos() - vtx[vi[1]].parpos());
    }
    
    /// edge length in 3D space
    Real sLength(const DnVertexArray & vtx) const {
      return norm(vtx[vi[0]].eval() - vtx[vi[1]].eval());
    }

  private:
    
    /// source and target edge
    uint vi[2];
    
    /// exactly two neighbor faces
    uint nbf[2];
};

#endif
