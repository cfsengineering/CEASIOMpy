
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
 
#ifndef SURF_CASCADEMESH_H
#define SURF_CASCADEMESH_H

#include "surface.h"

/** Specialized semi-structured triangle mesh generator.
 *
 * CascadeMesh starts with a grid of points which typically contains a set
 * of finely discretized lines following the chord (u-coordinate) of a wing,
 * and repeatedly inserts points between these lines in order to achieve a
 * prescribed triangle stretch ratio.
 *
 * \ingroup meshgen
 * \sa Surface
*/
class CascadeMesh
{
  public:
    
    /// empty cascade
    CascadeMesh() : m_psf(0), m_nrows(0), m_ncols(0),
      m_maxkinsert(5), m_gentris(true) {}

    /// start with grid g
    CascadeMesh(const Surface *srf, const PointGrid<2> & g);
    
    /// generate mesh with stretch below limit
    void generate(Real stretchlimit = 20., uint kmax = 5,
                  bool generateTriangles = true);
    
    /// access uv-plane points after mesh generation
    const PointList<2> uvpoints() const {return m_ppt;}

    /// export mesh after processing
    void exportMesh(PointList<2> & qts, Indices & tri) const;
    
    /// export mesh after processing
    void exportMesh(PointList<2> & qts, PointList<3> & pts, 
                    Indices & tri) const;
    
  private:
    
    /// initialize from grid
    void init(const PointGrid<2> & g);
    
    /// access point of the original grid
    const Vct2 & qgrid(uint i, uint j) const {
      assert(i < m_nrows and j < m_ncols);
      return m_ppt[j*m_nrows + i];
    }
    
    /// access point of the original grid
    const Vct3 & pgrid(uint i, uint j) const {
      assert(i < m_nrows and j < m_ncols);
      return m_vtx[j*m_nrows + i];
    }
    
    /// insert point and return index
    uint injectPoint(const Vct2 & q) {
      m_ppt.push_back(q);
      m_vtx.push_back( m_psf->eval(q[0], q[1]) );
      return m_ppt.size()-1;
    }
    
    /// insert 2^k - 1 points in row irow
    void injectPoints(uint irow, uint jcol, uint k, Indices & a);

    /// insert 2^k - 1 points in row irow, do not create triangles
    void injectPoints(uint irow, uint jcol, uint k);
    
    /// generate a single triangles, flip direction if necessary
    void addTriangle(uint a, uint b, uint c); 
    
    /// generate triangles for a block
    void addBlock23(const uint a[2], const uint b[3]);
    
    /// generate triangles for a block
    void addBlock22(const uint a[2], const uint b[2]);
    
    /// determine actual stretch ratio of a single patch
    Real stretchp(uint irow, uint jcol) const;
    
    /// determine worst stretch at vertex row
    Real stretch(uint irow, uint jcol) const;
    
    /// wrap distance for column jcol
    Real wrap(uint jcol) const;
    
    /// refine a single column
    void processColumn(uint jcol, Real mxst);
    
  private:
    
    /// list of points in parameter plane
    PointList<2> m_ppt;
    
    /// points in 3D space
    PointList<3> m_vtx;
    
    /// surface to use
    const Surface *m_psf;
    
    /// dimensions of the grid used for initialization
    uint m_nrows, m_ncols;
    
    /// triangles
    Indices m_itri;
    
    /// maximum allowed insertion level
    uint m_maxkinsert;

    /// whether to generate triangles or just points
    bool m_gentris;
};

#endif
