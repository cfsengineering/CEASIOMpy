
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
 
#ifndef GENUA_MXELEMENTTREE_H
#define GENUA_MXELEMENTTREE_H

#include "kdop.h"
#include "implicittree.h"
#include "mxmesh.h"

/** Element search tree for MxMesh.

  \todo
  - Extend nearest() to all element types
  - Test whether bounding volumes can use single precision

  \ingroup mesh
  \sa MxMesh
*/
class MxElementTree
{
public:

  typedef Dop3d3<Real> DopType;

  /// empty tree
  MxElementTree() {}

  /// allocate tree for all elements in the entire mesh
  void allocate(MxMeshPtr pm, uint mincount = 8);

  /// allocate tree for sections listed
  void allocateSections(MxMeshPtr pm, const Indices & sects, uint mincount = 8);

  /// sort entire tree, computes bounding volumes
  void sort();

  /// access minimum element count per node
  uint minElemCount() const {return itree.minSize();}

  /// number of elements searched
  uint nelements() const {return elix.size();}

  /// access stored mesh
  MxMeshPtr mesh() {return pmx;}

  /// access bounding volume
  DopType & dop(uint k) {
    assert(k < bvol.size());
    return bvol[k];
  }

  /// access mesh node
  const Vct3 & point(uint k) const {return pmx->node(k);}

  /// access element mapping
  uint mappedIndex(uint k) const {
    assert(k < elix.size());
    return elix[k];
  }

  /// access element vertices through mapping
  const uint *mappedElement(uint k, uint & nv, uint & isec) const {
    assert(pmx);
    return pmx->globalElement(elix[k], nv, isec);
  }

  /// locate surface element which is nearest to point p
  uint nearest(const Vct3 & p) const;

  /// find all surface elements within radius r of p
  bool find(const Vct3 & p, Real radius, Indices & eix) const;

private:

  /// determine distance of p from element k
  Real elementDistance(const Vct3 & p, uint k) const;

  /// distance of p from Tri3
  Real edTri3(const Vct3 & p, const uint *vi) const;

  template <int N>
  Real edMultiTri3(const Vct3 &p, const uint map[], const uint vi[]) const
  {
    Real mindst = std::numeric_limits<Real>::max();
    uint w[3];
    for (int i=0; i<N; ++i) {
      for (int k=0; k<3; ++k)
        w[k] = vi[ map[3*i+k] ];
      Real dsq = this->edTri3(p, w);
      mindst = std::min(dsq, mindst);
    }
    return mindst;
  }

private:

  /// pointer to mesh to use
  MxMeshPtr pmx;

  /// binary tree
  ImplicitTree itree;

  /// element indices used in tree
  Indices elix;

  /// bounding volumes for nodes
  std::vector<DopType> bvol;
};

/** Element seach tree for deformation mapping.
 *
 * This is a specialized search tree which is used to map surface data from
 * a structural mesh composed of different surface (shell or membrane) elements
 * to a set of points. The latter points are usually nodes of an aerodynamic
 * mesh, but could also serve a different purpose.
 *
 * As this class is meant to be used with very large datasets, it is currently
 * written to use single precision computations in order to save space and/or
 * allow a larger portion of the data structures to fit into cache.
 *
 * \ingroup mesh
 * \sa MxMesh
 */
class MxTriTree
{
public:

  typedef Dop3d3<float> DopType;

  struct Subset {
    Indices elementList;
    uint isection;
    bool operator== (const Subset &a) const {return isection == a.isection;}
    bool operator< (const Subset &a) const {return isection < a.isection;}
    bool operator< (uint a) const {return isection < a;}
  };

  typedef std::vector<Subset> SubsetArray;

  // only here because MSVC 2008 does not find the operator< in struct Subset
  struct SubsetCompare {
    bool operator() (const Subset &a, const Subset &b) const {
      return a.isection < b.isection;
    }
    bool operator() (const Subset &a, uint b) const {
      return a.isection < b;
    }
    bool operator() (uint a, const Subset &b) const {
      return a < b.isection;
    }
  };

  /// empty tree
  MxTriTree(uint mincount = 4) : m_mincount(mincount) {}

  /// gather all surface elements (shell elements)
  void build(const MxMesh &msh);

  /// gather elements from specified sections
  void build(const MxMesh &msh, const Indices &sections);

  /// gather specified elements from one section
  void build(const MxMesh &msh, const SubsetArray &sba);

  /// create tree from raw triangle data
  void build(const PointList<3,float> &pts, const Indices &tri);

  /// create tree from raw triangle data
  void build(const PointList<3,double> &pts, const Indices &tri);

  /// access set of global node indices used
  const Indices & globalNodes() const {return m_gnix;}

  /// identify triangle nearest to p (thread-safe)
  uint nearestTriangle(const Vct3 & p) const {return nearestTriangle(Vct3f(p));}

  /// identify triangle nearest to p (thread-safe)
  uint nearestTriangle(const Vct3f & pf) const;

  /// determine projection coefficients for a single point (thread-safe)
  bool projection(const Vct3 &p, uint nodes[], float coef[]) const;

  /// assemble sparse mapping operator
  void projection(const PointList<3> &vtx, const Indices &imap,
                  CsrMatrix<float,1> &op, uint ncol = 0) const;

  /// true if no triangles present in tree
  bool empty() const {return m_tri.empty();}

  /// number of triangles
  uint ntriangles() const {return m_tri.size()/3;}

  /// access vertex indices of triangle k
  const uint *vertices(uint k) const {
    assert(3*k+2 < m_tri.size());
    return &m_tri[3*k];
  }

  /// number of vertices stored
  uint nvertices() const {return m_vtx.size();}

  /// access vertex k
  const Vct3f & vertex(uint k) const {return m_vtx[k];}

  /// access bounding volume for a single node
  DopType & dop(uint k) {
    assert(k < m_dop.size());
    return m_dop[k];
  }

  /// access bounding volume for a single node
  const DopType & dop(uint k) const {
    assert(k < m_dop.size());
    return m_dop[k];
  }

  /// triangle index from tree node index
  uint triangleIndex(uint k) const {return m_itree.index(k);}

  /// global element index from triangle index
  uint globalElement(uint itri) const {
    assert(itri < m_gelix.size());
    return m_gelix[itri];
  }

  /// access index offset range for node k
  void offsetRange(uint k, uint & beg, uint & end) const {
    m_itree.offsetRange(k, beg, end);
  }

  /// test whether node inode is a leaf node
  bool leaf(uint inode) const {
    return m_itree.rightChild(inode) >= m_dop.size();
  }

  /// left child of node inode
  uint leftChild(uint inode) const { return m_itree.leftChild(inode); }

  /// left child of node inode
  uint rightChild(uint inode) const { return m_itree.rightChild(inode); }

  /// minimum number of elements in node
  uint minElemCount() const {return m_mincount;}

  /// remove all triangles
  void clear();

  /// write projection surface as a mesh (for debugging)
  void dump(const std::string &fname) const;

private:

  /// allocate and sort tree
  void sort();

  /// split all elements of a given section into triangles
  void splitElements(const MxMesh &msh, uint isec,
                     const Indices &elix = Indices());

  /// distance of point to its projection on triangle
  float tridist(uint itri, const Vct3f &pf) const;

private:

  /// vertices indexed by triangles
  PointList<3,float> m_vtx;

  /// triangles vertices mapping m_vtx
  Indices m_tri;

  /// global node indices of the vertices in m_vtx
  Indices m_gnix;

  /// global element indices for the triangles in m_tri
  Indices m_gelix;

  /// balanced binary tree
  ImplicitTree m_itree;

  /// bounding volumes
  std::vector<DopType> m_dop;

  /// minimum number of triangles in node
  uint m_mincount;
};

#endif // MXELEMENTTREE_H
