
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
 
#ifndef SURF_TTINODE_H
#define SURF_TTINODE_H

#include "forward.h"
#include <vector>
#include <genua/svector.h>

class TTIntersection;

/** Point shared by two (or more) intersection segments.
 *
 * \ingroup meshgen
 * \sa MeshComponent
 */
class TTiNode
{
  public:
    
    /// undefined node
    TTiNode() : bEnforced(false) {
      std::fill(mpp, mpp+3, (const MeshComponent*) 0);
    }
    
    /// define node with 3D point alone
    TTiNode(const Vct3 & pt) : p(pt), bEnforced(false) {
      std::fill(mpp, mpp+3, (const MeshComponent*) 0);
      assert(std::isfinite(dot(pt,pt)));
    } 

    /// standard attachment to two intersection segments
    bool attach(const TTIntersection & sa, const TTIntersection & sb);
    
    /// set surface and parametric point association
    void parametric(uint k, const MeshComponent *s, const Vct2 & uv) {
      assert(k < 3);
      mpp[k] = s;
      q[k] = uv;
    }
    
    /// add parametric values for averaging 
    uint addParametric(const MeshComponent *s, const Vct2 & uv, uint ctr[]) {
      uint k;
      for (k = 0; k < 3; ++k) {
        if (mpp[k] == s or mpp[k] == 0)
          break;
      }
      assert(k < 3);
      mpp[k] = s;
      q[k] += uv; // accumulate uv, divided by count in average()
      ++ctr[k];
      return k;
    }
    
    /// compute average
    void average(const uint ctr[]);
    
    /// location in 3D space
    const Vct3 & location() const {return p;}
    
    /// normal in 3D space
    const Vct3 & normal() const {return nrm;}
    
    /// find index of patch pointer
    uint index(const MeshComponent *s) const {
      for (int k=0; k<3; ++k) {
        if (mpp[k] == s)
          return k;
      }
      return NotFound;
    }
    
    /// access uv-parameter on patch k
    const Vct2 & parameter(uint k) const {
      assert(k < 3);
      return q[k];
    }

    /// true if one of the attached segments is enforced
    bool enforced() const {return bEnforced;}
    
    /// change enforcement status
    void enforced(bool flag) {bEnforced = flag;}

    /// gap between defined surfaces 
    Real gap() const;
    
    /// move parameter towards boundary if within tol
    void snapToBoundary(Real tol);
    
    /// return true if this node is on any surface boundary
    bool onBoundary(Real tol = gmepsilon) const;

    /// determine local filter criteria from attached components
    void localCriteria(Real & maxlen, Real & minlen, Real & maxphi) const;
    
    /// reduce gap by means of repeated projection
    Real reproject(int niter, Real maxdst, Real dtol);
    
    /// replace position in mesh by mean location on surfaces
    void mesh2surface(); 
    
  private:
    
    /// for now, a node may be on max three surfaces
    const MeshComponent *mpp[3];
    
    /// parameter space coordinates on three surfaces
    Vct2 q[3]; 
    
    /// location and normal in physical space
    Vct3 p, nrm;

    /// indicates that one attached intersection was enforced
    bool bEnforced;
};

typedef std::vector<TTiNode> TTiNodeArray;

#endif
