
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
 
#ifndef SURF_DNVERTEX_H
#define SURF_DNVERTEX_H

#include <iostream>
#include <genua/defines.h>
#include <genua/point.h>
#include <genua/line.h>
#include <surf/surface.h>

class DnVertex;
class DnEdge;
class DnTriangle;

typedef std::vector<DnVertex>      DnVertexArray;
typedef std::vector<DnEdge>        DnEdgeArray;
typedef std::vector<DnTriangle>    DnTriangleArray;

/** Triangulation vertex.

  Vertex representation which contains both the 3D position and the
  location of the point in the parameter plane (u,v). Hence, a DnVertex
  is always defined on a single parametric surface. The local surface
  normal is also stored.

 \ingroup meshgen
 \sa DnMesh
  */
class DnVertex
{
  public:
    
    /// undefined vertex
    DnVertex() {}
    
    /// create a new vertex
    DnVertex(const Surface & srf, const Vct2 & p) : uv(p) {
      Vct3 Su, Sv;
      srf.plane(uv[0], uv[1], xyz, Su, Sv);
      nrm = cross(Su, Sv);
      Real len = norm(nrm);
      if (len > 0)
        nrm /= len;
    
      assert(std::isfinite(uv[0]));
      assert(std::isfinite(uv[1]));
      assert(std::isfinite(xyz[0]));
      assert(std::isfinite(xyz[1]));
      assert(std::isfinite(xyz[2]));
      assert(std::isfinite(nrm[0]));
      assert(std::isfinite(nrm[1]));
      assert(std::isfinite(nrm[2]));
    }

    /// access parameter position
    const Vct2 & parpos() const {return uv;}
    
    /// access 3D position on surface
    const Vct3 & eval() const {return xyz;}
    
    /// access surface normal vector
    const Vct3 & normal() const {return nrm;}
    
    /// move vertex in parameter plain only
    void displace(const Vct2 & p) {
      uv = p;
      xyz = vct(p[0], p[1], 0.0);
      nrm = vct(0.0, 0.0, 1.0);
    }
    
    /// move vertex
    void displace(const Surface & srf, const Vct2 & p) {
      uv = p;
      xyz = srf.eval(uv[0], uv[1]);
      nrm = srf.normal(uv[0], uv[1]);
      
      assert(std::isfinite(uv[0]));
      assert(std::isfinite(uv[1]));
      assert(std::isfinite(xyz[0]));
      assert(std::isfinite(xyz[1]));
      assert(std::isfinite(xyz[2]));
      assert(std::isfinite(nrm[0]));
      assert(std::isfinite(nrm[1]));
      assert(std::isfinite(nrm[2]));
    }
    
    /// append a triangle to neighbor list
    uint attachTriangle(uint fi) {
      if (fi != NotFound) {
        nbf.push_back(fi);
        return nbf.size()-1;
      } else
        return NotFound;
    }
    
    /// remove triangle from neighbor list
    void detachTriangle(uint fi) {
      if (fi != NotFound) {
        Indices::iterator pos = std::find(nbf.begin(), nbf.end(), fi);
        if (pos != nbf.end())
          nbf.erase(pos);
      }
    }

    /// neighbor triangles
    const Indices & nbTriangles() const {return nbf;}

    /// remove all neighbors
    void clearNeighbors() {
      nbf.clear();
    }
    
    /// check if vertex can be moved to pt
    bool canMoveTo(const DnVertexArray & vtx, const Vct2 & pt) const;
    
  private:
    
    /// 3D position and local surface normal
    Vct3 xyz, nrm;
    
    /// position in parameter space
    Vct2 uv;
    
    /// list of triangles which share this vertex
    Indices nbf;
};

#endif

